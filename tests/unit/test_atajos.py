# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas de la lista de atajos de teclado, con NVDA simulado."""

import builtins
import os
import sys
import types
import unittest
from types import SimpleNamespace

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miAjedrezAccesible")
_PO_ES = os.path.join(_RAIZ, "addon", "locale", "es", "LC_MESSAGES", "nvda.po")
sys.path.insert(0, _COMPLEMENTO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import po  # noqa: E402

_gettext, _ngettext = po.traducciones(_PO_ES)
_MAPEOS: dict = {}


def _modulo(nombre: str, **atributos) -> types.ModuleType:
	modulo = types.ModuleType(nombre)
	modulo.__dict__.update(atributos)
	return modulo


def _instalar_traduccion() -> None:
	builtins._ = _gettext
	builtins.ngettext = _ngettext


# Simulación mínima de los módulos de NVDA que usa interfaz/atajos.py.
sys.modules.setdefault("addonHandler", _modulo("addonHandler", initTranslation=_instalar_traduccion))
sys.modules.setdefault("ui", _modulo("ui", browseableMessage=lambda *a, **k: None))
sys.modules.setdefault(
	"logHandler",
	_modulo("logHandler", log=SimpleNamespace(debugWarning=lambda *a, **k: None)),
)
sys.modules["inputCore"] = _modulo(
	"inputCore",
	manager=SimpleNamespace(getAllGestureMappings=lambda obj, ancestors: _MAPEOS),
	getDisplayTextForGestureIdentifier=lambda gesto: ("teclado", gesto.split(":", 1)[1]),
)
_instalar_traduccion()

from interfaz import atajos  # noqa: E402


class Celda:
	pass


class CeldaLeccion(Celda):
	pass


Complemento = type("GlobalPlugin", (), {"__module__": atajos._PAQUETE})


def info(cls, orden: str, *gestos: str) -> SimpleNamespace:
	return SimpleNamespace(cls=cls, scriptName=orden, gestures=list(gestos))


class PruebaAtajos(unittest.TestCase):
	def setUp(self) -> None:
		_MAPEOS.clear()
		_MAPEOS["MiAjedrezAccesible"] = {
			"a": info(Celda, "piezas_propias", "kb:f1"),
			# Una persona cambió F5 por Control+E.
			"b": info(Celda, "estado", "kb:control+e"),
			"c": info(Celda, "menu", "kb:applications", "kb:shift+f10"),
			"d": info(CeldaLeccion, "pista", "kb:f6"),
			"e": info(Complemento, "abrir_tablero"),
			"f": info(Complemento, "retos", "kb:nvda+shift+r"),
		}

	def test_partida(self):
		html = atajos.html_atajos({atajos.Contexto.PARTIDA: Celda()})
		self.assertIn("<h2>Moverse por el tablero</h2>", html)
		self.assertIn("f1: Tus piezas.", html)
		# La tecla real, no la original.
		self.assertIn("control+e: A quién le toca, el número de jugada y la última jugada.", html)
		self.assertIn("applications, shift+f10: Menú de la partida", html)
		self.assertIn("Alt+F4: Cerrar la ventana.", html)
		self.assertIn("sin tecla asignada: Abrir el tablero", html)
		self.assertIn("nvda+shift+r: Abrir los Retos.", html)
		# Las teclas de la lección no son de la partida.
		self.assertNotIn("Lecciones</h2>", html)

	def test_leccion(self):
		html = atajos.html_atajos({atajos.Contexto.LECCION: CeldaLeccion()})
		self.assertIn("<h2>Lecciones</h2>", html)
		self.assertIn("f6: Pista", html)
		self.assertIn("control+e: En qué ejercicio estás", html)
		self.assertNotIn("Deshacer la última jugada", html)

	def test_repaso_sin_mover_piezas(self):
		html = atajos.html_atajos({atajos.Contexto.REPASO: Celda()})
		self.assertIn("<h2>Repaso de una partida</h2>", html)
		self.assertNotIn("<h2>Mover piezas</h2>", html)

	def test_todas_sin_repetir(self):
		html = atajos.html_atajos(
			{
				atajos.Contexto.PARTIDA: Celda(),
				atajos.Contexto.LECCION: CeldaLeccion(),
				atajos.Contexto.RETOS: CeldaLeccion(),
				atajos.Contexto.REPASO: Celda(),
			},
		)
		self.assertEqual(html.count("<h2>Moverse por el tablero</h2>"), 1)
		for titulo in ("Lecciones", "Retos", "Repaso de una partida", "Desde cualquier lugar"):
			self.assertIn(f"<h2>{titulo}</h2>", html)


if __name__ == "__main__":
	unittest.main()
