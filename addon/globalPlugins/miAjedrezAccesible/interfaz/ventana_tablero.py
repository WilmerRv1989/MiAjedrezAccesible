# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Ventana del tablero: el dibujo para quien ve la pantalla y el menú de la partida."""

import datetime
import os
from collections.abc import Callable

import addonHandler
import api
import core
import speech
import tones
import ui
import winUser
import wx
from gui.message import MessageDialog, ReturnCode
from logHandler import log

from ..ajedrez import archivo_pgn
from ..ajedrez.estadisticas import EstadisticasPartidas
from ..ajedrez.configuracion import ConfiguracionPartida, Modo
from ..ajedrez.motor import NIVELES
from ..ajedrez.partida import Partida
from ..ajedrez.reloj import Reloj, texto_tiempo
from . import archivos, atajos, dialogos, preferencias
from .computadora import Computadora
from .tablero_ajedrez import CuadriculaAjedrez

# python-chess queda disponible después de importar el paquete «ajedrez».
import chess  # noqa: E402

addonHandler.initTranslation()

# Colores del dibujo: contraste alto entre casillas, piezas y marcas.
_COLOR_FONDO = wx.Colour(40, 40, 40)
_COLOR_CLARA = wx.Colour(240, 217, 181)
_COLOR_OSCURA = wx.Colour(181, 136, 99)
_COLOR_ULTIMA_JUGADA = wx.Colour(205, 210, 106)
_COLOR_SELECCION = wx.Colour(246, 224, 94)
_COLOR_DESTINO = wx.Colour(47, 133, 90)
_COLOR_FOCO = wx.Colour(30, 111, 217)
_COLOR_PIEZA = wx.Colour(0, 0, 0)
_COLOR_COORDENADA = wx.Colour(255, 255, 255)
_COLOR_MANZANA = wx.Colour(200, 30, 45)

# Símbolos Unicode de las piezas: contorno para las blancas y relleno para las negras.
_SIMBOLOS = {
	chess.WHITE: {
		chess.KING: "♔",
		chess.QUEEN: "♕",
		chess.ROOK: "♖",
		chess.BISHOP: "♗",
		chess.KNIGHT: "♘",
		chess.PAWN: "♙",
	},
	chess.BLACK: {
		chess.KING: "♚",
		chess.QUEEN: "♛",
		chess.ROOK: "♜",
		chess.BISHOP: "♝",
		chess.KNIGHT: "♞",
		chess.PAWN: "♟",
	},
}

_MARGEN = 28
_TAMANO_INICIAL = 640
# Cada cuánto se mira el reloj (fin del tiempo y avisos).
_INTERVALO_RELOJ_MS = 250
_TONO_AVISO_RELOJ = (660, 120)
# Al ocultar el tablero, el mensaje espera a que NVDA anuncie la ventana que recibe el foco.
_ESPERA_OCULTAR_MS = 1000


class PanelTablero(wx.Panel):
	"""Dibuja el tablero y recibe el foco del sistema. NVDA lo cambia por la casilla virtual."""

	def __init__(self, padre: wx.Window) -> None:
		super().__init__(padre, style=wx.WANTS_CHARS)
		# Translators: accessible name of the chess board.
		self.SetLabel(_("Chess board"))
		self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
		self.cuadricula: CuadriculaAjedrez | None = None
		self.Bind(wx.EVT_PAINT, self._al_pintar)
		self.Bind(wx.EVT_SIZE, lambda evento: self.Refresh())

	def AcceptsFocus(self) -> bool:
		return True

	def _lado_casilla(self) -> int:
		ancho, alto = self.GetClientSize()
		return max(8, (min(ancho, alto) - 2 * _MARGEN) // 8)

	def rectangulo_casilla(self, fila: int, columna: int) -> tuple[int, int, int, int]:
		lado = self._lado_casilla()
		return (_MARGEN + columna * lado, _MARGEN + fila * lado, lado, lado)

	def _al_pintar(self, evento: wx.PaintEvent) -> None:
		dc = wx.AutoBufferedPaintDC(self)
		dc.SetBackground(wx.Brush(_COLOR_FONDO))
		dc.Clear()
		cuadricula = self.cuadricula
		if cuadricula is None:
			return
		tablero = cuadricula.tablero
		lado = self._lado_casilla()
		ultima = tablero.move_stack[-1] if tablero.move_stack else None
		destinos = cuadricula.destinos()
		fuente_piezas = wx.Font(
			wx.FontInfo(max(6, int(lado * 0.55))).FaceName("Segoe UI Symbol"),
		)
		fuente_coordenadas = wx.Font(wx.FontInfo(max(6, _MARGEN // 2)).Bold())
		for fila in range(8):
			for columna in range(8):
				casilla = cuadricula.casilla(fila, columna)
				x, y, _ancho, _alto = self.rectangulo_casilla(fila, columna)
				oscura = (chess.square_file(casilla) + chess.square_rank(casilla)) % 2 == 0
				color = _COLOR_OSCURA if oscura else _COLOR_CLARA
				if casilla == cuadricula.origen:
					color = _COLOR_SELECCION
				elif ultima is not None and casilla in (ultima.from_square, ultima.to_square):
					color = _COLOR_ULTIMA_JUGADA
				dc.SetPen(wx.TRANSPARENT_PEN)
				dc.SetBrush(wx.Brush(color))
				dc.DrawRectangle(x, y, lado, lado)
				pieza = tablero.piece_at(casilla)
				if pieza is not None:
					dc.SetFont(fuente_piezas)
					dc.SetTextForeground(_COLOR_PIEZA)
					simbolo = _SIMBOLOS[pieza.color][pieza.piece_type]
					ancho_texto, alto_texto = dc.GetTextExtent(simbolo)
					dc.DrawText(simbolo, x + (lado - ancho_texto) // 2, y + (lado - alto_texto) // 2)
				if cuadricula.tiene_marca(casilla):
					dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))
					dc.SetBrush(wx.Brush(_COLOR_MANZANA))
					dc.DrawCircle(x + lado // 2, y + lado // 2, max(4, lado // 4))
					dc.SetPen(wx.TRANSPARENT_PEN)
				if casilla in destinos:
					dc.SetBrush(wx.Brush(_COLOR_DESTINO))
					dc.DrawCircle(x + lado // 2, y + lado // 2, max(3, lado // 8))
				if fila == cuadricula.fila and columna == cuadricula.columna:
					dc.SetBrush(wx.TRANSPARENT_BRUSH)
					dc.SetPen(wx.Pen(_COLOR_FOCO, max(2, lado // 16)))
					dc.DrawRectangle(x, y, lado, lado)
		# Coordenadas alrededor del tablero.
		dc.SetFont(fuente_coordenadas)
		dc.SetTextForeground(_COLOR_COORDENADA)
		for indice in range(8):
			casilla_columna = cuadricula.casilla(7, indice)
			letra = chess.FILE_NAMES[chess.square_file(casilla_columna)]
			x, y, _ancho, _alto = self.rectangulo_casilla(7, indice)
			ancho_texto, _alto_texto = dc.GetTextExtent(letra)
			dc.DrawText(letra, x + (lado - ancho_texto) // 2, y + lado + 4)
			casilla_fila = cuadricula.casilla(indice, 0)
			numero = chess.RANK_NAMES[chess.square_rank(casilla_fila)]
			x, y, _ancho, _alto = self.rectangulo_casilla(indice, 0)
			ancho_texto, alto_texto = dc.GetTextExtent(numero)
			dc.DrawText(numero, (_MARGEN - ancho_texto) // 2, y + (lado - alto_texto) // 2)


class VentanaBase(wx.Frame):
	"""Ventana con un tablero: lo que comparten las partidas y las lecciones."""

	cuadricula: CuadriculaAjedrez

	def __init__(self, titulo: str, al_cerrar: Callable[[], None]) -> None:
		super().__init__(None, title=titulo, size=(_TAMANO_INICIAL, _TAMANO_INICIAL))
		self._al_cerrar = al_cerrar
		self._cerrando_sin_preguntar = False
		self._iniciada = False
		self.panel = PanelTablero(self)
		self.Bind(wx.EVT_CLOSE, self._al_cerrar_ventana)
		self.Bind(wx.EVT_ACTIVATE, self._al_activar)
		self.CentreOnScreen()

	def _instalar(self, cuadricula: CuadriculaAjedrez) -> None:
		"""Cada subclase crea su cuadrícula después de inicializar la ventana y la instala aquí."""
		self.cuadricula = cuadricula
		self.panel.cuadricula = cuadricula

	def _al_mostrar_por_primera_vez(self) -> None:
		"""Se llama una sola vez, cuando la ventana se muestra por primera vez."""

	def _confirmar_cierre(self) -> bool:
		"""Si devuelve False, la ventana no se cierra."""
		return True

	def mostrar(self) -> None:
		self.Show()
		self.Raise()
		winUser.setForegroundWindow(self.GetHandle())
		self.panel.SetFocus()
		if not self._iniciada:
			self._iniciada = True
			self._al_mostrar_por_primera_vez()

	def cerrar_sin_preguntar(self) -> None:
		self._cerrando_sin_preguntar = True
		self.Close(force=True)

	def _al_activar(self, evento: wx.ActivateEvent) -> None:
		if evento.GetActive():
			self.panel.SetFocus()
		evento.Skip()

	def _al_cerrar_ventana(self, evento: wx.CloseEvent) -> None:
		if not self._cerrando_sin_preguntar and evento.CanVeto() and not self._confirmar_cierre():
			evento.Veto()
			return
		self._antes_de_destruir()
		self.cuadricula.cerrar()
		self._al_cerrar()
		self.Destroy()

	def _antes_de_destruir(self) -> None:
		"""Se llama justo antes de cerrar la ventana."""

	# Reloj y diálogos. Solo las partidas con reloj redefinen estos métodos.

	def al_jugar(self) -> None:
		"""Se llama después de cada jugada, de la persona o de la computadora."""

	def al_cambiar(self) -> None:
		"""Se llama cuando la partida cambia sin una jugada nueva: al deshacer o al aceptar tablas."""

	def suspender_reloj(self) -> None:
		"""Mientras hay un menú o un diálogo abierto."""

	def continuar_reloj(self) -> None:
		"""Cierra una suspensión de `suspender_reloj`."""

	def texto_reloj(self) -> str:
		# Translators: reported when pressing F7 where there is no clock.
		return _("There is no clock here.")

	def mostrar_modal(self, dialogo: wx.Dialog, al_terminar: Callable[[int], None] | None = None) -> None:
		"""Como `dialogos.mostrar_modal`, con el reloj suspendido mientras el diálogo está abierto."""
		self.suspender_reloj()

		def terminar(resultado: int) -> None:
			self.continuar_reloj()
			if al_terminar is not None:
				al_terminar(resultado)

		dialogos.mostrar_modal(dialogo, terminar)

	def _confirmar(self, mensaje: str, titulo: str) -> bool:
		"""Pregunta Aceptar o Cancelar, con el reloj suspendido."""
		self.suspender_reloj()
		try:
			return MessageDialog.confirm(mensaje, titulo, parent=self) == ReturnCode.OK
		finally:
			self.continuar_reloj()

	# Atajos de teclado.

	@property
	def contexto_atajos(self) -> atajos.Contexto:
		return atajos.Contexto.PARTIDA

	def mostrar_atajos(self) -> None:
		wx.CallAfter(atajos.mostrar, {self.contexto_atajos: self.cuadricula.celda_actual})

	def mostrar_menu(self, opciones: list[tuple[str, Callable[[], None], bool]]) -> None:
		"""Menú emergente sobre la casilla actual. Cada opción: (texto, acción, habilitada).

		Todos los menús terminan igual: «Atajos de teclado» y, al final, cerrar.
		"""
		# Translators: item of the menus of the board windows.
		opciones = [*opciones[:-1], (_("&Keyboard shortcuts"), self.mostrar_atajos, True), opciones[-1]]
		menu = wx.Menu()
		for texto, accion, habilitada in opciones:
			elemento = menu.Append(wx.ID_ANY, texto)
			elemento.Enable(habilitada)
			menu.Bind(wx.EVT_MENU, lambda evento, accion=accion: wx.CallAfter(accion), elemento)
		wx.CallAfter(self._abrir_menu, menu)

	def _abrir_menu(self, menu: wx.Menu) -> None:
		x, y, lado, _alto = self.panel.rectangulo_casilla(self.cuadricula.fila, self.cuadricula.columna)
		self.suspender_reloj()
		try:
			self.panel.PopupMenu(menu, wx.Point(x + lado // 2, y + lado // 2))
		finally:
			self.continuar_reloj()
			menu.Destroy()

	def mostrar_menu_partida(self) -> None:
		raise NotImplementedError


class VentanaTablero(VentanaBase):
	"""Ventana de una partida. Se oculta desde el menú de la partida y se cierra con Alt+F4.

	Si la partida tiene reloj, lo lleva aquí: lo pone en marcha, lo pasa de un bando a otro,
	lo suspende con los menús y diálogos, avisa del tiempo que queda y termina la partida
	cuando se acaba. Tras cada cambio guarda la partida para poder continuarla si NVDA se cierra.
	"""

	def __init__(
		self,
		partida: Partida,
		configuracion: ConfiguracionPartida,
		al_ocultar: Callable[[], None],
		al_cerrar: Callable[[], None],
		al_pedir_nueva_partida: Callable[[], None],
		restante: dict[chess.Color, float] | None = None,
	) -> None:
		if configuracion.modo is Modo.COMPUTADORA:
			# Translators: title of the chess board window when playing against the computer.
			titulo = _("MiAjedrezAccesible - Against the computer, level {level}").format(
				level=configuracion.nivel,
			)
		else:
			# Translators: title of the chess board window for a game between two people.
			titulo = _("MiAjedrezAccesible - Two players")
		control = configuracion.control_tiempo
		if control.con_reloj:
			titulo = f"{titulo} - {control.etiqueta()}"
		super().__init__(titulo, al_cerrar)
		self.partida = partida
		self.configuracion = configuracion
		self._al_ocultar = al_ocultar
		self._al_pedir_nueva_partida = al_pedir_nueva_partida
		self.color_persona = configuracion.color_persona()
		computadora = None
		if self.color_persona is not None:
			computadora = Computadora(NIVELES[configuracion.nivel], al_fallar=self._fallo_de_la_computadora)
		self.reloj: Reloj | None = None
		if control.con_reloj:
			# Contra la computadora solo cuenta el tiempo de la persona.
			cuentan = (self.color_persona,) if self.color_persona is not None else (chess.WHITE, chess.BLACK)
			self.reloj = Reloj(control, cuentan, restante)
		self._pausado_al_ocultar = False
		# El resultado se anota en las estadísticas una sola vez por partida.
		self._resultado_anotado = False
		self._temporizador = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self._al_temporizador, self._temporizador)
		self._instalar(CuadriculaAjedrez(self.panel, self, partida, self.color_persona, computadora))

	def _al_mostrar_por_primera_vez(self) -> None:
		if self.reloj is not None and not self.partida.terminada:
			self.reloj.poner_en_marcha(self.partida.turno)
			self._temporizador.Start(_INTERVALO_RELOJ_MS)
		self.cuadricula.iniciar()

	def _fallo_de_la_computadora(self) -> None:
		self.cuadricula.fallo_de_la_computadora()

	def mostrar(self) -> None:
		super().mostrar()
		if self._pausado_al_ocultar and self.reloj is not None:
			# El reloj se pausó al ocultar el tablero: sigue al volver.
			self._pausado_al_ocultar = False
			self.reloj.reanudar()

	def ocultar(self) -> None:
		if self.reloj is not None and not self.reloj.pausado and not self.partida.terminada:
			self.reloj.pausar()
			self._pausado_al_ocultar = True
		self.guardar_automatico()
		self.Hide()
		self._al_ocultar()
		# El foco se va a otra ventana: se espera a que NVDA la anuncie.
		core.callLater(
			_ESPERA_OCULTAR_MS,
			ui.message,
			# Translators: reported after hiding the board from the game menu.
			_("Board hidden. To return, open Tools, MiAjedrezAccesible, Return to the game."),
		)

	def _confirmar_cierre(self) -> bool:
		if self.partida.en_curso and not self._confirmar(
			# Translators: asked when closing the board window during a game.
			_("The game is in progress. If you close the board, the game will be lost. Close it?"),
			# Translators: title of the confirmation to close the board.
			_("Close the board"),
		):
			return False
		# Cerrar a propósito descarta la partida: ya no se ofrecerá continuarla.
		archivos.borrar(archivos.ruta_guardado_automatico())
		return True

	def _antes_de_destruir(self) -> None:
		self._temporizador.Stop()

	# Reloj.

	def al_jugar(self) -> None:
		if self.reloj is not None and self.partida.historial:
			if self.partida.terminada:
				self.reloj.detener()
			else:
				self.reloj.tras_jugada(self.partida.historial[-1].color, self.partida.turno)
		self._anotar_resultado()
		self.guardar_automatico()

	def al_cambiar(self) -> None:
		if self.reloj is not None:
			if self.partida.terminada:
				self.reloj.detener()
			else:
				self.reloj.poner_en_marcha(self.partida.turno)
		self._anotar_resultado()
		self.guardar_automatico()

	def _anotar_resultado(self) -> None:
		if self._resultado_anotado or not self.partida.terminada:
			return
		self._resultado_anotado = True
		try:
			estadisticas = EstadisticasPartidas(archivos.ruta_estadisticas())
			estadisticas.registrar(self.partida, self.configuracion, self.color_persona)
			estadisticas.guardar()
		except OSError:
			log.debugWarning("No se pudo guardar el resultado de la partida", exc_info=True)

	def suspender_reloj(self) -> None:
		if self.reloj is not None:
			self.reloj.suspender()

	def continuar_reloj(self) -> None:
		if self.reloj is not None:
			self.reloj.continuar()

	def texto_reloj(self) -> str:
		reloj = self.reloj
		if reloj is None:
			# Translators: reported when pressing F7 in a game without a clock.
			return _("This game has no clock.")
		if self.color_persona is not None:
			# Translators: time left on your clock, for example "Your time: 4 minutes and 32 seconds."
			texto = _("Your time: {time}.").format(time=texto_tiempo(reloj.tiempo(self.color_persona)))
		else:
			# Translators: time left on both clocks, for example "White: 4 minutes. Black: 3 minutes and 10 seconds."
			texto = _("White: {white}. Black: {black}.").format(
				white=texto_tiempo(reloj.tiempo(chess.WHITE)),
				black=texto_tiempo(reloj.tiempo(chess.BLACK)),
			)
		if reloj.pausado and not self.partida.terminada:
			# Translators: added to the time left when the clock is paused.
			texto += " " + _("The clock is paused.")
		return texto

	def _texto_aviso(self, color: chess.Color, segundos: int) -> str:
		tiempo = texto_tiempo(segundos)
		if self.color_persona is not None:
			# Translators: warning when little time is left, for example "Time left: 30 seconds."
			return _("Time left: {time}.").format(time=tiempo)
		if color == chess.WHITE:
			# Translators: warning for white when little time is left, for example "White, time left: 30 seconds."
			return _("White, time left: {time}.").format(time=tiempo)
		# Translators: warning for black when little time is left, for example "Black, time left: 30 seconds."
		return _("Black, time left: {time}.").format(time=tiempo)

	def _al_temporizador(self, evento: wx.TimerEvent) -> None:
		reloj = self.reloj
		if reloj is None or self.partida.terminada:
			self._temporizador.Stop()
			return
		color = reloj.agotado()
		if color is not None:
			self._sin_tiempo(color)
			return
		aviso = reloj.aviso_pendiente()
		if aviso is not None and preferencias.avisos_reloj():
			tones.beep(*_TONO_AVISO_RELOJ)
			ui.message(self._texto_aviso(*aviso), speechPriority=speech.Spri.NEXT)

	def _sin_tiempo(self, color: chess.Color) -> None:
		texto = self.partida.perder_por_tiempo(color)
		self._temporizador.Stop()
		if self.cuadricula.computadora is not None:
			self.cuadricula.computadora.descartar_pendientes()
		self.cuadricula.origen = None
		self.panel.Refresh()
		self.al_cambiar()
		tones.beep(*_TONO_AVISO_RELOJ)
		ui.message(texto)

	def _pausar_o_reanudar(self) -> None:
		if self.reloj is None or self.partida.terminada:
			return
		if self.reloj.pausado:
			self.reloj.reanudar()
			# Translators: reported after resuming the clock from the game menu.
			self.cuadricula.decir_al_volver(_("Clock running."))
		else:
			self.reloj.pausar()
			# Translators: reported after pausing the clock from the game menu.
			self.cuadricula.decir_al_volver(
				_("Clock paused. It runs again when you play a move or choose Resume clock."),
			)
		self.guardar_automatico()

	# Guardar la partida.

	def texto_pgn(self) -> str:
		return archivo_pgn.exportar(self.partida, self.configuracion, self.color_persona, self.reloj)

	def guardar_automatico(self) -> None:
		"""Guarda la partida en curso para poder continuarla; si terminó, borra lo guardado."""
		ruta = archivos.ruta_guardado_automatico()
		if self.partida.terminada or not self.partida.historial:
			archivos.borrar(ruta)
			return
		try:
			archivos.escribir(ruta, self.texto_pgn())
		except OSError:
			log.debugWarning("No se pudo guardar la partida en curso", exc_info=True)

	def _guardar_partida(self) -> None:
		dialogo = wx.FileDialog(
			self,
			# Translators: title of the dialog to save a game.
			_("Save game"),
			defaultDir=archivos.carpeta_partidas(),
			defaultFile=archivo_pgn.nombre_archivo(datetime.datetime.now()),
			wildcard=dialogos.comodin_pgn(),
			style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
		)

		def al_terminar(resultado: int) -> None:
			if resultado != wx.ID_OK:
				return
			ruta = dialogo.GetPath()
			if not ruta.lower().endswith(".pgn"):
				ruta += ".pgn"
			try:
				archivos.escribir(ruta, self.texto_pgn())
			except OSError:
				log.error("No se pudo guardar la partida", exc_info=True)
				# Translators: reported when a game cannot be saved.
				self.cuadricula.decir_al_volver(_("The game could not be saved."))
				return
			# Translators: reported after saving a game, for example "Game saved: Game 2026-10-03 15.30.pgn".
			self.cuadricula.decir_al_volver(_("Game saved: {name}").format(name=os.path.basename(ruta)))

		self.mostrar_modal(dialogo, al_terminar)

	def _copiar_partida(self) -> None:
		api.copyToClip(self.texto_pgn(), notify=False)
		# Translators: reported after copying the game to the clipboard.
		self.cuadricula.decir_al_volver(_("Game copied to the clipboard in PGN format."))

	# Menú de la partida (tecla Aplicaciones o Mayúsculas+F10).

	def mostrar_menu_partida(self) -> None:
		en_juego = not self.partida.terminada
		if self.cuadricula.contra_computadora:
			# Translators: item of the game menu when playing against the computer.
			tablas = _("Offer a &draw")
		else:
			# Translators: item of the game menu in a game between two people.
			tablas = _("Agree to a &draw")
		opciones: list[tuple[str, Callable[[], None], bool]] = [
			# Translators: item of the game menu.
			(_("&Flip board"), self.cuadricula.girar, True),
			(tablas, self._acordar_tablas, en_juego),
			# Translators: item of the game menu.
			(_("&Resign"), self._abandonar, en_juego),
		]
		if self.reloj is not None:
			if self.reloj.pausado:
				# Translators: item of the game menu that starts the paused clock again.
				pausa = _("Res&ume clock")
			else:
				# Translators: item of the game menu that pauses the clock.
				pausa = _("Pa&use clock")
			opciones.append((pausa, self._pausar_o_reanudar, en_juego))
		opciones += [
			# Translators: item of the game menu.
			(_("&Save game..."), self._guardar_partida, True),
			# Translators: item of the game menu.
			(_("C&opy game"), self._copiar_partida, True),
			# Translators: item of the game menu.
			(_("&New game"), self._al_pedir_nueva_partida, True),
			# Translators: item of the game menu.
			(_("&Hide board"), self.ocultar, True),
			# Translators: item of the game menu.
			(_("&Close board"), self.Close, True),
		]
		self.mostrar_menu(opciones)

	def _acordar_tablas(self) -> None:
		if self.cuadricula.contra_computadora:
			self.cuadricula.ofrecer_tablas()
			return
		if self._confirmar(
			# Translators: asked before ending the game in a draw by agreement.
			_("Do both players agree to a draw?"),
			# Translators: title of the draw confirmation.
			_("Draw"),
		):
			self._terminar_partida(self.partida.acordar_tablas())

	def _abandonar(self) -> None:
		if self.cuadricula.contra_computadora:
			# Translators: asked before resigning a game against the computer.
			if self._confirmar(_("Resign the game?"), _("Resign")):
				self.cuadricula.computadora.descartar_pendientes()
				self._terminar_partida(self.partida.abandonar(self.cuadricula.bando_propio))
			return
		if self.partida.turno == chess.WHITE:
			# Translators: asked before white resigns.
			pregunta = _("Does white resign the game?")
		else:
			# Translators: asked before black resigns.
			pregunta = _("Does black resign the game?")
		# Translators: title of the resign confirmation.
		if self._confirmar(pregunta, _("Resign")):
			self._terminar_partida(self.partida.abandonar(self.partida.turno))

	def _terminar_partida(self, anuncio: str) -> None:
		self.cuadricula.origen = None
		self.panel.Refresh()
		self.al_cambiar()
		self.cuadricula.decir_al_volver(anuncio)

	def confirmar_deshacer(self) -> None:
		def preguntar() -> None:
			if self._confirmar(
				# Translators: asked before undoing the last move.
				_("Undo the last move?"),
				# Translators: title of the undo confirmation.
				_("Undo"),
			):
				self.cuadricula.deshacer_confirmado()

		wx.CallAfter(preguntar)
