# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Diálogos de la partida: escribir una jugada, elegir la pieza de coronación y ver la planilla.

También el diálogo de nueva partida.
Todos son controles normales de Windows, que NVDA lee sin nada especial.
Se muestran con `mostrar_modal`, que los abre fuera de la ejecución de la orden de teclado,
como recomienda NVDA para no bloquear su bucle principal.
"""

from collections.abc import Callable

import addonHandler
import ui
import wx
from gui import guiHelper

from ..ajedrez import notacion
from ..ajedrez.anunciador import mayuscula_inicial, nombre_tipo
from ..ajedrez.configuracion import ConfiguracionPartida, EleccionColor, Modo
from ..ajedrez.motor import NIVELES
from ..ajedrez.reloj import CONTROLES

# python-chess queda disponible después de importar el paquete «ajedrez».
import chess  # noqa: E402

addonHandler.initTranslation()

# Piezas a las que puede coronar un peón, en el orden en que se ofrecen.
PIEZAS_CORONACION = (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)


def comodin_pgn() -> str:
	"""Filtro de los diálogos de abrir y guardar partidas."""
	# Translators: file type in the dialogs to open and save games.
	partidas = _("Chess games")
	# Translators: file type in the dialogs to open and save games.
	todos = _("All files")
	return f"{partidas} (*.pgn)|*.pgn|{todos} (*.*)|*.*"


def mostrar_modal(dialogo: wx.Dialog, al_terminar: Callable[[int], None] | None = None) -> None:
	"""Muestra un diálogo modal sin bloquear la orden que lo pidió y lo destruye al cerrarse."""

	def ejecutar() -> None:
		try:
			resultado = dialogo.ShowModal()
			if al_terminar is not None:
				al_terminar(resultado)
		finally:
			dialogo.Destroy()

	wx.CallAfter(ejecutar)


class DialogoJugada(wx.Dialog):
	"""Campo de texto para escribir una jugada. No se cierra mientras la jugada no sea válida."""

	def __init__(self, padre: wx.Window, interpretar: Callable[[str], object]) -> None:
		# Translators: title of the dialog to type a move.
		super().__init__(padre, title=_("Type a move"))
		self._interpretar = interpretar
		self.jugada: object | None = None
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.campo: wx.TextCtrl = ayudante.addLabeledControl(
			# Translators: label of the field where a move is typed.
			_("&Move:"),
			wx.TextCtrl,
		)
		ayudante.addItem(
			# Translators: help shown under the move field.
			wx.StaticText(self, label=_("Examples: Nf3, exd5, O-O, e8=Q or g1f3.")),
		)
		ayudante.addDialogDismissButtons(wx.OK | wx.CANCEL, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		principal.Fit(self)
		self.Bind(wx.EVT_BUTTON, self._al_aceptar, id=wx.ID_OK)
		self.CentreOnParent()
		self.campo.SetFocus()

	def _al_aceptar(self, evento: wx.CommandEvent) -> None:
		try:
			self.jugada = self._interpretar(self.campo.GetValue())
		except notacion.ErrorJugada as error:
			ui.message(str(error))
			self.campo.SetFocus()
			self.campo.SelectAll()
			return
		self.EndModal(wx.ID_OK)


class DialogoNuevaPartida(wx.Dialog):
	"""Modo, color, nivel y reloj de una partida nueva. Empieza con lo elegido la vez anterior."""

	def __init__(self, padre: wx.Window | None, anterior: ConfiguracionPartida) -> None:
		# Translators: title of the new game dialog.
		super().__init__(padre, title=_("New game"))
		self._modos = list(Modo)
		self._colores = list(EleccionColor)
		self._niveles = sorted(NIVELES)
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.modo: wx.Choice = ayudante.addLabeledControl(
			# Translators: label of the game mode choice in the new game dialog.
			_("&Mode:"),
			wx.Choice,
			choices=[m.etiqueta() for m in self._modos],
		)
		self.color: wx.Choice = ayudante.addLabeledControl(
			# Translators: label of the color choice in the new game dialog.
			_("&Play as:"),
			wx.Choice,
			choices=[c.etiqueta() for c in self._colores],
		)
		self.nivel: wx.Choice = ayudante.addLabeledControl(
			# Translators: label of the difficulty level choice in the new game dialog.
			_("&Level:"),
			wx.Choice,
			choices=[NIVELES[n].descripcion() for n in self._niveles],
		)
		self._relojes = list(CONTROLES)
		self.reloj: wx.Choice = ayudante.addLabeledControl(
			# Translators: label of the clock choice in the new game dialog.
			_("&Clock:"),
			wx.Choice,
			choices=[c.etiqueta() for c in self._relojes],
		)
		ayudante.addDialogDismissButtons(wx.OK | wx.CANCEL, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		principal.Fit(self)
		self.modo.SetSelection(self._modos.index(anterior.modo))
		self.color.SetSelection(self._colores.index(anterior.color))
		self.nivel.SetSelection(self._niveles.index(anterior.nivel))
		self.reloj.SetSelection([c.id for c in self._relojes].index(anterior.reloj))
		self.modo.Bind(wx.EVT_CHOICE, lambda evento: self._actualizar())
		self._actualizar()
		self.CentreOnScreen()
		self.modo.SetFocus()

	def _actualizar(self) -> None:
		# El color y el nivel solo tienen sentido contra la computadora.
		contra_computadora = self._modos[self.modo.GetSelection()] is Modo.COMPUTADORA
		self.color.Enable(contra_computadora)
		self.nivel.Enable(contra_computadora)

	def configuracion(self) -> ConfiguracionPartida:
		return ConfiguracionPartida(
			modo=self._modos[self.modo.GetSelection()],
			color=self._colores[self.color.GetSelection()],
			nivel=self._niveles[self.nivel.GetSelection()],
			reloj=self._relojes[self.reloj.GetSelection()].id,
		)


def dialogo_coronacion(padre: wx.Window) -> wx.SingleChoiceDialog:
	opciones = [mayuscula_inicial(nombre_tipo(tipo)) for tipo in PIEZAS_CORONACION]
	return wx.SingleChoiceDialog(
		padre,
		# Translators: prompt of the dialog shown when a pawn reaches the last rank.
		_("Choose the piece for the promotion:"),
		# Translators: title of the dialog shown when a pawn reaches the last rank.
		_("Promotion"),
		opciones,
	)


class DialogoPlanilla(wx.Dialog):
	"""Lista de las jugadas de la partida, de la primera a la última."""

	def __init__(self, padre: wx.Window, lineas: list[str], seleccion: int | None = None) -> None:
		# Translators: title of the score sheet dialog.
		super().__init__(padre, title=_("Score sheet"))
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.lista: wx.ListBox = ayudante.addLabeledControl(
			# Translators: label of the list of moves in the score sheet.
			_("&Moves:"),
			wx.ListBox,
			choices=lineas,
			size=(500, 300),
		)
		# Translators: button that closes the score sheet.
		ayudante.addDialogDismissButtons(wx.Button(self, wx.ID_CANCEL, _("&Close")), separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		principal.Fit(self)
		self.SetEscapeId(wx.ID_CANCEL)
		if lineas:
			self.lista.SetSelection(
				len(lineas) - 1 if seleccion is None else max(0, min(seleccion, len(lineas) - 1)),
			)
		self.CentreOnParent()
		self.lista.SetFocus()
