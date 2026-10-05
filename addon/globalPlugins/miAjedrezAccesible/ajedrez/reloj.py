# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Reloj de ajedrez: tiempo por bando, incremento por jugada, pausas y avisos.

Solo corre el reloj del bando al que le toca y que «cuenta»: contra la computadora, solo el de la
persona. Se detiene de dos maneras: la pausa que elige la persona y las suspensiones automáticas
mientras hay un menú o un diálogo abierto (pueden anidarse).
"""

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass

import chess

from . import anunciador
from .idioma import _, ngettext

# Avisos de tiempo restante, en segundos.
AVISOS = (60, 30, 10)


@dataclass(frozen=True)
class ControlTiempo:
	id: str
	minutos: int
	incremento: int

	@property
	def con_reloj(self) -> bool:
		return self.minutos > 0

	@property
	def pgn(self) -> str:
		"""Etiqueta TimeControl de PGN: «600+5», o «-» sin reloj."""
		return f"{self.minutos * 60}+{self.incremento}" if self.con_reloj else "-"

	def etiqueta(self) -> str:
		if not self.con_reloj:
			# Translators: clock choice in the new game dialog.
			return _("No clock")
		if self.incremento:
			# Translators: clock choice in the new game dialog, for example "10 minutes + 5 seconds per move".
			return _("{minutes} minutes + {seconds} seconds per move").format(
				minutes=self.minutos,
				seconds=self.incremento,
			)
		# Translators: clock choice in the new game dialog, for example "30 minutes".
		return _("{minutes} minutes").format(minutes=self.minutos)


SIN_RELOJ = ControlTiempo("sin", 0, 0)
CONTROLES = (
	SIN_RELOJ,
	ControlTiempo("30+0", 30, 0),
	ControlTiempo("15+10", 15, 10),
	ControlTiempo("10+5", 10, 5),
	ControlTiempo("5+3", 5, 3),
)


def control(id_control: str) -> ControlTiempo:
	return next((c for c in CONTROLES if c.id == id_control), SIN_RELOJ)


def texto_tiempo(segundos: float) -> str:
	"""«4 minutos y 32 segundos», «1 minuto», «9 segundos»."""
	total = max(0, int(segundos))
	minutos, resto = divmod(total, 60)
	partes = []
	if minutos:
		# Translators: part of a time on the clock, for example "4 minutes".
		partes.append(ngettext("{n} minute", "{n} minutes", minutos).format(n=minutos))
	if resto or not minutos:
		# Translators: part of a time on the clock, for example "32 seconds".
		partes.append(ngettext("{n} second", "{n} seconds", resto).format(n=resto))
	return anunciador.unir_lista(partes)


class Reloj:
	def __init__(
		self,
		control_tiempo: ControlTiempo,
		cuentan: Iterable[chess.Color],
		restante: dict[chess.Color, float] | None = None,
		ahora: Callable[[], float] = time.monotonic,
	) -> None:
		self.control = control_tiempo
		self.cuentan = frozenset(cuentan)
		inicial = float(control_tiempo.minutos * 60)
		self.restante = {chess.WHITE: inicial, chess.BLACK: inicial}
		if restante:
			self.restante.update({c: float(v) for c, v in restante.items()})
		self._ahora = ahora
		self._corre: chess.Color | None = None
		self._desde = ahora()
		self.pausado = False
		self._suspensiones = 0
		# Avisos ya dados; los que ya pasaron al cargar una partida no se repiten.
		self._avisados: dict[chess.Color, set[int]] = {
			c: {a for a in AVISOS if self.restante[c] <= a} for c in (chess.WHITE, chess.BLACK)
		}

	@property
	def _contando(self) -> bool:
		return self._corre is not None and not self.pausado and self._suspensiones == 0

	def _acumular(self) -> None:
		"""Descuenta lo transcurrido antes de cambiar el estado del reloj."""
		ahora = self._ahora()
		if self._contando:
			assert self._corre is not None
			self.restante[self._corre] -= ahora - self._desde
		self._desde = ahora

	def tiempo(self, color: chess.Color) -> float:
		restante = self.restante[color]
		if self._contando and color == self._corre:
			restante -= self._ahora() - self._desde
		return max(0.0, restante)

	@property
	def corriendo(self) -> chess.Color | None:
		"""El bando cuyo reloj está corriendo ahora mismo, o None."""
		return self._corre if self._contando else None

	def poner_en_marcha(self, turno: chess.Color) -> None:
		"""Pone a correr el reloj del bando al que le toca (si cuenta), sin incremento."""
		self._acumular()
		self._corre = turno if turno in self.cuentan else None

	def tras_jugada(self, color: chess.Color, turno: chess.Color) -> None:
		"""`color` acaba de jugar: suma su incremento y pasa el reloj a `turno`."""
		self._acumular()
		if color in self.cuentan:
			self.restante[color] += self.control.incremento
			self._avisados[color] = {a for a in self._avisados[color] if self.restante[color] <= a}
			# Jugar quita la pausa.
			self.pausado = False
		self._corre = turno if turno in self.cuentan else None

	def detener(self) -> None:
		"""Fin de la partida: ningún reloj vuelve a correr."""
		self._acumular()
		self._corre = None

	def pausar(self) -> None:
		self._acumular()
		self.pausado = True

	def reanudar(self) -> None:
		self._acumular()
		self.pausado = False

	def suspender(self) -> None:
		"""Mientras hay un menú o un diálogo abierto. Cada suspensión se cierra con `continuar`."""
		self._acumular()
		self._suspensiones += 1

	def continuar(self) -> None:
		self._acumular()
		self._suspensiones = max(0, self._suspensiones - 1)

	def agotado(self) -> chess.Color | None:
		"""El bando que se quedó sin tiempo, o None."""
		if self._corre is not None and self.tiempo(self._corre) <= 0:
			return self._corre
		return None

	def aviso_pendiente(self) -> tuple[chess.Color, int] | None:
		"""Un aviso que toca dar ahora: (bando, segundos). Si se saltaron varios, solo el menor."""
		for color in sorted(self.cuentan):
			tiempo = self.tiempo(color)
			nuevos = [a for a in AVISOS if tiempo <= a and a not in self._avisados[color]]
			if nuevos:
				self._avisados[color].update(a for a in AVISOS if tiempo <= a)
				return color, min(nuevos)
		return None
