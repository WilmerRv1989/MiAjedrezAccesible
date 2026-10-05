# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas del reloj y de las partidas en PGN (sin NVDA)."""

import datetime
import os
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miAjedrezAccesible")
_PO_ES = os.path.join(_RAIZ, "addon", "locale", "es", "LC_MESSAGES", "nvda.po")
sys.path.insert(0, _COMPLEMENTO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import po  # noqa: E402
from ajedrez import archivo_pgn, idioma, reloj  # noqa: E402
from ajedrez.configuracion import ConfiguracionPartida, EleccionColor, Modo  # noqa: E402
from ajedrez.partida import Motivo, Partida  # noqa: E402

import chess  # noqa: E402

idioma.configurar(*po.traducciones(_PO_ES))
FECHA = datetime.date(2026, 10, 3)


class Tiempo:
	"""Un reloj de pared falso que avanza a mano."""

	def __init__(self) -> None:
		self.ahora = 0.0

	def __call__(self) -> float:
		return self.ahora


def jugar(partida: Partida, *jugadas: str) -> None:
	for uci in jugadas:
		partida.jugar(chess.Move.from_uci(uci))


class PruebaReloj(unittest.TestCase):
	def setUp(self) -> None:
		self.tiempo = Tiempo()

	def nuevo(self, id_control: str = "10+5", cuentan=(chess.WHITE, chess.BLACK)) -> reloj.Reloj:
		return reloj.Reloj(reloj.control(id_control), cuentan, ahora=self.tiempo)

	def test_controles(self):
		self.assertFalse(reloj.control("sin").con_reloj)
		self.assertEqual(reloj.control("10+5").pgn, "600+5")
		self.assertEqual(reloj.control("sin").pgn, "-")
		self.assertEqual(reloj.control("otro"), reloj.SIN_RELOJ)
		self.assertEqual(reloj.control("15+10").etiqueta(), "15 minutos + 10 segundos por jugada")
		self.assertEqual(reloj.control("30+0").etiqueta(), "30 minutos")

	def test_texto_tiempo(self):
		self.assertEqual(reloj.texto_tiempo(272.9), "4 minutos y 32 segundos")
		self.assertEqual(reloj.texto_tiempo(60), "1 minuto")
		self.assertEqual(reloj.texto_tiempo(1), "1 segundo")
		self.assertEqual(reloj.texto_tiempo(-3), "0 segundos")

	def test_corre_el_del_turno_e_incremento(self):
		r = self.nuevo()
		r.poner_en_marcha(chess.WHITE)
		self.tiempo.ahora = 10
		self.assertEqual(r.tiempo(chess.WHITE), 590)
		self.assertEqual(r.tiempo(chess.BLACK), 600)
		r.tras_jugada(chess.WHITE, chess.BLACK)
		self.assertEqual(r.tiempo(chess.WHITE), 595)
		self.tiempo.ahora = 30
		self.assertEqual(r.tiempo(chess.WHITE), 595)
		self.assertEqual(r.tiempo(chess.BLACK), 580)

	def test_contra_la_computadora_solo_cuenta_la_persona(self):
		r = self.nuevo(cuentan=(chess.BLACK,))
		r.poner_en_marcha(chess.WHITE)
		self.tiempo.ahora = 100
		r.tras_jugada(chess.WHITE, chess.BLACK)
		self.assertEqual(r.tiempo(chess.WHITE), 600)
		self.assertEqual(r.corriendo, chess.BLACK)

	def test_pausa_y_suspensiones(self):
		r = self.nuevo()
		r.poner_en_marcha(chess.WHITE)
		self.tiempo.ahora = 10
		r.pausar()
		self.tiempo.ahora = 100
		self.assertEqual(r.tiempo(chess.WHITE), 590)
		r.reanudar()
		self.tiempo.ahora = 110
		self.assertEqual(r.tiempo(chess.WHITE), 580)
		# Suspensiones anidadas: un menú que abre un diálogo.
		r.suspender()
		r.suspender()
		self.tiempo.ahora = 200
		r.continuar()
		self.tiempo.ahora = 250
		self.assertEqual(r.tiempo(chess.WHITE), 580)
		r.continuar()
		self.tiempo.ahora = 260
		self.assertEqual(r.tiempo(chess.WHITE), 570)

	def test_jugar_quita_la_pausa(self):
		r = self.nuevo(cuentan=(chess.WHITE,))
		r.poner_en_marcha(chess.WHITE)
		r.pausar()
		r.tras_jugada(chess.WHITE, chess.BLACK)
		self.assertFalse(r.pausado)

	def test_agotado_y_avisos(self):
		r = self.nuevo("5+3")
		r.poner_en_marcha(chess.WHITE)
		self.tiempo.ahora = 240
		self.assertEqual(r.aviso_pendiente(), (chess.WHITE, 60))
		self.assertIsNone(r.aviso_pendiente())
		# Si se saltan varios avisos, solo se da el menor.
		self.tiempo.ahora = 295
		self.assertEqual(r.aviso_pendiente(), (chess.WHITE, 10))
		self.assertIsNone(r.agotado())
		self.tiempo.ahora = 300
		self.assertEqual(r.agotado(), chess.WHITE)
		r.detener()
		self.assertIsNone(r.agotado())

	def test_el_incremento_rearma_los_avisos(self):
		r = self.nuevo("5+3")
		r.poner_en_marcha(chess.WHITE)
		self.tiempo.ahora = 271
		self.assertEqual(r.aviso_pendiente(), (chess.WHITE, 30))
		r.tras_jugada(chess.WHITE, chess.BLACK)
		r.tras_jugada(chess.BLACK, chess.WHITE)
		self.assertGreater(r.tiempo(chess.WHITE), 30)
		self.tiempo.ahora = 275
		self.assertEqual(r.aviso_pendiente(), (chess.WHITE, 30))

	def test_tiempos_cargados(self):
		r = reloj.Reloj(reloj.control("10+5"), (chess.WHITE,), {chess.WHITE: 25.0}, ahora=self.tiempo)
		r.poner_en_marcha(chess.WHITE)
		# Los avisos que ya pasaron no se repiten al continuar la partida.
		self.assertIsNone(r.aviso_pendiente())
		self.tiempo.ahora = 16
		self.assertEqual(r.aviso_pendiente(), (chess.WHITE, 10))


class PruebaFinales(unittest.TestCase):
	def test_tiempo(self):
		partida = Partida()
		self.assertEqual(
			partida.perder_por_tiempo(chess.WHITE), "Se acabó el tiempo de las blancas. Ganan las negras.",
		)
		self.assertEqual(partida.resultado_pgn, "0-1")
		self.assertTrue(partida.terminada)

	def test_tiempo_sin_material_para_dar_mate(self):
		# Rey y dama blancos contra rey solo: las negras no pueden dar mate.
		partida = Partida("8/8/4k3/8/8/8/4K3/7Q b - - 0 1")
		self.assertNotIn("tablas", partida.perder_por_tiempo(chess.BLACK))
		self.assertEqual(partida.resultado_pgn, "1-0")
		partida = Partida("8/8/4k3/8/8/8/4K3/7Q w - - 0 1")
		self.assertIn("tablas", partida.perder_por_tiempo(chess.WHITE))
		self.assertEqual(partida.resultado_pgn, "1/2-1/2")

	def test_resultados(self):
		self.assertEqual(Partida().resultado_pgn, "*")
		partida = Partida()
		partida.abandonar(chess.WHITE)
		self.assertEqual(partida.resultado_pgn, "0-1")
		mate = Partida()
		jugar(mate, "f2f3", "e7e5", "g2g4", "d8h4")
		self.assertEqual(mate.resultado_pgn, "0-1")


class PruebaPgn(unittest.TestCase):
	def test_ida_y_vuelta(self):
		partida = Partida()
		jugar(partida, "e2e4", "e7e5", "g1f3")
		configuracion = ConfiguracionPartida(Modo.COMPUTADORA, EleccionColor.NEGRAS, 4, "10+5")
		r = reloj.Reloj(configuracion.control_tiempo, (chess.BLACK,), {chess.BLACK: 321.5})
		texto = archivo_pgn.exportar(partida, configuracion, chess.BLACK, r, FECHA)
		self.assertIn('[Date "2026.10.03"]', texto)
		self.assertIn('[White "Computadora, nivel 4"]', texto)
		self.assertIn('[Black "Persona"]', texto)
		self.assertIn('[TimeControl "600+5"]', texto)
		self.assertIn("1. e4 e5 2. Nf3 *", texto)
		cargada = archivo_pgn.importar(texto)
		self.assertTrue(cargada.se_puede_continuar)
		self.assertEqual(cargada.configuracion, configuracion)
		self.assertEqual(cargada.color_persona, chess.BLACK)
		self.assertAlmostEqual(cargada.restante[chess.BLACK], 321.5, places=1)
		self.assertEqual(cargada.partida.tablero.fen(), partida.tablero.fen())
		self.assertEqual(cargada.partida.planilla(), partida.planilla())

	def test_dos_personas_sin_reloj(self):
		partida = Partida()
		jugar(partida, "d2d4")
		configuracion = ConfiguracionPartida(Modo.DOS_PERSONAS)
		cargada = archivo_pgn.importar(archivo_pgn.exportar(partida, configuracion, None, None, FECHA))
		self.assertEqual(cargada.configuracion.modo, Modo.DOS_PERSONAS)
		self.assertIsNone(cargada.color_persona)
		self.assertIsNone(cargada.restante)

	def test_final_acordado(self):
		for terminar, motivo in (
			(lambda p: p.abandonar(chess.BLACK), Motivo.ABANDONO),
			(lambda p: p.acordar_tablas(), Motivo.ACUERDO),
			(lambda p: p.perder_por_tiempo(chess.WHITE), Motivo.TIEMPO),
		):
			partida = Partida()
			jugar(partida, "e2e4")
			texto_final = terminar(partida)
			texto = archivo_pgn.exportar(partida, ConfiguracionPartida(), chess.WHITE, None, FECHA)
			cargada = archivo_pgn.importar(texto)
			self.assertFalse(cargada.se_puede_continuar)
			self.assertEqual(cargada.partida.final_acordado.motivo, motivo)
			self.assertEqual(cargada.partida.texto_final(), texto_final)
			if motivo is Motivo.TIEMPO:
				self.assertIn('[Termination "Time forfeit"]', texto)

	def test_partida_ajena(self):
		texto = """[Event "Casual"]
[White "Ana"]
[Black "Luis"]
[Result "1-0"]

1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0
"""
		cargada = archivo_pgn.importar(texto)
		self.assertIsNone(cargada.configuracion)
		self.assertFalse(cargada.se_puede_continuar)
		self.assertEqual((cargada.blancas, cargada.negras), ("Ana", "Luis"))
		self.assertTrue(cargada.partida.tablero.is_checkmate())
		self.assertFalse(cargada.incompleta)

	def test_resultado_sin_motivo(self):
		cargada = archivo_pgn.importar('[Result "0-1"]\n\n1. e4 e5 0-1\n')
		self.assertEqual(cargada.partida.final_acordado.motivo, Motivo.RESULTADO)
		self.assertEqual(cargada.partida.texto_final(), "Ganan las negras.")

	def test_jugada_ilegal(self):
		cargada = archivo_pgn.importar("1. e4 e5 2. Ke3 Nc6 *\n")
		self.assertTrue(cargada.incompleta)
		self.assertEqual(len(cargada.partida.historial), 2)

	def test_no_es_una_partida(self):
		self.assertIsNone(archivo_pgn.importar(""))
		self.assertIsNone(archivo_pgn.importar("Lista de la compra: pan y leche."))

	def test_posicion_inicial_propia(self):
		fen = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"
		partida = Partida(fen)
		jugar(partida, "e2e4")
		cargada = archivo_pgn.importar(
			archivo_pgn.exportar(partida, ConfiguracionPartida(), chess.WHITE, None, FECHA),
		)
		self.assertEqual(cargada.partida.tablero.root().fen(), fen)

	def test_nombre_de_archivo(self):
		momento = datetime.datetime(2026, 10, 3, 15, 30)
		self.assertEqual(archivo_pgn.nombre_archivo(momento), "Partida 2026-10-03 15.30.pgn")


class PruebaRepaso(unittest.TestCase):
	def setUp(self) -> None:
		partida = Partida()
		jugar(partida, "e2e4", "e7e5", "g1f3")
		partida.abandonar(chess.BLACK)
		self.repaso = archivo_pgn.Repaso(partida)

	def test_avanzar_y_retroceder(self):
		repaso = self.repaso
		self.assertEqual((repaso.indice, repaso.total), (0, 3))
		self.assertIsNone(repaso.retroceder())
		self.assertTrue(repaso.avanzar().startswith("1. Peón blanco de e2 a e4."))
		self.assertTrue(repaso.avanzar().startswith("1. Peón negro de e7 a e5."))
		ultima = repaso.avanzar()
		self.assertIn("Fin de la partida: Las negras abandonan. Ganan las blancas.", ultima)
		self.assertIsNone(repaso.avanzar())
		self.assertEqual(repaso.retroceder(), "Atrás: 2. Caballo blanco de g1 a f3.")
		self.assertEqual(repaso.indice, 2)

	def test_saltos_y_estado(self):
		repaso = self.repaso
		repaso.ir_al_final()
		self.assertEqual(repaso.indice, 3)
		self.assertIn("Tras 3 de 3 jugadas.", repaso.texto_estado())
		self.assertIn("Fin de la partida", repaso.texto_estado())
		repaso.ir_al_principio()
		self.assertEqual(repaso.partida.tablero.fen(), chess.STARTING_FEN)
		self.assertNotIn("Fin de la partida", repaso.texto_estado())


class PruebaConfiguracion(unittest.TestCase):
	def test_reloj(self):
		self.assertEqual(ConfiguracionPartida().reloj, "sin")
		self.assertEqual(ConfiguracionPartida(reloj="otro").reloj, "sin")
		configuracion = ConfiguracionPartida.desde_textos("computadora", "negras", 5, "5+3")
		self.assertEqual(configuracion.control_tiempo.incremento, 3)


if __name__ == "__main__":
	unittest.main()
