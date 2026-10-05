# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Práctica generada del bloque C: capturar, proteger, capturar sin perder la pieza, valor de
las piezas, jaque, salir del jaque, jaque mate, mate con dama y rey, y ataque doble.

Cada generador coloca piezas al azar siguiendo un patrón y comprueba con `objetivos` que el
ejercicio tiene solución y que no todas las jugadas valen. Si no, lo intenta de nuevo.
"""

import random
from collections.abc import Callable
from dataclasses import replace

import chess

from .. import anunciador
from ..idioma import _
from ..notacion import san_en_espanol
from . import objetivos
from .modelo import Ejercicio, TipoEjercicio
from .objetivos import Forma, Objetivo

_INTENTOS = 400
_PIEZAS_MENORES_Y_MAYORES = (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)


class SinEjercicio(Exception):
	"""No se encontró una posición válida tras muchos intentos."""


def _pieza(tipo: chess.PieceType, color: chess.Color) -> chess.Piece:
	return chess.Piece(tipo, color)


def _nombre(tablero: chess.Board, casilla: chess.Square) -> str:
	pieza = tablero.piece_at(casilla)
	assert pieza is not None
	return anunciador.nombre_pieza(pieza)


def _lista_piezas(tablero: chess.Board, casillas) -> str:
	return anunciador.unir_lista(
		[
			anunciador.pieza_en_casilla(tablero.piece_at(c), c)
			for c in sorted(casillas)
			if tablero.piece_at(c)
		],
	)


def _tus_piezas(tablero: chess.Board) -> str:
	"""«Tus piezas: torre blanca en e8 y rey blanco en g1.»"""
	casillas = sorted(chess.SquareSet(tablero.occupied_co[chess.WHITE]))
	# Translators: list of the learner's pieces in a practice exercise.
	return _("Your pieces: {pieces}.").format(pieces=_lista_piezas(tablero, casillas))


def _posicion_legal(tablero: chess.Board) -> bool:
	"""Las negras no pueden empezar en jaque, y los reyes no pueden estar juntos."""
	reyes = [tablero.king(chess.WHITE), tablero.king(chess.BLACK)]
	if None not in reyes and chess.square_distance(*reyes) < 2:
		return False
	for casilla in chess.SquareSet(tablero.pawns):
		if chess.square_rank(casilla) in (0, 7):
			return False
	negras = tablero.copy()
	negras.turn = chess.BLACK
	return not (tablero.king(chess.BLACK) is not None and negras.is_check())


def _ejemplo(tablero: chess.Board, validas: list[chess.Move], azar: random.Random) -> str:
	jugada = azar.choice(validas)
	# Translators: practice hint that shows one correct move, for example "For example: White knight from b1 to c3."
	return _("For example: {move}").format(move=anunciador.describir_jugada(tablero, jugada))


class GeneradorJugadas:
	def __init__(self, azar: random.Random) -> None:
		self.azar = azar

	def _vacia(self, excluir) -> chess.Square:
		while True:
			casilla = self.azar.randrange(64)
			if casilla not in excluir:
				return casilla

	def _intentar(self, crear: Callable[[], Ejercicio | None]) -> Ejercicio:
		for _intento in range(_INTENTOS):
			ejercicio = crear()
			if ejercicio is not None:
				return ejercicio
		raise SinEjercicio

	def _jugada(
		self,
		tablero: chess.Board,
		inicio: chess.Square,
		objetivo: Objetivo,
		instruccion: str,
		pista: str,
		casilla: chess.Square | None = None,
		forma: Forma | None = None,
		jugadas: frozenset[str] = frozenset(),
		mensaje_error: str = "",
		segunda_pista: str | None = None,
	) -> Ejercicio | None:
		"""Crea el ejercicio si es válido: con solución y con al menos una jugada equivocada."""
		if not _posicion_legal(tablero):
			return None
		legales = [j for j in tablero.legal_moves if j.promotion in (None, chess.QUEEN)]
		validas = objetivos.jugadas_que_cumplen(tablero, objetivo, casilla, forma, jugadas)
		if not validas or len(validas) == len(legales):
			return None
		return Ejercicio(
			id="",
			tipo=TipoEjercicio.JUGADA,
			posicion=tablero.board_fen(),
			enroques=tablero.castling_xfen(),
			al_paso=chess.square_name(tablero.ep_square) if tablero.ep_square is not None else "-",
			inicio=inicio,
			objetivo=objetivo,
			casilla=casilla,
			forma=forma,
			jugadas=jugadas,
			mensaje_error=mensaje_error,
			instruccion=instruccion,
			pistas=(pista, segunda_pista or _ejemplo(tablero, validas, self.azar)),
			solucion=validas[0].uci(),
		)

	# Lección 11: proteger.

	def proteger(self, nivel: int) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			tipo = self.azar.choice([chess.KNIGHT, chess.BISHOP, chess.ROOK])
			casilla = self._vacia([])
			tablero.set_piece_at(casilla, _pieza(tipo, chess.WHITE))
			atacantes_posibles = [
				c for c in chess.SQUARES if c != casilla and chess.square_rank(c) not in (0, 7)
			]
			atacante = self.azar.choice(atacantes_posibles)
			tablero.set_piece_at(
				atacante,
				_pieza(self.azar.choice([chess.PAWN, chess.KNIGHT, chess.BISHOP]), chess.BLACK),
			)
			if casilla not in tablero.attacks(atacante) or tablero.attackers(chess.WHITE, casilla):
				return None
			for _ayudante in range(self.azar.choice([1, 2])):
				ayudante = self._vacia(tablero.piece_map())
				tipo_ayudante = self.azar.choice([chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK])
				tablero.set_piece_at(ayudante, _pieza(tipo_ayudante, chess.WHITE))
			if tablero.attackers(chess.WHITE, casilla):
				return None
			forma = Forma.DEFENDER if nivel == 3 else None
			datos = {
				"attacker": anunciador.pieza_en_casilla(tablero.piece_at(atacante), atacante),
				"piece": anunciador.nombre_pieza(tablero.piece_at(casilla)),
				"square": chess.square_name(casilla),
			}
			if forma is Forma.DEFENDER:
				# Translators: practice instruction; {attacker} is like "black knight on f6".
				instruccion = _(
					"The {attacker} attacks your {piece} on {square}. Protect it with another piece, without moving it.",
				).format(**datos)
			else:
				# Translators: practice instruction; {attacker} is like "black knight on f6".
				instruccion = _(
					"The {attacker} attacks your {piece} on {square}. Save it: move it to a safe square, "
					"protect it, or capture the attacker.",
				).format(**datos)
			# Translators: practice hint.
			pista = _("Press X on your piece to hear who attacks it and who defends it.")
			return self._jugada(tablero, casilla, Objetivo.PROTEGER, instruccion, pista, casilla, forma)

		return self._intentar(crear)

	# Lección 12: capturar sin perder la pieza.

	def captura_segura(self, nivel: int) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			tipo = self.azar.choice([chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT])
			casilla = self._vacia([])
			tablero.set_piece_at(casilla, _pieza(tipo, chess.WHITE))
			alcanzables = [c for c in tablero.attacks(casilla) if chess.square_rank(c) not in (0, 7)]
			cantidad = 3 if nivel == 3 else 2
			if len(alcanzables) < cantidad:
				return None
			objetivos_negros = self.azar.sample(alcanzables, cantidad)
			for objetivo in objetivos_negros:
				tablero.set_piece_at(
					objetivo,
					_pieza(self.azar.choice([chess.PAWN, chess.KNIGHT, chess.BISHOP]), chess.BLACK),
				)
			defensor = self._vacia(tablero.piece_map())
			if chess.square_rank(defensor) in (0, 7):
				return None
			tablero.set_piece_at(
				defensor,
				_pieza(self.azar.choice([chess.PAWN, chess.KNIGHT, chess.BISHOP]), chess.BLACK),
			)
			if nivel >= 2:
				otro = self._vacia(tablero.piece_map())
				if chess.square_rank(otro) in (0, 7):
					return None
				tablero.set_piece_at(otro, _pieza(chess.PAWN, chess.BLACK))
			inseguras = [
				j
				for j in tablero.legal_moves
				if tablero.is_capture(j) and objetivos.atacada(objetivos.tras(tablero, j), j.to_square)
			]
			if not inseguras:
				return None
			# Translators: practice instruction.
			instruccion = _(
				"Your {piece} on {square} can capture several pieces. Capture without losing your piece.",
			).format(
				piece=anunciador.nombre_pieza(tablero.piece_at(casilla)),
				square=chess.square_name(casilla),
			)
			# Translators: practice hint.
			pista = _("Press X on each black piece: if it has defenders, be careful.")
			return self._jugada(tablero, casilla, Objetivo.CAPTURA_SEGURA, instruccion, pista)

		return self._intentar(crear)

	# Lección 13: el valor de las piezas.

	def mejor_captura(self, nivel: int) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			tipo = self.azar.choice([chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT])
			casilla = self._vacia([])
			tablero.set_piece_at(casilla, _pieza(tipo, chess.WHITE))
			alcanzables = [c for c in tablero.attacks(casilla) if chess.square_rank(c) not in (0, 7)]
			cantidad = 2 if nivel == 1 else 3
			if len(alcanzables) < cantidad:
				return None
			tipos = self.azar.sample([chess.PAWN, chess.KNIGHT, chess.ROOK, chess.QUEEN], cantidad)
			for objetivo, tipo_negro in zip(self.azar.sample(alcanzables, cantidad), tipos, strict=True):
				tablero.set_piece_at(objetivo, _pieza(tipo_negro, chess.BLACK))
			if len(objetivos.mejores_capturas(tablero)) != 1:
				return None
			# Translators: practice instruction.
			instruccion = _(
				"Your {piece} on {square} can capture several pieces. Capture the one worth the most.",
			).format(
				piece=anunciador.nombre_pieza(tablero.piece_at(casilla)),
				square=chess.square_name(casilla),
			)
			# Translators: practice hint with the values of the pieces.
			pista = _("Remember: pawn 1, knight 3, bishop 3, rook 5, queen 9.")
			return self._jugada(tablero, casilla, Objetivo.MEJOR_CAPTURA, instruccion, pista)

		return self._intentar(crear)

	# Lección 14: el jaque.

	def jaque(self, nivel: int) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			rey_negro = self._vacia([])
			tablero.set_piece_at(rey_negro, _pieza(chess.KING, chess.BLACK))
			tablero.set_piece_at(self._vacia(tablero.piece_map()), _pieza(chess.KING, chess.WHITE))
			piezas = []
			for _p in range(1 if nivel == 1 else 2):
				casilla = self._vacia(tablero.piece_map())
				tablero.set_piece_at(
					casilla,
					_pieza(self.azar.choice(_PIEZAS_MENORES_Y_MAYORES), chess.WHITE),
				)
				piezas.append(casilla)
			if nivel == 3:
				for _p in range(2):
					tablero.set_piece_at(self._vacia(tablero.piece_map()), _pieza(chess.PAWN, chess.BLACK))
			if tablero.is_check():
				return None
			# Translators: practice instruction.
			instruccion = _("Give check to the black king on {square}.").format(
				square=chess.square_name(rey_negro),
			)
			instruccion += " " + _tus_piezas(tablero)
			# Translators: practice hint.
			pista = _("Look for a square from which one of your pieces attacks the king.")
			return self._jugada(tablero, piezas[0], Objetivo.JAQUE, instruccion, pista)

		return self._intentar(crear)

	# Lección 15: salir del jaque.

	def salir_jaque(self, nivel: int) -> Ejercicio:
		forma = {1: Forma.REY, 2: Forma.TAPAR, 3: Forma.CAPTURAR}[nivel]

		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			rey = self._vacia([])
			tablero.set_piece_at(rey, _pieza(chess.KING, chess.WHITE))
			tipo_jaque = self.azar.choice([chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT])
			atacante = self._vacia([rey])
			if chess.square_rank(atacante) in (0, 7) and tipo_jaque == chess.PAWN:
				return None
			tablero.set_piece_at(atacante, _pieza(tipo_jaque, chess.BLACK))
			if rey not in tablero.attacks(atacante):
				return None
			for _p in range(2):
				tablero.set_piece_at(
					self._vacia(tablero.piece_map()),
					_pieza(self.azar.choice(_PIEZAS_MENORES_Y_MAYORES), chess.WHITE),
				)
			tablero.turn = chess.WHITE
			if not tablero.is_check() or len(tablero.checkers()) != 1:
				return None
			datos = {"piece": anunciador.pieza_en_casilla(tablero.piece_at(atacante), atacante)}
			if forma is Forma.REY:
				# Translators: practice instruction; {piece} is like "black rook on e8".
				instruccion = _(
					"The {piece} gives check to your king. Get out of check by moving the king.",
				).format(**datos)
			elif forma is Forma.TAPAR:
				# Translators: practice instruction; {piece} is like "black rook on e8".
				instruccion = _(
					"The {piece} gives check to your king. Get out of check by blocking it.",
				).format(**datos)
			else:
				# Translators: practice instruction; {piece} is like "black rook on e8".
				instruccion = _(
					"The {piece} gives check to your king. Get out of check by capturing it.",
				).format(**datos)
			# Translators: practice hint.
			pista = _(
				"There are three ways out of check: move the king, block the check, or capture the piece.",
			)
			instruccion += " " + _tus_piezas(tablero)
			return self._jugada(tablero, rey, Objetivo.SALIR_JAQUE, instruccion, pista, forma=forma)

		return self._intentar(crear)

	# Lecciones 16 y 17: jaque mate.

	def mate(self, nivel: int, solo_dama: bool = False) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			columna = self.azar.randrange(8)
			rey_negro = chess.square(columna, 7)
			tablero.set_piece_at(rey_negro, _pieza(chess.KING, chess.BLACK))
			patron = (
				"dama"
				if solo_dama
				else {1: "pasillo", 2: "torre_rey", 3: self.azar.choice(["dama", "torre_rey", "pasillo"])}[
					nivel
				]
			)
			if patron == "pasillo":
				for c in (columna - 1, columna, columna + 1):
					if 0 <= c <= 7:
						tablero.set_piece_at(chess.square(c, 6), _pieza(chess.PAWN, chess.BLACK))
				tablero.set_piece_at(self._vacia(tablero.piece_map()), _pieza(chess.KING, chess.WHITE))
				pieza = chess.ROOK
			else:
				rey_blanco = chess.square(columna, 5)
				tablero.set_piece_at(rey_blanco, _pieza(chess.KING, chess.WHITE))
				pieza = chess.QUEEN if patron == "dama" else chess.ROOK
			casilla = self._vacia(tablero.piece_map())
			tablero.set_piece_at(casilla, _pieza(pieza, chess.WHITE))
			if len(objetivos.jugadas_que_cumplen(tablero, Objetivo.MATE)) > 2:
				return None
			# Translators: practice instruction.
			instruccion = _("Give checkmate to the black king on {square}.").format(
				square=chess.square_name(rey_negro),
			)
			instruccion += " " + _tus_piezas(tablero)
			# Translators: practice hint.
			pista = _("Where could the king escape? Give check and close every escape at the same time.")
			return self._jugada(tablero, casilla, Objetivo.MATE, instruccion, pista)

		return self._intentar(crear)

	def mate_en_dos(self) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			columna = self.azar.randrange(8)
			rey_negro = chess.square(columna, 7)
			tablero.set_piece_at(rey_negro, _pieza(chess.KING, chess.BLACK))
			rey_blanco = chess.square(min(7, max(0, columna + self.azar.choice([-2, -1, 0, 1, 2]))), 5)
			tablero.set_piece_at(rey_blanco, _pieza(chess.KING, chess.WHITE))
			dama = self._vacia(tablero.piece_map())
			tablero.set_piece_at(dama, _pieza(chess.QUEEN, chess.WHITE))
			if not _posicion_legal(tablero) or objetivos.tiene_mate_en_uno(tablero):
				return None
			soluciones = [j for j in tablero.legal_moves if objetivos.es_mate_en_dos(tablero, j)]
			if not soluciones:
				return None
			return Ejercicio(
				id="",
				tipo=TipoEjercicio.MATE,
				posicion=tablero.board_fen(),
				inicio=dama,
				jugadas_mate=2,
				# Translators: practice instruction for a mate in two.
				instruccion=_("Mate in two: the black king is on {square}. Black will defend.").format(
					square=chess.square_name(rey_negro),
				)
				+ " "
				+ _tus_piezas(tablero),
				pistas=(
					# Translators: practice hint for a mate in two.
					_("First lock the king on its row without giving check; then finish."),
					_ejemplo(tablero, soluciones, self.azar),
				),
				solucion=soluciones[0].uci(),
			)

		return self._intentar(crear)

	# Lección 18: el ataque doble.

	def ataque_doble(self, nivel: int) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			atacante = chess.QUEEN if nivel == 3 else chess.KNIGHT
			horquilla = self._vacia([])
			vacio = chess.Board(None)
			vacio.set_piece_at(horquilla, _pieza(atacante, chess.WHITE))
			destinos = list(vacio.attacks(horquilla))
			if len(destinos) < 3:
				return None
			blancos = self.azar.sample(destinos, 2)
			tipos = (
				[chess.KING, self.azar.choice([chess.ROOK, chess.QUEEN])]
				if nivel >= 2
				else self.azar.sample(
					[chess.ROOK, chess.QUEEN, chess.BISHOP],
					2,
				)
			)
			for casilla, tipo in zip(blancos, tipos, strict=True):
				tablero.set_piece_at(casilla, _pieza(tipo, chess.BLACK))
			origen_vacio = chess.Board(None)
			origen_vacio.set_piece_at(horquilla, _pieza(atacante, chess.WHITE))
			origenes = [c for c in origen_vacio.attacks(horquilla) if not tablero.piece_at(c)]
			if not origenes:
				return None
			origen = self.azar.choice(origenes)
			tablero.set_piece_at(origen, _pieza(atacante, chess.WHITE))
			if tablero.king(chess.BLACK) is not None:
				tablero.set_piece_at(self._vacia(tablero.piece_map()), _pieza(chess.KING, chess.WHITE))
			# Translators: practice instruction; {targets} is like "black rook on a8 and black king on e8".
			instruccion = _("With your {piece} on {square}, attack at the same time {targets}.").format(
				piece=anunciador.nombre_pieza(tablero.piece_at(origen)),
				square=chess.square_name(origen),
				targets=_lista_piezas(tablero, blancos),
			)
			# Translators: practice hint.
			pista = _("Look for one square from which your piece reaches both targets, and where it is safe.")
			return self._jugada(tablero, origen, Objetivo.ATAQUE_DOBLE, instruccion, pista)

		return self._intentar(crear)

	# Lección 19: el enroque.

	def enroque(self, nivel: int) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			tablero.set_piece_at(chess.E1, _pieza(chess.KING, chess.WHITE))
			lados = {1: [self.azar.choice("KQ")], 2: ["K", "Q"], 3: ["K", "Q"]}[nivel]
			for lado in lados:
				tablero.set_piece_at(chess.H1 if lado == "K" else chess.A1, _pieza(chess.ROOK, chess.WHITE))
			tablero.set_piece_at(
				chess.square(self.azar.randrange(8), self.azar.choice([6, 7])),
				_pieza(chess.KING, chess.BLACK),
			)
			if nivel == 3:
				# Una pieza negra vigila una casilla por la que el rey pasaría en uno de los enroques.
				vigilada = self.azar.choice([chess.F1, chess.G1, chess.D1, chess.C1])
				tipo = self.azar.choice([chess.ROOK, chess.BISHOP])
				atacante = self._vacia(tablero.piece_map())
				tablero.set_piece_at(atacante, _pieza(tipo, chess.BLACK))
				if vigilada not in tablero.attacks(atacante):
					return None
			tablero.set_castling_fen("".join(lados))
			if tablero.is_check():
				return None
			if nivel == 3:
				forma = None
				# Translators: practice instruction about castling when one side is forbidden.
				instruccion = _(
					"Castle. Careful: one of the two castlings is forbidden, because the king would pass over an attacked square.",
				)
			else:
				forma = (
					Forma.CORTO
					if (len(lados) == 1 and lados[0] == "K") or (nivel == 2 and self.azar.random() < 0.5)
					else Forma.LARGO
				)
				if len(lados) == 1:
					forma = Forma.CORTO if lados[0] == "K" else Forma.LARGO
				if forma is Forma.CORTO:
					# Translators: practice instruction.
					instruccion = _("Castle kingside: the king goes from e1 to g1.")
				else:
					# Translators: practice instruction.
					instruccion = _("Castle queenside: the king goes from e1 to c1.")
			instruccion += " " + _tus_piezas(tablero)
			# Translators: practice hint about castling on the board.
			pista = _(
				"Pick up the king and drop it two squares towards the rook. Or press J and type O-O or O-O-O.",
			)
			return self._jugada(tablero, chess.E1, Objetivo.ENROQUE, instruccion, pista, forma=forma)

		return self._intentar(crear)

	# Lección 20: la captura al paso.

	def al_paso(self, nivel: int) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			columna = self.azar.randrange(8)
			negro = chess.square(columna, 4)
			tablero.set_piece_at(negro, _pieza(chess.PAWN, chess.BLACK))
			vecinas = [c for c in (columna - 1, columna + 1) if 0 <= c <= 7]
			blancos = vecinas if nivel == 3 and len(vecinas) == 2 else [self.azar.choice(vecinas)]
			for c in blancos:
				tablero.set_piece_at(chess.square(c, 4), _pieza(chess.PAWN, chess.WHITE))
			if nivel >= 2:
				# Una captura normal como distracción.
				otra = chess.square(blancos[0] + (blancos[0] - columna), 5)
				if not 0 <= chess.square_file(otra) <= 7 or tablero.piece_at(otra):
					return None
				tablero.set_piece_at(
					otra,
					_pieza(self.azar.choice([chess.KNIGHT, chess.BISHOP]), chess.BLACK),
				)
			tablero.ep_square = chess.square(columna, 5)
			# Translators: practice instruction about en passant; squares like d7, d5 and e5.
			instruccion = _(
				"The black pawn has just moved two squares, from {origin} to {target}, next to your pawn. Capture it en passant.",
			).format(origin=chess.square_name(chess.square(columna, 6)), target=chess.square_name(negro))
			# Translators: practice hint about en passant.
			pista = _("Your pawn moves diagonally to the square the black pawn skipped: {square}.").format(
				square=chess.square_name(tablero.ep_square),
			)
			return self._jugada(tablero, chess.square(blancos[0], 4), Objetivo.AL_PASO, instruccion, pista)

		return self._intentar(crear)

	# Lección 21: tablas y ahogado.

	def tablas(self, nivel: int) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board(None)
			rey_negro = self.azar.choice([chess.A8, chess.H8, chess.A1, chess.H1, chess.B8, chess.G8])
			tablero.set_piece_at(rey_negro, _pieza(chess.KING, chess.BLACK))
			tablero.set_piece_at(self._vacia([rey_negro]), _pieza(chess.KING, chess.WHITE))
			pieza = chess.ROOK if nivel == 1 else chess.QUEEN
			casilla = self._vacia(tablero.piece_map())
			tablero.set_piece_at(casilla, _pieza(pieza, chess.WHITE))
			if not _posicion_legal(tablero):
				return None
			ahogos = [j for j in tablero.legal_moves if objetivos.es_ahogado(objetivos.tras(tablero, j))]
			if not ahogos:
				return None
			if nivel < 3:
				mates = objetivos.jugadas_que_cumplen(tablero, Objetivo.MATE)
				if not 1 <= len(mates) <= 2:
					return None
				# Translators: practice instruction; a mate exists but some moves stalemate.
				instruccion = _(
					"Give checkmate to the black king on {square}. Careful: some moves would stalemate it.",
				).format(
					square=chess.square_name(rey_negro),
				)
				objetivo = Objetivo.MATE
			else:
				if len(ahogos) < 2:
					return None
				# Translators: practice instruction; several moves would stalemate.
				instruccion = _("Make a move that does not stalemate the black king on {square}.").format(
					square=chess.square_name(rey_negro),
				)
				objetivo = Objetivo.NO_AHOGAR
			instruccion += " " + _tus_piezas(tablero)
			# Translators: practice hint about stalemate.
			pista = _(
				"Stalemate: the black king is not in check and has no moves. Count its free squares after your move.",
			)
			return self._jugada(tablero, casilla, objetivo, instruccion, pista)

		return self._intentar(crear)

	# Lección 22: la notación.

	def notacion(self, nivel: int) -> Ejercicio:
		def crear() -> Ejercicio | None:
			tablero = chess.Board()
			for _jugada_al_azar in range(self.azar.randrange(4, 16)):
				jugadas = list(tablero.legal_moves)
				if not jugadas:
					return None
				tablero.push(self.azar.choice(jugadas))
			if tablero.turn != chess.WHITE or tablero.is_game_over() or tablero.is_check():
				return None
			candidatas = [j for j in tablero.legal_moves if j.promotion in (None, chess.QUEEN)]
			if nivel == 1:
				candidatas = [
					j for j in candidatas if not tablero.is_capture(j) and not tablero.gives_check(j)
				]
			elif nivel == 2:
				candidatas = [j for j in candidatas if tablero.is_capture(j)]
			else:
				candidatas = [j for j in candidatas if tablero.gives_check(j) or tablero.is_castling(j)]
			if not candidatas:
				return None
			jugada = self.azar.choice(candidatas)
			san = san_en_espanol(tablero, jugada)
			limpio = chess.Board(tablero.fen())
			# Translators: practice instruction; {move} describes a move in words.
			instruccion = _("Press J and type this move in notation: {move}").format(
				move=anunciador.describir_jugada(limpio, jugada),
			)
			# Translators: practice hint about notation.
			pista = _("Piece letter (none for pawns), an x if it captures, and the destination square.")
			# Translators: practice hint that gives the notation of the move.
			segunda = _("It is written {notation}.").format(notation=san)
			# Translators: said when another move was played in a notation exercise.
			error = _("That is not the requested move. Its notation is {notation}.").format(notation=san)
			return self._jugada(
				limpio,
				jugada.from_square,
				Objetivo.NOTACION,
				instruccion,
				pista,
				jugadas=frozenset([jugada.uci()]),
				mensaje_error=error,
				segunda_pista=segunda,
			)

		return self._intentar(crear)

	# Lección 23: la guerra de peones.

	def guerra_peones(self, nivel: int) -> Ejercicio:
		cantidad = {1: 3, 2: 5, 3: 8}[nivel]
		primera = self.azar.randrange(0, 9 - cantidad)
		columnas = range(primera, primera + cantidad)
		tablero = chess.Board(None)
		for c in columnas:
			tablero.set_piece_at(chess.square(c, 1), _pieza(chess.PAWN, chess.WHITE))
			tablero.set_piece_at(chess.square(c, 6), _pieza(chess.PAWN, chess.BLACK))
		return Ejercicio(
			id="",
			tipo=TipoEjercicio.GUERRA_PEONES,
			posicion=tablero.board_fen(),
			inicio=chess.square(primera, 1),
			# Translators: practice instruction for the pawn war; {n} is the number of pawns of each side.
			instruccion=_("Pawn war, {n} against {n}. Whoever promotes first wins.").format(n=cantidad),
			pistas=(
				# Translators: practice hint for the pawn war.
				_("A pawn with no enemy pawns ahead, on its file or the next ones, cannot be stopped."),
				# Translators: practice hint for the pawn war.
				_("Do not leave an enemy pawn free to run: block it or capture it."),
			),
		)

	# Extra 1: jugar solo escribiendo.

	def solo_escribiendo(self, nivel: int) -> Ejercicio:
		if nivel < 3:
			# Niveles 1 y 2: escribir en notación una jugada dicha con palabras.
			return replace(self.notacion(nivel + 1), solo_escrito=True)
		# Nivel 3: mate en una «sin mirar», con todas las piezas descritas en la instrucción.
		ejercicio = self.mate(self.azar.choice([1, 2, 3]))
		tablero = ejercicio.tablero()
		negras = sorted(chess.SquareSet(tablero.occupied_co[chess.BLACK]))
		# Translators: practice instruction for a blindfold mate; {black} and {white} list pieces and squares.
		instruccion = _(
			"Without looking. Black pieces: {black}. Your pieces: {white}. Type the move that gives checkmate.",
		).format(
			black=_lista_piezas(tablero, negras),
			white=_lista_piezas(tablero, sorted(chess.SquareSet(tablero.occupied_co[chess.WHITE]))),
		)
		return replace(ejercicio, instruccion=instruccion, a_ciegas=True, solo_escrito=True, inicio=chess.A1)
