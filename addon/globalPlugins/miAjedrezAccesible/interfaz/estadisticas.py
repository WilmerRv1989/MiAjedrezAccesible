# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""«Mis estadísticas»: un mensaje navegable de NVDA, con un título por sección (se salta con H)."""

from html import escape

import addonHandler
import languageHandler
import ui

from ..ajedrez.curso.modelo import cargar_curso, carpeta_de_idioma
from ..ajedrez.curso.progreso import Progreso
from ..ajedrez.estadisticas import EstadisticasPartidas, secciones
from ..ajedrez.retos import ProgresoRetos
from . import archivos
from . import curso as interfaz_curso
from . import retos as interfaz_retos

addonHandler.initTranslation()


def html_estadisticas() -> str:
	partes = []
	for titulo, lineas in secciones(
		cargar_curso(carpeta_de_idioma(languageHandler.getLanguage())),
		Progreso(interfaz_curso.ruta_progreso()),
		ProgresoRetos(interfaz_retos.ruta_progreso()),
		EstadisticasPartidas(archivos.ruta_estadisticas()),
	):
		elementos = "".join(f"<li>{escape(linea)}</li>" for linea in lineas)
		partes.append(f"<h2>{escape(titulo)}</h2><ul>{elementos}</ul>")
	return "".join(partes)


def mostrar() -> None:
	ui.browseableMessage(
		html_estadisticas(),
		# Translators: title of the statistics window.
		title=_("My statistics"),
		isHtml=True,
		closeButton=True,
		copyButton=True,
	)
