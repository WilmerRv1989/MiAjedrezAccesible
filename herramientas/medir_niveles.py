# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Mide la fuerza de los niveles sin que nadie tenga que jugar.

Cada nivel juega contra un «principiante simulado»: da mate si puede, captura la pieza más valiosa
que tenga a mano y, si no, mueve al azar. Se parece a alguien que conoce las reglas pero no calcula.
El resultado es el porcentaje de puntos que consigue la computadora (victoria 1, tablas 0,5).

Uso (necesita Stockfish, ver obtener_stockfish.py):
	uv run python herramientas/medir_niveles.py            (niveles 1 a 4, 20 partidas cada uno)
	uv run python herramientas/medir_niveles.py 1 2 5 -n 10
"""

import argparse
import os
import random
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_RAIZ, "addon", "globalPlugins", "miAjedrezAccesible"))

from ajedrez import motor  # noqa: E402

import chess  # noqa: E402

_VALOR = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
_MAXIMO_MEDIAS_JUGADAS = 200


def jugada_de_principiante(tablero: chess.Board, azar: random.Random) -> chess.Move:
	jugadas = list(tablero.legal_moves)
	for jugada in jugadas:
		tablero.push(jugada)
		mate = tablero.is_checkmate()
		tablero.pop()
		if mate:
			return jugada
	capturas = [j for j in jugadas if tablero.is_capture(j)]
	if not capturas:
		return azar.choice(jugadas)

	def valor(jugada: chess.Move) -> int:
		pieza = tablero.piece_at(jugada.to_square)
		return _VALOR[pieza.piece_type] if pieza else 1  # captura al paso

	mejor = max(valor(j) for j in capturas)
	return azar.choice([j for j in capturas if valor(j) == mejor])


def jugar_partida(
	stockfish: motor.Motor,
	nivel: motor.Nivel,
	color_computadora: chess.Color,
	azar: random.Random,
) -> float:
	"""Devuelve los puntos de la computadora: 1, 0,5 o 0."""
	tablero = chess.Board()
	while not tablero.is_game_over(claim_draw=True) and tablero.ply() < _MAXIMO_MEDIAS_JUGADAS:
		if tablero.turn == color_computadora:
			jugada = stockfish.elegir_jugada(tablero, nivel)
		else:
			jugada = jugada_de_principiante(tablero, azar)
		tablero.push(jugada)
	resultado = tablero.outcome(claim_draw=True)
	if resultado is None or resultado.winner is None:
		return 0.5
	return 1.0 if resultado.winner == color_computadora else 0.0


def medir(numero_nivel: int, partidas: int, semilla: int = 1) -> float:
	"""Porcentaje de puntos de la computadora contra el principiante simulado."""
	azar = random.Random(semilla)
	stockfish = motor.Motor(azar=random.Random(semilla + 1))
	try:
		puntos = sum(
			jugar_partida(
				stockfish,
				motor.NIVELES[numero_nivel],
				chess.WHITE if i % 2 == 0 else chess.BLACK,
				azar,
			)
			for i in range(partidas)
		)
	finally:
		stockfish.cerrar()
	return 100 * puntos / partidas


def main() -> int:
	argumentos = argparse.ArgumentParser(description=__doc__)
	argumentos.add_argument("niveles", nargs="*", type=int, default=[1, 2, 3, 4])
	argumentos.add_argument("-n", "--partidas", type=int, default=20)
	opciones = argumentos.parse_args()
	for numero in opciones.niveles:
		porcentaje = medir(numero, opciones.partidas)
		print(f"Nivel {numero}: la computadora consigue el {porcentaje:.0f} % de los puntos")
	return 0


if __name__ == "__main__":
	sys.exit(main())
