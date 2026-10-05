# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Objetivos de los ejercicios de una jugada: dar jaque, salir del jaque, capturar sin perder
la pieza, proteger, elegir la mejor captura, ataque doble y jaque mate.

Cada objetivo dice si una jugada lo cumple y, si no, explica por qué con calma.
Las piezas negras no se mueven en estos ejercicios: solo cuenta la jugada de las blancas.
"""

from enum import StrEnum

import chess

from .. import anunciador
from ..idioma import _, ngettext

VALOR = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


class Objetivo(StrEnum):
	JAQUE = "jaque"
	MATE = "mate"
	SALIR_JAQUE = "salir_jaque"
	CAPTURAR = "capturar"
	CAPTURA_SEGURA = "captura_segura"
	MEJOR_CAPTURA = "mejor_captura"
	PROTEGER = "proteger"
	ATAQUE_DOBLE = "ataque_doble"
	ENROQUE = "enroque"
	AL_PASO = "al_paso"
	# Cualquier jugada que no ahogue al rey negro.
	NO_AHOGAR = "no_ahogar"
	# Una jugada concreta, escrita con la tecla J (las jugadas válidas van en el ejercicio).
	NOTACION = "notacion"


class Forma(StrEnum):
	"""Forma exigida al salir del jaque o al proteger una pieza."""

	REY = "rey"
	TAPAR = "tapar"
	CAPTURAR = "capturar"
	MOVER = "mover"
	DEFENDER = "defender"
	CORTO = "corto"
	LARGO = "largo"


def _nombres(casillas) -> str:
	return anunciador.unir_lista([chess.square_name(c) for c in sorted(casillas)])


def _piezas_en(tablero: chess.Board, casillas) -> str:
	textos = []
	for casilla in sorted(casillas):
		pieza = tablero.piece_at(casilla)
		if pieza is not None:
			textos.append(anunciador.pieza_en_casilla(pieza, casilla))
	return anunciador.unir_lista(textos)


def tras(tablero: chess.Board, jugada: chess.Move) -> chess.Board:
	"""Tablero después de la jugada de las blancas, con el turno de las negras."""
	siguiente = tablero.copy(stack=False)
	siguiente.push(jugada)
	return siguiente


def atacada(tablero: chess.Board, casilla: chess.Square) -> bool:
	return bool(tablero.attackers(chess.BLACK, casilla))


def defendida(tablero: chess.Board, casilla: chess.Square) -> bool:
	return bool(tablero.attackers(chess.WHITE, casilla))


def es_ahogado(tablero_negras: chess.Board) -> bool:
	"""Ahogado de las negras, solo si tienen rey (en los ejercicios sin rey no hay ahogado)."""
	return tablero_negras.king(chess.BLACK) is not None and tablero_negras.is_stalemate()


def es_mate(tablero_negras: chess.Board) -> bool:
	return tablero_negras.king(chess.BLACK) is not None and tablero_negras.is_checkmate()


def piezas_atacadas_valiosas(tablero: chess.Board, desde: chess.Square) -> list[chess.Square]:
	"""Piezas negras que no son peones (el rey incluido) atacadas por la pieza de `desde`."""
	resultado = []
	for casilla in tablero.attacks(desde):
		pieza = tablero.piece_at(casilla)
		if pieza is not None and pieza.color == chess.BLACK and pieza.piece_type != chess.PAWN:
			resultado.append(casilla)
	return resultado


def forma_de_salida(tablero: chess.Board, jugada: chess.Move) -> Forma:
	"""Cómo sale del jaque una jugada legal de las blancas."""
	if tablero.piece_type_at(jugada.from_square) == chess.KING:
		return Forma.REY
	if tablero.is_capture(jugada):
		return Forma.CAPTURAR
	return Forma.TAPAR


def mejores_capturas(tablero: chess.Board) -> set[chess.Move]:
	"""Capturas que se llevan la pieza de más valor."""
	capturas = [j for j in tablero.legal_moves if tablero.is_capture(j)]
	if not capturas:
		return set()

	def valor(j: chess.Move) -> int:
		pieza = tablero.piece_at(j.to_square)
		return VALOR[pieza.piece_type] if pieza else 1

	maximo = max(valor(j) for j in capturas)
	return {j for j in capturas if valor(j) == maximo}


def evaluar(
	tablero: chess.Board,
	jugada: chess.Move,
	objetivo: Objetivo,
	casilla: chess.Square | None = None,
	forma: Forma | None = None,
	jugadas_validas: frozenset[str] = frozenset(),
) -> tuple[bool, str]:
	"""¿Cumple `jugada` (legal, de las blancas) el objetivo? Devuelve (cumple, explicación si no)."""
	if jugadas_validas:
		if jugada.uci() in jugadas_validas:
			return True, ""
		return False, _explicar(tablero, jugada, objetivo, casilla)
	despues = tras(tablero, jugada)
	cumple = _cumple(tablero, despues, jugada, objetivo, casilla, forma)
	if cumple:
		return True, ""
	if objetivo is Objetivo.SALIR_JAQUE and forma is not None:
		return False, _explicar_forma(forma)
	if objetivo is Objetivo.ENROQUE and forma is not None and tablero.is_castling(jugada):
		return False, _explicar_forma(forma)
	if (
		objetivo is Objetivo.PROTEGER
		and forma is not None
		and _cumple(tablero, despues, jugada, objetivo, casilla, None)
	):
		return False, _explicar_forma(forma)
	return False, _explicar(tablero, jugada, objetivo, casilla)


def _cumple(
	tablero: chess.Board,
	despues: chess.Board,
	jugada: chess.Move,
	objetivo: Objetivo,
	casilla: chess.Square | None,
	forma: Forma | None,
) -> bool:
	if objetivo is Objetivo.JAQUE:
		return despues.is_check()
	if objetivo is Objetivo.MATE:
		return es_mate(despues)
	if objetivo is Objetivo.SALIR_JAQUE:
		return forma is None or forma_de_salida(tablero, jugada) == forma
	if objetivo is Objetivo.CAPTURAR:
		return tablero.is_capture(jugada) and (casilla is None or jugada.to_square == casilla)
	if objetivo is Objetivo.CAPTURA_SEGURA:
		return tablero.is_capture(jugada) and not atacada(despues, jugada.to_square)
	if objetivo is Objetivo.MEJOR_CAPTURA:
		return jugada in mejores_capturas(tablero)
	if objetivo is Objetivo.ATAQUE_DOBLE:
		if len(piezas_atacadas_valiosas(despues, jugada.to_square)) < 2:
			return False
		return not atacada(despues, jugada.to_square) or defendida(despues, jugada.to_square)
	if objetivo is Objetivo.ENROQUE:
		if not tablero.is_castling(jugada):
			return False
		corto = tablero.is_kingside_castling(jugada)
		return forma is None or (forma is Forma.CORTO) == corto
	if objetivo is Objetivo.AL_PASO:
		return tablero.is_en_passant(jugada)
	if objetivo is Objetivo.NO_AHOGAR:
		return not es_ahogado(despues)
	if objetivo is Objetivo.PROTEGER:
		assert casilla is not None
		if jugada.from_square == casilla:
			# La pieza se movió: tiene que quedar a salvo.
			return forma in (None, Forma.MOVER) and not atacada(despues, jugada.to_square)
		if jugada.to_square in tablero.attackers(chess.BLACK, casilla) and forma is None:
			# Capturar al atacante también la salva, si no quedan otros atacantes.
			return not atacada(despues, casilla)
		return forma in (None, Forma.DEFENDER) and (
			not atacada(despues, casilla) or defendida(despues, casilla)
		)
	return False


def _explicar_forma(forma: Forma) -> str:
	if forma is Forma.REY:
		# Translators: said when the check was escaped in another way than the one requested.
		return _("You got out of check, but this exercise asks you to move the king.")
	if forma is Forma.TAPAR:
		# Translators: said when the check was escaped in another way than the one requested.
		return _("You got out of check, but this exercise asks you to block the check.")
	if forma is Forma.CAPTURAR:
		# Translators: said when the check was escaped in another way than the one requested.
		return _("You got out of check, but this exercise asks you to capture the piece that gives check.")
	if forma is Forma.CORTO:
		# Translators: said when the wrong castling was played.
		return _("That was queenside castling; this exercise asks for kingside castling.")
	if forma is Forma.LARGO:
		# Translators: said when the wrong castling was played.
		return _("That was kingside castling; this exercise asks for queenside castling.")
	if forma is Forma.MOVER:
		# Translators: said when a piece was protected instead of moved away.
		return _("Here protecting is not enough: move the piece to a safe square.")
	# Translators: said when a piece was moved away instead of protected.
	return _("This exercise asks you to protect the piece without moving it.")


def _explicar(
	tablero: chess.Board,
	jugada: chess.Move,
	objetivo: Objetivo,
	casilla: chess.Square | None,
) -> str:
	despues = tras(tablero, jugada)
	destino = jugada.to_square
	pieza = tablero.piece_at(jugada.from_square)
	capturada = tablero.piece_at(destino)
	if objetivo is Objetivo.ENROQUE:
		# Translators: said when a move is not castling; explains how to castle on the board.
		return _("That move is not castling. Pick up the king and drop it two squares towards the rook.")
	if objetivo is Objetivo.AL_PASO:
		# Translators: said when a move is not an en passant capture.
		return _(
			"That is not an en passant capture. Your pawn must move diagonally to the square the black pawn skipped.",
		)
	if objetivo is Objetivo.NO_AHOGAR:
		# Translators: said when a move stalemates the black king in an exercise.
		return _("Stalemate! The black king is not in check and has no moves: that would be a draw.")
	if objetivo in (Objetivo.JAQUE, Objetivo.MATE):
		if es_ahogado(despues):
			# Translators: said when a move stalemates the black king in an exercise.
			return _("Stalemate! The black king is not in check and has no moves: that would be a draw.")
		if not despues.is_check():
			# Translators: said when a move was expected to give check.
			return _("That move does not give check.")
		rey = despues.king(chess.BLACK)
		escapes = [j.to_square for j in despues.legal_moves if j.from_square == rey]
		if escapes:
			# Translators: said when a check is not checkmate; {squares} lists where the king can go.
			return _("It is check, but not checkmate: the black king can go to {squares}.").format(
				squares=_nombres(set(escapes)),
			)
		# Translators: said when a check is not checkmate because black can block or capture.
		return _("It is check, but not checkmate: black can defend by blocking or capturing.")
	if objetivo in (Objetivo.CAPTURAR, Objetivo.CAPTURA_SEGURA, Objetivo.MEJOR_CAPTURA) and capturada is None:
		# Translators: said when a capture was expected.
		return _("That move does not capture anything.")
	if objetivo is Objetivo.CAPTURAR and casilla is not None and capturada is not None:
		# Translators: said when the wrong piece was captured; {square} is the requested square.
		return _("You captured {piece}, but this exercise asks for the piece on {square}.").format(
			piece=anunciador.nombre_pieza(capturada),
			square=chess.square_name(casilla),
		)
	if objetivo is Objetivo.CAPTURA_SEGURA and pieza is not None:
		# Translators: said when a capture is not safe, for example
		# "Careful: on d7 your piece can be captured by black bishop on c8."
		return _("Careful: on {square} your piece can be captured by {attackers}.").format(
			square=chess.square_name(destino),
			attackers=_piezas_en(despues, despues.attackers(chess.BLACK, destino)),
		)
	if objetivo is Objetivo.MEJOR_CAPTURA and capturada is not None:
		# Translators: said when a capture is not the most valuable one.
		return _("You captured {piece}, worth {value}, but there is a piece worth more.").format(
			piece=anunciador.nombre_pieza(capturada),
			value=VALOR[capturada.piece_type],
		)
	if objetivo is Objetivo.ATAQUE_DOBLE:
		cantidad = len(piezas_atacadas_valiosas(despues, destino))
		if cantidad >= 2:
			# Translators: said when a double attack leaves the attacking piece unprotected.
			return _("You attack two pieces, but on {square} your piece can be captured for free.").format(
				square=chess.square_name(destino),
			)
		# Translators: said when a move does not attack two pieces; {n} is how many it attacks.
		return ngettext(
			"From there your piece attacks only {n} valuable piece.",
			"From there your piece attacks only {n} valuable pieces.",
			cantidad,
		).format(n=cantidad)
	if objetivo is Objetivo.PROTEGER and casilla is not None:
		protegida = destino if jugada.from_square == casilla else casilla
		atacantes = despues.attackers(chess.BLACK, protegida)
		# Translators: said when the attacked piece is still in danger after the move.
		return _("Your piece is still in danger: {attackers} can capture it.").format(
			attackers=_piezas_en(despues, atacantes),
		)
	# Translators: generic message when a move does not solve the exercise.
	return _("That move does not solve the exercise.")


def jugadas_que_cumplen(
	tablero: chess.Board,
	objetivo: Objetivo,
	casilla: chess.Square | None = None,
	forma: Forma | None = None,
	jugadas_validas: frozenset[str] = frozenset(),
) -> list[chess.Move]:
	return [
		j
		for j in tablero.legal_moves
		if j.promotion in (None, chess.QUEEN)
		and evaluar(tablero, j, objetivo, casilla, forma, jugadas_validas)[0]
	]


# Mate en dos, con defensa de las negras.


def tiene_mate_en_uno(tablero_blancas: chess.Board) -> bool:
	for jugada in tablero_blancas.legal_moves:
		tablero_blancas.push(jugada)
		mate = es_mate(tablero_blancas)
		tablero_blancas.pop()
		if mate:
			return True
	return False


def defensa(tablero_negras: chess.Board) -> tuple[chess.Move | None, bool]:
	"""La mejor respuesta de las negras y si con ella evitan el mate en una.

	Prefiere una respuesta tras la que las blancas no tengan mate en una; si todas lo permiten,
	elige la que deja al rey negro más casillas (la defensa más tenaz).
	"""
	mejor: chess.Move | None = None
	mejor_movilidad = -1
	for respuesta in tablero_negras.legal_moves:
		tablero_negras.push(respuesta)
		evita = not tiene_mate_en_uno(tablero_negras)
		tablero_negras.pop()
		if evita:
			return respuesta, True
		tablero_negras.push(respuesta)
		tablero_negras.push(chess.Move.null())
		movilidad = sum(1 for _j in tablero_negras.legal_moves)
		tablero_negras.pop()
		tablero_negras.pop()
		if movilidad > mejor_movilidad:
			mejor, mejor_movilidad = respuesta, movilidad
	return mejor, False


def es_mate_en_dos(tablero_blancas: chess.Board, jugada: chess.Move) -> bool:
	"""¿La jugada fuerza mate en la siguiente, responda lo que responda el negro?"""
	despues = tras(tablero_blancas, jugada)
	if es_mate(despues):
		return True
	if not any(True for _j in despues.legal_moves):
		return False
	_respuesta, evita = defensa(despues)
	return not evita


def valor_de(tablero: chess.Board, casilla: chess.Square) -> int:
	pieza = tablero.piece_at(casilla)
	return VALOR[pieza.piece_type] if pieza else 0
