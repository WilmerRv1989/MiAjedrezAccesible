# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Retos: problemas a tu nivel, por tema, el reto del día y la racha."""

import datetime
import os
import random
from collections.abc import Callable
from enum import StrEnum

import addonHandler
import globalVars
import speech
import ui
import wx
from gui import guiHelper
from gui.message import displayDialogAsModal

from ..ajedrez import anunciador, retos
from ..ajedrez.curso.sesion import Resultado, SesionEjercicio, Sonido
from ..ajedrez.retos import Problema, ProgresoRetos, Retos, Tema
from . import atajos
from .ventana_leccion import VentanaLeccion

# python-chess queda disponible después de importar el paquete «ajedrez».
import chess  # noqa: E402

addonHandler.initTranslation()

_ESPERA_INSTRUCCION_MS = 400


def ruta_progreso() -> str:
	return os.path.join(globalVars.appArgs.configPath, "miAjedrezAccesible", "retos.json")


class Modo(StrEnum):
	NIVEL = "nivel"
	TEMA = "tema"
	DIARIO = "diario"
	RACHA = "racha"


def nombre_modo(modo: Modo) -> str:
	nombres = {
		# Translators: name of a Challenges mode.
		Modo.NIVEL: _("Challenge at your level"),
		# Translators: name of a Challenges mode.
		Modo.TEMA: _("By theme"),
		# Translators: name of a Challenges mode.
		Modo.DIARIO: _("Daily challenge"),
		# Translators: name of a Challenges mode.
		Modo.RACHA: _("Streak"),
	}
	return nombres[modo]


class DialogoTexto(wx.Dialog):
	"""Unos párrafos y dos botones: Empezar y Volver."""

	def __init__(self, titulo: str, parrafos: list[str]) -> None:
		super().__init__(None, title=titulo)
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		for parrafo in parrafos:
			texto = wx.StaticText(self, label=parrafo)
			texto.Wrap(520)
			ayudante.addItem(texto)
		botones = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that starts the challenges.
		empezar = botones.addButton(self, id=wx.ID_OK, label=_("&Start"))
		# Translators: button that goes back to the previous list.
		botones.addButton(self, id=wx.ID_CANCEL, label=_("&Back"))
		ayudante.addDialogDismissButtons(botones, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		principal.Fit(self)
		empezar.SetDefault()
		self.SetEscapeId(wx.ID_CANCEL)
		self.CentreOnScreen()
		empezar.SetFocus()


class DialogoNivelInicial(wx.Dialog):
	"""La primera vez: «¿Cuánto sabes de ajedrez?». Después, el nivel se ajusta solo."""

	def __init__(self) -> None:
		# Translators: title of the Challenges dialogs.
		super().__init__(None, title=_("Challenges"))
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		texto = wx.StaticText(
			self,
			# Translators: introduction shown the first time Challenges are opened.
			label=_(
				"Challenges are real puzzles from games played on Lichess. Your opponent has just moved "
				"and it is your turn: find the best move. After each puzzle your level goes up or down, "
				"so the puzzles adapt to you.",
			),
		)
		texto.Wrap(520)
		ayudante.addItem(texto)
		self.opciones = wx.RadioBox(
			self,
			# Translators: question asked the first time Challenges are opened.
			label=_("How much chess do you know?"),
			choices=[
				# Translators: answer to "How much chess do you know?".
				_("I am learning"),
				# Translators: answer to "How much chess do you know?".
				_("I know how to play"),
				# Translators: answer to "How much chess do you know?".
				_("I play well"),
			],
			majorDimension=1,
			style=wx.RA_SPECIFY_COLS,
		)
		ayudante.addItem(self.opciones)
		botones = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that confirms the starting level of the challenges.
		aceptar = botones.addButton(self, id=wx.ID_OK, label=_("&OK"))
		# Translators: button that closes a dialog without saving.
		botones.addButton(self, id=wx.ID_CANCEL, label=_("&Cancel"))
		ayudante.addDialogDismissButtons(botones, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		principal.Fit(self)
		aceptar.SetDefault()
		self.SetEscapeId(wx.ID_CANCEL)
		self.CentreOnScreen()
		self.opciones.SetFocus()

	def nivel(self) -> int:
		return retos.NIVELES_INICIALES[max(0, self.opciones.GetSelection())]


class DialogoLista(wx.Dialog):
	"""Una lista con un texto de resumen encima y los botones Empezar y Cerrar (o Volver)."""

	def __init__(self, titulo: str, resumen: str, etiqueta: str, elementos: list[str], cerrar: str) -> None:
		super().__init__(None, title=titulo)
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		if resumen:
			texto = wx.StaticText(self, label=resumen)
			texto.Wrap(560)
			ayudante.addItem(texto)
		self.lista: wx.ListBox = ayudante.addLabeledControl(
			etiqueta,
			wx.ListBox,
			choices=elementos,
			size=(560, 220),
		)
		botones = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that starts the selected challenge mode or theme.
		empezar = botones.addButton(self, id=wx.ID_OK, label=_("&Start"))
		botones.addButton(self, id=wx.ID_CANCEL, label=cerrar)
		ayudante.addDialogDismissButtons(botones, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		principal.Fit(self)
		empezar.SetDefault()
		self.SetEscapeId(wx.ID_CANCEL)
		self.lista.SetSelection(0)
		self.lista.Bind(wx.EVT_LISTBOX_DCLICK, lambda evento: self.EndModal(wx.ID_OK))
		self.CentreOnScreen()
		self.lista.SetFocus()

	def elegido(self) -> int:
		return max(0, self.lista.GetSelection())


class ControladorRetos:
	"""Lleva los retos. Tiene la misma forma que el controlador del curso para usar su ventana."""

	contexto_atajos = atajos.Contexto.RETOS

	def __init__(self) -> None:
		self.retos = Retos(retos.cargar_problemas())
		self.progreso = ProgresoRetos(ruta_progreso())
		self.azar = random.Random()
		self.ventana: VentanaLeccion | None = None
		self.sesion: SesionEjercicio | None = None
		self.problema: Problema | None = None
		self.modo = Modo.NIVEL
		self.tema: Tema | None = None
		# Aciertos de la racha en curso.
		self.aciertos = 0
		# Problemas vistos en esta tanda, para no repetirlos.
		self._vistos: set[str] = set()
		# El problema actual ya cambió el nivel (se resolvió o se falló).
		self._registrado = False
		# El reto del día ya se había jugado hoy al empezarlo: no cambia el nivel.
		self._dia_repetido = False

	# Diálogos.

	def abrir(self) -> None:
		wx.CallAfter(self._abrir)

	def _abrir(self) -> None:
		if self.ventana is not None:
			self.ventana.mostrar()
			return
		if self.progreso.nivel is None:
			dialogo = DialogoNivelInicial()
			try:
				if displayDialogAsModal(dialogo) != wx.ID_OK:
					return
				self.progreso.nivel = dialogo.nivel()
			finally:
				dialogo.Destroy()
			self.progreso.guardar()
		self._elegir_modo()

	def _resumen(self) -> str:
		# Translators: summary at the top of the Challenges dialog.
		return _("Your level: {level}. Puzzles solved: {solved}.").format(
			level=self.progreso.nivel,
			solved=len(self.progreso.resueltos),
		)

	def _texto_dia(self) -> str:
		hoy = datetime.date.today()
		seguidos = self.progreso.dias_seguidos_hasta(hoy)
		if not self.progreso.dia_jugado(hoy):
			# Translators: state of the daily challenge in the Challenges dialog.
			estado = _("pending for today.")
		elif self.progreso.dia_resuelto:
			# Translators: state of the daily challenge in the Challenges dialog.
			estado = _("solved today.")
		else:
			# Translators: state of the daily challenge in the Challenges dialog.
			estado = _("played today, not solved. You can try it again.")
		texto = f"{nombre_modo(Modo.DIARIO)}: {estado}"
		if seguidos:
			# Translators: consecutive days with the daily challenge solved.
			texto += " " + ngettext("{n} day in a row.", "{n} days in a row.", seguidos).format(n=seguidos)
		return texto

	def _elegir_modo(self) -> None:
		modos = [Modo.NIVEL, Modo.TEMA, Modo.DIARIO, Modo.RACHA]
		elementos = [
			# Translators: description of a Challenges mode in the list of modes.
			nombre_modo(Modo.NIVEL) + ": " + _("puzzles of a difficulty similar to your level."),
			# Translators: description of a Challenges mode in the list of modes.
			nombre_modo(Modo.TEMA) + ": " + _("checkmates, double attack, pin and more."),
			self._texto_dia(),
			# Translators: description of the Streak mode; {record} is the best streak.
			nombre_modo(Modo.RACHA)
			+ ": "
			+ _("solve as many puzzles in a row as you can, each one a bit harder. Record: {record}.").format(
				record=self.progreso.record_racha,
			),
		]
		dialogo = DialogoLista(
			_("Challenges"),
			self._resumen(),
			# Translators: label of the list of Challenges modes.
			_("&Modes:"),
			elementos,
			# Translators: button that closes the Challenges dialog.
			_("&Close"),
		)
		try:
			respuesta = displayDialogAsModal(dialogo)
			modo = modos[dialogo.elegido()]
		finally:
			dialogo.Destroy()
		if respuesta != wx.ID_OK:
			return
		if modo is Modo.TEMA:
			self._elegir_tema()
		else:
			self._empezar(modo)

	def _elegir_tema(self) -> None:
		temas = list(Tema)
		elementos = []
		for tema in temas:
			# Translators: a theme in the list of themes, for example "Pin. Solved: 3."
			texto = _("{theme}. Solved: {n}.").format(
				theme=retos.nombre_tema(tema),
				n=self.progreso.resueltos_de(tema),
			)
			if tema in (Tema.CLAVADA, Tema.DESCUBIERTA):
				# Translators: added to the themes that are not taught in the lessons.
				texto += " " + _("New: not in the lessons.")
			elementos.append(texto)
		dialogo = DialogoLista(
			# Translators: title of the list of puzzle themes.
			_("Challenges by theme"),
			"",
			# Translators: label of the list of puzzle themes.
			_("&Themes:"),
			elementos,
			# Translators: button that goes back to the list of Challenges modes.
			_("&Back"),
		)
		try:
			respuesta = displayDialogAsModal(dialogo)
			tema = temas[dialogo.elegido()]
		finally:
			dialogo.Destroy()
		if respuesta != wx.ID_OK:
			self._elegir_modo()
			return
		explicacion = DialogoTexto(retos.nombre_tema(tema), [retos.explicacion_tema(tema)])
		try:
			respuesta = displayDialogAsModal(explicacion)
		finally:
			explicacion.Destroy()
		if respuesta != wx.ID_OK:
			self._elegir_tema()
			return
		self._empezar(Modo.TEMA, tema)

	# Problemas.

	def _empezar(self, modo: Modo, tema: Tema | None = None) -> None:
		self.modo = modo
		self.tema = tema
		self.aciertos = 0
		self._vistos = set()
		self._cargar(self._elegir_problema())
		if modo is Modo.TEMA and tema is not None:
			titulo_modo = f"{nombre_modo(modo)}: {retos.nombre_tema(tema)}"
		else:
			titulo_modo = nombre_modo(modo)
		# Translators: title of the Challenges window, for example "Challenges - Streak".
		titulo = _("Challenges - {mode}").format(mode=titulo_modo)
		assert self.sesion is not None
		self.ventana = VentanaLeccion(self, titulo, self.sesion, al_cerrar=self._al_cerrar_ventana)
		self.ventana.mostrar()

	def _elegir_problema(self) -> Problema:
		nivel = self.progreso.nivel or retos.NIVELES_INICIALES[0]
		excluir = self.progreso.resueltos | self._vistos
		if self.modo is Modo.DIARIO:
			return self.retos.del_dia(datetime.date.today())
		if self.modo is Modo.RACHA:
			return self.retos.para_racha(self.aciertos, self._vistos, self.azar)
		return self.retos.cerca_de(nivel, excluir, self.azar, self.tema)

	def _cargar(self, problema: Problema) -> None:
		self._dejar_problema()
		self.problema = problema
		self._vistos.add(problema.id)
		self._registrado = False
		self._dia_repetido = self.modo is Modo.DIARIO and self.progreso.dia_jugado(datetime.date.today())
		ejercicio = retos.ejercicio_de_problema(
			problema,
			self.tema if self.modo is Modo.TEMA else None,
			ver_jugada=self.modo is not Modo.RACHA,
		)
		self.sesion = SesionEjercicio(ejercicio)

	def _dejar_problema(self) -> None:
		"""Al pasar a otro problema o cerrar: si se vio la jugada y no se resolvió, cuenta como fallado."""
		if self.sesion is not None and self.sesion.vio_jugada and not self.sesion.completado:
			self._registrar(resuelto=False)

	def _registrar(self, resuelto: bool) -> int | None:
		"""Cambia el nivel una sola vez por problema. Devuelve el nivel nuevo, o None si no cambia."""
		if self._registrado or self.problema is None or self.modo is Modo.RACHA:
			return None
		self._registrado = True
		nuevo = self.progreso.registrar(self.problema, resuelto, cambia_nivel=not self._dia_repetido)
		if self.modo is Modo.DIARIO:
			self.progreso.registrar_dia(datetime.date.today(), resuelto)
		self.progreso.guardar()
		return nuevo

	def _siguiente(self) -> None:
		if self.ventana is None:
			return
		self._cargar(self._elegir_problema())
		assert self.sesion is not None
		self.ventana.cuadricula.cargar(self.sesion)
		self.anunciar_ejercicio()

	def _al_cerrar_ventana(self) -> None:
		self._dejar_problema()
		self.ventana = None
		self.sesion = None
		self.problema = None

	def cerrar(self) -> None:
		if self.ventana is not None:
			self.ventana.cerrar_sin_preguntar()

	# Lo que usan la ventana y el tablero.

	def texto_instruccion(self) -> str:
		if self.sesion is None or self.problema is None:
			return ""
		if self.modo is Modo.RACHA:
			# Translators: start of each puzzle of a streak, for example "Streak: 3 solved."
			inicio = _("Streak: {n} solved.").format(n=self.aciertos)
		elif self.modo is Modo.DIARIO:
			inicio = nombre_modo(Modo.DIARIO) + "."
		else:
			# Translators: start of each puzzle, for example "Difficulty 850."
			inicio = _("Difficulty {n}.").format(n=self.problema.dificultad)
		return f"{inicio} {self.sesion.instruccion_actual()}"

	def texto_explicacion(self) -> str:
		if self.modo is Modo.TEMA and self.tema is not None:
			return retos.explicacion_tema(self.tema)
		# Translators: explanation of the Challenges, read with Shift+F2.
		return _(
			"Your opponent has just moved and it is your turn: find the best move. F1 lists your pieces "
			"and Shift+F1 those of your opponent. F6 gives hints: first the theme, then which piece to "
			"move and finally the move, but then the puzzle counts as failed.",
		)

	def texto_progreso(self) -> str:
		# Translators: start of the progress report in Challenges, for example "Your level: 1000."
		nivel = _("Your level: {level}.").format(level=self.progreso.nivel)
		return f"{nivel} {self.texto_instruccion()}"

	def anunciar_ejercicio(self, al_abrir: bool = False) -> None:
		texto = self.texto_instruccion()
		if al_abrir:
			wx.CallLater(_ESPERA_INSTRUCCION_MS, ui.message, texto, speechPriority=speech.Spri.NEXT)
		else:
			ui.message(texto, speechPriority=speech.Spri.NEXT)

	def _texto_solucion(self) -> str:
		assert self.sesion is not None
		guion = self.sesion.ejercicio.guion
		if self.sesion.paso >= len(guion):
			return ""
		jugada = chess.Move.from_uci(guion[self.sesion.paso][0])
		# Translators: the correct move of a puzzle, said when a streak ends.
		return _("The move was: {move}").format(
			move=anunciador.describir_jugada(self.sesion.partida.tablero, jugada),
		)

	def ejercicio_fallado(self, resultado: Resultado) -> tuple[str, bool]:
		"""Tras una jugada equivocada. Devuelve el texto que se añade y si el problema termina."""
		if self.modo is Modo.RACHA:
			record = self.progreso.registrar_racha(self.aciertos)
			self.progreso.guardar()
			partes = [
				self._texto_solucion(),
				# Translators: said when a streak ends; {n} is how many puzzles were solved.
				ngettext(
					"Streak over: you solved {n} puzzle.",
					"Streak over: you solved {n} puzzles.",
					self.aciertos,
				).format(n=self.aciertos),
			]
			if record and self.aciertos:
				# Translators: said when a streak beats the record.
				partes.append(_("New record!"))
			else:
				# Translators: the best streak, said when a streak ends.
				partes.append(_("Your record is {n}.").format(n=self.progreso.record_racha))
			# Translators: said at the end of a streak.
			partes.append(_("Press Enter to start a new streak."))
			return " ".join(partes), True
		self._registrar(resuelto=False)
		# Translators: said after a wrong move in a puzzle.
		return _("Try again, or press F6 for a hint."), False

	def ejercicio_completado(self, resultado: Resultado) -> tuple[str, Sonido | None]:
		assert self.sesion is not None
		if self.modo is Modo.RACHA:
			if not self._registrado:
				# Un problema reiniciado después de resolverlo no vuelve a contar.
				self._registrado = True
				self.aciertos += 1
			if self.progreso.registrar_racha(self.aciertos):
				self.progreso.guardar()
			# Translators: said after solving a puzzle of a streak.
			texto = _("Streak: {n}. Press Enter for the next one, a bit harder.").format(n=self.aciertos)
			return texto, None
		partes = []
		limpio = not self.sesion.fallado
		nuevo = self._registrar(resuelto=limpio)
		if self._dia_repetido:
			# Translators: said when the daily challenge is solved again on the same day.
			partes.append(_("You had already played today's challenge, so your level does not change."))
		elif not limpio:
			# Translators: said when a puzzle is solved after a mistake or after the hint told the move.
			partes.append(
				_("Solved, but with a mistake or with the move from a hint. Your level: {level}.").format(
					level=self.progreso.nivel,
				),
			)
		elif nuevo is not None:
			# Translators: said when a puzzle is solved at the first attempt.
			partes.append(_("Your level goes up to {level}.").format(level=nuevo))
		if self.modo is Modo.DIARIO:
			# Los días seguidos cuentan aunque haya habido algún fallo; el nivel, no.
			hoy = datetime.date.today()
			self.progreso.registrar_dia(hoy, True)
			self.progreso.guardar()
			seguidos = self.progreso.dias_seguidos_hasta(hoy)
			if seguidos:
				# Translators: consecutive days with the daily challenge solved.
				partes.append(
					ngettext("{n} day in a row.", "{n} days in a row.", seguidos).format(n=seguidos),
				)
			# Translators: said after the daily challenge.
			partes.append(_("Come back tomorrow for a new one. Press Enter to go back to Challenges."))
		else:
			# Translators: said after solving a puzzle.
			partes.append(_("Press Enter for another puzzle."))
		return " ".join(partes), Sonido.LECCION if self.modo is Modo.DIARIO else None

	def continuar(self) -> None:
		if self.modo is Modo.DIARIO:
			self.volver_a_retos()
			return
		if self.modo is Modo.RACHA and self.sesion is not None and not self.sesion.completado:
			# La racha terminó: empieza otra.
			self.aciertos = 0
			self._vistos = set()
		self._siguiente()

	def reiniciar_ejercicio(self) -> None:
		if self.ventana is None or self.sesion is None:
			return
		# Una sesión nueva del mismo problema, que recuerda si ya se falló.
		anterior = self.sesion
		self.sesion = SesionEjercicio(anterior.ejercicio)
		self.sesion.errores = anterior.errores
		self.sesion.vio_jugada = anterior.vio_jugada
		self.ventana.cuadricula.cargar(self.sesion)
		self.anunciar_ejercicio()

	def otro_problema(self) -> None:
		if self.modo is Modo.RACHA and self.sesion is not None and not self.sesion.completado:
			# Saltar un problema de la racha la termina.
			self.aciertos = 0
			self._vistos = set()
		self._siguiente()

	def volver_a_retos(self) -> None:
		if self.ventana is not None:
			self.ventana.cerrar_sin_preguntar()
		wx.CallAfter(self._abrir)

	def opciones_menu(self, cerrar: Callable[[], None]) -> list[tuple[str, Callable[[], None], bool]]:
		opciones = [
			# Translators: item of the Challenges menu.
			(_("&Restart puzzle"), self.reiniciar_ejercicio, True),
		]
		if self.modo is not Modo.DIARIO:
			# Translators: item of the Challenges menu.
			opciones.append((_("&Another puzzle"), self.otro_problema, True))
		opciones += [
			# Translators: item of the Challenges menu.
			(_("Back to &Challenges"), self.volver_a_retos, True),
			# Translators: item of the Challenges menu.
			(_("&Close"), cerrar, True),
		]
		return opciones
