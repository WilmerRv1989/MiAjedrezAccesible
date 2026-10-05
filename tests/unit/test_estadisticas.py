# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas de las estadísticas y de las preferencias de anuncio (sin NVDA)."""

import datetime
import json
import os
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miAjedrezAccesible")
_PO_ES = os.path.join(_RAIZ, "addon", "locale", "es", "LC_MESSAGES", "nvda.po")
sys.path.insert(0, _COMPLEMENTO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import po  # noqa: E402
from ajedrez import anunciador, idioma, retos  # noqa: E402
from ajedrez.anunciador import FormaJugada  # noqa: E402
from ajedrez.configuracion import ConfiguracionPartida  # noqa: E402
from ajedrez.curso import modelo  # noqa: E402
from ajedrez.curso.progreso import Progreso  # noqa: E402
from ajedrez.estadisticas import EstadisticasPartidas, secciones  # noqa: E402
from ajedrez.partida import Partida  # noqa: E402
from ajedrez.retos import ProgresoRetos  # noqa: E402

import chess  # noqa: E402

idioma.configurar(*po.traducciones(_PO_ES))
CURSO = modelo.cargar_curso(modelo.carpeta_de_idioma("es"))


def mate_del_loco() -> Partida:
	"""Ganan las negras en dos jugadas."""
	partida = Partida()
	for uci in ("f2f3", "e7e5", "g2g4", "d8h4"):
		partida.jugar(chess.Move.from_uci(uci))
	return partida


class PruebaPartidas(unittest.TestCase):
	def setUp(self) -> None:
		self.carpeta = tempfile.TemporaryDirectory()
		self.ruta = os.path.join(self.carpeta.name, "partidas.json")

	def tearDown(self) -> None:
		self.carpeta.cleanup()

	def test_registrar_y_guardar(self):
		e = EstadisticasPartidas(self.ruta)
		nivel3 = ConfiguracionPartida(nivel=3)
		e.registrar(mate_del_loco(), nivel3, chess.BLACK)
		e.registrar(mate_del_loco(), nivel3, chess.WHITE)
		tiempo = Partida()
		tiempo.perder_por_tiempo(chess.WHITE)
		e.registrar(tiempo, ConfiguracionPartida(nivel=5), chess.WHITE)
		tablas = Partida()
		tablas.acordar_tablas()
		e.registrar(tablas, ConfiguracionPartida(nivel=5), chess.WHITE)
		e.registrar(mate_del_loco(), ConfiguracionPartida(), None)
		# Una partida sin terminar no cuenta.
		e.registrar(Partida(), nivel3, chess.WHITE)
		e.guardar()
		otra = EstadisticasPartidas(self.ruta)
		self.assertEqual(otra.computadora, {3: [1, 0, 1], 5: [0, 1, 1]})
		self.assertEqual(otra.total_computadora, 4)
		self.assertEqual(otra.perdidas_por_tiempo, 1)
		self.assertEqual(otra.dos_personas, 1)
		self.assertEqual(otra.nivel_mas_alto_ganado(), 3)

	def test_archivo_danado(self):
		with open(self.ruta, "w", encoding="utf-8") as archivo:
			json.dump({"version": 1, "computadora": {"x": "y"}}, archivo)
		e = EstadisticasPartidas(self.ruta)
		self.assertEqual(e.computadora, {})


class PruebaSecciones(unittest.TestCase):
	def setUp(self) -> None:
		self.carpeta = tempfile.TemporaryDirectory()
		self.ruta = lambda nombre: os.path.join(self.carpeta.name, nombre)

	def tearDown(self) -> None:
		self.carpeta.cleanup()

	def texto(self, progreso, retos_progreso, partidas) -> dict[str, str]:
		return {
			titulo: " ".join(lineas)
			for titulo, lineas in secciones(CURSO, progreso, retos_progreso, partidas)
		}

	def test_sin_nada(self):
		texto = self.texto(
			Progreso(self.ruta("progreso.json")),
			ProgresoRetos(self.ruta("retos.json")),
			EstadisticasPartidas(self.ruta("partidas.json")),
		)
		self.assertEqual(list(texto), ["Partidas", "Aprender a jugar", "Retos"])
		self.assertIn("Todavía no has terminado ninguna partida.", texto["Partidas"])
		self.assertIn("Lecciones completadas: 0 de 23.", texto["Aprender a jugar"])
		self.assertIn("Siguiente lección: 1, Filas, columnas y coordenadas.", texto["Aprender a jugar"])
		self.assertIn("Todavía no has empezado los Retos.", texto["Retos"])

	def test_con_progreso(self):
		progreso = Progreso(self.ruta("progreso.json"))
		for ejercicio in CURSO.leccion("1").ejercicios:
			progreso.registrar(ejercicio.id, 3)
		progreso.registrar_practica("4", 2, 14)
		retos_progreso = ProgresoRetos(self.ruta("retos.json"))
		retos_progreso.nivel = 1000
		problema = retos.cargar_problemas()[0]
		retos_progreso.registrar(problema, True)
		retos_progreso.registrar_racha(6)
		retos_progreso.registrar_dia(datetime.date(2026, 10, 5), True)
		partidas = EstadisticasPartidas(self.ruta("partidas.json"))
		partidas.registrar(mate_del_loco(), ConfiguracionPartida(nivel=2), chess.BLACK)
		texto = self.texto(progreso, retos_progreso, partidas)
		self.assertIn("Contra la computadora: 1 partida. Ganadas 1, tablas 0, perdidas 0.", texto["Partidas"])
		self.assertIn("Nivel 2: ganadas 1, tablas 0, perdidas 0.", texto["Partidas"])
		self.assertIn("Nivel más alto al que has ganado: 2.", texto["Partidas"])
		self.assertIn("Lecciones completadas: 1 de 23.", texto["Aprender a jugar"])
		self.assertIn("Siguiente lección: 2, Diagonales y el centro.", texto["Aprender a jugar"])
		self.assertIn("Mejor ronda de práctica: 14 de 15 estrellas.", texto["Aprender a jugar"])
		self.assertIn(f"Tu nivel: {retos_progreso.nivel}.", texto["Retos"])
		self.assertIn("resueltos a la primera: 1 de 1 (100 %)", texto["Retos"])
		self.assertIn("Récord de racha: 6.", texto["Retos"])
		self.assertIn("1 día seguido", texto["Retos"])

	def test_nivel_mas_alto_de_retos(self):
		with tempfile.TemporaryDirectory() as carpeta:
			ruta = os.path.join(carpeta, "retos.json")
			progreso = ProgresoRetos(ruta)
			progreso.nivel = 1000
			problema = retos.cargar_problemas()[2000]
			progreso.registrar(problema, True)
			subida = progreso.nivel
			progreso.registrar(problema, False)
			self.assertLess(progreso.nivel, subida)
			self.assertEqual(progreso.nivel_mas_alto, subida)
			progreso.guardar()
			self.assertEqual(ProgresoRetos(ruta).nivel_mas_alto, subida)


class PruebaPreferencias(unittest.TestCase):
	def tearDown(self) -> None:
		anunciador.configurar(FormaJugada.PALABRAS, False)

	def test_forma_de_anunciar(self):
		anunciador.configurar(FormaJugada.NOTACION, False)
		self.assertEqual(Partida().jugar(chess.Move.from_uci("g1f3")), "Cf3. Juegan negras.")
		anunciador.configurar(FormaJugada.AMBAS, False)
		self.assertEqual(
			Partida().jugar(chess.Move.from_uci("g1f3")),
			"Cf3. Caballo blanco de g1 a f3. Juegan negras.",
		)
		# Los enroques siempre con palabras; el jaque, aparte y sin signo.
		anunciador.configurar(FormaJugada.NOTACION, False)
		enroque = Partida("4k3/8/8/8/8/8/8/4K2R w K - 0 1")
		self.assertNotIn("O-O", enroque.jugar(chess.Move.from_uci("e1g1")))
		jaque = Partida("4k3/8/8/8/8/8/8/R3K3 w - - 0 1")
		self.assertEqual(jaque.jugar(chess.Move.from_uci("a1a8")), "Ta8. Jaque. Juegan negras.")

	def test_casilla_primero(self):
		tablero = chess.Board()
		self.assertEqual(anunciador.describir_casilla(tablero, chess.G1), "Caballo blanco, g1")
		anunciador.configurar(FormaJugada.PALABRAS, True)
		self.assertEqual(anunciador.describir_casilla(tablero, chess.G1), "g1, caballo blanco")
		self.assertEqual(anunciador.describir_casilla(tablero, chess.E4), "e4")


if __name__ == "__main__":
	unittest.main()
