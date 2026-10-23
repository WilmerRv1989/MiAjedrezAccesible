# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Con NVDA en otro idioma: el curso en inglés y la notación con letras inglesas (sin NVDA).

El español es el modo por defecto y lo comprueban el resto de las pruebas; aquí se activa el
inglés solo dentro de cada prueba y se vuelve a dejar el español al terminar.
"""

import json
import os
import re
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miAjedrezAccesible")
_LECCIONES = os.path.join(_COMPLEMENTO, "lecciones")
sys.path.insert(0, _COMPLEMENTO)

from ajedrez import idioma, notacion  # noqa: E402
from ajedrez.curso import modelo  # noqa: E402
from ajedrez.partida import Partida  # noqa: E402

import chess  # noqa: E402

CLAVES_DE_TEXTO = (
	"titulo",
	"explicacion",
	"instruccion",
	"pistas",
	"mensaje_error",
	"corona_dama",
	"corona_otra",
	"mensaje_final",
)


def leer(carpeta: str, nombre: str):
	with open(os.path.join(_LECCIONES, carpeta, nombre), encoding="utf-8") as archivo:
		return json.load(archivo)


def sin_textos(objeto):
	"""Los datos de una lección sin sus textos: posiciones, jugadas, soluciones…"""
	if isinstance(objeto, dict):
		return {k: sin_textos(v) for k, v in objeto.items() if k not in CLAVES_DE_TEXTO}
	if isinstance(objeto, list):
		return [sin_textos(x) for x in objeto]
	return objeto


def textos(objeto):
	if isinstance(objeto, dict):
		for k, v in objeto.items():
			if k in CLAVES_DE_TEXTO:
				yield from v if isinstance(v, list) else [v]
			else:
				yield from textos(v)
	elif isinstance(objeto, list):
		for x in objeto:
			yield from textos(x)


class ConLetrasInglesas(unittest.TestCase):
	def setUp(self) -> None:
		idioma.configurar_letras(False)

	def tearDown(self) -> None:
		idioma.configurar_letras(True)


class PruebaIdioma(unittest.TestCase):
	def test_es_espanol(self):
		for codigo in ("es", "es_CO", "es_ES", "ES"):
			self.assertTrue(idioma.es_espanol(codigo), codigo)
		for codigo in ("en", "id", "pt_BR", "fr"):
			self.assertFalse(idioma.es_espanol(codigo), codigo)

	def test_carpeta_de_las_lecciones(self):
		self.assertTrue(modelo.carpeta_de_idioma("es").endswith(os.path.join("lecciones", "es")))
		self.assertTrue(modelo.carpeta_de_idioma("es_CR").endswith(os.path.join("lecciones", "es")))
		for codigo in ("en", "en_US", "id", "pt_BR"):
			self.assertTrue(modelo.carpeta_de_idioma(codigo).endswith(os.path.join("lecciones", "en")), codigo)


class PruebaCursoEnIngles(unittest.TestCase):
	def test_misma_estructura_que_el_espanol(self):
		"""Las lecciones en inglés solo cambian los textos: las posiciones y soluciones son las mismas."""
		nombres = sorted(os.listdir(os.path.join(_LECCIONES, "es")))
		self.assertEqual(sorted(os.listdir(os.path.join(_LECCIONES, "en"))), nombres)
		for nombre in nombres:
			es = leer("es", nombre)
			en = leer("en", nombre)
			self.assertEqual(sin_textos(en), sin_textos(es), nombre)
			self.assertEqual(len(list(textos(en))), len(list(textos(es))), nombre)

	def test_textos_en_ingles(self):
		espanol = re.compile(r"[ñáéíóú¡¿]|\b(Pulsa|casilla|jugada|peón|torre|alfil|caballo|dama|rey)\b", re.IGNORECASE)
		for nombre in os.listdir(os.path.join(_LECCIONES, "en")):
			datos = leer("en", nombre)
			for texto in textos(datos):
				self.assertTrue(texto.strip(), nombre)
				self.assertIsNone(espanol.search(texto), f"{nombre}: {texto}")

	def test_carga_el_curso(self):
		curso = modelo.cargar_curso(modelo.carpeta_de_idioma("en"))
		espanol = modelo.cargar_curso(modelo.carpeta_de_idioma("es"))
		self.assertEqual([le.id for le in curso.lecciones], [le.id for le in espanol.lecciones])
		self.assertEqual(curso.leccion("1").titulo, "Ranks, files and coordinates")


class PruebaNotacionInglesa(ConLetrasInglesas):
	def test_la_r_es_la_torre(self):
		tablero = chess.Board("4k3/8/8/8/8/8/8/R3K3 w Q - 0 1")
		self.assertEqual(notacion.interpretar(tablero, "Rd1").uci(), "a1d1")
		self.assertEqual(notacion.interpretar(tablero, "Kd2").uci(), "e1d2")

	def test_letras_inglesas(self):
		tablero = chess.Board()
		self.assertEqual(notacion.interpretar(tablero, "Nf3").uci(), "g1f3")
		self.assertEqual(notacion.interpretar(tablero, "nf3").uci(), "g1f3")
		self.assertEqual(notacion.interpretar(tablero, "e4").uci(), "e2e4")
		with self.assertRaises(notacion.ErrorJugada):
			notacion.interpretar(tablero, "Cf3")

	def test_coronacion_y_enroque(self):
		tablero = chess.Board("4k3/1P6/8/8/8/8/8/R3K3 w Q - 0 1")
		self.assertEqual(notacion.interpretar(tablero, "b8=Q").uci(), "b7b8q")
		self.assertEqual(notacion.interpretar(tablero, "b8R").uci(), "b7b8r")
		self.assertEqual(notacion.interpretar(tablero, "O-O-O").uci(), "e1c1")

	def test_planilla_y_anuncio(self):
		partida = Partida()
		partida.jugar(chess.Move.from_uci("g1f3"))
		self.assertEqual(partida.historial[0].san, "Nf3")
		self.assertEqual(notacion.san_en_espanol(chess.Board(), chess.Move.from_uci("g1f3")), "Nf3")

	def test_lo_que_piden_las_lecciones(self):
		"""Cada jugada que el curso en inglés pide escribir se entiende como la esperada."""
		curso = modelo.cargar_curso(modelo.carpeta_de_idioma("en"))
		pedidas = {
			"22.1": "e4",
			"22.2": "Nf3",
			"22.3": "Nxe5",
			"22.4": "O-O",
			"22.5": "Bxf7+",
			"x1.1": "b8=Q",
			"x1.2": "Nbd2",
			"x1.3": "exd6",
			"x1.4": "O-O-O",
			"x1.5": "Qh7",
			"x1.7": "Rd8",
			"x1.8": "Qd8",
		}
		for leccion in curso.lecciones:
			for ejercicio in leccion.ejercicios:
				if ejercicio.id in pedidas:
					jugada = notacion.interpretar(ejercicio.tablero(), pedidas[ejercicio.id])
					self.assertEqual(jugada.uci(), ejercicio.solucion, ejercicio.id)


class PruebaEspanolIntacto(unittest.TestCase):
	def test_la_r_sigue_siendo_el_rey(self):
		tablero = chess.Board("4k3/8/8/8/8/8/8/R3K3 w Q - 0 1")
		self.assertEqual(notacion.interpretar(tablero, "Rd2").uci(), "e1d2")
		self.assertEqual(notacion.interpretar(tablero, "Td1").uci(), "a1d1")
		self.assertEqual(notacion.san_en_espanol(chess.Board(), chess.Move.from_uci("g1f3")), "Cf3")


if __name__ == "__main__":
	unittest.main()
