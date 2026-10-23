# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Funciones de traducción para la lógica del ajedrez.

Dentro de NVDA, el complemento llama a `configurar` con las funciones de gettext del complemento.
En las pruebas se puede configurar con una traducción cargada del archivo .po,
o dejar el texto original en inglés.
"""

from collections.abc import Callable


def _sin_traduccion(texto: str) -> str:
	return texto


def _plural_sin_traduccion(singular: str, plural: str, cantidad: int) -> str:
	return singular if cantidad == 1 else plural


_gettext: Callable[[str], str] = _sin_traduccion
_ngettext: Callable[[str, str, int], str] = _plural_sin_traduccion
# Letras de pieza: las españolas (R rey, D dama, T torre, A alfil, C caballo) con NVDA en español,
# las inglesas (K, Q, R, B, N) en cualquier otro idioma.
_letras_espanolas = True


def configurar(gettext: Callable[[str], str], ngettext_: Callable[[str, str, int], str]) -> None:
	global _gettext, _ngettext
	_gettext = gettext
	_ngettext = ngettext_


def es_espanol(codigo_idioma: str) -> bool:
	"""Si un código de idioma de NVDA («es», «es_CO», «en»…) es español."""
	return codigo_idioma.split("_")[0].lower() == "es"


def configurar_letras(espanolas: bool) -> None:
	global _letras_espanolas
	_letras_espanolas = espanolas


def letras_espanolas() -> bool:
	return _letras_espanolas


def _(texto: str) -> str:
	return _gettext(texto)


def ngettext(singular: str, plural: str, cantidad: int) -> str:
	return _ngettext(singular, plural, cantidad)
