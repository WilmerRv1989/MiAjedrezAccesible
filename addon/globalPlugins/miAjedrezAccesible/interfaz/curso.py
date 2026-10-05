# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""«Aprender a jugar»: lista de lecciones, presentación, ejercicios y «Practicar más»."""

import os
from collections.abc import Callable

import addonHandler
import globalVars
import languageHandler
import speech
import ui
import wx
from gui import guiHelper
from gui.message import displayDialogAsModal

from ..ajedrez import retos
from ..ajedrez.configuracion import ConfiguracionPartida, EleccionColor, Modo
from ..ajedrez.curso import practica
from ..ajedrez.curso.modelo import Curso, Ejercicio, Leccion, cargar_curso, carpeta_de_idioma
from ..ajedrez.curso.practica import GeneradorPractica, RondaPractica
from ..ajedrez.curso.progreso import Progreso
from ..ajedrez.curso.sesion import Resultado, SesionEjercicio, Sonido
from . import atajos, sonidos
from .ventana_leccion import VentanaLeccion, titulo_leccion

addonHandler.initTranslation()

# Tras abrir la ventana, la instrucción espera a que NVDA anuncie la casilla.
_ESPERA_INSTRUCCION_MS = 400
# Al abrir la primera partida desde el curso, el mensaje espera a que se abra el tablero.
_ESPERA_PARTIDA_MS = 1500
# Respuesta del diálogo de lecciones cuando se pulsa «Practicar».
ID_PRACTICAR = wx.NewIdRef()


def ruta_progreso() -> str:
	return os.path.join(globalVars.appArgs.configPath, "miAjedrezAccesible", "progreso.json")


def texto_estado(leccion: Leccion, progreso: Progreso) -> str:
	total = len(leccion.ejercicios)
	hechos = sum(1 for e in leccion.ejercicios if progreso.superado(e.id))
	if hechos == total:
		if leccion.estrellas_posibles:
			# Translators: state of a completed lesson in the list of lessons.
			texto = _("Completed, {stars} of {total} stars.").format(
				stars=progreso.estrellas_de(leccion),
				total=leccion.estrellas_posibles,
			)
		else:
			# Translators: state of a completed lesson without stars in the list of lessons.
			texto = _("Completed.")
	elif hechos:
		# Translators: state of a lesson started but not finished, in the list of lessons.
		texto = _("In progress: {done} of {total} exercises.").format(done=hechos, total=total)
	else:
		# Translators: state of a lesson not started, in the list of lessons.
		texto = _("Pending.")
	mejor = progreso.mejor_practica(leccion.id)
	if mejor is not None:
		# Translators: best practice round of a lesson, shown in the list of lessons.
		texto += " " + _("Best practice: {stars} of {total}.").format(
			stars=mejor,
			total=3 * practica.TAMANO_RONDA,
		)
	return texto


class DialogoLecciones(wx.Dialog):
	def __init__(self, curso: Curso, progreso: Progreso, seleccion: Leccion | None) -> None:
		# Translators: title of the list of lessons of the course.
		super().__init__(None, title=_("Learn to play"))
		self._lecciones = curso.lecciones
		textos = []
		for leccion in self._lecciones:
			texto = f"{titulo_leccion(leccion) if leccion.extra else leccion.id + '. ' + leccion.titulo}. "
			texto += texto_estado(leccion, progreso)
			bloque = curso.bloque_de(leccion)
			if bloque.lecciones[0] == leccion and leccion.extra:
				# Translators: heading before the extra lessons in the list of lessons.
				texto = _("Extras.") + " " + texto
			elif bloque.lecciones[0] == leccion:
				# Translators: block heading before the first lesson of a block, for example "Block B, The pieces".
				texto = (
					_("Block {block}, {title}.").format(block=bloque.id, title=bloque.titulo) + " " + texto
				)
			textos.append(texto)
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.lista: wx.ListBox = ayudante.addLabeledControl(
			# Translators: label of the list of lessons.
			_("&Lessons:"),
			wx.ListBox,
			choices=textos,
			size=(560, 320),
		)
		botones = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that starts the selected lesson.
		empezar = botones.addButton(self, id=wx.ID_OK, label=_("&Start"))
		# Translators: button that starts a practice round of the selected lesson.
		self.practicar = botones.addButton(self, id=ID_PRACTICAR, label=_("&Practice"))
		# Translators: button that closes the list of lessons.
		botones.addButton(self, id=wx.ID_CANCEL, label=_("&Close"))
		ayudante.addDialogDismissButtons(botones, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		principal.Fit(self)
		empezar.SetDefault()
		self.SetEscapeId(wx.ID_CANCEL)
		self.practicar.Bind(wx.EVT_BUTTON, lambda evento: self.EndModal(ID_PRACTICAR))
		self.lista.SetSelection(self._indice_inicial(progreso, seleccion))
		self.lista.Bind(wx.EVT_LISTBOX_DCLICK, lambda evento: self.EndModal(wx.ID_OK))
		self.lista.Bind(wx.EVT_LISTBOX, lambda evento: self._actualizar())
		self._actualizar()
		self.CentreOnScreen()
		self.lista.SetFocus()

	def _actualizar(self) -> None:
		self.practicar.Enable(practica.tiene_practica(self.leccion_elegida().id))

	def _indice_inicial(self, progreso: Progreso, seleccion: Leccion | None) -> int:
		if seleccion is not None and seleccion in self._lecciones:
			return self._lecciones.index(seleccion)
		for indice, leccion in enumerate(self._lecciones):
			if not progreso.leccion_completada(leccion):
				return indice
		return 0

	def leccion_elegida(self) -> Leccion:
		return self._lecciones[max(0, self.lista.GetSelection())]


class DialogoPresentacion(wx.Dialog):
	"""Explicación de la lección. NVDA lee el texto al abrirse; NVDA+B lo vuelve a leer."""

	def __init__(self, leccion: Leccion, indice_inicial: int) -> None:
		super().__init__(None, title=titulo_leccion(leccion))
		parrafos = list(leccion.explicacion)
		cantidad = len(leccion.ejercicios)
		parrafos.append(
			# Translators: said at the end of a lesson explanation; {n} is the number of exercises.
			ngettext("This lesson has {n} exercise.", "This lesson has {n} exercises.", cantidad).format(
				n=cantidad,
			),
		)
		if indice_inicial:
			# Translators: said when a lesson is resumed; {n} is the exercise number.
			parrafos.append(_("You will continue from exercise {n}.").format(n=indice_inicial + 1))
		principal = wx.BoxSizer(wx.VERTICAL)
		ayudante = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		for parrafo in parrafos:
			texto = wx.StaticText(self, label=parrafo)
			texto.Wrap(520)
			ayudante.addItem(texto)
		botones = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that starts the exercises of a lesson.
		empezar = botones.addButton(self, id=wx.ID_OK, label=_("&Start"))
		# Translators: button that goes back to the list of lessons.
		botones.addButton(self, id=wx.ID_CANCEL, label=_("&Back"))
		ayudante.addDialogDismissButtons(botones, separated=True)
		principal.Add(ayudante.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(principal)
		principal.Fit(self)
		empezar.SetDefault()
		self.SetEscapeId(wx.ID_CANCEL)
		self.CentreOnScreen()
		empezar.SetFocus()


class ControladorCurso:
	"""Lleva la lección o la práctica en curso. Solo hay una ventana de lección a la vez."""

	contexto_atajos = atajos.Contexto.LECCION

	def __init__(self, al_empezar_partida: Callable[[ConfiguracionPartida], None] | None = None) -> None:
		self._al_empezar_partida = al_empezar_partida
		self.curso = cargar_curso(carpeta_de_idioma(languageHandler.getLanguage()))
		self.progreso = Progreso(ruta_progreso())
		self.generador = GeneradorPractica()
		self.ventana: VentanaLeccion | None = None
		self.leccion: Leccion | None = None
		# Ronda en curso si se está practicando; None en una lección.
		self.ronda: RondaPractica | None = None
		self.indice = 0
		self.sesion: SesionEjercicio | None = None

	@property
	def practicando(self) -> bool:
		return self.ronda is not None

	@property
	def cantidad(self) -> int:
		if self.ronda is not None:
			return self.ronda.tamano
		return len(self.leccion.ejercicios) if self.leccion else 0

	def _ejercicio(self, indice: int) -> Ejercicio:
		if self.ronda is not None:
			return self.ronda.ejercicio(indice)
		assert self.leccion is not None
		return self.leccion.ejercicios[indice]

	# Lista y presentación.

	def abrir_lista(self, seleccion: Leccion | None = None) -> None:
		wx.CallAfter(self._abrir_lista, seleccion)

	def _abrir_lista(self, seleccion: Leccion | None) -> None:
		if self.ventana is not None:
			self.ventana.mostrar()
			return
		dialogo = DialogoLecciones(self.curso, self.progreso, seleccion)
		try:
			respuesta = displayDialogAsModal(dialogo)
			leccion = dialogo.leccion_elegida()
		finally:
			dialogo.Destroy()
		if respuesta == wx.ID_OK:
			self._presentar(leccion)
		elif respuesta == ID_PRACTICAR:
			self._practicar(leccion)

	def _presentar(self, leccion: Leccion) -> None:
		indice = self.progreso.primer_pendiente(leccion)
		dialogo = DialogoPresentacion(leccion, indice)
		try:
			respuesta = displayDialogAsModal(dialogo)
		finally:
			dialogo.Destroy()
		if respuesta != wx.ID_OK:
			self._abrir_lista(leccion)
			return
		self._abrir_ventana(leccion, None, indice)

	def _practicar(self, leccion: Leccion) -> None:
		ronda = RondaPractica(leccion.id, self.progreso.nivel_practica(leccion.id), self.generador)
		self._abrir_ventana(leccion, ronda, 0)

	def _abrir_ventana(self, leccion: Leccion, ronda: RondaPractica | None, indice: int) -> None:
		self.leccion = leccion
		self.ronda = ronda
		self.indice = indice
		self.sesion = SesionEjercicio(self._ejercicio(indice))
		if ronda is not None:
			# Translators: title of the practice window, for example "Practice - Lesson 4: The rook".
			titulo = _("Practice - {lesson}").format(lesson=titulo_leccion(leccion))
		else:
			# Translators: title of the lesson window, for example "Learn to play - Lesson 4: The rook".
			titulo = _("Learn to play - {lesson}").format(lesson=titulo_leccion(leccion))
		self.ventana = VentanaLeccion(self, titulo, self.sesion, al_cerrar=self._al_cerrar_ventana)
		self.ventana.mostrar()

	def _al_cerrar_ventana(self) -> None:
		self.ventana = None
		self.sesion = None

	def cerrar(self) -> None:
		if self.ventana is not None:
			self.ventana.cerrar_sin_preguntar()

	# Textos de ayuda.

	def texto_instruccion(self) -> str:
		if self.sesion is None:
			return ""
		if self.ronda is not None:
			# Translators: start of each practice exercise, for example "Practice 2 of 5, level 1."
			numero = _("Practice {n} of {total}, level {level}.").format(
				n=self.indice + 1,
				total=self.cantidad,
				level=self.ronda.nivel,
			)
		else:
			# Translators: start of each exercise, for example "Exercise 2 of 6."
			numero = _("Exercise {n} of {total}.").format(n=self.indice + 1, total=self.cantidad)
		return f"{numero} {self.sesion.instruccion_actual()}"

	def texto_explicacion(self) -> str:
		return " ".join(self.leccion.explicacion) if self.leccion else ""

	def texto_progreso(self) -> str:
		texto = self.texto_instruccion()
		if self.sesion is not None and self.sesion.ejercicio.manzanas:
			texto += " " + self.sesion.texto_manzanas()
		return texto

	def anunciar_ejercicio(self, al_abrir: bool = False) -> None:
		texto = self.texto_instruccion()
		if al_abrir:
			# Al abrir la ventana, primero se anuncia la casilla con el foco; la instrucción va detrás.
			wx.CallLater(_ESPERA_INSTRUCCION_MS, ui.message, texto, speechPriority=speech.Spri.NEXT)
		else:
			ui.message(texto, speechPriority=speech.Spri.NEXT)

	# Ejercicios.

	def ejercicio_completado(self, resultado: Resultado) -> tuple[str, Sonido | None]:
		"""Guarda el progreso. Devuelve el texto que se añade al anuncio y el sonido que lo acompaña."""
		assert self.leccion is not None and self.sesion is not None
		ultimo = self.indice + 1 >= self.cantidad
		if self.ronda is not None:
			self.ronda.registrar(resultado.estrellas)
			if not ultimo:
				return _("Press Enter to continue."), None
			self.progreso.registrar_practica(
				self.leccion.id,
				self.ronda.nivel_siguiente(),
				self.ronda.ganadas,
			)
			self.progreso.guardar()
			return (
				self.ronda.texto_final()
				+ " "
				# Translators: said at the end of a practice round.
				+ _(
					"Press Enter for another round. To go back to the list, open the menu with the Applications key.",
				),
				Sonido.LECCION,
			)
		self.progreso.registrar(self.sesion.ejercicio.id, resultado.estrellas)
		self.progreso.guardar()
		if not ultimo:
			# Translators: said after solving an exercise, before the next one.
			return _("Press Enter to continue."), None
		partes = self._resumen_leccion()
		sugerencia = retos.sugerencia_de_leccion(self.leccion.id)
		if sugerencia:
			partes.append(sugerencia)
		# Translators: said at the end of a lesson.
		partes.append(_("Press Enter to go back to the list of lessons."))
		if practica.tiene_practica(self.leccion.id):
			# Translators: said at the end of a lesson that can be practiced.
			partes.append(_("To practice more, open the menu with the Applications key."))
		return " ".join(partes), Sonido.LECCION

	def _resumen_leccion(self) -> list[str]:
		"""«¡Lección completada! Ganaste X de Y estrellas.» y, si toca, el mensaje final del bloque."""
		assert self.leccion is not None
		partes = []
		if self.leccion.estrellas_posibles:
			# Translators: said when a lesson is completed, with the stars earned.
			partes.append(
				_("Lesson completed! You earned {stars} of {total} stars.").format(
					stars=self.progreso.estrellas_de(self.leccion),
					total=self.leccion.estrellas_posibles,
				),
			)
		else:
			# Translators: said when a lesson without stars is completed.
			partes.append(_("Lesson completed!"))
		if self.curso.es_ultima_del_bloque(self.leccion):
			partes.append(self.curso.bloque_de(self.leccion).mensaje_final)
		return partes

	def empezar_partida_del_curso(self, resultado: Resultado) -> None:
		"""Ejercicio «Tu primera partida»: guarda el progreso, cierra la lección y abre la partida."""
		assert self.sesion is not None
		self.progreso.registrar(self.sesion.ejercicio.id, resultado.estrellas)
		self.progreso.guardar()
		ultimo = self.leccion is not None and self.indice + 1 >= self.cantidad
		partes = self._resumen_leccion() if ultimo else []
		sonidos.reproducir(Sonido.LECCION if ultimo else Sonido.EXITO)
		if self.ventana is not None:
			self.ventana.cerrar_sin_preguntar()
		if self._al_empezar_partida is None:
			return
		self._al_empezar_partida(ConfiguracionPartida(Modo.COMPUTADORA, EleccionColor.BLANCAS, 1))
		# Translators: said when the first game of the course starts.
		partes.append(_("Good luck in your first game!"))
		# Se dice cuando la partida ya está abierta, después del anuncio de la casilla.
		wx.CallLater(_ESPERA_PARTIDA_MS, ui.message, " ".join(partes), speechPriority=speech.Spri.NEXT)

	def continuar(self) -> None:
		if self.leccion is None:
			return
		if self.indice + 1 < self.cantidad:
			self._ir_al_ejercicio(self.indice + 1)
		elif self.ronda is not None:
			# Otra ronda con el nivel que corresponde.
			self.ronda = RondaPractica(self.leccion.id, self.ronda.nivel_siguiente(), self.generador)
			self._ir_al_ejercicio(0)
		else:
			self.volver_a_la_lista(siguiente=True)

	def _ir_al_ejercicio(self, indice: int, ejercicio: Ejercicio | None = None) -> None:
		if self.ventana is None:
			return
		self.indice = indice
		self.sesion = SesionEjercicio(ejercicio or self._ejercicio(indice))
		self.ventana.cuadricula.cargar(self.sesion)
		self.anunciar_ejercicio()

	def reiniciar_ejercicio(self) -> None:
		self._ir_al_ejercicio(self.indice)

	def saltar_ejercicio(self) -> None:
		if self.leccion is None:
			return
		if self.ronda is not None:
			# En la práctica, saltar cambia el ejercicio por otro del mismo nivel.
			self._ir_al_ejercicio(self.indice, self.ronda.cambiar(self.indice))
		elif self.indice + 1 < self.cantidad:
			self._ir_al_ejercicio(self.indice + 1)
		else:
			self.volver_a_la_lista(siguiente=True)

	def practicar_mas(self) -> None:
		leccion = self.leccion
		if leccion is None:
			return
		if self.ventana is not None:
			self.ventana.cerrar_sin_preguntar()
		wx.CallAfter(self._practicar, leccion)

	def volver_a_la_lista(self, siguiente: bool = False) -> None:
		leccion = self.leccion
		if leccion is not None and siguiente:
			leccion = self.curso.siguiente(leccion) or leccion
		if self.ventana is not None:
			self.ventana.cerrar_sin_preguntar()
		self.abrir_lista(leccion)

	def opciones_menu(self, cerrar: Callable[[], None]) -> list[tuple[str, Callable[[], None], bool]]:
		if self.ronda is not None:
			# Translators: item of the practice menu.
			saltar = _("&Another exercise")
		else:
			# Translators: item of the lesson menu.
			saltar = _("&Skip exercise")
		opciones = [
			# Translators: item of the lesson menu.
			(_("&Restart exercise"), self.reiniciar_ejercicio, True),
			(saltar, self.saltar_ejercicio, True),
		]
		if self.ronda is None and self.leccion is not None and practica.tiene_practica(self.leccion.id):
			# Translators: item of the lesson menu.
			opciones.append((_("&Practice more"), self.practicar_mas, True))
		opciones += [
			# Translators: item of the lesson menu.
			(_("Back to the &list of lessons"), self.volver_a_la_lista, True),
			# Translators: item of the lesson menu.
			(_("&Close"), cerrar, True),
		]
		return opciones
