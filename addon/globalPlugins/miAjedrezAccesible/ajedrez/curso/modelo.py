# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Bloques, lecciones y ejercicios del curso, leídos de los archivos JSON de `lecciones/<idioma>/`."""

import glob
import json
import os
from dataclasses import dataclass
from enum import StrEnum

import chess

from .objetivos import Forma, Objetivo

CARPETA_LECCIONES = os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"lecciones",
)
IDIOMA_POR_DEFECTO = "es"

# Atajos para las posiciones más usadas.
POSICIONES = {
	"vacio": "8/8/8/8/8/8/8/8",
	"inicial": chess.STARTING_BOARD_FEN,
}


class TipoEjercicio(StrEnum):
	# Ir a una casilla y pulsar Intro (vale cualquiera de las respuestas).
	IR_A = "ir_a"
	# Pulsar Intro en todas las casillas indicadas, en cualquier orden.
	VISITAR = "visitar"
	# Recoger manzanas y capturar piezas negras que no se mueven.
	MANZANAS = "manzanas"
	# Coronar un peón.
	CORONAR = "coronar"
	# Una sola jugada que cumpla un objetivo (dar jaque, proteger, capturar sin perder la pieza…).
	JUGADA = "jugada"
	# Dar mate en varias jugadas; las negras se defienden.
	MATE = "mate"
	# Minijuego: solo peones; gana quien corona primero o deja al rival sin jugadas.
	GUERRA_PEONES = "guerra_peones"
	# Empieza una partida de verdad contra la computadora.
	PARTIDA = "partida"
	# Una partida corta guiada: cada jugada se pide con palabras y las negras responden con un guion.
	PARTIDA_ESCRITA = "partida_escrita"
	# Un problema de Retos: el rival acaba de jugar y hay que encontrar la mejor jugada.
	PROBLEMA = "problema"


@dataclass(frozen=True)
class Ejercicio:
	id: str
	tipo: TipoEjercicio
	posicion: str
	instruccion: str
	pistas: tuple[str, ...]
	inicio: chess.Square | None = None
	respuestas: frozenset[chess.Square] = frozenset()
	manzanas: frozenset[chess.Square] = frozenset()
	# Casillas cuyas piezas negras hay que capturar; None si no hay que capturar.
	capturar: frozenset[chess.Square] | None = None
	minimo: int | None = None
	titulo: str | None = None
	corona_dama: str = ""
	corona_otra: str = ""
	# Ejercicio creado por «Practicar más»: todos dan estrellas y no cuentan para la lección.
	practica: bool = False
	# Ejercicios de jugada: objetivo, casilla y forma que exige, jugadas válidas fijas
	# (si se indican) y mensaje propio para una jugada equivocada.
	objetivo: Objetivo | None = None
	casilla: chess.Square | None = None
	forma: Forma | None = None
	jugadas: frozenset[str] = frozenset()
	mensaje_error: str = ""
	# Ejercicios de mate: número de jugadas de las blancas.
	jugadas_mate: int = 1
	# Solución de referencia (en notación UCI), para las pruebas.
	solucion: str | None = None
	# Derechos de enroque y casilla de captura al paso, como en la notación FEN («KQ», «d6»).
	enroques: str = "-"
	al_paso: str = "-"
	# Solo se puede jugar escribiendo con la tecla J (no tomando piezas con Intro).
	solo_escrito: bool = False
	# Reto «a ciegas»: el tablero no dice qué pieza hay en cada casilla.
	a_ciegas: bool = False
	# Partida escrita: pares (jugada de las blancas, respuesta de las negras o None), en UCI.
	guion: tuple[tuple[str, str | None], ...] = ()
	# Turno en la posición inicial, como en la notación FEN («w» o «b»).
	turno: str = "w"
	# Problemas: jugada del rival que se hace al empezar (UCI) y si la pista puede decir la jugada.
	jugada_previa: str = ""
	ver_jugada: bool = True

	@property
	def da_estrellas(self) -> bool:
		return self.practica or self.tipo in (
			TipoEjercicio.MANZANAS,
			TipoEjercicio.CORONAR,
			TipoEjercicio.JUGADA,
			TipoEjercicio.MATE,
			TipoEjercicio.GUERRA_PEONES,
			TipoEjercicio.PARTIDA_ESCRITA,
		)

	@property
	def estrellas_por_intentos(self) -> bool:
		"""Las estrellas dependen de los fallos y las pistas, no del número de jugadas."""
		return self.tipo in (
			TipoEjercicio.IR_A,
			TipoEjercicio.VISITAR,
			TipoEjercicio.JUGADA,
			TipoEjercicio.MATE,
			TipoEjercicio.GUERRA_PEONES,
			TipoEjercicio.PARTIDA_ESCRITA,
		)

	def tablero(self) -> chess.Board:
		"""Tablero inicial del ejercicio. Salvo en los problemas, siempre juegan las blancas."""
		return chess.Board(f"{self.posicion} {self.turno} {self.enroques} {self.al_paso} 0 1")

	@property
	def color(self) -> chess.Color:
		"""Color de quien resuelve: en los problemas, el contrario del que hace la jugada previa."""
		if self.jugada_previa:
			return self.turno != "w"
		return chess.WHITE

	def casilla_inicial(self) -> chess.Square:
		"""Donde empieza el foco: la indicada, o la primera pieza propia, o a1."""
		if self.inicio is not None:
			return self.inicio
		propias = sorted(chess.SquareSet(self.tablero().occupied_co[self.color]))
		return propias[0] if propias else chess.A1


@dataclass(frozen=True)
class Leccion:
	id: str
	titulo: str
	explicacion: tuple[str, ...]
	ejercicios: tuple[Ejercicio, ...]
	bloque_id: str
	bloque_titulo: str
	# Las lecciones extra son opcionales: van al final de la lista y se numeran aparte.
	extra: bool = False
	numero: str = ""

	@property
	def estrellas_posibles(self) -> int:
		return 3 * sum(1 for e in self.ejercicios if e.da_estrellas)


@dataclass(frozen=True)
class Bloque:
	id: str
	titulo: str
	mensaje_final: str
	lecciones: tuple[Leccion, ...]


@dataclass(frozen=True)
class Curso:
	bloques: tuple[Bloque, ...]

	@property
	def lecciones(self) -> list[Leccion]:
		return [leccion for bloque in self.bloques for leccion in bloque.lecciones]

	def leccion(self, id_leccion: str) -> Leccion | None:
		return next((le for le in self.lecciones if le.id == id_leccion), None)

	def siguiente(self, leccion: Leccion) -> Leccion | None:
		lecciones = self.lecciones
		indice = lecciones.index(leccion)
		return lecciones[indice + 1] if indice + 1 < len(lecciones) else None

	def bloque_de(self, leccion: Leccion) -> Bloque:
		return next(b for b in self.bloques if b.id == leccion.bloque_id)

	def es_ultima_del_bloque(self, leccion: Leccion) -> bool:
		return self.bloque_de(leccion).lecciones[-1] == leccion


def _casillas(nombres: list[str]) -> frozenset[chess.Square]:
	return frozenset(chess.parse_square(n) for n in nombres)


def _ejercicio(datos: dict, solo_escrito: bool = False) -> Ejercicio:
	posicion = POSICIONES.get(datos["posicion"], datos["posicion"])
	capturar_datos = datos.get("capturar")
	capturar: frozenset[chess.Square] | None
	if capturar_datos == "todas":
		tablero = chess.Board(f"{posicion} w - - 0 1")
		capturar = frozenset(chess.SquareSet(tablero.occupied_co[chess.BLACK]))
	elif capturar_datos:
		capturar = _casillas(capturar_datos)
	else:
		capturar = None
	return Ejercicio(
		id=datos["id"],
		tipo=TipoEjercicio(datos["tipo"]),
		posicion=posicion,
		instruccion=datos["instruccion"],
		pistas=tuple(datos.get("pistas", ())),
		inicio=chess.parse_square(datos["inicio"]) if "inicio" in datos else None,
		respuestas=_casillas(datos.get("respuestas", [])),
		manzanas=_casillas(datos.get("manzanas", [])),
		capturar=capturar,
		minimo=datos.get("minimo"),
		titulo=datos.get("titulo"),
		corona_dama=datos.get("corona_dama", ""),
		corona_otra=datos.get("corona_otra", ""),
		objetivo=Objetivo(datos["objetivo"]) if "objetivo" in datos else None,
		casilla=chess.parse_square(datos["casilla"]) if "casilla" in datos else None,
		forma=Forma(datos["forma"]) if "forma" in datos else None,
		jugadas=frozenset(datos.get("jugadas", [])),
		mensaje_error=datos.get("mensaje_error", ""),
		jugadas_mate=datos.get("jugadas_mate", 1),
		solucion=datos.get("solucion"),
		enroques=datos.get("enroques", "-"),
		al_paso=datos.get("al_paso", "-"),
		solo_escrito=datos.get("solo_escrito", solo_escrito),
		a_ciegas=datos.get("a_ciegas", False),
		guion=tuple((par[0], par[1] if len(par) > 1 else None) for par in datos.get("guion", [])),
	)


def _bloque(datos: dict) -> Bloque:
	extra = datos.get("extra", False)
	lecciones = tuple(
		Leccion(
			id=le["id"],
			titulo=le["titulo"],
			explicacion=tuple(le["explicacion"]),
			ejercicios=tuple(_ejercicio(e, le.get("solo_escrito", False)) for e in le["ejercicios"]),
			bloque_id=datos["id"],
			bloque_titulo=datos["titulo"],
			extra=extra,
			numero=str(posicion + 1) if extra else le["id"],
		)
		for posicion, le in enumerate(datos["lecciones"])
	)
	return Bloque(
		id=datos["id"],
		titulo=datos["titulo"],
		mensaje_final=datos["mensaje_final"],
		lecciones=lecciones,
	)


def carpeta_de_idioma(idioma: str, carpeta: str = CARPETA_LECCIONES) -> str:
	"""Carpeta de lecciones para un idioma como «es_CR»: prueba «es_CR», luego «es».

	Si no hay lecciones en ese idioma: en español para cualquier variante del español, y en inglés
	para el resto de los idiomas (lo entiende más gente que el español).
	"""
	base = idioma.split("_")[0]
	respaldo = IDIOMA_POR_DEFECTO if base.lower() == "es" else "en"
	for candidato in (idioma, base, respaldo, IDIOMA_POR_DEFECTO):
		ruta = os.path.join(carpeta, candidato)
		if candidato and os.path.isdir(ruta):
			return ruta
	return os.path.join(carpeta, IDIOMA_POR_DEFECTO)


def cargar_curso(carpeta: str) -> Curso:
	bloques = []
	for ruta in sorted(glob.glob(os.path.join(carpeta, "bloque_*.json"))):
		with open(ruta, encoding="utf-8") as archivo:
			bloques.append(_bloque(json.load(archivo)))
	return Curso(bloques=tuple(bloques))
