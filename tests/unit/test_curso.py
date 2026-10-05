# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Pruebas del curso «Aprender a jugar» (sin NVDA)."""

import os
import random
import sys
import tempfile
import time
import unittest

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COMPLEMENTO = os.path.join(_RAIZ, "addon", "globalPlugins", "miAjedrezAccesible")
_PO_ES = os.path.join(_RAIZ, "addon", "locale", "es", "LC_MESSAGES", "nvda.po")
sys.path.insert(0, _COMPLEMENTO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import po  # noqa: E402
from ajedrez import anunciador, idioma  # noqa: E402
from ajedrez.curso import guerra_peones, modelo, objetivos, practica, resolver  # noqa: E402
from ajedrez.curso.progreso import Progreso  # noqa: E402
from ajedrez.curso.sesion import SesionEjercicio, Sonido, texto_orientacion  # noqa: E402

import chess  # noqa: E402

idioma.configurar(*po.traducciones(_PO_ES))
CURSO = modelo.cargar_curso(modelo.carpeta_de_idioma("es"))


def ejercicio(id_ejercicio: str) -> modelo.Ejercicio:
	return next(e for le in CURSO.lecciones for e in le.ejercicios if e.id == id_ejercicio)


def jugar(sesion: SesionEjercicio, uci: str):
	jugada = chess.Move.from_uci(uci)
	anuncio = sesion.partida.jugar(jugada)
	return sesion.tras_jugada(jugada, anuncio)


class PruebaContenido(unittest.TestCase):
	def test_estructura(self):
		self.assertEqual([b.id for b in CURSO.bloques], ["A", "B", "C", "D", "E", "X"])
		self.assertEqual([le.id for le in CURSO.lecciones], [*(str(n) for n in range(1, 24)), "x1"])
		ids = [e.id for le in CURSO.lecciones for e in le.ejercicios]
		self.assertEqual(len(ids), 121)
		extra = CURSO.leccion("x1")
		self.assertTrue(extra.extra)
		self.assertEqual(extra.numero, "1")
		self.assertTrue(all(e.solo_escrito for e in extra.ejercicios))
		self.assertFalse(any(e.solo_escrito for e in CURSO.leccion("22").ejercicios))
		self.assertEqual(len(ids), len(set(ids)), "Hay ejercicios con el mismo identificador")

	def test_cada_ejercicio_tiene_instruccion_y_dos_pistas(self):
		for leccion in CURSO.lecciones:
			self.assertTrue(leccion.explicacion)
			for e in leccion.ejercicios:
				with self.subTest(ejercicio=e.id):
					self.assertTrue(e.instruccion)
					self.assertEqual(len(e.pistas), 2)
					if e.tipo in (modelo.TipoEjercicio.IR_A, modelo.TipoEjercicio.VISITAR):
						self.assertTrue(e.respuestas)
					elif e.tipo in (modelo.TipoEjercicio.JUGADA, modelo.TipoEjercicio.MATE):
						self.assertIsNotNone(e.solucion)
					elif e.tipo in (modelo.TipoEjercicio.GUERRA_PEONES, modelo.TipoEjercicio.PARTIDA):
						pass
					elif e.tipo is modelo.TipoEjercicio.PARTIDA_ESCRITA:
						self.assertTrue(e.guion)
					else:
						self.assertIsNotNone(e.minimo)
						self.assertTrue(e.manzanas or e.capturar or e.tipo is modelo.TipoEjercicio.CORONAR)
						# Las manzanas están en casillas vacías.
						tablero = e.tablero()
						for casilla in e.manzanas:
							self.assertIsNone(tablero.piece_at(casilla))

	def test_el_minimo_de_cada_ejercicio_es_correcto(self):
		for leccion in CURSO.lecciones:
			for e in leccion.ejercicios:
				if e.tipo not in (modelo.TipoEjercicio.MANZANAS, modelo.TipoEjercicio.CORONAR):
					continue
				with self.subTest(ejercicio=e.id):
					solucion = resolver.resolver(e)
					self.assertIsNotNone(solucion, "El ejercicio no tiene solución")
					self.assertEqual(len(solucion), e.minimo)

	def test_la_solucion_completa_el_ejercicio_con_tres_estrellas(self):
		for leccion in CURSO.lecciones:
			for e in leccion.ejercicios:
				if e.tipo not in (modelo.TipoEjercicio.MANZANAS, modelo.TipoEjercicio.CORONAR):
					continue
				with self.subTest(ejercicio=e.id):
					sesion = SesionEjercicio(e)
					resultado = None
					for jugada in resolver.resolver(e):
						resultado = jugar(sesion, jugada.uci())
					self.assertTrue(resultado.completado)
					self.assertEqual(resultado.estrellas, 3)

	def test_jugadas_y_mates_del_bloque_c(self):
		for leccion in CURSO.lecciones:
			for e in leccion.ejercicios:
				if e.tipo not in (modelo.TipoEjercicio.JUGADA, modelo.TipoEjercicio.MATE):
					continue
				with self.subTest(ejercicio=e.id):
					tablero = e.tablero()
					negras = tablero.copy()
					negras.turn = chess.BLACK
					self.assertFalse(tablero.king(chess.BLACK) is not None and negras.is_check())
					solucion = chess.Move.from_uci(e.solucion)
					self.assertIn(solucion, tablero.legal_moves)
					if e.tipo is modelo.TipoEjercicio.MATE:
						self.assertFalse(objetivos.tiene_mate_en_uno(tablero))
						self.assertTrue(objetivos.es_mate_en_dos(tablero, solucion))
						continue
					cumple, _explicacion = objetivos.evaluar(
						tablero, solucion, e.objetivo, e.casilla, e.forma, e.jugadas,
					)
					self.assertTrue(cumple)
					# La solución del ejercicio completa la sesión con tres estrellas.
					sesion = SesionEjercicio(e)
					resultado = jugar(sesion, e.solucion)
					self.assertTrue(resultado.completado)
					self.assertEqual(resultado.estrellas, 3)

	def test_carpeta_de_idioma(self):
		self.assertTrue(modelo.carpeta_de_idioma("es_CR").endswith(os.path.join("lecciones", "es")))
		self.assertTrue(modelo.carpeta_de_idioma("fr").endswith(os.path.join("lecciones", "es")))


class PruebaSesion(unittest.TestCase):
	def test_ir_a_con_orientacion(self):
		sesion = SesionEjercicio(ejercicio("1.3"))
		resultado = sesion.elegir_casilla(chess.C4)
		self.assertFalse(resultado.completado)
		self.assertEqual(resultado.texto, "Estás en c4. Busca e4: está 2 columnas a la derecha.")
		resultado = sesion.elegir_casilla(chess.E4)
		self.assertTrue(resultado.completado)
		self.assertEqual(resultado.sonido, Sonido.EXITO)
		self.assertIsNone(resultado.estrellas)

	def test_orientacion_en_dos_direcciones(self):
		self.assertEqual(
			texto_orientacion(chess.A1, chess.B3),
			"Estás en a1. Busca b3: está una columna a la derecha y 2 filas más arriba.",
		)
		self.assertEqual(
			texto_orientacion(chess.H8, chess.H7), "Estás en h8. Busca h7: está una fila más abajo.",
		)

	def test_varias_respuestas(self):
		sesion = SesionEjercicio(ejercicio("1.6"))
		self.assertIn("no es una de ellas", sesion.elegir_casilla(chess.B1).texto)
		self.assertTrue(sesion.elegir_casilla(chess.G1).completado)

	def test_visitar(self):
		sesion = SesionEjercicio(ejercicio("2.4"))
		self.assertEqual(sesion.elegir_casilla(chess.D4).texto, "¡d4! Quedan 3.")
		self.assertEqual(sesion.elegir_casilla(chess.D4).texto, "Ya visitaste d4.")
		self.assertEqual(
			sesion.siguiente_pista(), "Las cuatro están juntas, formando un cuadrado en el medio del tablero.",
		)
		self.assertEqual(sesion.siguiente_pista(), "Te faltan: e4, d5 y e5.")
		sesion.elegir_casilla(chess.E4)
		self.assertEqual(sesion.elegir_casilla(chess.E5).texto, "¡e5! Queda 1.")
		self.assertTrue(sesion.elegir_casilla(chess.D5).completado)

	def test_manzanas_y_estrellas(self):
		sesion = SesionEjercicio(ejercicio("4.2"))
		self.assertEqual(sesion.texto_manzanas(), "Quedan 2 manzanas: a6 y f6.")
		resultado = jugar(sesion, "a1a6")
		self.assertEqual(resultado.texto, "Torre blanca de a1 a a6. ¡Manzana! Queda 1.")
		self.assertEqual(resultado.sonido, Sonido.MANZANA)
		self.assertEqual(sesion.partida.turno, chess.WHITE)
		resultado = jugar(sesion, "a6f6")
		self.assertTrue(resultado.completado)
		self.assertIn("¡Manzana!", resultado.texto)
		self.assertIn("Tres estrellas", resultado.texto)
		self.assertEqual(sesion.texto_manzanas(), "Recogiste todas las manzanas.")

	def test_menos_estrellas_con_jugadas_de_mas(self):
		sesion = SesionEjercicio(ejercicio("4.1"))
		jugar(sesion, "d4d5")
		jugar(sesion, "d5d6")
		resultado = jugar(sesion, "d6d7")
		self.assertEqual(resultado.estrellas, 2)
		sesion = SesionEjercicio(ejercicio("4.1"))
		for uci in ("d4a4", "a4a5", "a5d5", "d5d7"):
			resultado = jugar(sesion, uci)
		self.assertEqual(resultado.estrellas, 1)

	def test_capturas(self):
		sesion = SesionEjercicio(ejercicio("4.5"))
		self.assertFalse(jugar(sesion, "a1a5").completado)
		self.assertFalse(jugar(sesion, "a5e5").completado)
		self.assertTrue(jugar(sesion, "e5e8").completado)

	def test_alfil_solo_no_termina_por_material_insuficiente(self):
		sesion = SesionEjercicio(ejercicio("5.1"))
		self.assertFalse(sesion.partida.terminada)
		self.assertTrue(sesion.partida.destinos_legales(chess.C1))

	def test_coronar(self):
		sesion = SesionEjercicio(ejercicio("9.4"))
		resultado = jugar(sesion, "c7c8n")
		self.assertTrue(resultado.completado)
		self.assertIn("Casi siempre conviene la dama", resultado.texto)
		sesion = SesionEjercicio(ejercicio("9.4"))
		self.assertIn("una dama nueva", jugar(sesion, "c7c8q").texto)

	def test_casilla_inicial(self):
		self.assertEqual(ejercicio("4.1").casilla_inicial(), chess.D4)
		self.assertEqual(ejercicio("1.2").casilla_inicial(), chess.H1)


class PruebaPractica(unittest.TestCase):
	EJERCICIOS_POR_NIVEL = 25

	def test_todos_los_ejercicios_generados_son_validos_y_rapidos(self):
		generador = practica.GeneradorPractica(random.Random(2026))
		for id_leccion in sorted(practica.LECCIONES_CON_PRACTICA):
			for nivel in (1, 2, 3):
				inicio = time.perf_counter()
				for _vez in range(self.EJERCICIOS_POR_NIVEL):
					e = generador.generar(id_leccion, nivel)
					with self.subTest(leccion=id_leccion, nivel=nivel, ejercicio=e.instruccion):
						self.assertTrue(e.practica and e.da_estrellas)
						self.assertTrue(e.instruccion)
						self.assertEqual(len(e.pistas), 2)
						if e.tipo in (modelo.TipoEjercicio.IR_A, modelo.TipoEjercicio.VISITAR):
							self.assertTrue(e.respuestas)
						elif e.tipo is modelo.TipoEjercicio.GUERRA_PEONES:
							tablero = e.tablero()
							self.assertTrue(tablero.pieces(chess.PAWN, chess.WHITE))
							self.assertTrue(tablero.pieces(chess.PAWN, chess.BLACK))
						elif e.tipo is modelo.TipoEjercicio.JUGADA:
							tablero = e.tablero()
							validas = objetivos.jugadas_que_cumplen(
								tablero, e.objetivo, e.casilla, e.forma, e.jugadas,
							)
							self.assertTrue(validas)
							self.assertLess(len(validas), sum(1 for _j in tablero.legal_moves))
						elif e.tipo is modelo.TipoEjercicio.MATE:
							self.assertTrue(
								objetivos.es_mate_en_dos(e.tablero(), chess.Move.from_uci(e.solucion)),
							)
						else:
							solucion = resolver.resolver(e, solo_desde=e.inicio)
							self.assertIsNotNone(solucion)
							self.assertEqual(len(solucion), e.minimo)
							self.assertLessEqual(e.minimo, 6)
							for casilla in e.manzanas:
								self.assertIsNone(e.tablero().piece_at(casilla))
				promedio = (time.perf_counter() - inicio) / self.EJERCICIOS_POR_NIVEL
				self.assertLess(
					promedio, 0.5, f"Lección {id_leccion}, nivel {nivel}: {promedio:.2f} s por ejercicio",
				)

	def test_alfil_solo_en_casillas_de_su_color(self):
		generador = practica.GeneradorPractica(random.Random(5))
		for _vez in range(50):
			e = generador.generar("5", 2)
			oscura = anunciador.es_casilla_oscura(e.inicio)
			for casilla in e.manzanas | (e.capturar or frozenset()):
				self.assertEqual(anunciador.es_casilla_oscura(casilla), oscura)

	def test_ronda_y_niveles(self):
		generador = practica.GeneradorPractica(random.Random(1))
		ronda = practica.RondaPractica("4", 1, generador)
		self.assertEqual(ronda.ejercicio(0), ronda.ejercicio(0))
		otro = ronda.cambiar(0)
		self.assertEqual(ronda.ejercicio(0), otro)
		for estrellas in (3, 3, 3, 2, 2):
			ronda.registrar(estrellas)
		self.assertEqual(ronda.ganadas, 13)
		self.assertEqual(ronda.nivel_siguiente(), 2)
		self.assertIn("13 de 15", ronda.texto_final())
		baja = practica.RondaPractica("4", 2, generador)
		for estrellas in (1, 1, 2, 2, 2):
			baja.registrar(estrellas)
		self.assertEqual(baja.nivel_siguiente(), 1)
		igual = practica.RondaPractica("4", 3, generador)
		for estrellas in (3, 3, 3, 3, 3):
			igual.registrar(estrellas)
		self.assertEqual(igual.nivel_siguiente(), 3)

	def test_estrellas_en_ejercicios_de_casillas(self):
		generador = practica.GeneradorPractica(random.Random(3))
		e = generador.generar("1", 2)
		correcta = next(iter(e.respuestas))
		incorrecta = next(c for c in chess.SQUARES if c not in e.respuestas)
		sesion = SesionEjercicio(e)
		self.assertEqual(sesion.elegir_casilla(correcta).estrellas, 3)
		sesion = SesionEjercicio(e)
		sesion.elegir_casilla(incorrecta)
		self.assertEqual(sesion.elegir_casilla(correcta).estrellas, 2)


class PruebaJugadas(unittest.TestCase):
	def test_jugada_equivocada_se_deshace_y_explica(self):
		sesion = SesionEjercicio(ejercicio("12.1"))
		resultado = jugar(sesion, "d1d7")
		self.assertFalse(resultado.completado)
		self.assertIn("Cuidado", resultado.texto)
		self.assertIn("alfil negro en c8", resultado.texto)
		self.assertIn("Inténtalo otra vez", resultado.texto)
		# La jugada se deshizo: la dama vuelve a d1 y el caballo sigue en d7.
		self.assertEqual(sesion.partida.tablero.piece_type_at(chess.D1), chess.QUEEN)
		self.assertEqual(sesion.partida.tablero.piece_type_at(chess.D7), chess.KNIGHT)
		resultado = jugar(sesion, "d1h5")
		self.assertTrue(resultado.completado)
		self.assertEqual(resultado.estrellas, 2)

	def test_mensajes_de_mate(self):
		sesion = SesionEjercicio(ejercicio("17.3"))
		self.assertIn("Ahogado", jugar(sesion, "b1b6").texto)
		sesion = SesionEjercicio(ejercicio("16.3"))
		self.assertIn("no da jaque", jugar(sesion, "a1a2").texto)
		sesion = SesionEjercicio(ejercicio("16.2"))
		texto = jugar(sesion, "d1d4").texto
		self.assertIn("no es jaque mate", texto)
		self.assertIn("g8", texto)

	def test_forma_de_salir_del_jaque(self):
		sesion = SesionEjercicio(ejercicio("15.2"))
		resultado = jugar(sesion, "e1d1")
		self.assertIn("tapar el jaque", resultado.texto)
		self.assertTrue(jugar(sesion, "c1e3").completado)

	def test_mate_en_dos_con_defensa(self):
		sesion = SesionEjercicio(ejercicio("17.4"))
		resultado = jugar(sesion, "a6a7")
		self.assertFalse(resultado.completado)
		self.assertIn("Negras:", resultado.texto)
		self.assertEqual(sesion.partida.turno, chess.WHITE)
		final = None
		for jugada in sesion.partida.tablero.legal_moves:
			prueba = sesion.partida.tablero.copy()
			prueba.push(jugada)
			if prueba.is_checkmate():
				final = jugada
				break
		self.assertIsNotNone(final)
		resultado = jugar(sesion, final.uci())
		self.assertTrue(resultado.completado)

	def test_mate_en_dos_mal_empezado_vuelve_al_inicio(self):
		sesion = SesionEjercicio(ejercicio("17.4"))
		inicial = sesion.partida.tablero.board_fen()
		resultado = jugar(sesion, "a6a1")
		self.assertIn("Inténtalo de nuevo desde el principio", resultado.texto)
		self.assertEqual(sesion.partida.tablero.board_fen(), inicial)
		self.assertEqual(sesion.partida.historial, [])


class PruebaBloquesDyE(unittest.TestCase):
	def test_enroque_equivocado(self):
		sesion = SesionEjercicio(ejercicio("19.1"))
		self.assertIn("no es un enroque", jugar(sesion, "h1h2").texto)
		self.assertTrue(jugar(sesion, "e1g1").completado)

	def test_al_paso(self):
		sesion = SesionEjercicio(ejercicio("20.1"))
		self.assertIn("al paso", jugar(sesion, "e5e6").texto)
		resultado = jugar(sesion, "e5d6")
		self.assertTrue(resultado.completado)
		self.assertIn("captura al paso", resultado.texto)

	def test_notacion_con_mensaje_propio(self):
		sesion = SesionEjercicio(ejercicio("22.2"))
		self.assertIn("Pulsa J y escribe Cf3", jugar(sesion, "b1c3").texto)
		self.assertTrue(jugar(sesion, "g1f3").completado)

	def test_guerra_de_peones_termina(self):
		for semilla in range(6):
			sesion = SesionEjercicio(ejercicio("23.1"), azar=random.Random(semilla))
			azar_blancas = random.Random(100 + semilla)
			resultado = None
			for _turno in range(300):
				tablero = sesion.partida.tablero
				jugada = guerra_peones.elegir_jugada(tablero.copy(), azar_blancas, errores=0.0)
				resultado = jugar(sesion, jugada.uci())
				if resultado.completado:
					break
			with self.subTest(semilla=semilla):
				self.assertTrue(resultado.completado, "La guerra de peones no terminó")

	def test_partida_del_curso(self):
		sesion = SesionEjercicio(ejercicio("23.3"))
		self.assertTrue(sesion.empezar_partida().completado)

	def test_la_ia_corona_si_puede(self):
		tablero = chess.Board("8/4P3/8/8/8/8/p7/8 b - - 0 1")
		self.assertEqual(guerra_peones.elegir_jugada(tablero, random.Random(1)).uci(), "a2a1q")


class PruebaExtras(unittest.TestCase):
	def test_partida_escrita_completa(self):
		sesion = SesionEjercicio(ejercicio("x1.6"))
		self.assertIn("Tu jugada: Peón blanco de e2 a e4.", sesion.instruccion_actual())
		resultado = jugar(sesion, "d2d4")
		self.assertIn("Esa no es la jugada pedida", resultado.texto)
		self.assertEqual(len(sesion.partida.historial), 0)
		resultado = jugar(sesion, "e2e4")
		self.assertIn("Negras: Peón negro de e7 a e5.", resultado.texto)
		self.assertIn("Tu jugada: Alfil blanco de f1 a c4.", resultado.texto)
		jugar(sesion, "f1c4")
		jugar(sesion, "d1h5")
		resultado = jugar(sesion, "h5f7")
		self.assertTrue(resultado.completado)
		self.assertIn("Jaque mate", resultado.texto)
		self.assertEqual(resultado.estrellas, 2)

	def test_guion_legal(self):
		e = ejercicio("x1.6")
		tablero = e.tablero()
		for blancas, negras in e.guion:
			self.assertIn(chess.Move.from_uci(blancas), tablero.legal_moves)
			tablero.push_uci(blancas)
			if negras:
				self.assertIn(chess.Move.from_uci(negras), tablero.legal_moves)
				tablero.push_uci(negras)
		self.assertTrue(tablero.is_checkmate())

	def test_retos_sin_mirar(self):
		for id_ejercicio in ("x1.7", "x1.8"):
			e = ejercicio(id_ejercicio)
			self.assertTrue(e.a_ciegas and e.solo_escrito)
			# Empieza en una casilla vacía, para no delatar ninguna pieza.
			self.assertIsNone(e.tablero().piece_at(e.casilla_inicial()))

	def test_practica_del_extra(self):
		generador = practica.GeneradorPractica(random.Random(4))
		for nivel in (1, 2, 3):
			e = generador.generar("x1", nivel)
			self.assertTrue(e.solo_escrito)
			if nivel == 3:
				self.assertTrue(e.a_ciegas)
				self.assertIn("Piezas negras", e.instruccion)


class PruebaProgreso(unittest.TestCase):
	def test_practica(self):
		with tempfile.TemporaryDirectory() as carpeta:
			ruta = os.path.join(carpeta, "progreso.json")
			progreso = Progreso(ruta)
			self.assertEqual(progreso.nivel_practica("4"), 1)
			self.assertIsNone(progreso.mejor_practica("4"))
			progreso.registrar_practica("4", 2, 13)
			progreso.registrar_practica("4", 2, 9)
			progreso.guardar()
			otro = Progreso(ruta)
			self.assertEqual(otro.nivel_practica("4"), 2)
			self.assertEqual(otro.mejor_practica("4"), 13)

	def test_guardar_y_cargar(self):
		with tempfile.TemporaryDirectory() as carpeta:
			ruta = os.path.join(carpeta, "sub", "progreso.json")
			progreso = Progreso(ruta)
			leccion = CURSO.leccion("4")
			self.assertEqual(progreso.primer_pendiente(leccion), 0)
			progreso.registrar("4.1", 3)
			progreso.registrar("4.1", 1)
			progreso.registrar("4.2", 2)
			progreso.guardar()
			otro = Progreso(ruta)
			self.assertEqual(otro.ejercicios, {"4.1": 3, "4.2": 2})
			self.assertEqual(otro.primer_pendiente(leccion), 2)
			self.assertEqual(otro.estrellas_de(leccion), 5)
			self.assertEqual(leccion.estrellas_posibles, 18)
			self.assertFalse(otro.leccion_completada(leccion))

	def test_archivo_danado(self):
		with tempfile.TemporaryDirectory() as carpeta:
			ruta = os.path.join(carpeta, "progreso.json")
			with open(ruta, "w", encoding="utf-8") as archivo:
				archivo.write("{esto no es json")
			self.assertEqual(Progreso(ruta).ejercicios, {})


if __name__ == "__main__":
	unittest.main()
