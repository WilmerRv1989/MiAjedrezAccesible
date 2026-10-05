# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Panel del complemento en las opciones de NVDA (Preferencias, Opciones, MiAjedrezAccesible)."""

from collections.abc import Callable
from typing import ClassVar

import addonHandler
import ui
import wx
from gui import guiHelper
from gui.message import MessageDialog, ReturnCode
from gui.settingsDialogs import SettingsPanel

from ..ajedrez.anunciador import FormaJugada
from . import preferencias

addonHandler.initTranslation()


def _etiqueta_forma(forma: FormaJugada) -> str:
	if forma is FormaJugada.PALABRAS:
		# Translators: option for announcing moves in the settings panel.
		return _("In words (white knight from g1 to f3)")
	if forma is FormaJugada.NOTACION:
		# Translators: option for announcing moves in the settings panel.
		return _("In notation (Nf3)")
	# Translators: option for announcing moves in the settings panel.
	return _("Both (Nf3, white knight from g1 to f3)")


class PanelMiAjedrez(SettingsPanel):
	# Translators: title of the add-on panel in NVDA's settings.
	title = _("MiAjedrezAccesible")
	# Lo pone el complemento: borra el progreso y devuelve False si no se pudo (por ejemplo,
	# con una lección abierta).
	al_borrar_progreso: ClassVar[Callable[[], bool] | None] = None

	def makeSettings(self, settingsSizer: wx.BoxSizer) -> None:
		ayudante = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		datos = preferencias.seccion()
		self._formas = list(FormaJugada)
		self.forma: wx.Choice = ayudante.addLabeledControl(
			# Translators: label of the choice of how moves are announced, in the settings panel.
			_("&Announce moves:"),
			wx.Choice,
			choices=[_etiqueta_forma(f) for f in self._formas],
		)
		forma = datos["anuncio_jugadas"]
		self.forma.SetSelection(
			self._formas.index(FormaJugada(forma)) if forma in FormaJugada._value2member_map_ else 0,
		)
		self.casilla_primero: wx.CheckBox = ayudante.addItem(
			# Translators: check box in the settings panel.
			wx.CheckBox(self, label=_("Say the &square before the piece (g1, white knight)")),
		)
		self.casilla_primero.SetValue(bool(datos["casilla_primero"]))
		self.sonidos: wx.CheckBox = ayudante.addItem(
			# Translators: check box in the settings panel.
			wx.CheckBox(self, label=_("Play s&ounds (apples, correct answers, lessons completed)")),
		)
		self.sonidos.SetValue(bool(datos["sonidos"]))
		self.avisos: wx.CheckBox = ayudante.addItem(
			# Translators: check box in the settings panel.
			wx.CheckBox(self, label=_("&Warn when little time is left on the clock")),
		)
		self.avisos.SetValue(bool(datos["avisos_reloj"]))
		borrar = ayudante.addItem(
			# Translators: button in the settings panel.
			wx.Button(self, label=_("&Delete my progress and statistics...")),
		)
		borrar.Bind(wx.EVT_BUTTON, self._al_borrar)

	def onSave(self) -> None:
		datos = preferencias.seccion()
		datos["anuncio_jugadas"] = self._formas[self.forma.GetSelection()].value
		datos["casilla_primero"] = self.casilla_primero.GetValue()
		datos["sonidos"] = self.sonidos.GetValue()
		datos["avisos_reloj"] = self.avisos.GetValue()
		preferencias.aplicar()

	def _al_borrar(self, evento: wx.CommandEvent) -> None:
		respuesta = MessageDialog.confirm(
			# Translators: asked before deleting the progress and statistics.
			_(
				"This deletes your progress in the course and in Challenges, and the statistics of your games. "
				"It cannot be undone. Delete them?",
			),
			# Translators: title of the confirmation to delete the progress.
			_("Delete my progress and statistics"),
			parent=self,
		)
		if respuesta != ReturnCode.OK:
			return
		borrar = type(self).al_borrar_progreso
		if borrar is not None and borrar():
			# Translators: reported after deleting the progress and statistics.
			ui.message(_("Your progress and statistics were deleted."))
