# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""El tablero de ajedrez como cuadrícula virtual: casillas, teclas, tomar y soltar piezas."""

from typing import TYPE_CHECKING

import addonHandler
import speech
import tones
import ui
import wx
from scriptHandler import script

from ..ajedrez import anunciador, motor, notacion
from ..ajedrez.notacion import ErrorJugada
from ..ajedrez.partida import Partida
from ..nucleo.tablero_virtual import CeldaVirtual, CuadriculaVirtual
from . import dialogos
from .computadora import Computadora

# python-chess queda disponible después de importar el paquete «ajedrez».
import chess  # noqa: E402

if TYPE_CHECKING:
	from .ventana_tablero import VentanaTablero

addonHandler.initTranslation()

# Translators: category of the add-on commands in the Input gestures dialog.
CATEGORIA = _("MiAjedrezAccesible")

# Letras españolas para saltar a las piezas.
LETRAS_PIEZAS = {
	"r": chess.KING,
	"d": chess.QUEEN,
	"t": chess.ROOK,
	"a": chess.BISHOP,
	"c": chess.KNIGHT,
	"p": chess.PAWN,
}

# Tonos: error y destino posible.
_TONO_ERROR = (220, 80)
_TONO_POSIBLE = (880, 25)


def _tono_error() -> None:
	tones.beep(*_TONO_ERROR)


def decir(texto: str, tras_dialogo: bool = False) -> None:
	"""Dice un texto. Tras cerrar un diálogo, el foco vuelve al tablero y NVDA anuncia la casilla:
	por eso el texto se retrasa un instante, para que no lo corte."""
	if tras_dialogo:
		ui.delayedMessage(texto)
	else:
		ui.message(texto)


class CeldaAjedrez(CeldaVirtual):
	"""Casilla del tablero. Aquí están todas las teclas que funcionan dentro del tablero."""

	cuadricula: "CuadriculaAjedrez"

	# Navegación.

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Moves to the square above"),
		category=CATEGORIA,
		gesture="kb:upArrow",
	)
	def script_arriba(self, gesture) -> None:
		self.cuadricula.mover(-1, 0)

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Moves to the square below"),
		category=CATEGORIA,
		gesture="kb:downArrow",
	)
	def script_abajo(self, gesture) -> None:
		self.cuadricula.mover(1, 0)

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Moves to the square on the left"),
		category=CATEGORIA,
		gesture="kb:leftArrow",
	)
	def script_izquierda(self, gesture) -> None:
		self.cuadricula.mover(0, -1)

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Moves to the square on the right"),
		category=CATEGORIA,
		gesture="kb:rightArrow",
	)
	def script_derecha(self, gesture) -> None:
		self.cuadricula.mover(0, 1)

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Moves to the first square of the row"),
		category=CATEGORIA,
		gesture="kb:home",
	)
	def script_inicio_fila(self, gesture) -> None:
		self.cuadricula.ir_a(self.cuadricula.fila, 0)

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Moves to the last square of the row"),
		category=CATEGORIA,
		gesture="kb:end",
	)
	def script_fin_fila(self, gesture) -> None:
		self.cuadricula.ir_a(self.cuadricula.fila, self.cuadricula.columnas - 1)

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Moves to the rank of the number pressed, keeping the file"),
		category=CATEGORIA,
		gestures=[f"kb:{n}" for n in range(1, 9)],
	)
	def script_ir_a_fila(self, gesture) -> None:
		self.cuadricula.ir_a_fila_del_tablero(int(gesture.mainKeyName) - 1)

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_(
			"Moves to your next piece of that type (between two people, of the side to move): "
			"R king, D queen, T rook, A bishop, C knight, P pawn. With shift, the opponent's pieces",
		),
		category=CATEGORIA,
		gestures=[f"kb:{letra}" for letra in LETRAS_PIEZAS]
		+ [f"kb:shift+{letra}" for letra in LETRAS_PIEZAS],
	)
	def script_saltar_a_pieza(self, gesture) -> None:
		tipo = LETRAS_PIEZAS.get(gesture.mainKeyName)
		if tipo is None:
			return
		rival = "shift" in gesture.modifierNames
		self.cuadricula.saltar_a_pieza(tipo, rival)

	# Jugar.

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Picks up the piece on this square, or drops the selected piece here"),
		category=CATEGORIA,
		gestures=["kb:enter", "kb:numpadEnter", "kb:space"],
	)
	def script_activar(self, gesture) -> None:
		self.cuadricula.activar()

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Opens a field to type a move"),
		category=CATEGORIA,
		gesture="kb:j",
	)
	def script_escribir_jugada(self, gesture) -> None:
		self.cuadricula.escribir_jugada()

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Undoes the last move"),
		category=CATEGORIA,
		gesture="kb:control+z",
	)
	def script_deshacer(self, gesture) -> None:
		self.cuadricula.deshacer()

	# Información.

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Reports which pieces attack and defend this square"),
		category=CATEGORIA,
		gesture="kb:x",
	)
	def script_ataques(self, gesture) -> None:
		ui.message(anunciador.describir_ataques(self.cuadricula.tablero, self.cuadricula.casilla_actual))

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Lists your pieces (between two people, those of the side to move)"),
		category=CATEGORIA,
		gesture="kb:f1",
	)
	def script_piezas_propias(self, gesture) -> None:
		ui.message(anunciador.describir_piezas(self.cuadricula.tablero, self.cuadricula.bando_propio))

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Lists the opponent's pieces"),
		category=CATEGORIA,
		gesture="kb:shift+f1",
	)
	def script_piezas_rival(self, gesture) -> None:
		ui.message(anunciador.describir_piezas(self.cuadricula.tablero, not self.cuadricula.bando_propio))

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Moves to the destination square of the last move"),
		category=CATEGORIA,
		gesture="kb:l",
	)
	def script_ultima_jugada(self, gesture) -> None:
		self.cuadricula.ir_a_ultima_jugada()

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Reports the coordinate, color and content of this square"),
		category=CATEGORIA,
		gesture="kb:f3",
	)
	def script_detalle_casilla(self, gesture) -> None:
		ui.message(
			anunciador.describir_detalle_casilla(self.cuadricula.tablero, self.cuadricula.casilla_actual),
		)

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Opens the score sheet with all the moves"),
		category=CATEGORIA,
		gesture="kb:f4",
	)
	def script_planilla(self, gesture) -> None:
		self.cuadricula.mostrar_planilla()

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Reports whose turn it is, the move number and the last move"),
		category=CATEGORIA,
		gesture="kb:f5",
	)
	def script_estado(self, gesture) -> None:
		ui.message(self.cuadricula.partida.texto_estado())

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Reports the time left on the clock"),
		category=CATEGORIA,
		gesture="kb:f7",
	)
	def script_reloj(self, gesture) -> None:
		ui.message(self.cuadricula.ventana.texto_reloj())

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Shows the keyboard shortcuts of this window"),
		category=CATEGORIA,
	)
	def script_atajos(self, gesture) -> None:
		self.cuadricula.ventana.mostrar_atajos()

	# Ventana.

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Opens the game menu"),
		category=CATEGORIA,
		gestures=["kb:applications", "kb:shift+f10"],
	)
	def script_menu(self, gesture) -> None:
		self.cuadricula.ventana.mostrar_menu_partida()

	@script(
		# Translators: description of a chess board command in the Input gestures dialog.
		description=_("Drops the selected piece without moving it"),
		category=CATEGORIA,
		gesture="kb:escape",
	)
	def script_escape(self, gesture) -> None:
		if self.cuadricula.origen is not None:
			self.cuadricula.cancelar_seleccion()
		else:
			_tono_error()
			# Translators: reported when pressing Escape with no piece picked up.
			ui.message(_("No piece is selected."))


class CuadriculaAjedrez(CuadriculaVirtual):
	clase_celda = CeldaAjedrez

	def __init__(
		self,
		panel: wx.Window,
		ventana: "VentanaTablero",
		partida: Partida,
		color_persona: chess.Color | None = None,
		computadora: Computadora | None = None,
	) -> None:
		self.ventana = ventana
		self.partida = partida
		# Color con el que juega la persona contra la computadora; None entre dos personas.
		self.color_persona = color_persona
		self.computadora = computadora
		# Quien juega con negras las ve abajo.
		self.girado = color_persona == chess.BLACK
		# Casilla de la pieza tomada, o None si no hay ninguna.
		self.origen: chess.Square | None = None
		super().__init__(panel, filas=8, columnas=8)
		rey = self.tablero.king(self.bando_propio)
		self.fila, self.columna = self.posicion(rey if rey is not None else chess.E1)

	@property
	def tablero(self) -> chess.Board:
		return self.partida.tablero

	@property
	def contra_computadora(self) -> bool:
		return self.computadora is not None and self.color_persona is not None

	@property
	def bando_propio(self) -> chess.Color:
		"""Las piezas «propias»: las de la persona contra la computadora, o las del turno entre dos."""
		return self.color_persona if self.color_persona is not None else self.partida.turno

	def es_turno_computadora(self) -> bool:
		return self.contra_computadora and self.partida.turno != self.color_persona

	def _avisar_si_piensa(self) -> bool:
		"""Si la computadora tiene el turno, lo dice y devuelve True."""
		if self.partida.terminada or not self.es_turno_computadora():
			return False
		_tono_error()
		# Translators: reported when trying to play while the computer is choosing its move.
		ui.message(_("Wait: the computer is thinking."))
		return True

	def cerrar(self) -> None:
		if self.computadora is not None:
			self.computadora.cerrar()
		super().cerrar()

	# La computadora.

	def iniciar(self) -> None:
		"""Se llama al abrir el tablero: si la computadora empieza, se le pide su jugada."""
		self._turno_de_la_computadora()

	def _turno_de_la_computadora(self) -> None:
		if self.computadora is None or self.partida.terminada or not self.es_turno_computadora():
			return
		self.computadora.pedir_jugada(self.tablero, self._jugada_de_la_computadora)

	def _jugada_de_la_computadora(self, jugada: chess.Move) -> None:
		try:
			anuncio = self.partida.jugar(jugada)
		except ErrorJugada:
			return
		self.ventana.al_jugar()
		self.panel.Refresh()
		# En cola: no interrumpe el anuncio de la jugada de la persona.
		ui.message(
			# Translators: announcement of the computer's move, for example
			# "Computer: black knight from b8 to c6. White to move."
			_("Computer: {move}").format(move=anuncio),
			speechPriority=speech.Spri.NEXT,
		)

	def fallo_de_la_computadora(self) -> None:
		_tono_error()
		# Translators: reported when the chess engine cannot be started or stops working.
		ui.message(_("The computer could not play. Close the board and start a new game."))

	def ofrecer_tablas(self) -> None:
		if self.computadora is None or self.color_persona is None:
			return
		if self._avisar_si_piensa():
			return
		color_computadora = not self.color_persona

		def al_evaluar(valor_para_quien_mueve: int) -> None:
			if self.partida.turno == color_computadora:
				valor = valor_para_quien_mueve
			else:
				valor = -valor_para_quien_mueve
			if motor.acepta_tablas(valor):
				texto = self.partida.acordar_tablas()
				self.ventana.al_cambiar()
				self.origen = None
				self.panel.Refresh()
				# Translators: reported when the computer accepts a draw offer; followed by the result.
				ui.message(_("The computer accepts the draw.") + " " + texto)
			else:
				# Translators: reported when the computer declines a draw offer.
				ui.message(_("The computer declines the draw."))

		# Translators: reported while the computer considers a draw offer.
		ui.delayedMessage(_("Offering a draw..."))
		self.computadora.evaluar(self.tablero, al_evaluar)

	# Conversión entre la cuadrícula visual (fila 0 arriba) y las casillas del ajedrez.

	def casilla(self, fila: int, columna: int) -> chess.Square:
		if self.girado:
			return chess.square(7 - columna, fila)
		return chess.square(columna, 7 - fila)

	def posicion(self, casilla: chess.Square) -> tuple[int, int]:
		columna, fila = chess.square_file(casilla), chess.square_rank(casilla)
		if self.girado:
			return fila, 7 - columna
		return 7 - fila, columna

	@property
	def casilla_actual(self) -> chess.Square:
		return self.casilla(self.fila, self.columna)

	def destinos(self) -> set[chess.Square]:
		return self.partida.destinos_legales(self.origen) if self.origen is not None else set()

	def tiene_marca(self, casilla: chess.Square) -> bool:
		"""Casillas con una marca que se dibuja, como las manzanas de las lecciones."""
		return False

	# Lo que NVDA dice de cada casilla.

	def nombre_celda(self, fila: int, columna: int) -> str:
		casilla = self.casilla(fila, columna)
		texto = anunciador.describir_casilla(self.tablero, casilla)
		if casilla == self.origen:
			# Translators: added to the square name when its piece has been picked up.
			texto += ", " + _("selected piece")
		elif casilla in self.destinos():
			# Translators: added to the square name when the selected piece can move there.
			texto += ", " + _("possible")
		return texto

	def al_enfocar_celda(self, fila: int, columna: int) -> None:
		super().al_enfocar_celda(fila, columna)
		if self.casilla(fila, columna) in self.destinos():
			tones.beep(*_TONO_POSIBLE)

	def rectangulo_celda(self, fila: int, columna: int) -> tuple[int, int, int, int] | None:
		return self.panel.rectangulo_casilla(fila, columna)

	# Navegación propia del ajedrez.

	def ir_a_fila_del_tablero(self, fila_ajedrez: int) -> None:
		columna_ajedrez = chess.square_file(self.casilla_actual)
		self.ir_a(*self.posicion(chess.square(columna_ajedrez, fila_ajedrez)))

	def ir_a_ultima_jugada(self) -> None:
		jugada = self.partida.ultima_jugada()
		if jugada is None:
			# Translators: announced when no move has been played yet.
			ui.message(_("No moves yet."))
			return
		self.fila, self.columna = self.posicion(jugada.to_square)
		self.enfocar_celda_actual()

	def saltar_a_pieza(self, tipo: chess.PieceType, rival: bool) -> None:
		color = not self.bando_propio if rival else self.bando_propio
		casillas = sorted(self.tablero.pieces(tipo, color))
		if not casillas:
			pieza = anunciador.nombre_pieza(chess.Piece(tipo, color))
			# Translators: reported when jumping to a piece type that is not on the board.
			ui.message(_("There is no {piece}.").format(piece=pieza))
			return
		siguientes = [c for c in casillas if c > self.casilla_actual]
		destino = siguientes[0] if siguientes else casillas[0]
		self.fila, self.columna = self.posicion(destino)
		self.enfocar_celda_actual()

	def girar(self) -> None:
		casilla = self.casilla_actual
		self.girado = not self.girado
		self.fila, self.columna = self.posicion(casilla)
		self.panel.Refresh()
		if self.girado:
			# Translators: reported after flipping the board.
			ui.delayedMessage(_("Board flipped: black at the bottom."))
		else:
			# Translators: reported after flipping the board.
			ui.delayedMessage(_("Board flipped: white at the bottom."))

	# Tomar y soltar piezas.

	def activar(self) -> None:
		casilla = self.casilla_actual
		if self.partida.terminada:
			_tono_error()
			ui.message(self.partida.texto_final())
			return
		if self._avisar_si_piensa():
			return
		if self.origen is None:
			self._tomar(casilla)
		elif casilla == self.origen:
			self.cancelar_seleccion()
		elif casilla in self.destinos():
			self._mover(self.origen, casilla)
		elif self._se_puede_tomar(casilla):
			self._tomar(casilla)
		else:
			_tono_error()
			ui.message(self._mensaje_destino_invalido(self.origen))

	# Mensajes que el tablero de las lecciones adapta.

	def _mensaje_destino_invalido(self, origen: chess.Square) -> str:
		# Translators: reported when the selected piece cannot move to the current square.
		return _("The selected piece cannot go there.")

	def _mensaje_pieza_que_no_juega(self) -> str:
		# Translators: reported when trying to pick up a piece of the side not to move.
		return _("That piece cannot move now.")

	def _se_puede_tomar(self, casilla: chess.Square) -> bool:
		pieza = self.tablero.piece_at(casilla)
		return (
			pieza is not None
			and pieza.color == self.partida.turno
			and bool(self.partida.destinos_legales(casilla))
		)

	def _tomar(self, casilla: chess.Square) -> None:
		pieza = self.tablero.piece_at(casilla)
		if pieza is None:
			_tono_error()
			# Translators: reported when trying to pick up a piece on an empty square.
			ui.message(_("Empty square."))
			return
		if pieza.color != self.partida.turno:
			_tono_error()
			ui.message(self._mensaje_pieza_que_no_juega())
			return
		if not self.partida.destinos_legales(casilla):
			_tono_error()
			# Translators: reported when trying to pick up a piece that has no legal moves.
			ui.message(_("That piece has no legal moves."))
			return
		self.origen = casilla
		self.panel.Refresh()
		# Translators: reported after picking up a piece.
		ui.message(_("Piece selected."))

	def cancelar_seleccion(self) -> None:
		self.origen = None
		self.panel.Refresh()
		# Translators: reported after dropping the selected piece back without moving it.
		ui.message(_("Selection cancelled."))

	def _mover(self, origen: chess.Square, destino: chess.Square) -> None:
		if self.partida.requiere_coronacion(origen, destino):
			self._preguntar_coronacion(origen, destino)
		else:
			self._jugar(chess.Move(origen, destino), tras_dialogo=False)

	def _preguntar_coronacion(self, origen: chess.Square, destino: chess.Square) -> None:
		dialogo = dialogos.dialogo_coronacion(self.ventana)

		def al_terminar(resultado: int) -> None:
			if resultado != wx.ID_OK:
				# Translators: reported when the promotion dialog is cancelled.
				ui.delayedMessage(_("Promotion cancelled. The pawn stays selected."))
				return
			pieza = dialogos.PIEZAS_CORONACION[dialogo.GetSelection()]
			self._jugar(chess.Move(origen, destino, promotion=pieza), tras_dialogo=True)

		self.ventana.mostrar_modal(dialogo, al_terminar)

	def _jugar(self, jugada: chess.Move, tras_dialogo: bool) -> None:
		try:
			anuncio = self.partida.jugar(jugada)
		except ErrorJugada as error:
			_tono_error()
			ui.message(str(error))
			return
		self.origen = None
		self.fila, self.columna = self.posicion(jugada.to_square)
		self.panel.Refresh()
		self.ventana.al_jugar()
		self._tras_jugada(jugada, anuncio, tras_dialogo)

	def _tras_jugada(self, jugada: chess.Move, anuncio: str, tras_dialogo: bool) -> None:
		"""Anuncia la jugada de la persona y, si corresponde, da el turno a la computadora."""
		decir(anuncio, tras_dialogo)
		self._turno_de_la_computadora()

	def escribir_jugada(self) -> None:
		if self.partida.terminada:
			_tono_error()
			ui.message(self.partida.texto_final())
			return
		if self._avisar_si_piensa():
			return
		dialogo = dialogos.DialogoJugada(self.ventana, self._interpretar_jugada)

		def al_terminar(resultado: int) -> None:
			jugada = dialogo.jugada
			if resultado != wx.ID_OK or not isinstance(jugada, chess.Move):
				return
			self.origen = None
			if jugada.promotion is None and self.partida.requiere_coronacion(
				jugada.from_square,
				jugada.to_square,
			):
				self.origen = jugada.from_square
				self._preguntar_coronacion(jugada.from_square, jugada.to_square)
			else:
				self._jugar(jugada, tras_dialogo=True)

		self.ventana.mostrar_modal(dialogo, al_terminar)

	def _interpretar_jugada(self, texto: str) -> chess.Move:
		return notacion.interpretar(self.tablero, texto)

	def _jugadas_a_deshacer(self) -> int:
		"""Cuántas medias jugadas se deshacen para que vuelva a ser el turno de la persona."""
		if not self.contra_computadora:
			return 1
		# Si le toca a la persona, se deshacen la respuesta de la computadora y la jugada previa.
		# Si no (la persona terminó la partida con su jugada), solo esa jugada.
		return 2 if self.partida.turno == self.color_persona else 1

	def deshacer(self) -> None:
		if self._avisar_si_piensa():
			return
		if len(self.partida.historial) < self._jugadas_a_deshacer():
			_tono_error()
			# Translators: reported when there is no move to undo.
			ui.message(_("There are no moves to undo."))
			return
		self.ventana.confirmar_deshacer()

	def deshacer_confirmado(self) -> None:
		if self.es_turno_computadora() and not self.partida.terminada:
			# La computadora empezó a pensar mientras se confirmaba: no se deshace nada.
			return
		anuncio = self.partida.deshacer(self._jugadas_a_deshacer())
		if anuncio is None:
			return
		if self.computadora is not None:
			self.computadora.descartar_pendientes()
		self.origen = None
		self.panel.Refresh()
		self.ventana.al_cambiar()
		ui.delayedMessage(anuncio)

	def mostrar_planilla(self) -> None:
		lineas = self.partida.planilla()
		if not lineas:
			# Translators: reported when the score sheet has no moves yet.
			ui.message(_("The score sheet is empty."))
			return
		self.ventana.mostrar_modal(dialogos.DialogoPlanilla(self.ventana, lineas))
