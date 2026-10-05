# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Genera los sonidos del complemento como archivos WAV, sin material de terceros.

Cada sonido es una secuencia de notas con un timbre suave (fundamental más un armónico)
y una envolvente de ataque corto y caída exponencial, para que no resulte estridente.

Uso:
	uv run python herramientas/generar_sonidos.py
"""

import math
import os
import struct
import wave

FRECUENCIA_MUESTREO = 44100
VOLUMEN = 0.35
CARPETA = os.path.join(
	os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
	"addon",
	"globalPlugins",
	"miAjedrezAccesible",
	"sonidos",
)

# Frecuencias de las notas (en hercios).
DO5, MI5, SOL5, LA5, DO6, MI6, SOL6 = 523.25, 659.25, 783.99, 880.0, 1046.5, 1318.5, 1568.0

# Cada sonido: lista de (frecuencia, inicio en segundos, duración en segundos).
SONIDOS = {
	# Una manzana en la casilla: un toque breve y agudo.
	"manzana_cerca": [(SOL6, 0.0, 0.09)],
	# Manzana recogida: dos notas ascendentes.
	"manzana": [(MI6, 0.0, 0.12), (SOL6, 0.08, 0.2)],
	# Ejercicio superado: arpegio ascendente.
	"exito": [(DO5, 0.0, 0.25), (MI5, 0.1, 0.25), (SOL5, 0.2, 0.25), (DO6, 0.3, 0.5)],
	# Lección completada: melodía corta de celebración.
	"leccion": [
		(DO5, 0.0, 0.2),
		(MI5, 0.15, 0.2),
		(SOL5, 0.3, 0.2),
		(DO6, 0.45, 0.35),
		(SOL5, 0.75, 0.15),
		(DO6, 0.9, 0.8),
		(MI6, 0.9, 0.8),
	],
}


def muestras(notas: list[tuple[float, float, float]]) -> list[float]:
	duracion_total = max(inicio + duracion for _f, inicio, duracion in notas) + 0.05
	total = int(duracion_total * FRECUENCIA_MUESTREO)
	salida = [0.0] * total
	for frecuencia, inicio, duracion in notas:
		primera = int(inicio * FRECUENCIA_MUESTREO)
		cantidad = int(duracion * FRECUENCIA_MUESTREO)
		ataque = int(0.008 * FRECUENCIA_MUESTREO)
		for i in range(cantidad):
			t = i / FRECUENCIA_MUESTREO
			envolvente = (i / ataque if i < ataque else 1.0) * math.exp(-4.0 * t / duracion)
			onda = math.sin(2 * math.pi * frecuencia * t) + 0.3 * math.sin(4 * math.pi * frecuencia * t)
			salida[primera + i] += envolvente * onda
	pico = max(1e-9, max(abs(m) for m in salida))
	return [m / pico * VOLUMEN for m in salida]


def escribir(ruta: str, datos: list[float]) -> None:
	with wave.open(ruta, "wb") as archivo:
		archivo.setnchannels(1)
		archivo.setsampwidth(2)
		archivo.setframerate(FRECUENCIA_MUESTREO)
		archivo.writeframes(b"".join(struct.pack("<h", int(m * 32767)) for m in datos))


def main() -> None:
	os.makedirs(CARPETA, exist_ok=True)
	for nombre, notas in SONIDOS.items():
		ruta = os.path.join(CARPETA, f"{nombre}.wav")
		escribir(ruta, muestras(notas))
		print(f"{ruta} ({os.path.getsize(ruta) // 1024} KB)")


if __name__ == "__main__":
	main()
