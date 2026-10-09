# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Punto de entrada del complemento: el submenú en Herramientas de NVDA y la partida abierta."""

import os

import addonHandler
import globalPluginHandler
import globalVars
import gui
import wx
from gui.message import MessageDialog, ReturnCode, displayDialogAsModal
from logHandler import log
from NVDAObjects import NVDAObject
from NVDAObjects.window import Window
from scriptHandler import script

from .ajedrez import archivo_pgn, idioma
from .ajedrez.archivo_pgn import PartidaCargada
from .ajedrez.configuracion import ConfiguracionPartida
from .ajedrez.partida import Partida
from .interfaz import archivos, atajos, estadisticas, preferencias
from .interfaz.curso import ControladorCurso
from .interfaz.dialogos import DialogoNuevaPartida, comodin_pgn
from .interfaz.panel_configuracion import PanelMiAjedrez
from .interfaz.repaso import CeldaRepaso, VentanaRepaso
from .interfaz.tablero_ajedrez import CeldaAjedrez
from .interfaz.tablero_leccion import CeldaLeccion
from .interfaz.retos import ControladorRetos
from .interfaz.ventana_tablero import VentanaTablero
from .nucleo import tablero_virtual

addonHandler.initTranslation()
idioma.configurar(_, ngettext)

# Translators: name of the add-on, used as the submenu label and the input gestures category.
NOMBRE = _("MiAjedrezAccesible")

# Preferencias del complemento y lo último elegido en el diálogo de nueva partida.
preferencias.registrar()


# Respuesta de `_ofrecer_continuar` cuando se cierra la pregunta sin elegir.
_CANCELADO = object()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = NOMBRE

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._elemento_submenu: wx.MenuItem | None = None
		self._elemento_volver: wx.MenuItem | None = None
		self._ventana: VentanaTablero | None = None
		self._repaso: VentanaRepaso | None = None
		self._curso: ControladorCurso | None = None
		self._retos: ControladorRetos | None = None
		# En las pantallas seguras (inicio de sesión, control de cuentas) no hay menús ni ventanas.
		if globalVars.appArgs.secure:
			return
		self._crear_menu()
		PanelMiAjedrez.al_borrar_progreso = self._borrar_progreso
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(PanelMiAjedrez)

	# Menú en Herramientas.

	def _crear_menu(self) -> None:
		bandeja = gui.mainFrame.sysTrayIcon
		self._submenu = wx.Menu()
		nueva = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that starts a new chess game.
			_("&New game..."),
			# Translators: help text of the "New game" menu item.
			_("Start a new chess game"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.nueva_partida(), nueva)
		abrir = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that opens a saved game.
			_("&Open game..."),
			# Translators: help text of the "Open game" menu item.
			_("Continue a saved game or review a finished one"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.abrir_partida(), abrir)
		aprender = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that opens the chess course.
			_("&Learn to play..."),
			# Translators: help text of the "Learn to play" menu item.
			_("Guided lessons for people who are learning chess"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.aprender_a_jugar(), aprender)
		elemento_retos = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that opens the chess puzzles.
			_("&Challenges..."),
			# Translators: help text of the "Challenges" menu item.
			_("Chess puzzles that adapt to your level"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.abrir_retos(), elemento_retos)
		elemento_estadisticas = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that shows the statistics.
			_("My &statistics..."),
			# Translators: help text of the "My statistics" menu item.
			_("Your games, your progress in the course and in Challenges"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.mostrar_estadisticas(), elemento_estadisticas)
		elemento_atajos = self._submenu.Append(
			wx.ID_ANY,
			# Translators: item of the add-on submenu that shows all the keyboard shortcuts.
			_("&Keyboard shortcuts..."),
			# Translators: help text of the "Keyboard shortcuts" menu item.
			_("The keys of the board, the lessons, Challenges and the review"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.mostrar_atajos(), elemento_atajos)
		self._elemento_volver = wx.MenuItem(
			self._submenu,
			wx.ID_ANY,
			# Translators: item of the add-on submenu that shows a hidden game again.
			_("&Return to the game"),
			# Translators: help text of the "Return to the game" menu item.
			_("Show the board of the game in progress"),
		)
		bandeja.Bind(wx.EVT_MENU, lambda evento: self.volver_a_la_partida(), self._elemento_volver)
		self._elemento_submenu = bandeja.toolsMenu.AppendSubMenu(
			self._submenu,
			# Translators: label of the add-on submenu inside NVDA's Tools menu.
			_("Mi&AjedrezAccesible"),
			# Translators: help text of the add-on submenu.
			_("Accessible chess games"),
		)

	def _actualizar_menu(self) -> None:
		"""«Volver a la partida» solo aparece si hay un tablero oculto."""
		elemento = self._elemento_volver
		if elemento is None:
			return
		hay_oculta = self._ventana is not None and not self._ventana.IsShown()
		esta_en_menu = self._submenu.FindItemById(elemento.GetId()) is not None
		if hay_oculta and not esta_en_menu:
			self._submenu.Append(elemento)
		elif not hay_oculta and esta_en_menu:
			self._submenu.Remove(elemento)

	def terminate(self) -> None:
		if PanelMiAjedrez in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(PanelMiAjedrez)
		PanelMiAjedrez.al_borrar_progreso = None
		preferencias.quitar()
		if self._ventana is not None:
			# Se guarda con el tiempo actual del reloj, para continuarla al volver a NVDA.
			self._ventana.guardar_automatico()
			self._ventana.cerrar_sin_preguntar()
			self._ventana = None
		if self._repaso is not None:
			self._repaso.cerrar_sin_preguntar()
			self._repaso = None
		if self._curso is not None:
			self._curso.cerrar()
			self._curso = None
		if self._retos is not None:
			self._retos.cerrar()
			self._retos = None
		if (
			self._elemento_volver is not None
			and self._submenu.FindItemById(self._elemento_volver.GetId()) is None
		):
			# Si no está en el menú, nadie más lo destruye.
			self._elemento_volver.Destroy()
		self._elemento_volver = None
		if self._elemento_submenu is not None:
			try:
				gui.mainFrame.sysTrayIcon.toolsMenu.Remove(self._elemento_submenu)
				self._elemento_submenu.Destroy()
			except (RuntimeError, AttributeError):
				log.debugWarning("No se pudo quitar el menú de MiAjedrezAccesible", exc_info=True)
			self._elemento_submenu = None
		super().terminate()

	# Curso «Aprender a jugar».

	def aprender_a_jugar(self) -> None:
		if self._curso is None:
			try:
				self._curso = ControladorCurso(al_empezar_partida=self.empezar_partida_configurada)
			except Exception:
				log.error("No se pudo cargar el curso de MiAjedrezAccesible", exc_info=True)
				return
		self._curso.abrir_lista()

	@script(
		# Translators: description of the command that opens the chess course, shown in the Input gestures dialog.
		description=_("Opens the chess course Learn to play"),
	)
	def script_aprender_a_jugar(self, gesture) -> None:
		self.aprender_a_jugar()

	# Retos.

	def abrir_retos(self) -> None:
		if self._retos is None:
			try:
				self._retos = ControladorRetos()
			except Exception:
				log.error("No se pudieron cargar los retos de MiAjedrezAccesible", exc_info=True)
				return
		self._retos.abrir()

	@script(
		# Translators: description of the command that opens the chess puzzles, shown in the Input gestures dialog.
		description=_("Opens the chess Challenges"),
	)
	def script_retos(self, gesture) -> None:
		self.abrir_retos()

	# Estadísticas y progreso.

	def mostrar_estadisticas(self) -> None:
		wx.CallAfter(estadisticas.mostrar)

	@script(
		# Translators: description of the command that shows the statistics, shown in the Input gestures dialog.
		description=_("Shows your chess statistics"),
	)
	def script_estadisticas(self, gesture) -> None:
		self.mostrar_estadisticas()

	def mostrar_atajos(self) -> None:
		"""Todas las teclas, de todas las ventanas. Se consultan con casillas creadas solo para eso."""
		contextos = {
			atajos.Contexto.PARTIDA: CeldaAjedrez(cuadricula=None, fila=0, columna=0),
			atajos.Contexto.LECCION: CeldaLeccion(cuadricula=None, fila=0, columna=0),
			atajos.Contexto.RETOS: CeldaLeccion(cuadricula=None, fila=0, columna=0),
			atajos.Contexto.REPASO: CeldaRepaso(cuadricula=None, fila=0, columna=0),
		}
		wx.CallAfter(atajos.mostrar, contextos)

	def _borrar_progreso(self) -> bool:
		"""Cierra las lecciones y los retos abiertos y borra el progreso y las estadísticas."""
		for controlador in (self._curso, self._retos):
			if controlador is not None:
				controlador.cerrar()
		# Se vuelven a crear al abrirlos, ya sin progreso.
		self._curso = None
		self._retos = None
		for ruta in archivos.rutas_de_progreso():
			archivos.borrar(ruta)
		return True

	# Partidas.

	def nueva_partida(self) -> None:
		wx.CallAfter(self._nueva_partida)

	def empezar_partida_configurada(self, configuracion: ConfiguracionPartida) -> None:
		"""Empieza una partida sin pasar por el diálogo (por ejemplo, desde el curso)."""
		wx.CallAfter(self._empezar, configuracion, None)

	def _nueva_partida(self) -> None:
		if self._ventana is None:
			decision = self._ofrecer_continuar()
			if decision is _CANCELADO:
				return
			if decision is not None:
				self._empezar(decision.configuracion, None, decision)
				return
		padre = self._ventana if self._ventana is not None and self._ventana.IsShown() else None
		dialogo = DialogoNuevaPartida(padre, preferencias.configuracion_guardada())
		try:
			if displayDialogAsModal(dialogo) != wx.ID_OK:
				return
			configuracion = dialogo.configuracion()
		finally:
			dialogo.Destroy()
		preferencias.guardar_configuracion(configuracion)
		self._empezar(configuracion, padre)

	def _ofrecer_continuar(self) -> "PartidaCargada | object | None":
		"""Si quedó una partida sin terminar (NVDA se cerró con ella), pregunta si continuarla.

		Devuelve la partida si hay que continuarla, `_CANCELADO` si se cerró la pregunta,
		o None para empezar una nueva.
		"""
		ruta = archivos.ruta_guardado_automatico()
		if not os.path.isfile(ruta):
			return None
		try:
			cargada = archivo_pgn.importar(archivos.leer(ruta))
		except Exception:
			log.debugWarning("No se pudo leer la partida en curso guardada", exc_info=True)
			cargada = None
		if cargada is None or not cargada.se_puede_continuar:
			archivos.borrar(ruta)
			return None
		respuesta = MessageDialog.ask(
			# Translators: asked when starting a game while an unfinished game was saved.
			_("You have an unfinished game, after {moves} moves. Do you want to continue it?").format(
				moves=len(cargada.partida.historial),
			),
			# Translators: title of the question about an unfinished game.
			_("Unfinished game"),
			# Translators: button that continues the unfinished game.
			yesLabel=_("&Continue the game"),
			# Translators: button that discards the unfinished game and starts a new one.
			noLabel=_("&New game"),
		)
		if respuesta == ReturnCode.YES:
			return cargada
		if respuesta == ReturnCode.NO:
			return None
		return _CANCELADO

	def _empezar(
		self,
		configuracion: ConfiguracionPartida,
		padre: wx.Window | None,
		cargada: PartidaCargada | None = None,
	) -> None:
		if self._ventana is not None:
			if self._ventana.partida.en_curso:
				respuesta = MessageDialog.confirm(
					# Translators: asked when starting a new game while another one is in progress.
					_(
						"A game is in progress. If you start a new one, the current game will be lost. Start a new game?",
					),
					# Translators: title of the confirmation to start a new game.
					_("New game"),
					parent=padre,
				)
				if respuesta != ReturnCode.OK:
					return
			self._ventana.cerrar_sin_preguntar()
			self._ventana = None
		self._ventana = VentanaTablero(
			cargada.partida if cargada is not None else Partida(),
			configuracion,
			al_ocultar=self._actualizar_menu,
			al_cerrar=self._al_cerrar_ventana,
			al_pedir_nueva_partida=self.nueva_partida,
			restante=cargada.restante if cargada is not None else None,
		)
		# Una partida nueva sustituye a la que quedó guardada; una continuada pasa a ser la guardada.
		self._ventana.guardar_automatico()
		self._ventana.mostrar()
		self._actualizar_menu()
		if cargada is not None:
			# Translators: said when a saved game is continued; followed by the game state.
			continuada = _("Game continued.")
			self._ventana.cuadricula.decir_al_volver(f"{continuada} {cargada.partida.texto_estado()}")

	# Abrir partidas guardadas.

	def abrir_partida(self) -> None:
		wx.CallAfter(self._abrir_partida)

	def _abrir_partida(self) -> None:
		dialogo = wx.FileDialog(
			gui.mainFrame,
			# Translators: title of the dialog to open a saved game.
			_("Open game"),
			defaultDir=archivos.carpeta_partidas(),
			wildcard=comodin_pgn(),
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		)
		try:
			if displayDialogAsModal(dialogo) != wx.ID_OK:
				return
			ruta = dialogo.GetPath()
		finally:
			dialogo.Destroy()
		try:
			texto = archivos.leer(ruta)
			cargada = archivo_pgn.importar(texto)
		except Exception:
			log.debugWarning("No se pudo abrir la partida %s", ruta, exc_info=True)
			cargada = None
		if cargada is None:
			MessageDialog.alert(
				# Translators: reported when the chosen file does not contain a chess game.
				_("This file does not contain a chess game that can be read."),
				# Translators: title of the dialog to open a saved game.
				_("Open game"),
			)
			return
		if cargada.se_puede_continuar and cargada.configuracion is not None:
			self._empezar(cargada.configuracion, None, cargada)
			return
		if self._repaso is not None:
			self._repaso.cerrar_sin_preguntar()
		self._repaso = VentanaRepaso(cargada, os.path.basename(ruta), texto, al_cerrar=self._al_cerrar_repaso)
		self._repaso.mostrar()

	def _al_cerrar_repaso(self) -> None:
		self._repaso = None

	def volver_a_la_partida(self) -> None:
		if self._ventana is None:
			self.nueva_partida()
			return
		wx.CallAfter(self._mostrar_ventana)

	def _mostrar_ventana(self) -> None:
		if self._ventana is not None:
			self._ventana.mostrar()
			self._actualizar_menu()

	def _al_cerrar_ventana(self) -> None:
		self._ventana = None
		self._actualizar_menu()

	# Integración con NVDA.

	def chooseNVDAObjectOverlayClasses(self, obj: NVDAObject, clsList: list[type[NVDAObject]]) -> None:
		# El panel que dibuja el tablero pasa el foco a la casilla virtual actual.
		if isinstance(obj, Window) and tablero_virtual.cuadricula_de_ventana(obj.windowHandle):
			clsList.insert(0, tablero_virtual.PanelCuadricula)

	@script(
		# Translators: description of the command that opens the chess board, shown in the Input gestures dialog.
		description=_("Opens the chess board: returns to the game in progress or starts a new one"),
	)
	def script_abrir_tablero(self, gesture) -> None:
		if self._ventana is not None:
			self.volver_a_la_partida()
		else:
			self.nueva_partida()
