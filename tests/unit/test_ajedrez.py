# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas de la lógica del ajedrez (sin NVDA), con la traducción al español cargada."""

import os
import sys
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miAjedrezAccesible")
_PO_ES = os.path.join(_RAIZ, "addon", "locale", "es", "LC_MESSAGES", "nvda.po")
sys.path.insert(0, _COMPLEMENTO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import po  # noqa: E402
from ajedrez import anunciador, idioma, motor, notacion  # noqa: E402
from ajedrez.configuracion import ConfiguracionPartida, EleccionColor, Modo  # noqa: E402
from ajedrez.partida import Partida  # noqa: E402

import chess  # noqa: E402

idioma.configurar(*po.traducciones(_PO_ES))


def jugar_texto(partida: Partida, *jugadas: str) -> list[str]:
	return [partida.jugar(notacion.interpretar(partida.tablero, j)) for j in jugadas]


class PruebaTraduccion(unittest.TestCase):
	def test_todos_los_textos_estan_traducidos(self):
		sin_traducir = [
			e.msgid for e in po.leer(_PO_ES) if e.msgid and (not all(e.msgstr.values()) or e.fuzzy)
		]
		self.assertEqual(sin_traducir, [])


class PruebaCasillas(unittest.TestCase):
	def test_casilla_ocupada_y_vacia(self):
		tablero = chess.Board()
		self.assertEqual(anunciador.describir_casilla(tablero, chess.E1), "Rey blanco, e1")
		self.assertEqual(anunciador.describir_casilla(tablero, chess.D8), "Dama negra, d8")
		self.assertEqual(anunciador.describir_casilla(tablero, chess.E4), "e4")

	def test_detalle_casilla(self):
		tablero = chess.Board()
		self.assertEqual(
			anunciador.describir_detalle_casilla(tablero, chess.A1), "a1, casilla oscura, torre blanca",
		)
		self.assertEqual(anunciador.describir_detalle_casilla(tablero, chess.E4), "e4, casilla clara, vacía")

	def test_piezas_de_un_bando(self):
		self.assertEqual(
			anunciador.describir_piezas(chess.Board(), chess.WHITE),
			"Piezas blancas: Rey en e1. Dama en d1. Torres en a1 y h1. Alfiles en c1 y f1. "
			"Caballos en b1 y g1. Peones en a2, b2, c2, d2, e2, f2, g2 y h2.",
		)

	def test_ataques_y_defensas(self):
		tablero = chess.Board()
		self.assertEqual(
			anunciador.describir_ataques(tablero, chess.F3),
			"f3. Controlada por: caballo blanco en g1, peón blanco en e2 y peón blanco en g2.",
		)
		self.assertEqual(
			anunciador.describir_ataques(tablero, chess.E4),
			"e4. Ninguna pieza controla esta casilla.",
		)
		tablero = chess.Board("4k3/8/5n2/8/4P3/3P4/8/4K3 w - - 0 1")
		self.assertEqual(
			anunciador.describir_ataques(tablero, chess.E4),
			"Peón blanco, e4. Atacantes: caballo negro en f6. Defensores: peón blanco en d3.",
		)


class PruebaJugadas(unittest.TestCase):
	def test_mate_del_pastor(self):
		partida = Partida()
		anuncios = jugar_texto(partida, "e4", "e5", "Ac4", "Cc6", "Dh5", "Cf6", "Dxf7")
		self.assertEqual(anuncios[0], "Peón blanco de e2 a e4. Juegan negras.")
		self.assertEqual(anuncios[3], "Caballo negro de b8 a c6. Juegan blancas.")
		self.assertEqual(
			anuncios[-1],
			"Dama blanca de h5 captura peón negro en f7. Jaque mate. Ganan las blancas.",
		)
		self.assertTrue(partida.terminada)
		self.assertEqual(partida.planilla()[-1], "4. Dama blanca de h5 captura peón negro en f7. (Dxf7#)")

	def test_jaque(self):
		partida = Partida()
		anuncios = jugar_texto(partida, "e4", "f5", "Dh5")
		self.assertEqual(anuncios[-1], "Dama blanca de d1 a h5. Jaque. Juegan negras.")

	def test_enroques(self):
		partida = Partida("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
		self.assertEqual(jugar_texto(partida, "O-O")[0], "Blancas enrocan corto. Juegan negras.")
		self.assertEqual(jugar_texto(partida, "0-0-0")[0], "Negras enrocan largo. Juegan blancas.")

	def test_captura_al_paso(self):
		partida = Partida("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
		self.assertEqual(
			jugar_texto(partida, "exd6")[0],
			"Peón blanco de e5 captura al paso en d6. Juegan negras.",
		)

	def test_coronacion(self):
		partida = Partida("r3k3/1P6/8/8/8/8/8/4K3 w - - 0 1")
		jugada = notacion.interpretar(partida.tablero, "b8")
		self.assertIsNone(jugada.promotion)
		self.assertTrue(partida.requiere_coronacion(jugada.from_square, jugada.to_square))
		anuncio = partida.jugar(chess.Move(chess.B7, chess.B8, promotion=chess.KNIGHT))
		self.assertEqual(anuncio, "Peón blanco de b7 a b8, corona en caballo. Juegan negras.")

	def test_ahogado(self):
		partida = Partida("7k/8/6Q1/8/8/8/8/K7 w - - 0 1")
		self.assertEqual(jugar_texto(partida, "Df7")[0], "Dama blanca de g6 a f7. Tablas por ahogado.")

	def test_material_insuficiente(self):
		partida = Partida("4k3/8/8/8/8/8/3r4/4K3 w - - 0 1")
		self.assertEqual(
			jugar_texto(partida, "Rxd2")[0],
			"Rey blanco de e1 captura torre negra en d2. Tablas por material insuficiente.",
		)

	def test_deshacer(self):
		partida = Partida()
		jugar_texto(partida, "e4")
		self.assertEqual(partida.deshacer(), "Jugada deshecha: Peón blanco de e2 a e4. Juegan blancas.")
		self.assertIsNone(partida.deshacer())

	def test_tablas_y_abandono(self):
		partida = Partida()
		jugar_texto(partida, "e4")
		self.assertTrue(partida.en_curso)
		self.assertEqual(partida.abandonar(chess.BLACK), "Las negras abandonan. Ganan las blancas.")
		self.assertTrue(partida.terminada)
		self.assertFalse(partida.en_curso)
		self.assertEqual(Partida().acordar_tablas(), "Tablas por acuerdo.")

	def test_estado(self):
		partida = Partida()
		self.assertEqual(partida.texto_estado(), "Juegan blancas. Jugada 1. Todavía no hay jugadas.")
		jugar_texto(partida, "e4", "f5", "Dh5")
		self.assertEqual(
			partida.texto_estado(),
			"Juegan negras. Jugada 2. En jaque. Última jugada: Dama blanca de d1 a h5.",
		)


class PruebaNotacion(unittest.TestCase):
	def setUp(self):
		self.tablero = chess.Board()

	def jugada(self, texto: str) -> str:
		return notacion.interpretar(self.tablero, texto).uci()

	def test_espanol_ingles_y_coordenadas(self):
		self.assertEqual(self.jugada("Cf3"), "g1f3")
		self.assertEqual(self.jugada("Nf3"), "g1f3")
		self.assertEqual(self.jugada("cf3"), "g1f3")
		self.assertEqual(self.jugada("g1f3"), "g1f3")
		self.assertEqual(self.jugada("g1-f3"), "g1f3")
		self.assertEqual(self.jugada("e4"), "e2e4")
		self.assertEqual(self.jugada(" e4+ "), "e2e4")

	def test_captura_de_peon_no_se_confunde_con_alfil(self):
		tablero = chess.Board("4k3/8/8/1p6/P7/8/8/4K3 w - - 0 1")
		self.assertEqual(notacion.interpretar(tablero, "axb5").uci(), "a4b5")

	def test_coronacion_escrita(self):
		tablero = chess.Board("4k3/1P6/8/8/8/8/8/4K3 w - - 0 1")
		self.assertEqual(notacion.interpretar(tablero, "b8=D").uci(), "b7b8q")
		self.assertEqual(notacion.interpretar(tablero, "b8T").uci(), "b7b8r")
		self.assertEqual(notacion.interpretar(tablero, "b7b8c").uci(), "b7b8n")
		self.assertEqual(notacion.interpretar(tablero, "b7b8").uci(), "b7b8")

	def test_errores(self):
		with self.assertRaises(notacion.ErrorJugada) as error:
			notacion.interpretar(self.tablero, "xyz")
		self.assertEqual(
			str(error.exception), "No entiendo esa jugada. Ejemplos: Cf3, exd5, O-O, e8=D o g1f3.",
		)
		with self.assertRaises(notacion.ErrorJugada) as error:
			notacion.interpretar(self.tablero, "e5")
		self.assertEqual(str(error.exception), "Esa jugada no es posible en esta posición.")
		with self.assertRaises(notacion.ErrorJugada) as error:
			notacion.interpretar(self.tablero, "")
		self.assertEqual(str(error.exception), "Escribe primero una jugada.")

	def test_ambigua(self):
		tablero = chess.Board("4k3/8/8/8/8/8/8/1N2KN2 w - - 0 1")
		with self.assertRaises(notacion.ErrorJugada) as error:
			notacion.interpretar(tablero, "Cd2")
		self.assertIn("Jugada ambigua", str(error.exception))
		self.assertEqual(notacion.interpretar(tablero, "Cbd2").uci(), "b1d2")

	def test_san_en_espanol(self):
		self.assertEqual(notacion.san_en_espanol(self.tablero, chess.Move.from_uci("g1f3")), "Cf3")
		tablero = chess.Board("3r1k2/4P3/8/8/8/8/8/4K3 w - - 0 1")
		self.assertEqual(notacion.san_en_espanol(tablero, chess.Move.from_uci("e7d8q")), "exd8=D+")


class PruebaContraComputadora(unittest.TestCase):
	def test_deshacer_dos_jugadas(self):
		partida = Partida()
		jugar_texto(partida, "e4", "e5")
		self.assertIsNone(partida.deshacer(3))
		self.assertEqual(partida.deshacer(2), "Deshechas las dos últimas jugadas. Juegan blancas.")
		self.assertEqual(partida.historial, [])
		self.assertEqual(partida.tablero.fen(), chess.STARTING_FEN)

	def test_ultima_jugada(self):
		partida = Partida()
		self.assertIsNone(partida.ultima_jugada())
		jugar_texto(partida, "Cf3")
		self.assertEqual(partida.ultima_jugada(), chess.Move.from_uci("g1f3"))

	def test_niveles(self):
		self.assertEqual(sorted(motor.NIVELES), list(range(1, 11)))
		habilidades = [motor.NIVELES[n].habilidad for n in range(1, 11)]
		self.assertEqual(habilidades, sorted(habilidades))
		self.assertEqual(motor.NIVELES[1].profundidad, 1)
		self.assertEqual(motor.NIVELES[10].habilidad, 20)
		self.assertEqual(motor.NIVELES[3].descripcion(), "3: principiante")
		self.assertEqual(motor.NIVELES[10].descripcion(), "10: máximo")

	def test_regla_de_tablas(self):
		self.assertTrue(motor.acepta_tablas(-300))
		self.assertTrue(motor.acepta_tablas(50))
		self.assertFalse(motor.acepta_tablas(51))

	def test_configuracion(self):
		por_defecto = ConfiguracionPartida()
		self.assertEqual(por_defecto.color_persona(), chess.WHITE)
		negras = ConfiguracionPartida(color=EleccionColor.NEGRAS)
		self.assertEqual(negras.color_persona(), chess.BLACK)
		azar = ConfiguracionPartida(color=EleccionColor.AZAR)
		self.assertEqual(azar.color_persona(elegir=lambda opciones: opciones[1]), chess.BLACK)
		dos = ConfiguracionPartida(modo=Modo.DOS_PERSONAS, color=EleccionColor.NEGRAS)
		self.assertIsNone(dos.color_persona())
		rara = ConfiguracionPartida.desde_textos("otro", "verde", 99)
		self.assertEqual(rara, ConfiguracionPartida())
		self.assertEqual(Modo.COMPUTADORA.etiqueta(), "Contra la computadora")


class PruebaErroresIntencionados(unittest.TestCase):
	def test_niveles_bajos_se_equivocan_y_los_altos_no(self):
		errores = [motor.NIVELES[n].errores for n in range(1, 11)]
		self.assertEqual(errores, sorted(errores, reverse=True))
		self.assertGreater(motor.NIVELES[1].errores, 0)
		self.assertEqual(motor.NIVELES[5].errores, 0)

	def test_un_error_es_una_jugada_legal_sin_consultar_al_motor(self):
		# Con errores = 1 siempre se equivoca: no hace falta que Stockfish exista.
		siempre_falla = motor.Nivel(0, habilidad=0, tiempo=0.1, errores=1.0)
		falso = motor.Motor(ruta="no-existe.exe")
		tablero = chess.Board()
		for _vez in range(20):
			jugada = falso.elegir_jugada(tablero, siempre_falla)
			self.assertTrue(tablero.is_legal(jugada))
			tablero.push(jugada)
			if tablero.is_game_over():
				break
		self.assertIsNone(falso._motor)


@unittest.skipUnless(os.path.isfile(motor.RUTA_STOCKFISH), "Stockfish no está descargado")
@unittest.skipUnless(os.environ.get("MEDIR_NIVELES"), "Medición lenta: definir MEDIR_NIVELES=1")
class PruebaEscalaDeNiveles(unittest.TestCase):
	def test_el_nivel_1_es_mas_facil_que_el_4(self):
		sys.path.insert(0, os.path.join(_RAIZ, "herramientas"))
		import medir_niveles

		facil = medir_niveles.medir(1, partidas=20)
		dificil = medir_niveles.medir(4, partidas=20)
		self.assertLess(facil, 50)
		self.assertGreater(dificil, facil)


@unittest.skipUnless(os.path.isfile(motor.RUTA_STOCKFISH), "Stockfish no está descargado")
class PruebaStockfish(unittest.TestCase):
	def test_juega_una_jugada_legal_y_se_cierra(self):
		stockfish = motor.Motor()
		try:
			tablero = chess.Board()
			for numero in (1, 5, 10):
				jugada = stockfish.elegir_jugada(tablero, motor.NIVELES[numero])
				self.assertTrue(tablero.is_legal(jugada))
			# Con una dama de ventaja, la evaluación para quien la tiene es claramente positiva.
			ventaja = chess.Board("4k3/8/8/8/8/8/8/3QK3 w - - 0 1")
			self.assertGreater(stockfish.evaluar(ventaja), 500)
		finally:
			stockfish.cerrar()
		stockfish.cerrar()


if __name__ == "__main__":
	unittest.main()
