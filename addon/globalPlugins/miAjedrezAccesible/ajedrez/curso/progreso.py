# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Progreso del curso: qué ejercicios están superados y con cuántas estrellas.

Se guarda en un archivo JSON. Un archivo dañado o de otra versión no impide usar el curso:
simplemente se empieza de cero.
"""

import json
import os

from .modelo import Leccion

VERSION = 1


class Progreso:
	def __init__(self, ruta: str) -> None:
		self.ruta = ruta
		# Ejercicio superado → mejores estrellas (0 en los ejercicios sin estrellas).
		self.ejercicios: dict[str, int] = {}
		# Práctica por lección: nivel actual y mejor ronda (estrellas).
		self.practica: dict[str, dict[str, int]] = {}
		self.cargar()

	def cargar(self) -> None:
		try:
			with open(self.ruta, encoding="utf-8") as archivo:
				datos = json.load(archivo)
		except (OSError, ValueError):
			return
		if isinstance(datos, dict) and datos.get("version") == VERSION:
			ejercicios = datos.get("ejercicios", {})
			if isinstance(ejercicios, dict):
				self.ejercicios = {str(k): int(v) for k, v in ejercicios.items() if isinstance(v, int)}
			practica = datos.get("practica", {})
			if isinstance(practica, dict):
				self.practica = {
					str(k): {"nivel": int(v.get("nivel", 1)), "mejor": int(v.get("mejor", 0))}
					for k, v in practica.items()
					if isinstance(v, dict)
				}

	def guardar(self) -> None:
		os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
		temporal = self.ruta + ".tmp"
		with open(temporal, "w", encoding="utf-8") as archivo:
			json.dump(
				{"version": VERSION, "ejercicios": self.ejercicios, "practica": self.practica},
				archivo,
				ensure_ascii=False,
				indent=1,
			)
		os.replace(temporal, self.ruta)

	def registrar(self, id_ejercicio: str, estrellas: int | None) -> None:
		"""Marca un ejercicio como superado, conservando las mejores estrellas."""
		valor = estrellas or 0
		self.ejercicios[id_ejercicio] = max(valor, self.ejercicios.get(id_ejercicio, 0))

	def superado(self, id_ejercicio: str) -> bool:
		return id_ejercicio in self.ejercicios

	def leccion_completada(self, leccion: Leccion) -> bool:
		return all(self.superado(e.id) for e in leccion.ejercicios)

	def estrellas_de(self, leccion: Leccion) -> int:
		return sum(self.ejercicios.get(e.id, 0) for e in leccion.ejercicios if e.da_estrellas)

	def primer_pendiente(self, leccion: Leccion) -> int:
		"""Índice del primer ejercicio sin superar; 0 si la lección ya está completa (se repite)."""
		for indice, ejercicio in enumerate(leccion.ejercicios):
			if not self.superado(ejercicio.id):
				return indice
		return 0

	# Práctica.

	def nivel_practica(self, id_leccion: str) -> int:
		return self.practica.get(id_leccion, {}).get("nivel", 1)

	def mejor_practica(self, id_leccion: str) -> int | None:
		datos = self.practica.get(id_leccion)
		return datos["mejor"] if datos else None

	def registrar_practica(self, id_leccion: str, nivel_siguiente: int, estrellas: int) -> None:
		anterior = self.practica.get(id_leccion, {})
		self.practica[id_leccion] = {
			"nivel": nivel_siguiente,
			"mejor": max(estrellas, anterior.get("mejor", 0)),
		}
