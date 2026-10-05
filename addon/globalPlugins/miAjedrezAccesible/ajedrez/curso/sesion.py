# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Lo que pasa durante un ejercicio: casillas elegidas, jugadas, manzanas, estrellas y pistas."""

import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import chess

from .. import anunciador
from ..idioma import _, ngettext
from ..partida import Partida
from . import guerra_peones, objetivos
from .modelo import Ejercicio, TipoEjercicio


class Sonido(StrEnum):
	MANZANA = "manzana"
	EXITO = "exito"
	LECCION = "leccion"


@dataclass(frozen=True)
class Resultado:
	texto: str
	completado: bool = False
	sonido: Sonido | None = None
	estrellas: int | None = None
	# Jugada equivocada en un problema (se deshace y el problema cuenta como fallado).
	fallo: bool = False


class PartidaLeccion(Partida):
	"""Partida sin rival ni final: tras cada jugada de las blancas vuelven a jugar las blancas.

	Las reglas de final de partida no se aplican: con un alfil solo, por ejemplo,
	python-chess diría «material insuficiente».
	"""

	@property
	def resultado(self) -> chess.Outcome | None:
		return None

	@property
	def terminada(self) -> bool:
		return False

	def texto_situacion(self) -> str:
		# Sin turno ni final; solo se avisa del jaque y del mate (si hay rey negro).
		if objetivos.es_mate(self.tablero):
			# Translators: announced after a move that gives checkmate in a lesson.
			return _("Checkmate.")
		if self.tablero.is_check():
			# Translators: announced after a move that gives check.
			return _("Check.")
		return ""

	def jugar(self, jugada: chess.Move) -> str:
		anuncio = super().jugar(jugada).strip()
		# Las piezas negras no se mueven: se pasa el turno sin jugar.
		self.tablero.push(chess.Move.null())
		return anuncio

	def deshacer_ultima(self) -> None:
		"""Deshace la última jugada de las blancas (y el turno que se pasó después)."""
		if not self.historial:
			return
		self.tablero.pop()
		self.tablero.pop()
		self.historial.pop()


class PartidaGuerra(Partida):
	"""Guerra de peones: las negras sí juegan, pero las reglas de final las decide la sesión
	(sin reyes, python-chess vería «ahogado» donde aquí pierde quien no puede mover)."""

	@property
	def resultado(self) -> chess.Outcome | None:
		return None

	@property
	def terminada(self) -> bool:
		return False

	def texto_situacion(self) -> str:
		return ""


def texto_rival(color: chess.Color, anuncio: str) -> str:
	"""Anuncio de la respuesta del rival: «Negras: …» o «Blancas: …»."""
	if color == chess.WHITE:
		# Translators: announcement of white's reply in a puzzle, for example "White: white king from g1 to h1."
		return _("White: {move}").format(move=anuncio)
	return _("Black: {move}").format(move=anuncio)


def texto_animo(elegir: Callable[[list[str]], str] = random.choice) -> str:
	return elegir(
		[
			# Translators: praise said when an exercise of the course is solved.
			_("Very good!"),
			# Translators: praise said when an exercise of the course is solved.
			_("Excellent!"),
			# Translators: praise said when an exercise of the course is solved.
			_("That's it!"),
			# Translators: praise said when an exercise of the course is solved.
			_("Perfect!"),
			# Translators: praise said when an exercise of the course is solved.
			_("You did it!"),
		],
	)


def texto_estrellas(estrellas: int) -> str:
	if estrellas >= 3:
		# Translators: said when an exercise is solved with the fewest possible moves.
		return _("With the fewest moves, amazing! Three stars.")
	if estrellas == 2:
		# Translators: said when an exercise is solved with a few extra moves.
		return _("You earned two stars. Try with fewer moves to get three.")
	# Translators: said when an exercise is solved with many extra moves.
	return _("You earned one star. Try with fewer moves to get more.")


def texto_direcciones(actual: chess.Square, buscada: chess.Square) -> str:
	"""Cómo llegar de una casilla a otra: «dos columnas a la derecha y una fila más arriba»."""
	columnas = chess.square_file(buscada) - chess.square_file(actual)
	filas = chess.square_rank(buscada) - chess.square_rank(actual)
	partes: list[str] = []
	if columnas > 0:
		# Translators: direction to a square; {n} is a number of files (columns).
		partes.append(
			ngettext("one column to the right", "{n} columns to the right", columnas).format(n=columnas),
		)
	elif columnas < 0:
		# Translators: direction to a square; {n} is a number of files (columns).
		partes.append(
			ngettext("one column to the left", "{n} columns to the left", -columnas).format(n=-columnas),
		)
	if filas > 0:
		# Translators: direction to a square; {n} is a number of ranks (rows).
		partes.append(ngettext("one row up", "{n} rows up", filas).format(n=filas))
	elif filas < 0:
		# Translators: direction to a square; {n} is a number of ranks (rows).
		partes.append(ngettext("one row down", "{n} rows down", -filas).format(n=-filas))
	return anunciador.unir_lista(partes)


def texto_estrellas_casillas(estrellas: int) -> str:
	if estrellas >= 3:
		# Translators: said when a practice square is found at the first attempt and without hints.
		return _("At the first attempt! Three stars.")
	if estrellas == 2:
		# Translators: said when a practice square is found after a mistake or a hint.
		return _("You earned two stars.")
	# Translators: said when a practice square is found after several mistakes or hints.
	return _("You earned one star. Keep practicing!")


def texto_orientacion(actual: chess.Square, buscada: chess.Square) -> str:
	"""«Estás en c4. Busca e4: está dos columnas a la derecha.»"""
	# Translators: guidance when Enter is pressed on a wrong square, for example
	# "You are on c4. Look for e4: it is two columns to the right."
	return _("You are on {current}. Look for {target}: it is {directions}.").format(
		current=chess.square_name(actual),
		target=chess.square_name(buscada),
		directions=texto_direcciones(actual, buscada),
	)


class SesionEjercicio:
	def __init__(self, ejercicio: Ejercicio, azar: random.Random | None = None) -> None:
		self.ejercicio = ejercicio
		self.azar = azar or random.Random()
		# En los mates las negras se defienden: es una partida normal. En la guerra de peones
		# juegan con sus propias reglas. En el resto, no juegan.
		fen = ejercicio.tablero().fen()
		self.partida: Partida
		if ejercicio.tipo in (TipoEjercicio.MATE, TipoEjercicio.PARTIDA_ESCRITA, TipoEjercicio.PROBLEMA):
			self.partida = Partida(fen)
		elif ejercicio.tipo is TipoEjercicio.GUERRA_PEONES:
			self.partida = PartidaGuerra(fen)
		else:
			self.partida = PartidaLeccion(fen)
		self.manzanas: set[chess.Square] = set(ejercicio.manzanas)
		self.visitadas: set[chess.Square] = set()
		self.jugadas = 0
		self.completado = False
		self.estrellas: int | None = None
		self._pistas_dadas = 0
		# Casillas equivocadas en los ejercicios de casillas.
		self.errores = 0
		# Paso del guion en las partidas escritas y en los problemas.
		self.paso = 0
		# Problemas: la pista dijo la jugada (cuenta como fallado).
		self.vio_jugada = False
		self._jugar_previa()

	def _jugar_previa(self) -> None:
		"""En los problemas, el rival hace su jugada antes de que empiece quien resuelve."""
		if self.ejercicio.jugada_previa:
			self.partida.jugar(chess.Move.from_uci(self.ejercicio.jugada_previa))

	@property
	def fallado(self) -> bool:
		"""Un problema con alguna jugada equivocada o resuelto con la jugada dicha por la pista."""
		return self.errores > 0 or self.vio_jugada

	@property
	def es_de_casillas(self) -> bool:
		"""Ejercicios en los que se elige una casilla con Intro, sin mover piezas."""
		return self.ejercicio.tipo in (TipoEjercicio.IR_A, TipoEjercicio.VISITAR)

	def tiene_manzana(self, casilla: chess.Square) -> bool:
		return casilla in self.manzanas

	# Ejercicios de casillas.

	def elegir_casilla(self, casilla: chess.Square) -> Resultado:
		respuestas = self.ejercicio.respuestas
		nombre = chess.square_name(casilla)
		if self.ejercicio.tipo is TipoEjercicio.IR_A:
			if casilla in respuestas:
				return self._completar()
			self.errores += 1
			if len(respuestas) == 1:
				return Resultado(texto_orientacion(casilla, next(iter(respuestas))))
			# Translators: said when Enter is pressed on a wrong square and several answers are valid.
			return Resultado(
				_("{square} is not one of them. Press F6 if you need a hint.").format(square=nombre),
			)
		# Visitar varias casillas.
		if casilla not in respuestas:
			self.errores += 1
			# Translators: said when Enter is pressed on a square that is not one of the squares to visit.
			return Resultado(
				_("{square} is not one of the squares you are looking for.").format(square=nombre),
			)
		if casilla in self.visitadas:
			# Translators: said when a square to visit is chosen again.
			return Resultado(_("You already visited {square}.").format(square=nombre))
		self.visitadas.add(casilla)
		faltan = len(respuestas) - len(self.visitadas)
		if faltan == 0:
			return self._completar()
		# Translators: said when one of the squares to visit is found; {n} is how many remain.
		texto = ngettext("{square}! {n} left.", "{square}! {n} left.", faltan).format(square=nombre, n=faltan)
		return Resultado(texto, sonido=Sonido.MANZANA)

	# Ejercicios de jugadas.

	def reiniciar_partida(self) -> None:
		"""Vuelve a la posición inicial del ejercicio, sin cambiar el objeto partida."""
		self.partida.tablero = self.ejercicio.tablero()
		self.partida.historial.clear()
		self.paso = 0
		self._jugar_previa()

	def _tablero_antes(self) -> chess.Board:
		"""Posición antes de la última jugada de las blancas."""
		antes = self.partida.tablero.copy()
		antes.pop()
		if isinstance(self.partida, PartidaLeccion):
			antes.pop()
		return antes

	def _tras_jugada_objetivo(self, jugada: chess.Move, anuncio: str) -> Resultado:
		e = self.ejercicio
		assert e.objetivo is not None
		cumple, explicacion = objetivos.evaluar(
			self._tablero_antes(),
			jugada,
			e.objetivo,
			e.casilla,
			e.forma,
			e.jugadas,
		)
		if cumple:
			final = self._completar()
			return Resultado(f"{anuncio} {final.texto}", True, final.sonido, final.estrellas)
		self.errores += 1
		if isinstance(self.partida, PartidaLeccion):
			self.partida.deshacer_ultima()
		# Translators: said after a wrong move in an exercise; the move is taken back.
		otra_vez = _("Try again.")
		return Resultado(f"{anuncio} {e.mensaje_error or explicacion} {otra_vez}")

	def _tras_jugada_mate(self, jugada: chess.Move, anuncio: str) -> Resultado:
		tablero = self.partida.tablero
		if objetivos.es_mate(tablero):
			final = self._completar()
			return Resultado(f"{anuncio} {final.texto}", True, final.sonido, final.estrellas)
		jugadas_hechas = sum(1 for r in self.partida.historial if r.color == chess.WHITE)
		# Translators: said when the moves of a mate exercise run out; the position is reset.
		no_fue_mate = _("That was not checkmate. Try again from the start.")
		if objetivos.es_ahogado(tablero):
			self._fallar_mate()
			# Translators: said when a mate exercise ends in stalemate; the position is reset.
			ahogado = _("Stalemate! That would be a draw. Try again from the start.")
			return Resultado(f"{anuncio} {ahogado}")
		if jugadas_hechas >= self.ejercicio.jugadas_mate:
			self._fallar_mate()
			return Resultado(f"{anuncio} {no_fue_mate}")
		respuesta, evita = objetivos.defensa(tablero.copy())
		if respuesta is None:
			self._fallar_mate()
			return Resultado(f"{anuncio} {no_fue_mate}")
		if evita:
			nombre = anunciador.describir_jugada(tablero, respuesta)
			self._fallar_mate()
			# Translators: said when black can defend against the mate; {move} is black's defence.
			texto = _(
				"With that move black defends: {move} And then there is no checkmate. Try again from the start.",
			)
			return Resultado(f"{anuncio} {texto.format(move=nombre)}")
		anuncio_negras = self.partida.jugar(respuesta)
		# Translators: announcement of black's reply in a mate exercise, for example "Black: black king from h8 to g8."
		negras = _("Black: {move}").format(move=anuncio_negras)
		return Resultado(f"{anuncio} {negras}")

	def _fallar_mate(self) -> None:
		self.errores += 1
		self.reiniciar_partida()

	def _tras_jugada_guerra(self, jugada: chess.Move, anuncio: str) -> Resultado:
		tablero = self.partida.tablero
		if jugada.promotion is not None or guerra_peones.sin_jugadas(tablero):
			if jugada.promotion is not None:
				# Translators: said when the learner wins the pawn war by promoting.
				motivo = _("You promoted first: you win the pawn war!")
			else:
				# Translators: said when the learner wins the pawn war because black cannot move.
				motivo = _("Black has no moves left: you win the pawn war!")
			final = self._completar()
			return Resultado(f"{anuncio} {motivo} {final.texto}", True, final.sonido, final.estrellas)
		respuesta = guerra_peones.elegir_jugada(tablero.copy(), self.azar)
		if respuesta is None:
			final = self._completar()
			return Resultado(f"{anuncio} {final.texto}", True, final.sonido, final.estrellas)
		anuncio_negras = self.partida.jugar(respuesta)
		# Translators: announcement of black's reply in a pawn war, for example "Black: black pawn from d7 to d5."
		negras = _("Black: {move}").format(move=anuncio_negras)
		if respuesta.promotion is not None or guerra_peones.sin_jugadas(self.partida.tablero):
			self.errores += 1
			self.reiniciar_partida()
			if respuesta.promotion is not None:
				# Translators: said when black wins the pawn war; the game starts again.
				motivo = _("Black promoted first. Let's play again from the start!")
			else:
				# Translators: said when the learner has no moves in the pawn war; the game starts again.
				motivo = _("You have no moves left, so black wins. Let's play again from the start!")
			return Resultado(f"{anuncio} {negras} {motivo}")
		return Resultado(f"{anuncio} {negras}")

	def texto_paso(self) -> str:
		"""En una partida escrita, la jugada que se pide ahora, dicha con palabras."""
		guion = self.ejercicio.guion
		if self.ejercicio.tipo is not TipoEjercicio.PARTIDA_ESCRITA or self.paso >= len(guion):
			return ""
		esperada = chess.Move.from_uci(guion[self.paso][0])
		# Translators: the move requested in a written game, for example "Your move: white pawn from e2 to e4."
		return _("Your move: {move}").format(move=anunciador.describir_jugada(self.partida.tablero, esperada))

	def instruccion_actual(self) -> str:
		paso = self.texto_paso()
		return f"{self.ejercicio.instruccion} {paso}" if paso else self.ejercicio.instruccion

	def _tras_jugada_escrita(self, jugada: chess.Move, anuncio: str) -> Resultado:
		guion = self.ejercicio.guion
		esperada, respuesta = guion[self.paso]
		if jugada.uci() != esperada:
			self.errores += 1
			self.partida.tablero.pop()
			self.partida.historial.pop()
			# Translators: said when another move than the requested one is played in a written game.
			no_es = _("That is not the requested move.")
			return Resultado(f"{anuncio} {no_es} {self.texto_paso()}")
		self.paso += 1
		partes = [anuncio]
		if respuesta is not None:
			anuncio_negras = self.partida.jugar(chess.Move.from_uci(respuesta))
			partes.append(_("Black: {move}").format(move=anuncio_negras))
		if self.paso >= len(guion):
			final = self._completar()
			partes.append(final.texto)
			return Resultado(" ".join(partes), True, final.sonido, final.estrellas)
		partes.append(self.texto_paso())
		return Resultado(" ".join(partes))

	def _tras_jugada_problema(self, jugada: chess.Move, anuncio: str) -> Resultado:
		guion = self.ejercicio.guion
		esperada, respuesta = guion[self.paso]
		# Cualquier mate resuelve el problema, aunque no sea la jugada de la solución.
		if jugada.uci() != esperada and not self.partida.tablero.is_checkmate():
			self.errores += 1
			self.partida.tablero.pop()
			self.partida.historial.pop()
			# Translators: said after a wrong move in a puzzle; the move is taken back.
			no_es = _("That is not the best move.")
			return Resultado(f"{anuncio} {no_es}", fallo=True)
		self.paso += 1
		# Tras acertar, las pistas vuelven a empezar por la pieza (el tema ya se dijo).
		self._pistas_dadas = min(self._pistas_dadas, 1)
		partes = [anuncio]
		if self.paso >= len(guion) or self.partida.terminada:
			final = self._completar()
			partes.append(final.texto)
			return Resultado(" ".join(partes), True, final.sonido, final.estrellas)
		if respuesta is not None:
			anuncio_rival = self.partida.jugar(chess.Move.from_uci(respuesta))
			partes.append(texto_rival(not self.ejercicio.color, anuncio_rival))
		# Translators: said in a puzzle after a correct move when the solution goes on.
		partes.append(_("Correct! Now find the next move."))
		return Resultado(" ".join(partes))

	def empezar_partida(self) -> Resultado:
		"""El ejercicio de tipo partida se supera al decidir empezarla."""
		return self._completar()

	def tras_jugada(self, jugada: chess.Move, anuncio: str) -> Resultado:
		"""Se llama después de hacer la jugada en `self.partida`."""
		if self.ejercicio.tipo is TipoEjercicio.GUERRA_PEONES:
			return self._tras_jugada_guerra(jugada, anuncio)
		if self.ejercicio.tipo is TipoEjercicio.PARTIDA_ESCRITA:
			return self._tras_jugada_escrita(jugada, anuncio)
		if self.ejercicio.tipo is TipoEjercicio.PROBLEMA:
			return self._tras_jugada_problema(jugada, anuncio)
		if self.ejercicio.tipo is TipoEjercicio.JUGADA:
			return self._tras_jugada_objetivo(jugada, anuncio)
		if self.ejercicio.tipo is TipoEjercicio.MATE:
			return self._tras_jugada_mate(jugada, anuncio)
		self.jugadas += 1
		partes = [anuncio]
		sonido = None
		if jugada.to_square in self.manzanas:
			self.manzanas.discard(jugada.to_square)
			sonido = Sonido.MANZANA
			if self.manzanas:
				# Translators: said when an apple is collected; {n} is how many apples remain.
				partes.append(
					ngettext("Apple! {n} left.", "Apple! {n} left.", len(self.manzanas)).format(
						n=len(self.manzanas),
					),
				)
			else:
				# Translators: said when the last apple is collected.
				partes.append(_("Apple!"))
		if self.ejercicio.tipo is TipoEjercicio.CORONAR and jugada.promotion:
			if jugada.promotion == chess.QUEEN:
				partes.append(self.ejercicio.corona_dama)
			else:
				partes.append(self.ejercicio.corona_otra)
		if self.objetivo_cumplido():
			final = self._completar()
			partes.append(final.texto)
			return Resultado(" ".join(p for p in partes if p), True, final.sonido, final.estrellas)
		return Resultado(" ".join(p for p in partes if p), sonido=sonido)

	def objetivo_cumplido(self) -> bool:
		tipo = self.ejercicio.tipo
		if tipo is TipoEjercicio.CORONAR:
			ultima = self.partida.ultima_jugada()
			return ultima is not None and ultima.promotion is not None
		if tipo is not TipoEjercicio.MANZANAS:
			return False
		if self.manzanas:
			return False
		for casilla in self.ejercicio.capturar or ():
			pieza = self.partida.tablero.piece_at(casilla)
			if pieza is not None and pieza.color == chess.BLACK:
				return False
		return True

	def _completar(self) -> Resultado:
		self.completado = True
		partes = [texto_animo()]
		if self.ejercicio.da_estrellas:
			self.estrellas = self.calcular_estrellas()
			if self.ejercicio.estrellas_por_intentos:
				partes.append(texto_estrellas_casillas(self.estrellas))
			else:
				partes.append(texto_estrellas(self.estrellas))
		return Resultado(" ".join(partes), True, Sonido.EXITO, self.estrellas)

	def calcular_estrellas(self) -> int:
		if self.ejercicio.estrellas_por_intentos:
			# Las estrellas dependen de los fallos y de las pistas.
			fallos = self.errores + self._pistas_dadas
			return 3 if fallos == 0 else 2 if fallos <= 2 else 1
		minimo = self.ejercicio.minimo or self.jugadas
		if self.jugadas <= minimo:
			return 3
		if self.jugadas <= minimo + 2:
			return 2
		return 1

	# Ayudas.

	def siguiente_pista(self) -> str:
		if self.ejercicio.tipo is TipoEjercicio.PROBLEMA:
			return self._pista_problema()
		pistas = self.ejercicio.pistas
		if not pistas:
			# Translators: said when an exercise has no hints.
			return _("There are no hints for this exercise.")
		pista = pistas[min(self._pistas_dadas, len(pistas) - 1)]
		self._pistas_dadas += 1
		faltan = sorted(self.ejercicio.respuestas - self.visitadas)
		return pista.format(faltan=anunciador.unir_lista([chess.square_name(c) for c in faltan]))

	def _pista_problema(self) -> str:
		"""Primero el tema del problema, luego qué pieza mover y, por último, la jugada."""
		if self.completado or self.paso >= len(self.ejercicio.guion):
			# Translators: said when asking for a hint after a puzzle is solved.
			return _("The puzzle is solved.")
		nivel = self._pistas_dadas
		if nivel == 0 and not self.ejercicio.pistas:
			nivel = 1
		self._pistas_dadas = nivel + 1
		if nivel == 0:
			return self.ejercicio.pistas[0]
		tablero = self.partida.tablero
		esperada = chess.Move.from_uci(self.ejercicio.guion[self.paso][0])
		if nivel == 1:
			pieza = tablero.piece_at(esperada.from_square)
			assert pieza is not None
			# Translators: hint in a puzzle, for example "Move the white knight on e4."
			return _("Move {piece} on {square}.").format(
				piece=anunciador.nombre_pieza_con_articulo(pieza),
				square=chess.square_name(esperada.from_square),
			)
		if not self.ejercicio.ver_jugada:
			self._pistas_dadas = nivel
			# Translators: said when asking for the move as a hint during a puzzle streak.
			return _("In a streak the hint cannot tell you the move. Think about it!")
		self.vio_jugada = True
		# Translators: last hint of a puzzle, for example "The move is: white knight from e4 to f6."
		return _("The move is: {move}").format(move=anunciador.describir_jugada(tablero, esperada))

	def texto_manzanas(self) -> str:
		if self.ejercicio.tipo is not TipoEjercicio.MANZANAS or not self.ejercicio.manzanas:
			# Translators: said when asking for apples in an exercise without apples.
			return _("There are no apples in this exercise.")
		if not self.manzanas:
			# Translators: said when all apples have been collected.
			return _("You collected all the apples.")
		nombres = [chess.square_name(c) for c in sorted(self.manzanas)]
		# Translators: how many apples remain and where; {squares} is a list like "a6 and f6".
		return ngettext("{n} apple left: {squares}.", "{n} apples left: {squares}.", len(nombres)).format(
			n=len(nombres),
			squares=anunciador.unir_lista(nombres),
		)
