# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Sonidos del complemento (generados por herramientas/generar_sonidos.py)."""

import os

import nvwave
from logHandler import log

from . import preferencias

CARPETA_SONIDOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sonidos")

MANZANA_CERCA = "manzana_cerca"


def reproducir(nombre: str) -> None:
	if not preferencias.sonidos_activados():
		return
	ruta = os.path.join(CARPETA_SONIDOS, f"{nombre}.wav")
	try:
		nvwave.playWaveFile(ruta, asynchronous=True)
	except Exception:
		log.debugWarning(f"No se pudo reproducir {ruta}", exc_info=True)
