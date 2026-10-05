# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas de Retos (sin NVDA)."""

import datetime
import json
import os
import random
import sys
import tempfile
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miAjedrezAccesible")
_PO_ES = os.path.join(_RAIZ, "addon", "locale", "es", "LC_MESSAGES", "nvda.po")
sys.path.insert(0, _COMPLEMENTO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import po  # noqa: E402
from ajedrez import idioma, retos  # noqa: E402
from ajedrez.curso.modelo import TipoEjercicio  # noqa: E402
from ajedrez.curso.sesion import SesionEjercicio  # noqa: E402
from ajedrez.retos import Problema, ProgresoRetos, Retos, Tema  # noqa: E402

import chess  # noqa: E402

idioma.configurar(*po.traducciones(_PO_ES))
PROBLEMAS = retos.cargar_problemas()
RETOS = Retos(PROBLEMAS)


def jugar(sesion: SesionEjercicio, uci: str):
	jugada = chess.Move.from_uci(uci)
	anuncio = sesion.partida.jugar(jugada)
	return sesion.tras_jugada(jugada, anuncio)


def problema(id_problema: str) -> Problema:
	return next(p for p in PROBLEMAS if p.id == id_problema)


def da_mate(sesion: SesionEjercicio, jugada: chess.Move) -> bool:
	tablero = sesion.partida.tablero.copy()
	tablero.push(jugada)
	return tablero.is_checkmate()


def con_varios_mates() -> tuple[Problema, str]:
	"""Un mate en una con otra jugada que también da mate."""
	for p in RETOS.por_tema[Tema.MATE_EN_UNO]:
		tablero = p.tablero()
		tablero.push_uci(p.jugadas[0])
		for jugada in tablero.legal_moves:
			if jugada.uci() == p.jugadas[1]:
				continue
			tablero.push(jugada)
			mate = tablero.is_checkmate()
			tablero.pop()
			if mate:
				return p, jugada.uci()
	raise AssertionError("No hay problemas con dos mates")


class PruebaDatos(unittest.TestCase):
	def test_cantidad_y_temas(self):
		self.assertEqual(len(PROBLEMAS), 5000)
		self.assertEqual(len({p.id for p in PROBLEMAS}), 5000)
		faciles = sum(1 for p in PROBLEMAS if p.dificultad < 1200)
		self.assertGreater(faciles, 2500)
		for tema in Tema:
			self.assertGreater(len(RETOS.por_tema[tema]), 50, tema)
		for p in PROBLEMAS:
			self.assertTrue(p.temas)
			self.assertTrue(2 <= len(p.jugadas) <= 6 and len(p.jugadas) % 2 == 0, p.id)

	def test_todos_se_resuelven(self):
		"""Cada problema se resuelve jugando su solución, y los de mate terminan en mate."""
		for p in PROBLEMAS:
			e = retos.ejercicio_de_problema(p)
			sesion = SesionEjercicio(e)
			self.assertEqual(sesion.partida.tablero.turn, e.color, p.id)
			resultado = None
			for propia, _respuesta in e.guion:
				resultado = jugar(sesion, propia)
			self.assertTrue(resultado and resultado.completado and not sesion.fallado, p.id)
			if Tema.MATE_EN_UNO in p.temas or Tema.MATE_EN_DOS in p.temas:
				self.assertTrue(sesion.partida.tablero.is_checkmate(), p.id)


class PruebaSesion(unittest.TestCase):
	def test_con_negras(self):
		p = next(p for p in PROBLEMAS if p.tablero().turn == chess.WHITE)
		e = retos.ejercicio_de_problema(p)
		self.assertEqual(e.tipo, TipoEjercicio.PROBLEMA)
		self.assertEqual(e.color, chess.BLACK)
		self.assertIn("Juegas con negras.", e.instruccion)
		self.assertIn("Tu rival acaba de jugar:", e.instruccion)
		# El foco empieza donde acaba de jugar el rival.
		self.assertEqual(e.casilla_inicial(), chess.Move.from_uci(p.jugadas[0]).to_square)
		sesion = SesionEjercicio(e)
		self.assertEqual(len(sesion.partida.historial), 1)

	def test_jugada_equivocada(self):
		p = RETOS.por_tema[Tema.ATAQUE_DOBLE][0]
		sesion = SesionEjercicio(retos.ejercicio_de_problema(p))
		antes = sesion.partida.tablero.fen()
		mala = next(
			j
			for j in sesion.partida.tablero.legal_moves
			if j.uci() != p.jugadas[1] and not da_mate(sesion, j)
		)
		resultado = jugar(sesion, mala.uci())
		self.assertTrue(resultado.fallo)
		self.assertFalse(resultado.completado)
		self.assertIn("Esa no es la mejor jugada.", resultado.texto)
		self.assertEqual(sesion.partida.tablero.fen(), antes)
		self.assertTrue(sesion.fallado)
		# Después se puede seguir y resolverlo.
		for propia, _respuesta in sesion.ejercicio.guion:
			resultado = jugar(sesion, propia)
		self.assertTrue(resultado.completado)

	def test_otro_mate_vale(self):
		p, otro = con_varios_mates()
		sesion = SesionEjercicio(retos.ejercicio_de_problema(p))
		resultado = jugar(sesion, otro)
		self.assertTrue(resultado.completado)
		self.assertFalse(sesion.fallado)

	def test_respuesta_del_rival(self):
		p = next(p for p in PROBLEMAS if len(p.jugadas) == 4)
		e = retos.ejercicio_de_problema(p)
		self.assertIn("La solución tiene 2 jugadas tuyas.", e.instruccion)
		sesion = SesionEjercicio(e)
		resultado = jugar(sesion, p.jugadas[1])
		self.assertFalse(resultado.completado)
		rival = "Blancas:" if e.color == chess.BLACK else "Negras:"
		self.assertIn(rival, resultado.texto)
		self.assertIn("¡Correcto! Ahora encuentra la siguiente jugada.", resultado.texto)
		self.assertEqual(sesion.partida.tablero.turn, e.color)

	def test_pistas(self):
		p = RETOS.por_tema[Tema.CLAVADA][0]
		sesion = SesionEjercicio(retos.ejercicio_de_problema(p, Tema.CLAVADA))
		self.assertIn("Aprovecha una clavada.", sesion.ejercicio.instruccion)
		self.assertTrue(sesion.siguiente_pista().startswith("Tema: Clavada."))
		self.assertTrue(sesion.siguiente_pista().startswith("Mueve "))
		self.assertFalse(sesion.vio_jugada)
		self.assertTrue(sesion.siguiente_pista().startswith("La jugada es: "))
		self.assertTrue(sesion.vio_jugada)
		self.assertTrue(sesion.fallado)

	def test_racha_no_dice_la_jugada(self):
		p = PROBLEMAS[0]
		sesion = SesionEjercicio(retos.ejercicio_de_problema(p, ver_jugada=False))
		sesion.siguiente_pista()
		sesion.siguiente_pista()
		self.assertIn("En la racha", sesion.siguiente_pista())
		self.assertFalse(sesion.vio_jugada)

	def test_reiniciar(self):
		p = next(p for p in PROBLEMAS if len(p.jugadas) == 4)
		sesion = SesionEjercicio(retos.ejercicio_de_problema(p))
		inicio = sesion.partida.tablero.fen()
		jugar(sesion, p.jugadas[1])
		sesion.reiniciar_partida()
		self.assertEqual(sesion.partida.tablero.fen(), inicio)
		self.assertEqual(sesion.paso, 0)


class PruebaSeleccion(unittest.TestCase):
	def test_cerca_de_tu_nivel(self):
		azar = random.Random(1)
		for nivel in (600, 1000, 1400):
			p = RETOS.cerca_de(nivel, set(), azar)
			self.assertLessEqual(abs(p.dificultad - nivel), 100)
		p = RETOS.cerca_de(1000, set(), azar, Tema.DESCUBIERTA)
		self.assertIn(Tema.DESCUBIERTA, p.temas)

	def test_excluye_y_amplia(self):
		azar = random.Random(2)
		al_paso = RETOS.por_tema[Tema.AL_PASO]
		vistos = {p.id for p in al_paso[:-1]}
		p = RETOS.cerca_de(400, vistos, azar, Tema.AL_PASO)
		self.assertEqual(p.id, al_paso[-1].id)
		# Si ya se vieron todos, repite uno en vez de fallar.
		todos = {p.id for p in al_paso}
		self.assertIn(RETOS.cerca_de(1000, todos, azar, Tema.AL_PASO), al_paso)

	def test_del_dia(self):
		fecha = datetime.date(2026, 10, 2)
		self.assertEqual(RETOS.del_dia(fecha), RETOS.del_dia(fecha))
		self.assertNotEqual(RETOS.del_dia(fecha), RETOS.del_dia(fecha + datetime.timedelta(days=1)))
		self.assertTrue(retos.DIA_MINIMO <= RETOS.del_dia(fecha).dificultad <= retos.DIA_MAXIMO)

	def test_racha_cada_vez_mas_dificil(self):
		azar = random.Random(3)
		primero = RETOS.para_racha(0, set(), azar)
		decimo = RETOS.para_racha(10, set(), azar)
		self.assertLess(primero.dificultad, 600)
		self.assertGreater(decimo.dificultad, 1000)


class PruebaNivel(unittest.TestCase):
	def test_nuevo_nivel(self):
		self.assertGreater(retos.nuevo_nivel(1000, 1000, True, 0), 1000)
		self.assertLess(retos.nuevo_nivel(1000, 1000, False, 0), 1000)
		# Resolver uno difícil sube más que resolver uno fácil.
		sube_dificil = retos.nuevo_nivel(1000, 1400, True, 50) - 1000
		sube_facil = retos.nuevo_nivel(1000, 600, True, 50) - 1000
		self.assertGreater(sube_dificil, sube_facil)
		self.assertEqual(retos.nuevo_nivel(400, 1500, False, 0), retos.NIVEL_MINIMO)

	def test_progreso(self):
		with tempfile.TemporaryDirectory() as carpeta:
			ruta = os.path.join(carpeta, "retos.json")
			progreso = ProgresoRetos(ruta)
			self.assertIsNone(progreso.nivel)
			progreso.nivel = 1000
			p = RETOS.por_tema[Tema.CLAVADA][0]
			nuevo = progreso.registrar(p, True)
			self.assertEqual(progreso.nivel, nuevo)
			self.assertIsNone(progreso.registrar(p, False, cambia_nivel=False))
			self.assertTrue(progreso.registrar_racha(4))
			self.assertFalse(progreso.registrar_racha(3))
			progreso.guardar()
			otra = ProgresoRetos(ruta)
			self.assertEqual(otra.nivel, nuevo)
			self.assertIn(p.id, otra.resueltos)
			self.assertEqual(otra.resueltos_de(Tema.CLAVADA), 1)
			self.assertEqual(otra.intentados, 2)
			self.assertEqual(otra.record_racha, 4)

	def test_archivo_danado(self):
		with tempfile.TemporaryDirectory() as carpeta:
			ruta = os.path.join(carpeta, "retos.json")
			with open(ruta, "w", encoding="utf-8") as archivo:
				json.dump({"version": 1, "nivel": "mucho", "temas": 3}, archivo)
			progreso = ProgresoRetos(ruta)
			self.assertIsNone(progreso.nivel)
			self.assertEqual(progreso.temas, {})

	def test_dias_seguidos(self):
		with tempfile.TemporaryDirectory() as carpeta:
			progreso = ProgresoRetos(os.path.join(carpeta, "retos.json"))
			lunes = datetime.date(2026, 10, 5)
			martes = lunes + datetime.timedelta(days=1)
			miercoles = martes + datetime.timedelta(days=1)
			progreso.registrar_dia(lunes, True)
			# Un fallo y luego el acierto el mismo día: cuenta el día.
			progreso.registrar_dia(martes, False)
			self.assertEqual(progreso.dias_seguidos_hasta(martes), 1)
			progreso.registrar_dia(martes, True)
			self.assertTrue(progreso.dia_jugado(martes))
			self.assertEqual(progreso.dias_seguidos_hasta(martes), 2)
			self.assertEqual(progreso.dias_seguidos_hasta(miercoles), 2)
			# Si pasa un día entero sin resolverlo, se pierden.
			self.assertEqual(progreso.dias_seguidos_hasta(miercoles + datetime.timedelta(days=1)), 0)
			progreso.registrar_dia(miercoles + datetime.timedelta(days=1), True)
			self.assertEqual(progreso.dias_seguidos, 1)


class PruebaSugerencias(unittest.TestCase):
	def test_lecciones(self):
		self.assertIn("Ataque doble", retos.sugerencia_de_leccion("18"))
		self.assertEqual(retos.sugerencia_de_leccion("1"), "")


if __name__ == "__main__":
	unittest.main()
