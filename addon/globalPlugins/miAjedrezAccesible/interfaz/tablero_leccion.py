# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""El tablero de las lecciones: el mismo de las partidas, con manzanas, pistas y ejercicios."""

from typing import TYPE_CHECKING

import addonHandler
import tones
import ui
import wx
from scriptHandler import script

from ..ajedrez.curso.modelo import TipoEjercicio
from ..ajedrez.curso.sesion import Resultado, SesionEjercicio
from . import sonidos
from .tablero_ajedrez import CATEGORIA, CeldaAjedrez, CuadriculaAjedrez

# python-chess queda disponible después de importar el paquete «ajedrez».
import chess  # noqa: E402

if TYPE_CHECKING:
	from .curso import ControladorCurso
	from .retos import ControladorRetos
	from .ventana_leccion import VentanaLeccion

addonHandler.initTranslation()

_TONO_AVISO = (220, 80)


class CeldaLeccion(CeldaAjedrez):
	cuadricula: "CuadriculaLeccion"

	@script(
		# Translators: description of a lesson command in the Input gestures dialog.
		description=_("Repeats the instruction of the exercise"),
		category=CATEGORIA,
		gesture="kb:f2",
	)
	def script_repetir_instruccion(self, gesture) -> None:
		ui.message(self.cuadricula.controlador.texto_instruccion())

	@script(
		# Translators: description of a lesson command in the Input gestures dialog.
		description=_("Repeats the explanation of the lesson"),
		category=CATEGORIA,
		gesture="kb:shift+f2",
	)
	def script_repetir_explicacion(self, gesture) -> None:
		ui.message(self.cuadricula.controlador.texto_explicacion())

	@script(
		# Translators: description of a lesson command in the Input gestures dialog.
		description=_("Gives a hint for the exercise"),
		category=CATEGORIA,
		gesture="kb:f6",
	)
	def script_pista(self, gesture) -> None:
		ui.message(self.cuadricula.sesion.siguiente_pista())

	@script(
		# Translators: description of a lesson command in the Input gestures dialog.
		description=_("Reports how many apples are left and where"),
		category=CATEGORIA,
		gesture="kb:m",
	)
	def script_manzanas(self, gesture) -> None:
		ui.message(self.cuadricula.sesion.texto_manzanas())

	# Teclas de la partida que en las lecciones cambian.

	def script_estado(self, gesture) -> None:
		ui.message(self.cuadricula.controlador.texto_progreso())

	# En los retos «sin mirar», las teclas de información no dicen qué piezas hay.

	def script_ataques(self, gesture) -> None:
		if not self.cuadricula.avisar_si_a_ciegas():
			super().script_ataques(gesture)

	def script_piezas_propias(self, gesture) -> None:
		if not self.cuadricula.avisar_si_a_ciegas():
			super().script_piezas_propias(gesture)

	def script_piezas_rival(self, gesture) -> None:
		if not self.cuadricula.avisar_si_a_ciegas():
			super().script_piezas_rival(gesture)

	def script_detalle_casilla(self, gesture) -> None:
		if not self.cuadricula.avisar_si_a_ciegas():
			super().script_detalle_casilla(gesture)

	def script_saltar_a_pieza(self, gesture) -> None:
		if not self.cuadricula.avisar_si_a_ciegas():
			super().script_saltar_a_pieza(gesture)

	def script_ultima_jugada(self, gesture) -> None:
		if not self.cuadricula.avisar_si_a_ciegas():
			super().script_ultima_jugada(gesture)

	def script_deshacer(self, gesture) -> None:
		tones.beep(*_TONO_AVISO)
		# Translators: said when pressing Control+Z during a lesson.
		ui.message(
			_(
				"To start the exercise again, open the menu with the Applications key and choose Restart exercise.",
			),
		)


class CuadriculaLeccion(CuadriculaAjedrez):
	clase_celda = CeldaLeccion

	def __init__(
		self,
		panel: wx.Window,
		ventana: "VentanaLeccion",
		controlador: "ControladorCurso | ControladorRetos",
		sesion: SesionEjercicio,
	) -> None:
		self.controlador = controlador
		self.sesion = sesion
		self.esperando_continuar = False
		# En los problemas de Retos también se juega con negras, y entonces se ven abajo.
		super().__init__(panel, ventana, sesion.partida, color_persona=sesion.ejercicio.color)
		self.fila, self.columna = self.posicion(sesion.ejercicio.casilla_inicial())

	def cargar(self, sesion: SesionEjercicio) -> None:
		"""Pone en el tablero un ejercicio nuevo y lleva el foco a su casilla inicial."""
		self.sesion = sesion
		self.partida = sesion.partida
		self.color_persona = sesion.ejercicio.color
		self.girado = self.color_persona == chess.BLACK
		self.origen = None
		self.esperando_continuar = False
		self.fila, self.columna = self.posicion(sesion.ejercicio.casilla_inicial())
		self.panel.Refresh()
		self.enfocar_celda_actual()

	# Manzanas.

	def tiene_marca(self, casilla: chess.Square) -> bool:
		return self.sesion.tiene_manzana(casilla)

	def avisar_si_a_ciegas(self) -> bool:
		"""En un reto «sin mirar», avisa de que no se puede mirar el tablero y devuelve True."""
		if not self.sesion.ejercicio.a_ciegas or self.esperando_continuar:
			return False
		tones.beep(*_TONO_AVISO)
		# Translators: said when trying to look at the pieces during a blindfold challenge.
		ui.message(
			_(
				"In this challenge you cannot look at the board: imagine the position. Press F2 to hear it again.",
			),
		)
		return True

	def nombre_celda(self, fila: int, columna: int) -> str:
		if self.sesion.ejercicio.a_ciegas and not self.esperando_continuar:
			# Reto «sin mirar»: solo la coordenada, sin decir qué pieza hay.
			return chess.square_name(self.casilla(fila, columna))
		texto = super().nombre_celda(fila, columna)
		if self.sesion.tiene_manzana(self.casilla(fila, columna)):
			# Translators: added to the square name when there is an apple to collect on it.
			texto += ", " + _("apple")
		return texto

	def al_enfocar_celda(self, fila: int, columna: int) -> None:
		super().al_enfocar_celda(fila, columna)
		if self.sesion.tiene_manzana(self.casilla(fila, columna)):
			sonidos.reproducir(sonidos.MANZANA_CERCA)

	# Intro, jugadas y resultados.

	def activar(self) -> None:
		if self.esperando_continuar:
			self.controlador.continuar()
			return
		if self.sesion.es_de_casillas:
			self._mostrar_resultado(self.sesion.elegir_casilla(self.casilla_actual))
			return
		if self.sesion.ejercicio.tipo is TipoEjercicio.PARTIDA:
			self.controlador.empezar_partida_del_curso(self.sesion.empezar_partida())
			return
		if self.sesion.ejercicio.solo_escrito:
			tones.beep(*_TONO_AVISO)
			# Translators: said when trying to pick up a piece in an exercise that must be solved by typing.
			ui.message(_("In this exercise, type the move: press J."))
			return
		super().activar()

	def _tras_jugada(self, jugada: chess.Move, anuncio: str, tras_dialogo: bool) -> None:
		resultado = self.sesion.tras_jugada(jugada, anuncio)
		self.panel.Refresh()
		self._mostrar_resultado(resultado, tras_dialogo)

	def _mostrar_resultado(self, resultado: Resultado, tras_dialogo: bool = False) -> None:
		texto = resultado.texto
		sonido = resultado.sonido
		if resultado.completado:
			self.esperando_continuar = True
			texto_extra, sonido_final = self.controlador.ejercicio_completado(resultado)
			texto = f"{texto} {texto_extra}"
			sonido = sonido_final or sonido
		elif resultado.fallo:
			tones.beep(*_TONO_AVISO)
			texto_extra, termina = self.controlador.ejercicio_fallado(resultado)
			texto = f"{texto} {texto_extra}"
			self.esperando_continuar = termina
		elif self.sesion.es_de_casillas and sonido is None:
			# Casilla equivocada: un aviso suave antes de la orientación.
			tones.beep(*_TONO_AVISO)
		if sonido is not None:
			sonidos.reproducir(sonido)
		self.decir(texto, tras_dialogo)

	def escribir_jugada(self) -> None:
		if self.esperando_continuar:
			# Translators: said when trying to play after an exercise is solved.
			ui.message(_("Press Enter to continue."))
			return
		if self.sesion.es_de_casillas:
			tones.beep(*_TONO_AVISO)
			# Translators: said when pressing J in an exercise where no piece has to be moved.
			ui.message(_("In this exercise you do not move pieces: go to the square and press Enter."))
			return
		super().escribir_jugada()

	# Mensajes adaptados a quien aprende.

	def _mensaje_destino_invalido(self, origen: chess.Square) -> str:
		pieza = self.tablero.piece_at(origen)
		recordatorios = {
			# Translators: reminder when a rook is dropped on a square it cannot reach.
			chess.ROOK: _(
				"The rook does not move like that. Remember: only in a straight line, without jumping.",
			),
			# Translators: reminder when a bishop is dropped on a square it cannot reach.
			chess.BISHOP: _(
				"The bishop does not move like that. Remember: only diagonally, without jumping.",
			),
			# Translators: reminder when a queen is dropped on a square it cannot reach.
			chess.QUEEN: _(
				"The queen does not move like that. Remember: in a straight line or diagonally, without jumping.",
			),
			# Translators: reminder when a king is dropped on a square it cannot reach.
			chess.KING: _(
				"The king cannot go there. Remember: only one square, and never to a square that is attacked.",
			),
			# Translators: reminder when a knight is dropped on a square it cannot reach.
			chess.KNIGHT: _("The knight does not move like that. Remember: it moves in an L shape."),
			# Translators: reminder when a pawn is dropped on a square it cannot reach.
			chess.PAWN: _(
				"The pawn does not move like that. Remember: it moves forward and captures diagonally.",
			),
		}
		if pieza is None:
			return super()._mensaje_destino_invalido(origen)
		return recordatorios[pieza.piece_type]

	def _mensaje_pieza_que_no_juega(self) -> str:
		if self.sesion.ejercicio.tipo in (
			TipoEjercicio.GUERRA_PEONES,
			TipoEjercicio.MATE,
			TipoEjercicio.PROBLEMA,
		):
			return super()._mensaje_pieza_que_no_juega()
		# Translators: said when trying to pick up a black piece during a lesson.
		return _("That piece belongs to your opponent: in these exercises it does not move.")
