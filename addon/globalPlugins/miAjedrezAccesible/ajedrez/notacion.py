# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Jugadas escritas por la persona y notación algebraica.

Con NVDA en español se aceptan:
- Notación algebraica en español: Cf3, Axf7, Dd1, Tfe1, O-O, e8=D.
- Las letras inglesas que no chocan con las españolas: K, Q, B y N (Nf3, Bxf7).
  La R es siempre «rey», como en español.
Con NVDA en otro idioma, la notación inglesa: Nf3, Bxf7, Qd1, Rfe1 (la R es la torre).
En los dos casos:
- Coordenadas: g1f3, g1-f3, e7e8d (la última letra es la pieza de coronación).
- Enroques con letra o con cero: O-O, 0-0, O-O-O, 0-0-0.
"""

import re

import chess

from .idioma import _, letras_espanolas

# Letras de pieza en español y su equivalente inglés (el que entiende python-chess).
_ESPANOL_A_INGLES = {"R": "K", "D": "Q", "T": "R", "A": "B", "C": "N"}
_LETRAS_INGLESAS_ACEPTADAS = set("KQBN")
_LETRAS_INGLESAS = set("KQRBN")
_INGLES_A_ESPANOL = str.maketrans("KQRBN", "RDTAC")

_COORDENADAS = re.compile(r"^([a-h][1-8])[-x:]?([a-h][1-8])=?([dtacqrbn])?$")
_CORONACION_FINAL = re.compile(r"([18])=?([DTACQRBN])$")
_PIEZA_CORONACION = {
	"d": chess.QUEEN,
	"q": chess.QUEEN,
	"t": chess.ROOK,
	"r": chess.ROOK,
	"a": chess.BISHOP,
	"b": chess.BISHOP,
	"c": chess.KNIGHT,
	"n": chess.KNIGHT,
}


class ErrorJugada(ValueError):
	"""La jugada escrita no se puede hacer. El mensaje está listo para decirse."""


def san_en_espanol(tablero: chess.Board, jugada: chess.Move) -> str:
	"""Notación algebraica de una jugada con las letras del idioma: «Cf3», «exd8=D» (en inglés, «Nf3»)."""
	san = tablero.san(jugada)
	return san.translate(_INGLES_A_ESPANOL) if letras_espanolas() else san


def _mensaje_no_entendida() -> str:
	# Translators: error when the typed move cannot be understood.
	return _("I do not understand that move. Examples: Nf3, exd5, O-O, e8=Q or g1f3.")


def _mensaje_ilegal() -> str:
	# Translators: error when a move is not allowed in the current position.
	return _("That move is not possible in this position.")


def _mensaje_ambigua() -> str:
	# Translators: error when a typed move could be made by more than one piece.
	return _(
		"That move is ambiguous: more than one piece can go there. "
		"Add the origin file or rank, for example Nbd2.",
	)


def _a_san_ingles(texto: str) -> str:
	"""Pasa las letras de pieza españolas a inglesas, sin tocar columnas ni enroques."""
	primera = texto[0]
	if not letras_espanolas():
		# Notación inglesa: se deja tal cual; solo se comprueba que la letra sea de una pieza.
		if primera.isupper() and primera not in _LETRAS_INGLESAS and primera != "O":
			raise ErrorJugada(_mensaje_no_entendida())
		return texto
	if primera in _ESPANOL_A_INGLES:
		texto = _ESPANOL_A_INGLES[primera] + texto[1:]
	elif primera.isupper() and primera not in _LETRAS_INGLESAS_ACEPTADAS and primera != "O":
		raise ErrorJugada(_mensaje_no_entendida())

	def cambiar_coronacion(coincidencia: re.Match[str]) -> str:
		letra = coincidencia.group(2)
		# En la coronación, R solo puede ser torre (no se corona en rey).
		inglesa = {"D": "Q", "T": "R", "A": "B", "C": "N"}.get(letra, letra)
		return f"{coincidencia.group(1)}={inglesa}"

	return _CORONACION_FINAL.sub(cambiar_coronacion, texto)


def _sin_coronacion(jugada: chess.Move) -> chess.Move:
	return chess.Move(jugada.from_square, jugada.to_square)


def interpretar(tablero: chess.Board, texto: str) -> chess.Move:
	"""Convierte lo que escribió la persona en una jugada legal.

	Si es un peón que llega a la última fila y no se indicó la pieza,
	devuelve la jugada sin coronación: quien llama debe preguntar la pieza.
	Lanza ErrorJugada con un mensaje listo para decirse si no se puede.
	"""
	limpio = texto.strip().replace(" ", "").rstrip("+#!?")
	if not limpio:
		# Translators: error when the move field is empty.
		raise ErrorJugada(_("Type a move first."))

	enroque = limpio.upper().replace("0", "O")
	if enroque in ("O-O", "OO"):
		return _desde_san(tablero, "O-O")
	if enroque in ("O-O-O", "OOO"):
		return _desde_san(tablero, "O-O-O")

	coordenadas = _COORDENADAS.match(limpio.lower())
	if coordenadas:
		origen = chess.parse_square(coordenadas.group(1))
		destino = chess.parse_square(coordenadas.group(2))
		letra = coordenadas.group(3)
		coronacion = _PIEZA_CORONACION[letra] if letra else None
		jugada = chess.Move(origen, destino, promotion=coronacion)
		if tablero.is_legal(jugada):
			return jugada
		if coronacion is None and tablero.is_legal(chess.Move(origen, destino, promotion=chess.QUEEN)):
			return jugada
		raise ErrorJugada(_mensaje_ilegal())

	# Primero se prueba tal cual; si la primera letra está en minúscula y es una letra
	# de pieza, se prueba también en mayúscula («cf3» → «Cf3»).
	# Así «axb5» sigue siendo una captura de peón y «cf3» funciona como caballo.
	candidatos = [limpio]
	if limpio[0] in ("rdtackqbn" if letras_espanolas() else "kqrbn"):
		candidatos.append(limpio[0].upper() + limpio[1:])
	error: ErrorJugada | None = None
	for candidato in candidatos:
		try:
			return _desde_san(tablero, candidato)
		except ErrorJugada as e:
			# Se guarda el error más informativo: ambigua > ilegal > no entendida.
			if error is None or _prioridad(e) > _prioridad(error):
				error = e
	assert error is not None
	raise error


def _prioridad(error: ErrorJugada) -> int:
	mensaje = str(error)
	if mensaje == _mensaje_ambigua():
		return 3
	if mensaje == _mensaje_ilegal():
		return 2
	return 1


def _desde_san(tablero: chess.Board, texto: str) -> chess.Move:
	san = _a_san_ingles(texto)
	try:
		return tablero.parse_san(san)
	except chess.AmbiguousMoveError:
		raise ErrorJugada(_mensaje_ambigua()) from None
	except chess.IllegalMoveError:
		# Un peón que llega a la última fila sin indicar la pieza: se pregunta después.
		if "=" not in san:
			try:
				return _sin_coronacion(tablero.parse_san(san + "=Q"))
			except ValueError:
				pass
		raise ErrorJugada(_mensaje_ilegal()) from None
	except chess.InvalidMoveError:
		raise ErrorJugada(_mensaje_no_entendida()) from None
