# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Preferencias del complemento, guardadas en la configuración de NVDA (sección miAjedrezAccesible)."""

import config

from ..ajedrez import anunciador
from ..ajedrez.anunciador import FormaJugada
from ..ajedrez.configuracion import NIVEL_POR_DEFECTO, ConfiguracionPartida

SECCION = "miAjedrezAccesible"
ESPECIFICACION = {
	# Lo último elegido en el diálogo de nueva partida.
	"modo": 'string(default="computadora")',
	"color": 'string(default="blancas")',
	"nivel": f"integer(default={NIVEL_POR_DEFECTO}, min=1, max=10)",
	"reloj": 'string(default="sin")',
	# Panel de configuración.
	"anuncio_jugadas": 'option("palabras", "notacion", "ambas", default="palabras")',
	"casilla_primero": "boolean(default=False)",
	"sonidos": "boolean(default=True)",
	"avisos_reloj": "boolean(default=True)",
}


def registrar() -> None:
	config.conf.spec[SECCION] = ESPECIFICACION
	config.post_configProfileSwitch.register(aplicar)
	aplicar()


def quitar() -> None:
	config.post_configProfileSwitch.unregister(aplicar)


def seccion():
	return config.conf[SECCION]


def aplicar() -> None:
	"""Pasa a la lógica del ajedrez las preferencias de anuncio."""
	datos = seccion()
	forma = datos["anuncio_jugadas"]
	anunciador.configurar(
		FormaJugada(forma) if forma in FormaJugada._value2member_map_ else FormaJugada.PALABRAS,
		bool(datos["casilla_primero"]),
	)


def sonidos_activados() -> bool:
	return bool(seccion()["sonidos"])


def avisos_reloj() -> bool:
	return bool(seccion()["avisos_reloj"])


def configuracion_guardada() -> ConfiguracionPartida:
	datos = seccion()
	return ConfiguracionPartida.desde_textos(datos["modo"], datos["color"], datos["nivel"], datos["reloj"])


def guardar_configuracion(configuracion: ConfiguracionPartida) -> None:
	datos = seccion()
	datos["modo"] = configuracion.modo.value
	datos["color"] = configuracion.color.value
	datos["nivel"] = configuracion.nivel
	datos["reloj"] = configuracion.reloj
