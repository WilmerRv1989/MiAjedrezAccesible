# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Stockfish por el protocolo UCI y los niveles de dificultad.

Todas las llamadas de `Motor` bloquean: quien lo use desde la interfaz debe llamarlas en otro hilo.
"""

import os
import random
import subprocess
from dataclasses import dataclass

import chess
import chess.engine

from .idioma import _

# Las tablas se aceptan si la computadora no va ganando por más de medio peón.
UMBRAL_TABLAS_CENTIPEONES = 50

RUTA_STOCKFISH = os.path.join(
	os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
	"bin",
	"stockfish",
	"stockfish.exe",
)


@dataclass(frozen=True)
class Nivel:
	numero: int
	# «Skill Level» de Stockfish, de 0 a 20.
	habilidad: int
	# Segundos que se deja pensar al motor en cada jugada.
	tiempo: float
	# Profundidad máxima en medias jugadas, o None para no limitarla.
	profundidad: int | None = None
	# Proporción de jugadas en las que se equivoca a propósito (juega una jugada legal al azar),
	# para que los niveles bajos se parezcan a alguien que está aprendiendo.
	errores: float = 0.0

	def limite(self) -> chess.engine.Limit:
		return chess.engine.Limit(time=self.tiempo, depth=self.profundidad)

	def descripcion(self) -> str:
		if self.numero <= 2:
			# Translators: description of a difficulty level of the computer.
			texto = _("learning the rules")
		elif self.numero <= 4:
			# Translators: description of a difficulty level of the computer.
			texto = _("beginner")
		elif self.numero <= 6:
			# Translators: description of a difficulty level of the computer.
			texto = _("intermediate")
		elif self.numero <= 8:
			# Translators: description of a difficulty level of the computer.
			texto = _("advanced")
		else:
			# Translators: description of a difficulty level of the computer.
			texto = _("maximum")
		# Translators: a difficulty level in the new game dialog, for example "3: beginner".
		return _("{level}: {description}").format(level=self.numero, description=texto)


NIVELES: dict[int, Nivel] = {
	n.numero: n
	for n in (
		# Errores medidos contra un principiante simulado (herramientas/medir_niveles.py):
		# con 60 % la computadora gana ~25 %; 40 % → ~40 %; 25 % → ~65 %; 10 % → ~80 %.
		Nivel(1, habilidad=0, tiempo=0.05, profundidad=1, errores=0.6),
		Nivel(2, habilidad=0, tiempo=0.1, errores=0.4),
		Nivel(3, habilidad=2, tiempo=0.2, errores=0.25),
		Nivel(4, habilidad=4, tiempo=0.2, errores=0.1),
		Nivel(5, habilidad=7, tiempo=0.4),
		Nivel(6, habilidad=10, tiempo=0.4),
		Nivel(7, habilidad=13, tiempo=0.7),
		Nivel(8, habilidad=16, tiempo=0.7),
		Nivel(9, habilidad=18, tiempo=1.0),
		Nivel(10, habilidad=20, tiempo=1.0),
	)
}


class Motor:
	"""Un proceso de Stockfish. Se inicia al pedirlo y se cierra con `cerrar`."""

	def __init__(self, ruta: str = RUTA_STOCKFISH, azar: random.Random | None = None) -> None:
		self.ruta = ruta
		self._azar = azar or random.Random()
		self._motor: chess.engine.SimpleEngine | None = None
		self._habilidad: int | None = None

	def iniciar(self) -> None:
		if self._motor is not None:
			return
		opciones: dict[str, int] = {}
		if os.name == "nt":
			# Sin ventana de consola.
			opciones["creationflags"] = subprocess.CREATE_NO_WINDOW
		self._motor = chess.engine.SimpleEngine.popen_uci(self.ruta, **opciones)

	def _listo(self) -> chess.engine.SimpleEngine:
		self.iniciar()
		assert self._motor is not None
		return self._motor

	def elegir_jugada(self, tablero: chess.Board, nivel: Nivel) -> chess.Move:
		if nivel.errores and self._azar.random() < nivel.errores:
			return self._azar.choice(list(tablero.legal_moves))
		motor = self._listo()
		if self._habilidad != nivel.habilidad:
			motor.configure({"Skill Level": nivel.habilidad})
			self._habilidad = nivel.habilidad
		resultado = motor.play(tablero, nivel.limite())
		if resultado.move is None:
			raise chess.engine.EngineError("El motor no devolvió ninguna jugada")
		return resultado.move

	def evaluar(self, tablero: chess.Board, segundos: float = 0.3) -> int:
		"""Evaluación en centipeones desde el punto de vista del bando que mueve."""
		info = self._listo().analyse(tablero, chess.engine.Limit(time=segundos))
		puntuacion = info.get("score")
		if puntuacion is None:
			return 0
		return puntuacion.relative.score(mate_score=100_000)

	def cerrar(self) -> None:
		if self._motor is None:
			return
		try:
			self._motor.quit()
		except Exception:
			# Si el motor no responde al cerrarse, se termina el proceso a la fuerza.
			self._motor.close()
		finally:
			self._motor = None


def acepta_tablas(evaluacion_para_la_computadora: int) -> bool:
	return evaluacion_para_la_computadora <= UMBRAL_TABLAS_CENTIPEONES
