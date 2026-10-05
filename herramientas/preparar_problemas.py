# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Prepara la selección de problemas de Retos a partir de la base de datos de Lichess (CC0).

Descarga `lichess_db_puzzle.csv.zst` (unos 300 MB) si no está, la recorre sin cargarla en
memoria y elige unos 5.000 problemas:
- bien valorados y muy jugados (popularidad, intentos y dificultad bien medida);
- cortos: como máximo 3 jugadas de quien resuelve;
- de los temas que usa MiAjedrezAccesible;
- con muchos problemas fáciles: la mitad por debajo de 1200.

El resultado, `problemas/problemas.jsonl.gz`, sí se guarda en git (ocupa poco).

Uso:
	uv run --with zstandard python herramientas/preparar_problemas.py [--csv RUTA]
"""

import argparse
import csv
import gzip
import io
import json
import os
import random
import sys
import urllib.request

URL = "https://database.lichess.org/lichess_db_puzzle.csv.zst"
DESCARGA = os.path.join("D:\\", "Claude", "herramientas", "lichess_db_puzzle.csv.zst")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "addon", "globalPlugins", "miAjedrezAccesible", "problemas", "problemas.jsonl.gz")

# Temas de Lichess que se usan, con el peso de cada uno en la selección.
TEMAS = {
	"mateIn1": 0.18,
	"mateIn2": 0.14,
	"backRankMate": 0.08,
	"hangingPiece": 0.14,
	"fork": 0.14,
	"promotion": 0.07,
	"enPassant": 0.03,
	"pin": 0.11,
	"discoveredAttack": 0.11,
}
TOTAL = 5000
SEMILLA = 2026
# Franjas de dificultad (de 100 en 100) y su peso: más problemas fáciles.
FRANJAS = list(range(400, 1900, 100))


def peso_franja(inicio: int) -> float:
	return 2.0 if inicio < 1200 else 1.0


def apto(fila: dict) -> bool:
	try:
		popularidad = int(fila["Popularity"])
		intentos = int(fila["NbPlays"])
		desviacion = int(fila["RatingDeviation"])
		dificultad = int(fila["Rating"])
	except (KeyError, ValueError):
		return False
	jugadas = fila["Moves"].split()
	# La primera jugada es del rival; luego, como máximo 3 de quien resuelve (6 en total).
	return (
		popularidad >= 85
		and intentos >= 1000
		and desviacion <= 85
		and 400 <= dificultad < 1900
		and 2 <= len(jugadas) <= 6
	)


def elegir(depositos: dict[tuple[str, int], list[dict]], factor: float) -> dict[str, dict]:
	azar = random.Random(SEMILLA)
	elegidos: dict[str, dict] = {}
	peso_total_franjas = sum(peso_franja(f) for f in FRANJAS)
	for tema, peso in TEMAS.items():
		cupo_tema = TOTAL * peso * factor
		for franja in FRANJAS:
			cupo = round(cupo_tema * peso_franja(franja) / peso_total_franjas)
			candidatos = [p for p in depositos.get((tema, franja), []) if p["id"] not in elegidos]
			azar.shuffle(candidatos)
			for problema in candidatos[:cupo]:
				elegidos[problema["id"]] = problema
	return elegidos


def leer_filas(ruta: str):
	import zstandard

	with open(ruta, "rb") as archivo:
		lector = zstandard.ZstdDecompressor().stream_reader(archivo)
		texto = io.TextIOWrapper(lector, encoding="utf-8", newline="")
		yield from csv.DictReader(texto)


def main() -> int:
	argumentos = argparse.ArgumentParser(description=__doc__)
	argumentos.add_argument("--csv", default=DESCARGA)
	opciones = argumentos.parse_args()
	if not os.path.isfile(opciones.csv):
		os.makedirs(os.path.dirname(opciones.csv), exist_ok=True)
		print(f"Descargando {URL}")
		urllib.request.urlretrieve(URL, opciones.csv)

	azar = random.Random(SEMILLA)
	# Muestreo por depósito para cada (tema, franja): no hace falta tener todo en memoria.
	capacidad = 400
	depositos: dict[tuple[str, int], list[dict]] = {}
	vistos: dict[tuple[str, int], int] = {}
	leidas = 0
	for fila in leer_filas(opciones.csv):
		leidas += 1
		if leidas % 500_000 == 0:
			print(f"  {leidas:,} filas leídas", flush=True)
		if not apto(fila):
			continue
		temas = [t for t in fila["Themes"].split() if t in TEMAS]
		if not temas:
			continue
		franja = (int(fila["Rating"]) // 100) * 100
		problema = {
			"id": fila["PuzzleId"],
			"fen": fila["FEN"],
			"jugadas": fila["Moves"],
			"dificultad": int(fila["Rating"]),
			"temas": temas,
		}
		for tema in temas:
			clave = (tema, franja)
			vistos[clave] = vistos.get(clave, 0) + 1
			deposito = depositos.setdefault(clave, [])
			if len(deposito) < capacidad:
				deposito.append(problema)
			else:
				posicion = azar.randrange(vistos[clave])
				if posicion < capacidad:
					deposito[posicion] = problema
	print(f"{leidas:,} filas leídas en total")

	# Las franjas fáciles tienen pocos problemas y los temas se solapan: se agrandan los cupos
	# hasta llegar al total, y luego se recorta al azar.
	factor = 1.0
	while True:
		elegidos = elegir(depositos, factor)
		if len(elegidos) >= TOTAL:
			break
		factor *= 1.05
	problemas = random.Random(SEMILLA).sample(sorted(elegidos.values(), key=lambda p: p["id"]), TOTAL)
	problemas.sort(key=lambda p: (p["dificultad"], p["id"]))
	os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
	with gzip.open(SALIDA, "wt", encoding="utf-8") as salida:
		for problema in problemas:
			salida.write(json.dumps(problema, ensure_ascii=False, separators=(",", ":")) + "\n")
	por_tema = {t: sum(1 for p in problemas if t in p["temas"]) for t in TEMAS}
	faciles = sum(1 for p in problemas if p["dificultad"] < 1200)
	print(f"{len(problemas)} problemas ({faciles} por debajo de 1200) en {SALIDA}")
	print(f"Tamaño: {os.path.getsize(SALIDA) // 1024} KB. Por tema: {por_tema}")
	return 0


if __name__ == "__main__":
	sys.exit(main())
