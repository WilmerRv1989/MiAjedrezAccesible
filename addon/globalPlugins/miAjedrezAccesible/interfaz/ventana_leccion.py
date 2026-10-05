# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Ventana de una lección o de una ronda de práctica: el tablero de los ejercicios y su menú."""

from collections.abc import Callable
from typing import TYPE_CHECKING

import addonHandler

from ..ajedrez.curso.modelo import Leccion
from ..ajedrez.curso.sesion import SesionEjercicio
from . import atajos
from .tablero_leccion import CuadriculaLeccion
from .ventana_tablero import VentanaBase

if TYPE_CHECKING:
	from .curso import ControladorCurso
	from .retos import ControladorRetos

addonHandler.initTranslation()


def titulo_leccion(leccion: Leccion) -> str:
	if leccion.extra:
		# Translators: title of an extra lesson, for example "Extra 1: Play only by typing".
		return _("Extra {number}: {title}").format(number=leccion.numero, title=leccion.titulo)
	# Translators: title of a lesson, for example "Lesson 4: The rook".
	return _("Lesson {number}: {title}").format(number=leccion.id, title=leccion.titulo)


class VentanaLeccion(VentanaBase):
	def __init__(
		self,
		controlador: "ControladorCurso | ControladorRetos",
		titulo: str,
		sesion: SesionEjercicio,
		al_cerrar: Callable[[], None],
	) -> None:
		super().__init__(titulo, al_cerrar)
		self.controlador = controlador
		self._instalar(CuadriculaLeccion(self.panel, self, controlador, sesion))

	def _al_mostrar_por_primera_vez(self) -> None:
		self.controlador.anunciar_ejercicio(al_abrir=True)

	@property
	def contexto_atajos(self) -> atajos.Contexto:
		return self.controlador.contexto_atajos

	def mostrar_menu_partida(self) -> None:
		self.mostrar_menu(self.controlador.opciones_menu(self.Close))
