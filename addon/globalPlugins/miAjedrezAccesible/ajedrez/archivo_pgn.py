# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Partidas en formato PGN: guardarlas, abrirlas y repasarlas.

Además de las etiquetas estándar, las partidas de MiAjedrezAccesible guardan el modo, el nivel,
el color de la persona y el tiempo que queda en el reloj, para poder continuarlas.
"""

import datetime
import io
from dataclasses import dataclass

import chess
import chess.pgn

from .configuracion import ConfiguracionPartida, EleccionColor, Modo
from .idioma import _
from .notacion import ErrorJugada
from .partida import Motivo, Partida, RegistroJugada
from .reloj import Reloj

EVENTO = "MiAjedrezAccesible"
CABECERA_MODO = "MiAjedrezModo"
CABECERA_NIVEL = "MiAjedrezNivel"
CABECERA_COLOR = "MiAjedrezColor"
CABECERA_RELOJ = "MiAjedrezReloj"
CABECERA_TIEMPO = {chess.WHITE: "MiAjedrezTiempoBlancas", chess.BLACK: "MiAjedrezTiempoNegras"}
CABECERA_FINAL = "MiAjedrezFinal"
CABECERA_FINAL_COLOR = "MiAjedrezFinalColor"
RESULTADOS = ("1-0", "0-1", "1/2-1/2")


def _texto_color(color: chess.Color | None) -> str:
	if color is None:
		return ""
	return EleccionColor.BLANCAS.value if color == chess.WHITE else EleccionColor.NEGRAS.value


def _color_de_texto(texto: str) -> chess.Color | None:
	if texto == EleccionColor.BLANCAS.value:
		return chess.WHITE
	if texto == EleccionColor.NEGRAS.value:
		return chess.BLACK
	return None


def nombres_jugadores(
	configuracion: ConfiguracionPartida,
	color_persona: chess.Color | None,
) -> tuple[str, str]:
	"""Nombres para las etiquetas White y Black."""
	if configuracion.modo is Modo.DOS_PERSONAS or color_persona is None:
		return (
			# Translators: name of the white player in a saved game between two people.
			_("Player 1"),
			# Translators: name of the black player in a saved game between two people.
			_("Player 2"),
		)
	# Translators: name of the person in a saved game against the computer.
	persona = _("Player")
	# Translators: name of the computer in a saved game, for example "Computer, level 3".
	computadora = _("Computer, level {level}").format(level=configuracion.nivel)
	return (persona, computadora) if color_persona == chess.WHITE else (computadora, persona)


def exportar(
	partida: Partida,
	configuracion: ConfiguracionPartida,
	color_persona: chess.Color | None,
	reloj: Reloj | None = None,
	fecha: datetime.date | None = None,
) -> str:
	juego = chess.pgn.Game.from_board(partida.tablero)
	cabeceras = juego.headers
	blancas, negras = nombres_jugadores(configuracion, color_persona)
	cabeceras["Event"] = EVENTO
	cabeceras["Site"] = "-"
	cabeceras["Date"] = (fecha or datetime.date.today()).strftime("%Y.%m.%d")
	cabeceras["Round"] = "-"
	cabeceras["White"] = blancas
	cabeceras["Black"] = negras
	cabeceras["Result"] = partida.resultado_pgn
	cabeceras["TimeControl"] = configuracion.control_tiempo.pgn
	final = partida.final_acordado
	if partida.terminada:
		cabeceras["Termination"] = "Time forfeit" if final and final.motivo is Motivo.TIEMPO else "Normal"
	cabeceras[CABECERA_MODO] = configuracion.modo.value
	cabeceras[CABECERA_NIVEL] = str(configuracion.nivel)
	cabeceras[CABECERA_COLOR] = _texto_color(color_persona)
	cabeceras[CABECERA_RELOJ] = configuracion.reloj
	if reloj is not None:
		for color, nombre in CABECERA_TIEMPO.items():
			cabeceras[nombre] = f"{reloj.tiempo(color):.1f}"
	if final is not None:
		cabeceras[CABECERA_FINAL] = final.motivo.value
		cabeceras[CABECERA_FINAL_COLOR] = _texto_color(final.color)
	return str(juego) + "\n"


@dataclass
class PartidaCargada:
	partida: Partida
	blancas: str
	negras: str
	fecha: str
	# Solo en las partidas guardadas por MiAjedrezAccesible.
	configuracion: ConfiguracionPartida | None
	color_persona: chess.Color | None
	restante: dict[chess.Color, float] | None
	# El archivo tenía jugadas que no se pudieron leer: se cargó hasta donde se pudo.
	incompleta: bool

	@property
	def se_puede_continuar(self) -> bool:
		return self.configuracion is not None and not self.partida.terminada


class _Lector(chess.pgn.GameBuilder):
	"""Anota los errores del archivo sin escribirlos en el registro de NVDA."""

	def handle_error(self, error: Exception) -> None:
		self.game.errors.append(error)


def importar(texto: str) -> PartidaCargada | None:
	"""Lee la primera partida del texto. Devuelve None si no hay ninguna partida."""
	juego = chess.pgn.read_game(io.StringIO(texto), Visitor=_Lector)
	if juego is None:
		return None
	cabeceras = juego.headers
	jugadas = list(juego.mainline_moves())
	es_nuestra = CABECERA_MODO in cabeceras
	if not jugadas and not es_nuestra and "FEN" not in cabeceras:
		return None
	try:
		partida = Partida(juego.board().fen())
	except ValueError:
		return None
	incompleta = bool(juego.errors)
	for jugada in jugadas:
		try:
			partida.jugar(jugada)
		except ErrorJugada:
			incompleta = True
			break
	resultado = cabeceras.get("Result", "*")
	if not partida.terminada and resultado in RESULTADOS:
		motivo_texto = cabeceras.get(CABECERA_FINAL, "")
		motivo = Motivo(motivo_texto) if motivo_texto in Motivo._value2member_map_ else Motivo.RESULTADO
		partida.terminar(motivo, _color_de_texto(cabeceras.get(CABECERA_FINAL_COLOR, "")), resultado)
	configuracion = None
	color_persona = None
	restante = None
	if es_nuestra:
		color_persona = _color_de_texto(cabeceras.get(CABECERA_COLOR, ""))
		try:
			nivel = int(cabeceras.get(CABECERA_NIVEL, "0"))
		except ValueError:
			nivel = 0
		configuracion = ConfiguracionPartida.desde_textos(
			cabeceras.get(CABECERA_MODO, ""),
			_texto_color(color_persona) or EleccionColor.BLANCAS.value,
			nivel,
			cabeceras.get(CABECERA_RELOJ, "sin"),
		)
		if configuracion.modo is Modo.COMPUTADORA and color_persona is None:
			color_persona = chess.WHITE
		if configuracion.modo is Modo.DOS_PERSONAS:
			color_persona = None
		if configuracion.control_tiempo.con_reloj:
			try:
				restante = {color: float(cabeceras[nombre]) for color, nombre in CABECERA_TIEMPO.items()}
			except (KeyError, ValueError):
				restante = None
	return PartidaCargada(
		partida=partida,
		blancas=cabeceras.get("White", "?"),
		negras=cabeceras.get("Black", "?"),
		fecha=cabeceras.get("Date", "?"),
		configuracion=configuracion,
		color_persona=color_persona,
		restante=restante,
		incompleta=incompleta,
	)


def nombre_archivo(momento: datetime.datetime) -> str:
	"""Nombre propuesto al guardar, por ejemplo «Partida 2026-10-03 15.30.pgn»."""
	# Translators: start of the file name proposed when saving a game, for example "Game 2026-10-03 15.30.pgn".
	return _("Game {date}").format(date=momento.strftime("%Y-%m-%d %H.%M")) + ".pgn"


class Repaso:
	"""Recorre una partida terminada o ajena jugada a jugada, hacia delante y hacia atrás."""

	def __init__(self, completa: Partida) -> None:
		self.completa = completa
		self.registros: list[RegistroJugada] = list(completa.historial)
		self.partida = Partida(completa.tablero.root().fen())

	@property
	def indice(self) -> int:
		"""Cuántas jugadas se han hecho en el tablero del repaso."""
		return len(self.partida.historial)

	@property
	def total(self) -> int:
		return len(self.registros)

	def _texto_final(self) -> str:
		if self.indice < self.total or not self.completa.terminada:
			return ""
		# Translators: said when the last move of a reviewed game is reached, followed by the result.
		return _("End of the game: {result}").format(result=self.completa.texto_final())

	def avanzar(self) -> str | None:
		"""Hace la siguiente jugada. Devuelve el anuncio, o None si ya no hay más."""
		if self.indice >= self.total:
			return None
		registro = self.registros[self.indice]
		# El tablero del repaso no aplica los finales acordados: se dicen aparte, al llegar al final.
		anuncio = self.partida.jugar(registro.jugada)
		partes = [f"{registro.numero}. {anuncio}"]
		final = self._texto_final()
		if final and not self.partida.terminada:
			partes.append(final)
		return " ".join(partes)

	def retroceder(self) -> str | None:
		if self.indice == 0:
			return None
		registro = self.partida.historial[-1]
		self.partida.deshacer(1)
		# Translators: said when going back one move while reviewing a game, for example
		# "Back: 12. White knight from g1 to f3."
		return _("Back: {move}").format(move=f"{registro.numero}. {registro.descripcion}")

	def ir_al_principio(self) -> None:
		while self.indice:
			self.partida.deshacer(1)

	def ir_al_final(self) -> None:
		while self.indice < self.total:
			self.partida.jugar(self.registros[self.indice].jugada)

	def texto_estado(self) -> str:
		# Translators: position in a reviewed game, for example "After 12 of 40 moves."
		posicion = _("After {n} of {total} moves.").format(n=self.indice, total=self.total)
		final = self._texto_final()
		partes = [posicion, self.partida.texto_estado()]
		if final and not self.partida.terminada:
			partes.append(final)
		return " ".join(partes)
