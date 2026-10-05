# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Lógica del ajedrez: reglas, frases y notación.

Este paquete no importa nada de NVDA, así que se puede probar fuera del lector de pantalla.
"""

import os
import sys

# python-chess va incluido en «lib» y usa importaciones absolutas («import chess»),
# por eso la carpeta se añade a la ruta de búsqueda de módulos.
_CARPETA_LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib")
if _CARPETA_LIB not in sys.path:
	sys.path.insert(0, _CARPETA_LIB)
