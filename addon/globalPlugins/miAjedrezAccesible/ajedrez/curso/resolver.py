# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Calcula el número mínimo de jugadas de un ejercicio de manzanas o de coronación.

Se usa en las pruebas para comprobar que cada ejercicio tiene solución y que su «minimo» es correcto.
Es una búsqueda en anchura sobre (posición, manzanas recogidas).
"""

from collections import deque

import chess

from .modelo import Ejercicio, TipoEjercicio
from .sesion import SesionEjercicio

LIMITE_JUGADAS = 12


def resolver(
	ejercicio: Ejercicio,
	limite: int = LIMITE_JUGADAS,
	solo_desde: chess.Square | None = None,
) -> list[chess.Move] | None:
	"""Devuelve una solución mínima, o None si no hay solución en `limite` jugadas.

	Con `solo_desde`, solo se mueve la pieza que empieza en esa casilla (la que se practica):
	la búsqueda es mucho más rápida y la solución describe un único recorrido.
	"""
	if ejercicio.tipo not in (TipoEjercicio.MANZANAS, TipoEjercicio.CORONAR):
		return None
	inicial = SesionEjercicio(ejercicio)
	cola: deque[tuple[chess.Board, frozenset[chess.Square], list[chess.Move], chess.Square | None]] = deque(
		[(inicial.partida.tablero.copy(stack=False), frozenset(ejercicio.manzanas), [], solo_desde)],
	)
	vistos = {(inicial.partida.tablero.board_fen(), frozenset(ejercicio.manzanas))}
	while cola:
		tablero, manzanas, camino, pieza = cola.popleft()
		if len(camino) >= limite:
			continue
		for jugada in list(tablero.legal_moves):
			if jugada.promotion not in (None, chess.QUEEN):
				continue
			if pieza is not None and jugada.from_square != pieza:
				continue
			siguiente = tablero.copy(stack=False)
			siguiente.push(jugada)
			siguiente.push(chess.Move.null())
			quedan = manzanas - {jugada.to_square}
			nuevo_camino = [*camino, jugada]
			if _cumplido(ejercicio, siguiente, quedan, jugada):
				return nuevo_camino
			clave = (siguiente.board_fen(), quedan)
			if clave not in vistos:
				vistos.add(clave)
				cola.append(
					(siguiente, quedan, nuevo_camino, jugada.to_square if pieza is not None else None),
				)
	return None


def _cumplido(
	ejercicio: Ejercicio,
	tablero: chess.Board,
	manzanas: frozenset[chess.Square],
	jugada: chess.Move,
) -> bool:
	if ejercicio.tipo is TipoEjercicio.CORONAR:
		return jugada.promotion is not None
	if manzanas:
		return False
	for casilla in ejercicio.capturar or ():
		pieza = tablero.piece_at(casilla)
		if pieza is not None and pieza.color == chess.BLACK:
			return False
	return True
