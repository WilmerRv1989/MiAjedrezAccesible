# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""La guerra de peones: un minijuego clásico de las escuelas de ajedrez.

Solo hay peones. Gana quien corona primero un peón, o quien deja al rival sin jugadas.
Stockfish no sirve aquí (necesita reyes), así que las negras eligen con una búsqueda propia
de poca profundidad, y a veces se equivocan a propósito para que quien aprende pueda ganar.
"""

import random

import chess

# Puntuación de una victoria: mucho más que cualquier evaluación de la posición.
_VICTORIA = 10_000


def sin_jugadas(tablero: chess.Board) -> bool:
	return not any(True for _j in tablero.legal_moves)


def _pasado(tablero: chess.Board, casilla: chess.Square, color: chess.Color) -> bool:
	"""Peón pasado: ningún peón rival delante, ni en su columna ni en las vecinas."""
	columna, fila = chess.square_file(casilla), chess.square_rank(casilla)
	for otro in tablero.pieces(chess.PAWN, not color):
		c, f = chess.square_file(otro), chess.square_rank(otro)
		if abs(c - columna) <= 1 and ((f > fila) if color == chess.WHITE else (f < fila)):
			return False
	return True


def evaluar(tablero: chess.Board) -> int:
	"""Evaluación desde el punto de vista de las blancas: avance y peones pasados."""
	total = 0
	for color, signo in ((chess.WHITE, 1), (chess.BLACK, -1)):
		for casilla in tablero.pieces(chess.PAWN, color):
			avance = chess.square_rank(casilla) if color == chess.WHITE else 7 - chess.square_rank(casilla)
			valor = 10 + avance * avance
			if _pasado(tablero, casilla, color):
				valor += 20 * avance
			total += signo * valor
	return total


def _negamax(tablero: chess.Board, profundidad: int, alfa: int, beta: int) -> int:
	signo = 1 if tablero.turn == chess.WHITE else -1
	jugadas = list(tablero.legal_moves)
	if not jugadas:
		# Quien no puede mover, pierde.
		return -_VICTORIA
	if profundidad == 0:
		return signo * evaluar(tablero)
	mejor = -_VICTORIA * 2
	for jugada in jugadas:
		if jugada.promotion is not None:
			return _VICTORIA + profundidad
		tablero.push(jugada)
		valor = -_negamax(tablero, profundidad - 1, -beta, -alfa)
		tablero.pop()
		mejor = max(mejor, valor)
		alfa = max(alfa, valor)
		if alfa >= beta:
			break
	return mejor


def elegir_jugada(
	tablero: chess.Board,
	azar: random.Random,
	profundidad: int = 3,
	errores: float = 0.25,
) -> chess.Move | None:
	"""Jugada para el bando que mueve. Con probabilidad `errores`, elige una jugada al azar."""
	jugadas = [j for j in tablero.legal_moves if j.promotion in (None, chess.QUEEN)]
	if not jugadas:
		return None
	coronaciones = [j for j in jugadas if j.promotion is not None]
	if coronaciones:
		return coronaciones[0]
	if azar.random() < errores:
		return azar.choice(jugadas)
	puntuadas = []
	for jugada in jugadas:
		tablero.push(jugada)
		valor = -_negamax(tablero, profundidad - 1, -_VICTORIA * 2, _VICTORIA * 2)
		tablero.pop()
		puntuadas.append((valor, jugada))
	mejor = max(v for v, _j in puntuadas)
	return azar.choice([j for v, j in puntuadas if v == mejor])
