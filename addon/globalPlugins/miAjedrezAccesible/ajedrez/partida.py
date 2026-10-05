# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Estado de una partida: tablero, historial de jugadas y final."""

from dataclasses import dataclass
from enum import StrEnum

import chess

from . import anunciador
from .idioma import _
from .notacion import ErrorJugada, san_en_espanol


@dataclass(frozen=True)
class RegistroJugada:
	jugada: chess.Move
	numero: int
	color: chess.Color
	descripcion: str
	san: str

	def texto_planilla(self) -> str:
		# Translators: one line of the score sheet, for example "1. White knight from g1 to f3. (Nf3)".
		return _("{number}. {description} ({notation})").format(
			number=self.numero,
			description=self.descripcion,
			notation=self.san,
		)


class Motivo(StrEnum):
	"""Finales que no deciden las reglas del tablero."""

	ACUERDO = "acuerdo"
	ABANDONO = "abandono"
	TIEMPO = "tiempo"
	# Final leído de un PGN ajeno: solo se conoce el resultado.
	RESULTADO = "resultado"


@dataclass(frozen=True)
class FinalAcordado:
	motivo: Motivo
	# Quien abandona o se queda sin tiempo; None en las tablas por acuerdo.
	color: chess.Color | None
	# Como en PGN: «1-0», «0-1» o «1/2-1/2».
	resultado: str
	texto: str


def texto_final_acordado(motivo: Motivo, color: chess.Color | None, resultado: str) -> str:
	if motivo is Motivo.ACUERDO:
		# Translators: announced when both players agree to a draw.
		return _("Draw by agreement.")
	if motivo is Motivo.ABANDONO:
		if color == chess.WHITE:
			# Translators: announced when white resigns.
			return _("White resigns. Black wins.")
		# Translators: announced when black resigns.
		return _("Black resigns. White wins.")
	if motivo is Motivo.TIEMPO:
		if resultado == "1/2-1/2":
			if color == chess.WHITE:
				# Translators: announced when white runs out of time but black has no mating material.
				return _("White's time is up, but black cannot checkmate: draw.")
			# Translators: announced when black runs out of time but white has no mating material.
			return _("Black's time is up, but white cannot checkmate: draw.")
		if color == chess.WHITE:
			# Translators: announced when white runs out of time.
			return _("White's time is up. Black wins.")
		# Translators: announced when black runs out of time.
		return _("Black's time is up. White wins.")
	if resultado == "1-0":
		# Translators: final result of a loaded game that ended without checkmate on the board.
		return _("White wins.")
	if resultado == "0-1":
		# Translators: final result of a loaded game that ended without checkmate on the board.
		return _("Black wins.")
	# Translators: final result of a loaded game that ended in a draw.
	return _("Draw.")


class Partida:
	def __init__(self, fen: str = chess.STARTING_FEN) -> None:
		self.tablero = chess.Board(fen)
		self.historial: list[RegistroJugada] = []
		# Final que no decide el tablero: tablas por acuerdo, abandono o tiempo.
		self.final_acordado: FinalAcordado | None = None

	@property
	def turno(self) -> chess.Color:
		return self.tablero.turn

	@property
	def resultado(self) -> chess.Outcome | None:
		# claim_draw=True: la triple repetición y la regla de 50 jugadas terminan la partida
		# sin que nadie tenga que reclamarlas.
		return self.tablero.outcome(claim_draw=True)

	@property
	def terminada(self) -> bool:
		return self.final_acordado is not None or self.resultado is not None

	@property
	def en_curso(self) -> bool:
		"""Hay jugadas hechas y la partida no ha terminado: cerrarla perdería algo."""
		return bool(self.historial) and not self.terminada

	def texto_final(self) -> str:
		if self.final_acordado is not None:
			return self.final_acordado.texto
		resultado = self.resultado
		return anunciador.describir_final(resultado) if resultado else ""

	def destinos_legales(self, origen: chess.Square) -> set[chess.Square]:
		if self.terminada:
			return set()
		return {j.to_square for j in self.tablero.legal_moves if j.from_square == origen}

	def requiere_coronacion(self, origen: chess.Square, destino: chess.Square) -> bool:
		return self.tablero.is_legal(chess.Move(origen, destino, promotion=chess.QUEEN))

	def jugar(self, jugada: chess.Move) -> str:
		"""Hace una jugada legal y devuelve el anuncio completo."""
		if self.terminada:
			# Translators: error when trying to move after the game has ended.
			raise ErrorJugada(_("The game is over."))
		if not self.tablero.is_legal(jugada):
			# Translators: error when a move is not allowed in the current position.
			raise ErrorJugada(_("That move is not possible in this position."))
		registro = RegistroJugada(
			jugada=jugada,
			numero=self.tablero.fullmove_number,
			color=self.tablero.turn,
			descripcion=anunciador.describir_jugada(self.tablero, jugada),
			san=san_en_espanol(self.tablero, jugada),
		)
		self.tablero.push(jugada)
		self.historial.append(registro)
		return f"{anunciador.texto_jugada(registro.descripcion, registro.san)} {self.texto_situacion()}"

	def texto_situacion(self) -> str:
		"""Lo que se dice tras una jugada: el final, o el jaque y a quién le toca."""
		if self.terminada:
			return self.texto_final()
		partes: list[str] = []
		if self.tablero.is_check():
			# Translators: announced after a move that gives check.
			partes.append(_("Check."))
		partes.append(anunciador.texto_turno(self.turno))
		return " ".join(partes)

	def deshacer(self, cantidad: int = 1) -> str | None:
		"""Deshace las últimas jugadas. Devuelve el anuncio, o None si no hay tantas jugadas."""
		if cantidad < 1 or len(self.historial) < cantidad:
			return None
		registro = self.historial[-1]
		for _jugada in range(cantidad):
			self.historial.pop()
			self.tablero.pop()
		self.final_acordado = None
		if cantidad == 1:
			# Translators: announced after undoing a move; followed by whose turn it is.
			texto = _("Move undone: {move}").format(move=registro.descripcion)
		else:
			# Translators: announced after undoing your move and the computer's reply;
			# followed by whose turn it is.
			texto = _("Last two moves undone.")
		return f"{texto} {anunciador.texto_turno(self.turno)}"

	def ultima_jugada(self) -> chess.Move | None:
		return self.historial[-1].jugada if self.historial else None

	@property
	def resultado_pgn(self) -> str:
		"""Resultado como en PGN: «1-0», «0-1», «1/2-1/2», o «*» si no ha terminado."""
		if self.final_acordado is not None:
			return self.final_acordado.resultado
		resultado = self.resultado
		return resultado.result() if resultado else "*"

	def terminar(self, motivo: Motivo, color: chess.Color | None, resultado: str) -> str:
		self.final_acordado = FinalAcordado(
			motivo,
			color,
			resultado,
			texto_final_acordado(motivo, color, resultado),
		)
		return self.final_acordado.texto

	def acordar_tablas(self) -> str:
		return self.terminar(Motivo.ACUERDO, None, "1/2-1/2")

	def abandonar(self, color: chess.Color) -> str:
		return self.terminar(Motivo.ABANDONO, color, "0-1" if color == chess.WHITE else "1-0")

	def perder_por_tiempo(self, color: chess.Color) -> str:
		"""Se acabó el tiempo de `color`: pierde, salvo que el rival no pueda dar mate (tablas)."""
		if self.tablero.has_insufficient_material(not color):
			resultado = "1/2-1/2"
		else:
			resultado = "0-1" if color == chess.WHITE else "1-0"
		return self.terminar(Motivo.TIEMPO, color, resultado)

	def texto_estado(self) -> str:
		"""Resumen de la situación: turno o final, número de jugada, última jugada y jaque."""
		partes: list[str] = []
		if self.terminada:
			partes.append(self.texto_final())
		else:
			partes.append(anunciador.texto_turno(self.turno))
			# Translators: current move number of the game.
			partes.append(_("Move {number}.").format(number=self.tablero.fullmove_number))
			if self.tablero.is_check():
				# Translators: announced when the side to move is in check.
				partes.append(_("In check."))
		if self.historial:
			# Translators: the last move played, followed by its description.
			partes.append(_("Last move: {move}").format(move=self.historial[-1].descripcion))
		else:
			# Translators: announced when no move has been played yet.
			partes.append(_("No moves yet."))
		return " ".join(partes)

	def planilla(self) -> list[str]:
		return [r.texto_planilla() for r in self.historial]
