# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Dónde se guardan las partidas: la carpeta de Documentos y el guardado automático."""

import os

import globalVars
from logHandler import log

# Identificador de Windows de la carpeta Documentos (FOLDERID_Documents).
_FOLDERID_DOCUMENTOS = "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"
NOMBRE_CARPETA = "MiAjedrezAccesible"


def carpeta_partidas() -> str:
	"""Documentos\\MiAjedrezAccesible (se crea si no existe)."""
	try:
		import shlobj

		documentos = shlobj.SHGetKnownFolderPath(_FOLDERID_DOCUMENTOS)
	except Exception:
		log.debugWarning("No se encontró la carpeta Documentos", exc_info=True)
		documentos = os.path.join(os.path.expanduser("~"), "Documents")
	carpeta = os.path.join(documentos, NOMBRE_CARPETA)
	try:
		os.makedirs(carpeta, exist_ok=True)
	except OSError:
		log.debugWarning("No se pudo crear la carpeta de partidas", exc_info=True)
		return documentos
	return carpeta


def ruta_guardado_automatico() -> str:
	return os.path.join(globalVars.appArgs.configPath, "miAjedrezAccesible", "partida_en_curso.pgn")


def carpeta_configuracion() -> str:
	return os.path.join(globalVars.appArgs.configPath, "miAjedrezAccesible")


def ruta_estadisticas() -> str:
	return os.path.join(carpeta_configuracion(), "partidas.json")


def rutas_de_progreso() -> list[str]:
	"""Todo lo que borra «Borrar mi progreso y estadísticas»: curso, Retos y partidas."""
	return [
		os.path.join(carpeta_configuracion(), nombre)
		for nombre in ("progreso.json", "retos.json", "partidas.json")
	]


def leer(ruta: str) -> str:
	"""Lee un PGN en UTF-8 o, si no lo es, en la codificación de Windows más habitual."""
	with open(ruta, "rb") as archivo:
		datos = archivo.read()
	try:
		return datos.decode("utf-8-sig")
	except UnicodeDecodeError:
		return datos.decode("cp1252", errors="replace")


def escribir(ruta: str, texto: str) -> None:
	"""Escribe primero en un archivo temporal, para no dejar nunca un archivo a medias."""
	os.makedirs(os.path.dirname(ruta), exist_ok=True)
	temporal = ruta + ".tmp"
	with open(temporal, "w", encoding="utf-8", newline="\n") as archivo:
		archivo.write(texto)
	os.replace(temporal, ruta)


def borrar(ruta: str) -> None:
	try:
		os.remove(ruta)
	except FileNotFoundError:
		pass
	except OSError:
		log.debugWarning("No se pudo borrar %s", ruta, exc_info=True)
