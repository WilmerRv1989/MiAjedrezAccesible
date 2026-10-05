# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Lector mínimo de archivos .po para las pruebas (sin compilar a .mo)."""

import ast
from dataclasses import dataclass, field


@dataclass
class Entrada:
	msgid: str = ""
	msgid_plural: str | None = None
	msgstr: dict[int, str] = field(default_factory=dict)
	fuzzy: bool = False


def leer(ruta: str) -> list[Entrada]:
	entradas: list[Entrada] = []
	actual = Entrada()
	campo: tuple[str, int] | None = None

	def cerrar() -> None:
		nonlocal actual, campo
		if actual.msgid or actual.msgstr:
			entradas.append(actual)
		actual = Entrada()
		campo = None

	with open(ruta, encoding="utf-8") as archivo:
		for linea in archivo:
			linea = linea.strip()
			if not linea:
				cerrar()
				continue
			if linea.startswith("#,") and "fuzzy" in linea:
				actual.fuzzy = True
				continue
			if linea.startswith("#"):
				continue
			if linea.startswith("msgid_plural "):
				campo = ("plural", 0)
				actual.msgid_plural = ast.literal_eval(linea[len("msgid_plural ") :])
			elif linea.startswith("msgid "):
				if actual.msgstr:
					cerrar()
				campo = ("msgid", 0)
				actual.msgid = ast.literal_eval(linea[len("msgid ") :])
			elif linea.startswith("msgstr["):
				indice = int(linea[len("msgstr[") : linea.index("]")])
				campo = ("msgstr", indice)
				actual.msgstr[indice] = ast.literal_eval(linea[linea.index("]") + 2 :])
			elif linea.startswith("msgstr "):
				campo = ("msgstr", 0)
				actual.msgstr[0] = ast.literal_eval(linea[len("msgstr ") :])
			elif linea.startswith('"') and campo is not None:
				texto = ast.literal_eval(linea)
				nombre, indice = campo
				if nombre == "msgid":
					actual.msgid += texto
				elif nombre == "plural":
					actual.msgid_plural = (actual.msgid_plural or "") + texto
				else:
					actual.msgstr[indice] += texto
	cerrar()
	return entradas


def traducciones(ruta: str):
	"""Devuelve funciones gettext y ngettext basadas en un archivo .po (español: plural si n != 1)."""
	simples: dict[str, str] = {}
	plurales: dict[str, tuple[str, str]] = {}
	for entrada in leer(ruta):
		if not entrada.msgid or entrada.fuzzy:
			continue
		if entrada.msgid_plural is not None:
			if entrada.msgstr.get(0) and entrada.msgstr.get(1):
				plurales[entrada.msgid] = (entrada.msgstr[0], entrada.msgstr[1])
		elif entrada.msgstr.get(0):
			simples[entrada.msgid] = entrada.msgstr[0]

	def gettext(texto: str) -> str:
		return simples.get(texto, texto)

	def ngettext(singular: str, plural: str, cantidad: int) -> str:
		formas = plurales.get(singular)
		if formas is None:
			return singular if cantidad == 1 else plural
		return formas[0] if cantidad == 1 else formas[1]

	return gettext, ngettext
