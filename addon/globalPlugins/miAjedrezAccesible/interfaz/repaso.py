# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Repaso de una partida guardada: el mismo tablero, de solo lectura, recorrido con Alt+flechas."""

from collections.abc import Callable

import addonHandler
import api
import speech
import tones
import ui
import wx
from scriptHandler import script

from ..ajedrez.archivo_pgn import PartidaCargada, Repaso
from . import atajos, dialogos
from .tablero_ajedrez import CATEGORIA, CeldaAjedrez, CuadriculaAjedrez
from .ventana_tablero import VentanaBase

# python-chess queda disponible después de importar el paquete «ajedrez».
import chess  # noqa: E402

addonHandler.initTranslation()

_TONO_LIMITE = (220, 80)
_ESPERA_PRESENTACION_MS = 400


class CeldaRepaso(CeldaAjedrez):
	cuadricula: "CuadriculaRepaso"

	@script(
		# Translators: description of a review command in the Input gestures dialog.
		description=_("While reviewing a game, plays the next move"),
		category=CATEGORIA,
		gesture="kb:alt+rightArrow",
	)
	def script_avanzar(self, gesture) -> None:
		self.cuadricula.avanzar()

	@script(
		# Translators: description of a review command in the Input gestures dialog.
		description=_("While reviewing a game, takes back the last move"),
		category=CATEGORIA,
		gesture="kb:alt+leftArrow",
	)
	def script_retroceder(self, gesture) -> None:
		self.cuadricula.retroceder()

	@script(
		# Translators: description of a review command in the Input gestures dialog.
		description=_("While reviewing a game, goes to the starting position"),
		category=CATEGORIA,
		gesture="kb:alt+home",
	)
	def script_ir_al_principio(self, gesture) -> None:
		self.cuadricula.ir_al_principio()

	@script(
		# Translators: description of a review command in the Input gestures dialog.
		description=_("While reviewing a game, goes to the final position"),
		category=CATEGORIA,
		gesture="kb:alt+end",
	)
	def script_ir_al_final(self, gesture) -> None:
		self.cuadricula.ir_al_final()

	def script_estado(self, gesture) -> None:
		ui.message(self.cuadricula.repaso.texto_estado())

	def script_deshacer(self, gesture) -> None:
		self.cuadricula.avisar_solo_lectura()


class CuadriculaRepaso(CuadriculaAjedrez):
	clase_celda = CeldaRepaso

	def __init__(
		self,
		panel: wx.Window,
		ventana: "VentanaRepaso",
		repaso: Repaso,
		color_persona: chess.Color | None,
	) -> None:
		self.repaso = repaso
		# Sin computadora: nadie juega. Si la persona jugó con negras, las ve abajo.
		super().__init__(panel, ventana, repaso.partida, color_persona=color_persona)

	def avisar_solo_lectura(self) -> None:
		tones.beep(*_TONO_LIMITE)
		# Translators: said when trying to move a piece while reviewing a game.
		ui.message(
			_("You are reviewing a game: Alt+Right arrow goes forward and Alt+Left arrow goes back."),
		)

	def activar(self) -> None:
		self.avisar_solo_lectura()

	def escribir_jugada(self) -> None:
		self.avisar_solo_lectura()

	def _al_cambiar_posicion(self) -> None:
		self.origen = None
		self.panel.Refresh()

	def avanzar(self) -> None:
		anuncio = self.repaso.avanzar()
		if anuncio is None:
			tones.beep(*_TONO_LIMITE)
			# Translators: said when trying to go forward at the end of a reviewed game.
			ui.message(_("This is the end of the game."))
			return
		self._al_cambiar_posicion()
		ui.message(anuncio)

	def retroceder(self) -> None:
		anuncio = self.repaso.retroceder()
		if anuncio is None:
			tones.beep(*_TONO_LIMITE)
			# Translators: said when trying to go back at the start of a reviewed game.
			ui.message(_("This is the starting position."))
			return
		self._al_cambiar_posicion()
		ui.message(anuncio)

	def ir_al_principio(self) -> None:
		self.repaso.ir_al_principio()
		self._al_cambiar_posicion()
		# Translators: said after going to the start of a reviewed game.
		ui.message(_("Starting position."))

	def ir_al_final(self) -> None:
		self.repaso.ir_al_final()
		self._al_cambiar_posicion()
		ui.message(self.repaso.texto_estado())

	def mostrar_planilla(self) -> None:
		lineas = self.repaso.completa.planilla()
		if not lineas:
			# Translators: reported when the score sheet has no moves yet.
			ui.message(_("The score sheet is empty."))
			return
		self.ventana.mostrar_modal(dialogos.DialogoPlanilla(self.ventana, lineas, self.repaso.indice - 1))


class VentanaRepaso(VentanaBase):
	cuadricula: CuadriculaRepaso

	def __init__(
		self,
		cargada: PartidaCargada,
		nombre: str,
		texto: str,
		al_cerrar: Callable[[], None],
	) -> None:
		# Translators: title of the window to review a game, for example "MiAjedrezAccesible - Review: Game.pgn".
		super().__init__(_("MiAjedrezAccesible - Review: {name}").format(name=nombre), al_cerrar)
		self.cargada = cargada
		# El texto original del archivo, para copiarlo tal cual.
		self._texto = texto
		self.repaso = Repaso(cargada.partida)
		self._instalar(CuadriculaRepaso(self.panel, self, self.repaso, cargada.color_persona))

	def _al_mostrar_por_primera_vez(self) -> None:
		partes = [
			# Translators: said when a game is opened for review, for example
			# "Reviewing Player against Computer, level 3: 42 moves."
			_("Reviewing {white} against {black}: {moves} moves.").format(
				white=self.cargada.blancas,
				black=self.cargada.negras,
				moves=self.repaso.total,
			),
			# Translators: said when a game is opened for review.
			_(
				"Alt+Right arrow goes forward, Alt+Left arrow goes back, and Alt+Home and Alt+End go to the start or the end.",
			),
		]
		if self.cargada.incompleta:
			# Translators: said when a game file had moves that could not be read.
			partes.append(_("Some moves of the file could not be read: the game is shown up to that point."))
		wx.CallLater(_ESPERA_PRESENTACION_MS, ui.message, " ".join(partes), speechPriority=speech.Spri.NEXT)

	@property
	def contexto_atajos(self) -> atajos.Contexto:
		return atajos.Contexto.REPASO

	def _copiar(self) -> None:
		api.copyToClip(self._texto, notify=False)
		# Translators: reported after copying the game to the clipboard.
		ui.delayedMessage(_("Game copied to the clipboard in PGN format."))

	def mostrar_menu_partida(self) -> None:
		self.mostrar_menu(
			[
				# Translators: item of the game menu.
				(_("&Flip board"), self.cuadricula.girar, True),
				# Translators: item of the review menu.
				(_("Go to the &start"), self.cuadricula.ir_al_principio, True),
				# Translators: item of the review menu.
				(_("Go to the &end"), self.cuadricula.ir_al_final, True),
				# Translators: item of the game menu.
				(_("C&opy game"), self._copiar, True),
				# Translators: item of the review menu.
				(_("&Close review"), self.Close, True),
			],
		)
