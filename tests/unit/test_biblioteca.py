# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""La copia de python-chess debe estar completa.

En NVDA todos los complementos comparten el mismo Python, y el módulo `chess` se carga una sola vez:
el primero que llega. Si nuestra copia estuviera recortada y se cargara antes que la de otro
complemento (por ejemplo, Chess Study), ese complemento no podría importar lo que le falta.
"""

import importlib
import os
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LIB = os.path.join(_RAIZ, "addon", "globalPlugins", "miAjedrezAccesible", "lib")
sys.path.insert(0, _LIB)


class PruebaBiblioteca(unittest.TestCase):
	def test_python_chess_completo(self):
		import chess

		self.assertEqual(chess.__version__, "1.11.2")
		for modulo in ("engine", "gaviota", "pgn", "polyglot", "svg", "syzygy", "variant"):
			with self.subTest(modulo=modulo):
				importlib.import_module(f"chess.{modulo}")


if __name__ == "__main__":
	unittest.main()
