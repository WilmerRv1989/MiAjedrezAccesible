# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Opciones de una partida nueva: modo, color, nivel y reloj."""

import random
from dataclasses import dataclass
from enum import StrEnum

import chess

from .idioma import _
from .motor import NIVELES
from .reloj import CONTROLES, ControlTiempo, control

NIVEL_POR_DEFECTO = 3


class Modo(StrEnum):
	COMPUTADORA = "computadora"
	DOS_PERSONAS = "dos_personas"

	def etiqueta(self) -> str:
		if self is Modo.COMPUTADORA:
			# Translators: game mode in the new game dialog.
			return _("Against the computer")
		# Translators: game mode in the new game dialog.
		return _("Two people on this computer")


class EleccionColor(StrEnum):
	BLANCAS = "blancas"
	NEGRAS = "negras"
	AZAR = "azar"

	def etiqueta(self) -> str:
		if self is EleccionColor.BLANCAS:
			# Translators: color choice in the new game dialog.
			return _("White")
		if self is EleccionColor.NEGRAS:
			# Translators: color choice in the new game dialog.
			return _("Black")
		# Translators: color choice in the new game dialog.
		return _("Random")


@dataclass(frozen=True)
class ConfiguracionPartida:
	modo: Modo = Modo.COMPUTADORA
	color: EleccionColor = EleccionColor.BLANCAS
	nivel: int = NIVEL_POR_DEFECTO
	# Identificador del control de tiempo («sin», «10+5»...).
	reloj: str = "sin"

	def __post_init__(self) -> None:
		if self.nivel not in NIVELES:
			object.__setattr__(self, "nivel", NIVEL_POR_DEFECTO)
		if self.reloj not in {c.id for c in CONTROLES}:
			object.__setattr__(self, "reloj", "sin")

	@property
	def control_tiempo(self) -> ControlTiempo:
		return control(self.reloj)

	def color_persona(self, elegir=random.choice) -> chess.Color | None:
		"""Color con el que juega la persona, o None entre dos personas. Resuelve «al azar»."""
		if self.modo is Modo.DOS_PERSONAS:
			return None
		if self.color is EleccionColor.BLANCAS:
			return chess.WHITE
		if self.color is EleccionColor.NEGRAS:
			return chess.BLACK
		return elegir([chess.WHITE, chess.BLACK])

	@classmethod
	def desde_textos(cls, modo: str, color: str, nivel: int, reloj: str = "sin") -> "ConfiguracionPartida":
		"""Crea la configuración a partir de lo guardado, ignorando valores desconocidos."""
		return cls(
			modo=Modo(modo) if modo in Modo._value2member_map_ else Modo.COMPUTADORA,
			color=EleccionColor(color)
			if color in EleccionColor._value2member_map_
			else EleccionColor.BLANCAS,
			nivel=nivel,
			reloj=reloj,
		)
