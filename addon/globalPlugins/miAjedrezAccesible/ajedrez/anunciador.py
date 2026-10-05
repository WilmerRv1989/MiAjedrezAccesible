# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Frases que se dicen durante la partida: casillas, jugadas, ataques y finales.

Las piezas se nombran con su color en una sola cadena traducible («white knight»),
porque en español el adjetivo concuerda en género: «caballo blanco», pero «dama blanca».
"""

from dataclasses import dataclass
from enum import StrEnum

import chess

from .idioma import _, ngettext

# Orden en que se enumeran las piezas: de la más importante a la menos.
ORDEN_PIEZAS = (chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN)


class FormaJugada(StrEnum):
	"""Cómo se anuncia cada jugada al hacerla."""

	PALABRAS = "palabras"
	NOTACION = "notacion"
	AMBAS = "ambas"


@dataclass
class Preferencias:
	forma_jugada: FormaJugada = FormaJugada.PALABRAS
	# Al recorrer el tablero: «g1, caballo blanco» en lugar de «Caballo blanco, g1».
	casilla_primero: bool = False


# Las cambia el panel de configuración del complemento; las pruebas usan los valores por defecto.
PREFERENCIAS = Preferencias()


def configurar(forma_jugada: FormaJugada, casilla_primero: bool) -> None:
	PREFERENCIAS.forma_jugada = forma_jugada
	PREFERENCIAS.casilla_primero = casilla_primero


def mayuscula_inicial(texto: str) -> str:
	return texto[:1].upper() + texto[1:]


def unir_lista(elementos: list[str]) -> str:
	"""Une una lista como en el habla: «a1, b1 y c1»."""
	if len(elementos) <= 1:
		return "".join(elementos)
	# Translators: joins the last two items of a spoken list, for example "a1, b1 and c1".
	return ", ".join(elementos[:-1]) + _(" and ") + elementos[-1]


def nombre_pieza(pieza: chess.Piece) -> str:
	"""Nombre de la pieza con su color, en minúsculas: «caballo blanco»."""
	nombres = {
		# Translators: a chess piece, lowercase.
		(chess.KING, chess.WHITE): _("white king"),
		# Translators: a chess piece, lowercase.
		(chess.QUEEN, chess.WHITE): _("white queen"),
		# Translators: a chess piece, lowercase.
		(chess.ROOK, chess.WHITE): _("white rook"),
		# Translators: a chess piece, lowercase.
		(chess.BISHOP, chess.WHITE): _("white bishop"),
		# Translators: a chess piece, lowercase.
		(chess.KNIGHT, chess.WHITE): _("white knight"),
		# Translators: a chess piece, lowercase.
		(chess.PAWN, chess.WHITE): _("white pawn"),
		# Translators: a chess piece, lowercase.
		(chess.KING, chess.BLACK): _("black king"),
		# Translators: a chess piece, lowercase.
		(chess.QUEEN, chess.BLACK): _("black queen"),
		# Translators: a chess piece, lowercase.
		(chess.ROOK, chess.BLACK): _("black rook"),
		# Translators: a chess piece, lowercase.
		(chess.BISHOP, chess.BLACK): _("black bishop"),
		# Translators: a chess piece, lowercase.
		(chess.KNIGHT, chess.BLACK): _("black knight"),
		# Translators: a chess piece, lowercase.
		(chess.PAWN, chess.BLACK): _("black pawn"),
	}
	return nombres[(pieza.piece_type, pieza.color)]


def nombre_pieza_con_articulo(pieza: chess.Piece) -> str:
	"""Nombre de la pieza con artículo determinado, en minúsculas: «la torre blanca»."""
	nombres = {
		# Translators: a chess piece with its definite article, lowercase.
		(chess.KING, chess.WHITE): _("the white king"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.QUEEN, chess.WHITE): _("the white queen"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.ROOK, chess.WHITE): _("the white rook"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.BISHOP, chess.WHITE): _("the white bishop"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.KNIGHT, chess.WHITE): _("the white knight"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.PAWN, chess.WHITE): _("the white pawn"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.KING, chess.BLACK): _("the black king"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.QUEEN, chess.BLACK): _("the black queen"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.ROOK, chess.BLACK): _("the black rook"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.BISHOP, chess.BLACK): _("the black bishop"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.KNIGHT, chess.BLACK): _("the black knight"),
		# Translators: a chess piece with its definite article, lowercase.
		(chess.PAWN, chess.BLACK): _("the black pawn"),
	}
	return nombres[(pieza.piece_type, pieza.color)]


def nombre_tipo(tipo: chess.PieceType, cantidad: int = 1) -> str:
	"""Nombre del tipo de pieza sin color, en minúsculas: «caballo», «caballos»."""
	if tipo == chess.KING:
		# Translators: a chess piece type, lowercase, singular and plural.
		return ngettext("king", "kings", cantidad)
	if tipo == chess.QUEEN:
		# Translators: a chess piece type, lowercase, singular and plural.
		return ngettext("queen", "queens", cantidad)
	if tipo == chess.ROOK:
		# Translators: a chess piece type, lowercase, singular and plural.
		return ngettext("rook", "rooks", cantidad)
	if tipo == chess.BISHOP:
		# Translators: a chess piece type, lowercase, singular and plural.
		return ngettext("bishop", "bishops", cantidad)
	if tipo == chess.KNIGHT:
		# Translators: a chess piece type, lowercase, singular and plural.
		return ngettext("knight", "knights", cantidad)
	# Translators: a chess piece type, lowercase, singular and plural.
	return ngettext("pawn", "pawns", cantidad)


def nombre_casilla(casilla: chess.Square) -> str:
	return chess.square_name(casilla)


def es_casilla_oscura(casilla: chess.Square) -> bool:
	# a1 es oscura: las casillas oscuras tienen columna y fila de la misma paridad.
	return (chess.square_file(casilla) + chess.square_rank(casilla)) % 2 == 0


def pieza_en_casilla(pieza: chess.Piece, casilla: chess.Square) -> str:
	# Translators: a piece and the square where it stands, for example "white knight on f3".
	return _("{piece} on {square}").format(piece=nombre_pieza(pieza), square=nombre_casilla(casilla))


def describir_casilla(tablero: chess.Board, casilla: chess.Square) -> str:
	"""Lo que se dice al llegar a una casilla: «Caballo blanco, g1» o solo «e4»."""
	pieza = tablero.piece_at(casilla)
	if pieza is None:
		return nombre_casilla(casilla)
	if PREFERENCIAS.casilla_primero:
		# Translators: spoken when the focus lands on an occupied square, with the square first,
		# for example "g1, white knight".
		return _("{square}, {piece}").format(piece=nombre_pieza(pieza), square=nombre_casilla(casilla))
	# Translators: spoken when the focus lands on an occupied square, for example "white knight, g1".
	texto = _("{piece}, {square}").format(piece=nombre_pieza(pieza), square=nombre_casilla(casilla))
	return mayuscula_inicial(texto)


def texto_jugada(descripcion: str, san: str) -> str:
	"""El anuncio de una jugada según la preferencia: «Caballo blanco de g1 a f3.», «Cf3.» o ambas.

	El jaque y el mate se dicen aparte, así que se quitan sus signos. Los enroques se dicen
	siempre con palabras, porque «O-O» se lee mal.
	"""
	forma = PREFERENCIAS.forma_jugada
	notacion = san.rstrip("+#")
	if forma is FormaJugada.PALABRAS or notacion.startswith("O-O"):
		return descripcion
	if forma is FormaJugada.NOTACION:
		return f"{notacion}."
	return f"{notacion}. {descripcion}"


def describir_detalle_casilla(tablero: chess.Board, casilla: chess.Square) -> str:
	"""Detalle completo de una casilla: coordenada, color y contenido."""
	if es_casilla_oscura(casilla):
		# Translators: color of a square of the chess board.
		color = _("dark square")
	else:
		# Translators: color of a square of the chess board.
		color = _("light square")
	pieza = tablero.piece_at(casilla)
	# Translators: content of a square with no piece.
	contenido = nombre_pieza(pieza) if pieza else _("empty")
	return ", ".join((nombre_casilla(casilla), color, contenido))


def texto_turno(color: chess.Color) -> str:
	if color == chess.WHITE:
		# Translators: announced after a move when it is white's turn.
		return _("White to move.")
	# Translators: announced after a move when it is black's turn.
	return _("Black to move.")


def texto_ganador(color: chess.Color) -> str:
	if color == chess.WHITE:
		# Translators: announced at the end of a game.
		return _("White wins.")
	# Translators: announced at the end of a game.
	return _("Black wins.")


def texto_enroque(color: chess.Color, corto: bool) -> str:
	if color == chess.WHITE:
		# Translators: announcement of a castling move.
		return _("White castles kingside.") if corto else _("White castles queenside.")
	# Translators: announcement of a castling move.
	return _("Black castles kingside.") if corto else _("Black castles queenside.")


def describir_jugada(tablero: chess.Board, jugada: chess.Move) -> str:
	"""Describe una jugada legal ANTES de hacerla en el tablero: «Caballo blanco de g1 a f3.»"""
	pieza = tablero.piece_at(jugada.from_square)
	if pieza is None:
		raise ValueError(f"No hay pieza en la casilla de origen de {jugada.uci()}")
	if tablero.is_castling(jugada):
		return texto_enroque(pieza.color, tablero.is_kingside_castling(jugada))
	datos = {
		"piece": nombre_pieza(pieza),
		"origin": nombre_casilla(jugada.from_square),
		"target": nombre_casilla(jugada.to_square),
	}
	if tablero.is_en_passant(jugada):
		# Translators: announcement of an en passant capture, for example
		# "white pawn from e5 captures en passant on d6".
		texto = _("{piece} from {origin} captures en passant on {target}").format(**datos)
	else:
		capturada = tablero.piece_at(jugada.to_square)
		if capturada is not None:
			# Translators: announcement of a capture, for example
			# "white bishop from c4 captures black pawn on f7".
			texto = _("{piece} from {origin} captures {captured} on {target}").format(
				captured=nombre_pieza(capturada),
				**datos,
			)
		else:
			# Translators: announcement of a normal move, for example "white knight from g1 to f3".
			texto = _("{piece} from {origin} to {target}").format(**datos)
	if jugada.promotion:
		# Translators: added to a move when a pawn promotes, for example
		# "white pawn from e7 to e8, promotes to queen".
		texto = _("{move}, promotes to {piece}").format(move=texto, piece=nombre_tipo(jugada.promotion))
	return mayuscula_inicial(texto) + "."


def describir_final(resultado: chess.Outcome) -> str:
	motivo = resultado.termination
	if motivo == chess.Termination.CHECKMATE and resultado.winner is not None:
		# Translators: announced when a game ends by checkmate; followed by the winner.
		return _("Checkmate.") + " " + texto_ganador(resultado.winner)
	if motivo == chess.Termination.STALEMATE:
		# Translators: announced when a game ends in a draw.
		return _("Draw by stalemate.")
	if motivo == chess.Termination.INSUFFICIENT_MATERIAL:
		# Translators: announced when a game ends in a draw.
		return _("Draw by insufficient material.")
	if motivo in (chess.Termination.FIFTY_MOVES, chess.Termination.SEVENTYFIVE_MOVES):
		# Translators: announced when a game ends in a draw.
		return _("Draw by the fifty-move rule.")
	if motivo in (chess.Termination.THREEFOLD_REPETITION, chess.Termination.FIVEFOLD_REPETITION):
		# Translators: announced when a game ends in a draw.
		return _("Draw by threefold repetition.")
	if resultado.winner is not None:
		# Translators: announced when a game ends for another reason; followed by the winner.
		return _("Game over.") + " " + texto_ganador(resultado.winner)
	# Translators: announced when a game ends in a draw for another reason.
	return _("Game over. Draw.")


def describir_ataques(tablero: chess.Board, casilla: chess.Square) -> str:
	"""Qué piezas atacan y defienden una casilla ocupada, o qué piezas controlan una vacía."""

	def listar(casillas: chess.SquareSet) -> str:
		textos: list[str] = []
		for origen in casillas:
			pieza = tablero.piece_at(origen)
			if pieza is not None:
				textos.append(pieza_en_casilla(pieza, origen))
		return unir_lista(textos)

	pieza = tablero.piece_at(casilla)
	partes = [describir_casilla(tablero, casilla) + "."]
	if pieza is None:
		controlan = tablero.attackers(chess.WHITE, casilla) | tablero.attackers(chess.BLACK, casilla)
		if controlan:
			# Translators: pieces attacking an empty square (they could capture there), followed by a list.
			partes.append(_("Controlled by: {list}.").format(list=listar(controlan)))
		else:
			# Translators: no piece attacks an empty square.
			partes.append(_("No piece controls this square."))
		return " ".join(partes)
	atacantes = tablero.attackers(not pieza.color, casilla)
	defensores = tablero.attackers(pieza.color, casilla)
	if atacantes:
		# Translators: opponent pieces attacking the piece on a square, followed by a list.
		partes.append(_("Attackers: {list}.").format(list=listar(atacantes)))
	else:
		# Translators: no opponent piece attacks the piece on a square.
		partes.append(_("No attackers."))
	if defensores:
		# Translators: own pieces defending the piece on a square, followed by a list.
		partes.append(_("Defenders: {list}.").format(list=listar(defensores)))
	else:
		# Translators: no own piece defends the piece on a square.
		partes.append(_("No defenders."))
	return " ".join(partes)


def describir_piezas(tablero: chess.Board, color: chess.Color) -> str:
	"""Todas las piezas de un bando: «Piezas blancas: rey en e1. Torres en a1 y h1. …»"""
	if color == chess.WHITE:
		# Translators: header of the list of all white pieces on the board.
		partes = [_("White pieces:")]
	else:
		# Translators: header of the list of all black pieces on the board.
		partes = [_("Black pieces:")]
	for tipo in ORDEN_PIEZAS:
		casillas = [nombre_casilla(c) for c in tablero.pieces(tipo, color)]
		if not casillas:
			continue
		# Translators: pieces of one type and their squares, for example "rooks on a1 and h1".
		texto = _("{pieces} on {squares}").format(
			pieces=nombre_tipo(tipo, len(casillas)),
			squares=unir_lista(casillas),
		)
		partes.append(mayuscula_inicial(texto) + ".")
	return " ".join(partes)
