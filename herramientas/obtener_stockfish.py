# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Descarga Stockfish del repositorio oficial y lo coloca dentro del complemento.

El ejecutable pesa más de 100 MB, el límite de GitHub para un archivo, así que no se guarda en git:
este script lo descarga, comprueba su huella SHA-256 y lo copia en `bin/stockfish/`.

Uso:
	uv run python herramientas/obtener_stockfish.py            (descarga)
	uv run python herramientas/obtener_stockfish.py --zip RUTA  (usa un zip ya descargado)
"""

import argparse
import hashlib
import os
import sys
import tempfile
import urllib.request
import zipfile

VERSION = "sf_19"
URL = (
	"https://github.com/official-stockfish/Stockfish/releases/download/"
	f"{VERSION}/stockfish-windows-x86-64-universal.zip"
)
SHA256 = "3c8bf1f9ea66a09350a40df4f632288285ac206d99f33ab5842c408fc30b48a7"
# Archivos que se copian del zip: el ejecutable, la licencia y los autores.
ARCHIVOS = {
	"stockfish/stockfish-windows-x86-64-universal.exe": "stockfish.exe",
	"stockfish/Copying.txt": "Copying.txt",
	"stockfish/AUTHORS": "AUTHORS",
}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "addon", "globalPlugins", "miAjedrezAccesible", "bin", "stockfish")


def huella(ruta: str) -> str:
	sha = hashlib.sha256()
	with open(ruta, "rb") as archivo:
		for bloque in iter(lambda: archivo.read(1 << 20), b""):
			sha.update(bloque)
	return sha.hexdigest()


def main() -> int:
	argumentos = argparse.ArgumentParser(description=__doc__)
	argumentos.add_argument("--zip", help="zip de Stockfish ya descargado")
	opciones = argumentos.parse_args()

	destino_exe = os.path.join(DESTINO, "stockfish.exe")
	marca = os.path.join(DESTINO, "version.txt")
	if os.path.isfile(destino_exe) and os.path.isfile(marca):
		with open(marca, encoding="utf-8") as archivo:
			if archivo.read().strip() == VERSION:
				print(f"Stockfish {VERSION} ya está en {DESTINO}")
				return 0

	ruta_zip = opciones.zip
	if ruta_zip is None:
		ruta_zip = os.path.join(tempfile.gettempdir(), f"stockfish-{VERSION}.zip")
		print(f"Descargando {URL}")
		urllib.request.urlretrieve(URL, ruta_zip)
	calculada = huella(ruta_zip)
	if calculada != SHA256:
		print(f"La huella no coincide.\n  esperada: {SHA256}\n  obtenida: {calculada}", file=sys.stderr)
		return 1

	os.makedirs(DESTINO, exist_ok=True)
	with zipfile.ZipFile(ruta_zip) as comprimido:
		for origen, nombre in ARCHIVOS.items():
			with comprimido.open(origen) as entrada, open(os.path.join(DESTINO, nombre), "wb") as salida:
				while bloque := entrada.read(1 << 20):
					salida.write(bloque)
	with open(marca, "w", encoding="utf-8") as archivo:
		archivo.write(VERSION + "\n")
	print(f"Stockfish {VERSION} copiado en {DESTINO}")
	return 0


if __name__ == "__main__":
	sys.exit(main())
