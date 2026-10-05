# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""La computadora como rival: pide jugadas a Stockfish en un hilo aparte y las entrega a la interfaz.

Todo el trabajo con el motor pasa por un único hilo, así las peticiones se atienden en orden
(primero se inicia el motor, luego cada jugada). Los resultados vuelven al hilo de la interfaz
con `wx.CallAfter`. Cada petición lleva un número de «generación»: si mientras tanto se deshizo
una jugada o se cerró el tablero, el resultado atrasado se descarta.
"""

import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

import wx
from logHandler import log

from ..ajedrez.motor import Motor, Nivel

# python-chess queda disponible después de importar el paquete «ajedrez».
import chess  # noqa: E402

# Aunque el motor decida antes, la jugada no se anuncia hasta pasado este tiempo.
PAUSA_MINIMA_SEGUNDOS = 0.5


class Computadora:
	def __init__(self, nivel: Nivel, al_fallar: Callable[[], None], motor: Motor | None = None) -> None:
		self.nivel = nivel
		self._al_fallar = al_fallar
		self._motor = motor or Motor()
		self._ejecutor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="miAjedrezAccesible.motor")
		self._generacion = 0
		self.pensando = False
		self._cerrada = False
		self._enviar(self._motor.iniciar, lambda _resultado: None)

	def _enviar(self, tarea: Callable[[], object], al_terminar: Callable[[object], None]) -> None:
		generacion = self._generacion

		def entregar(futuro: Future) -> None:
			if self._cerrada or generacion != self._generacion:
				return
			try:
				resultado = futuro.result()
			except Exception:
				log.error("Error del motor de ajedrez", exc_info=True)
				self.pensando = False
				self._al_fallar()
				return
			al_terminar(resultado)

		futuro = self._ejecutor.submit(tarea)
		futuro.add_done_callback(lambda f: wx.CallAfter(entregar, f))

	def pedir_jugada(self, tablero: chess.Board, al_elegir: Callable[[chess.Move], None]) -> None:
		copia = tablero.copy()
		nivel = self.nivel
		self.pensando = True

		def tarea() -> chess.Move:
			inicio = time.monotonic()
			jugada = self._motor.elegir_jugada(copia, nivel)
			espera = PAUSA_MINIMA_SEGUNDOS - (time.monotonic() - inicio)
			if espera > 0:
				time.sleep(espera)
			return jugada

		def al_terminar(jugada: object) -> None:
			self.pensando = False
			if isinstance(jugada, chess.Move):
				al_elegir(jugada)

		self._enviar(tarea, al_terminar)

	def evaluar(self, tablero: chess.Board, al_evaluar: Callable[[int], None]) -> None:
		"""Evalúa la posición desde el punto de vista del bando que mueve en `tablero`."""
		copia = tablero.copy()
		self.pensando = True

		def al_terminar(valor: object) -> None:
			self.pensando = False
			if isinstance(valor, int):
				al_evaluar(valor)

		self._enviar(lambda: self._motor.evaluar(copia), al_terminar)

	def descartar_pendientes(self) -> None:
		"""Ignora lo que el motor esté calculando (por ejemplo, tras deshacer jugadas)."""
		self._generacion += 1
		self.pensando = False

	def cerrar(self) -> None:
		if self._cerrada:
			return
		self.descartar_pendientes()
		self._cerrada = True
		self._ejecutor.submit(self._motor.cerrar)
		self._ejecutor.shutdown(wait=False)
