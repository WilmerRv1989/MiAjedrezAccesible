# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Cuadrícula virtual: un tablero de filas por columnas que NVDA lee como una tabla.

Cómo funciona:
- El juego dibuja el tablero en una ventana real de wx (un panel que recibe el foco del sistema).
- Cuando ese panel recibe el foco, `PanelCuadricula` (una capa que el complemento aplica
  al objeto de NVDA del panel) redirige el foco a la celda virtual actual.
- Cada celda es un `CeldaVirtual`: un objeto de NVDA sin ventana propia, cuyo nombre
  lo decide el juego. Moverse es darle el foco a otra celda, así NVDA la anuncia por voz y en braille.
- Las teclas que el juego no usa siguen hasta el panel real, que las ignora:
  no se escapan a otras aplicaciones.
"""

import os

import controlTypes
import eventHandler
import tones
import wx
from locationHelper import RectLTWH
from NVDAObjects import NVDAObject
from NVDAObjects.window import Window

# Cuadrículas abiertas, por identificador de ventana (hwnd) del panel que las dibuja.
_cuadriculas: dict[int, "CuadriculaVirtual"] = {}

# Tono que avisa de que no se puede seguir en esa dirección.
_TONO_BORDE_HZ = 180
_TONO_BORDE_MS = 40


def cuadricula_de_ventana(hwnd: int) -> "CuadriculaVirtual | None":
	return _cuadriculas.get(hwnd)


class PanelCuadricula(NVDAObject):
	"""Capa para el objeto de NVDA del panel real: le pasa el foco a la celda actual."""

	def _get_focusRedirect(self) -> "CeldaVirtual | None":
		cuadricula = _cuadriculas.get(self.windowHandle)
		return cuadricula.celda_actual if cuadricula else None


class CeldaVirtual(NVDAObject):
	"""Una celda de la cuadrícula. El juego define su nombre y sus órdenes de teclado."""

	# La celda de tabla no se anuncia como «celda» al recibir el foco: solo se oye su nombre.
	role = controlTypes.Role.TABLECELL

	def __init__(self, cuadricula: "CuadriculaVirtual", fila: int, columna: int) -> None:
		super().__init__()
		self.cuadricula = cuadricula
		self.fila = fila
		self.columna = columna

	def _get_processID(self) -> int:
		return os.getpid()

	def _get_windowHandle(self) -> int:
		return self.cuadricula.hwnd

	def _get_parent(self) -> NVDAObject | None:
		return self.cuadricula.objeto_panel()

	def _get_name(self) -> str:
		return self.cuadricula.nombre_celda(self.fila, self.columna)

	def _get_states(self) -> set[controlTypes.State]:
		return {controlTypes.State.FOCUSABLE, controlTypes.State.FOCUSED}

	def _get_location(self) -> RectLTWH | None:
		return self.cuadricula.ubicacion_celda(self.fila, self.columna)

	def _isEqual(self, other: "CeldaVirtual") -> bool:
		return (
			self.cuadricula is other.cuadricula and self.fila == other.fila and self.columna == other.columna
		)

	def event_gainFocus(self) -> None:
		super().event_gainFocus()
		self.cuadricula.al_enfocar_celda(self.fila, self.columna)


class CuadriculaVirtual:
	"""Lógica común de navegación. Cada juego hereda y define `nombre_celda` y sus órdenes."""

	clase_celda: type[CeldaVirtual] = CeldaVirtual

	def __init__(self, panel: wx.Window, filas: int, columnas: int) -> None:
		self.panel = panel
		self.hwnd: int = panel.GetHandle()
		self.filas = filas
		self.columnas = columnas
		self.fila = 0
		self.columna = 0
		self._celdas = [
			[self.clase_celda(cuadricula=self, fila=f, columna=c) for c in range(columnas)]
			for f in range(filas)
		]
		_cuadriculas[self.hwnd] = self

	def cerrar(self) -> None:
		_cuadriculas.pop(self.hwnd, None)

	@property
	def celda_actual(self) -> CeldaVirtual:
		return self._celdas[self.fila][self.columna]

	def objeto_panel(self) -> NVDAObject | None:
		return Window(windowHandle=self.hwnd)

	def tiene_foco(self) -> bool:
		foco = wx.Window.FindFocus()
		return foco is not None and foco.GetHandle() == self.hwnd

	def ir_a(self, fila: int, columna: int) -> None:
		"""Mueve el foco a una celda. Si está fuera de la cuadrícula, suena el tono de borde."""
		if not (0 <= fila < self.filas and 0 <= columna < self.columnas):
			tones.beep(_TONO_BORDE_HZ, _TONO_BORDE_MS)
			return
		self.fila = fila
		self.columna = columna
		self.enfocar_celda_actual()

	def mover(self, filas: int, columnas: int) -> None:
		self.ir_a(self.fila + filas, self.columna + columnas)

	def enfocar_celda_actual(self) -> None:
		if self.tiene_foco():
			eventHandler.executeEvent("gainFocus", self.celda_actual)

	def ubicacion_celda(self, fila: int, columna: int) -> RectLTWH | None:
		"""Rectángulo de la celda en la pantalla, para el resaltado y el ratón de NVDA."""
		try:
			rectangulo = self.rectangulo_celda(fila, columna)
			if rectangulo is None:
				return None
			x, y, ancho, alto = rectangulo
			esquina = self.panel.ClientToScreen(wx.Point(x, y))
		except RuntimeError:
			# El panel ya se destruyó (NVDA puede preguntar por una casilla de un tablero cerrado).
			return None
		return RectLTWH(esquina.x, esquina.y, ancho, alto)

	# Lo que cada juego debe o puede redefinir.

	def nombre_celda(self, fila: int, columna: int) -> str:
		raise NotImplementedError

	def rectangulo_celda(self, fila: int, columna: int) -> tuple[int, int, int, int] | None:
		"""Rectángulo (x, y, ancho, alto) de la celda dentro del panel, o None si no se dibuja."""
		return None

	def al_enfocar_celda(self, fila: int, columna: int) -> None:
		"""Se llama después de que NVDA anuncia la celda. Por defecto, redibuja el panel."""
		if self.panel:
			self.panel.Refresh()
