# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""«Atajos de teclado»: las teclas de cada ventana, tal como las tiene asignadas cada persona.

Las teclas se consultan a NVDA en el momento (como el diálogo Gestos de entrada), así que la
lista refleja los cambios hechos en Gestos de entrada. Las descripciones son propias de cada
contexto: F5, por ejemplo, dice cosas distintas en una partida, una lección o un reto.
"""

from collections.abc import Iterable
from enum import StrEnum
from html import escape

import addonHandler
import inputCore
import ui
from logHandler import log

addonHandler.initTranslation()

# Paquete del complemento, para reconocer las órdenes globales (las del menú Herramientas).
_PAQUETE = __name__.rsplit(".interfaz", 1)[0]


class Contexto(StrEnum):
	PARTIDA = "partida"
	LECCION = "leccion"
	RETOS = "retos"
	REPASO = "repaso"


# Una entrada: las órdenes que agrupa (o None si la tecla es fija, como Alt+F4), las teclas fijas
# en ese caso, y la descripción.
Entrada = tuple[tuple[str, ...] | None, str, str]


def _moverse() -> tuple[str, list[Entrada]]:
	return (
		# Translators: heading in the list of keyboard shortcuts.
		_("Moving around the board"),
		[
			# Translators: description in the list of keyboard shortcuts.
			(("arriba", "abajo", "izquierda", "derecha"), "", _("Move between the squares")),
			# Translators: description in the list of keyboard shortcuts.
			(("inicio_fila", "fin_fila"), "", _("First or last square of the row")),
			# Translators: description in the list of keyboard shortcuts.
			(("ir_a_fila",), "", _("Go to that rank, keeping the file")),
			(
				("saltar_a_pieza",),
				"",
				# Translators: description in the list of keyboard shortcuts.
				_(
					"Go to your next king, queen, rook, bishop, knight or pawn (R, D, T, A, C, P); "
					"with shift, to the opponent's pieces",
				),
			),
			# Translators: description in the list of keyboard shortcuts.
			(("ultima_jugada",), "", _("Go to the square of the last move")),
		],
	)


def _mover_piezas(contexto: Contexto) -> tuple[str, list[Entrada]]:
	entradas: list[Entrada] = [
		# Translators: description in the list of keyboard shortcuts.
		(("activar",), "", _("Pick up the piece of the square; with a piece picked up, drop it here")),
		# Translators: description in the list of keyboard shortcuts.
		(("escape",), "", _("Drop the selected piece without moving it")),
		# Translators: description in the list of keyboard shortcuts.
		(("escribir_jugada",), "", _("Type a move, for example Nf3 or e4")),
	]
	if contexto is Contexto.PARTIDA:
		entradas.append(
			# Translators: description in the list of keyboard shortcuts.
			(("deshacer",), "", _("Undo the last move (asks for confirmation)")),
		)
	else:
		entradas.append(
			# Translators: description in the list of keyboard shortcuts, in lessons and Challenges.
			(None, "", _("When an exercise is solved, Enter goes to the next one")),
		)
	# Translators: heading in the list of keyboard shortcuts.
	return _("Moving pieces"), entradas


def _informacion(contexto: Contexto) -> tuple[str, list[Entrada]]:
	estados = {
		# Translators: description of F5 in the list of keyboard shortcuts, during a game.
		Contexto.PARTIDA: _("Whose turn it is, the move number and the last move"),
		# Translators: description of F5 in the list of keyboard shortcuts, in lessons.
		Contexto.LECCION: _("Which exercise you are on and what you have to do"),
		# Translators: description of F5 in the list of keyboard shortcuts, in Challenges.
		Contexto.RETOS: _("Your level and the current puzzle"),
		# Translators: description of F5 in the list of keyboard shortcuts, while reviewing a game.
		Contexto.REPASO: _("How many moves you have gone through, whose turn it is and the last move"),
	}
	entradas: list[Entrada] = [
		# Translators: description in the list of keyboard shortcuts.
		(("ataques",), "", _("Which pieces attack and defend this square")),
		# Translators: description in the list of keyboard shortcuts.
		(("piezas_propias",), "", _("Your pieces")),
		# Translators: description in the list of keyboard shortcuts.
		(("piezas_rival",), "", _("The opponent's pieces")),
		# Translators: description in the list of keyboard shortcuts.
		(("detalle_casilla",), "", _("Coordinate, color and content of the square")),
		# Translators: description in the list of keyboard shortcuts.
		(("planilla",), "", _("Score sheet with all the moves")),
		(("estado",), "", estados[contexto]),
	]
	if contexto is Contexto.PARTIDA:
		# Translators: description in the list of keyboard shortcuts.
		entradas.append((("reloj",), "", _("Time left on the clock")))
	# Translators: heading in the list of keyboard shortcuts.
	return _("Information"), entradas


def _propias(contexto: Contexto) -> tuple[str, list[Entrada]] | None:
	if contexto is Contexto.LECCION:
		return (
			# Translators: heading in the list of keyboard shortcuts.
			_("Lessons"),
			[
				# Translators: description in the list of keyboard shortcuts.
				(("repetir_instruccion",), "", _("Repeat the instruction of the exercise")),
				# Translators: description in the list of keyboard shortcuts.
				(("repetir_explicacion",), "", _("Repeat the explanation of the lesson")),
				# Translators: description in the list of keyboard shortcuts.
				(("pista",), "", _("Hint: the first one helps a little, the next ones a lot more")),
				# Translators: description in the list of keyboard shortcuts.
				(("manzanas",), "", _("How many apples are left and where")),
			],
		)
	if contexto is Contexto.RETOS:
		return (
			# Translators: heading in the list of keyboard shortcuts.
			_("Challenges"),
			[
				# Translators: description in the list of keyboard shortcuts.
				(("repetir_instruccion",), "", _("Repeat the puzzle")),
				# Translators: description in the list of keyboard shortcuts.
				(("repetir_explicacion",), "", _("Repeat the explanation (of the theme, if you chose one)")),
				(
					("pista",),
					"",
					# Translators: description in the list of keyboard shortcuts.
					_("Hint: first the theme, then which piece to move and finally the move"),
				),
			],
		)
	if contexto is Contexto.REPASO:
		return (
			# Translators: heading in the list of keyboard shortcuts.
			_("Reviewing a game"),
			[
				# Translators: description in the list of keyboard shortcuts.
				(("avanzar",), "", _("Next move")),
				# Translators: description in the list of keyboard shortcuts.
				(("retroceder",), "", _("Go back one move")),
				# Translators: description in the list of keyboard shortcuts.
				(("ir_al_principio", "ir_al_final"), "", _("Go to the start or the end of the game")),
			],
		)
	return None


def _ventana(contexto: Contexto) -> tuple[str, list[Entrada]]:
	menus = {
		# Translators: description in the list of keyboard shortcuts.
		Contexto.PARTIDA: _("Game menu: flip board, draw, resign, clock, save, new game, hide and close"),
		# Translators: description in the list of keyboard shortcuts.
		Contexto.LECCION: _("Lesson menu: restart, skip, practice more, back to the list and close"),
		# Translators: description in the list of keyboard shortcuts.
		Contexto.RETOS: _("Challenges menu: restart, another puzzle, back to Challenges and close"),
		# Translators: description in the list of keyboard shortcuts.
		Contexto.REPASO: _("Review menu: flip board, start, end, copy and close"),
	}
	return (
		# Translators: heading in the list of keyboard shortcuts.
		_("Menu and window"),
		[
			(("menu",), "", menus[contexto]),
			# Translators: description in the list of keyboard shortcuts.
			(("atajos",), "", _("This list of keyboard shortcuts")),
			# Translators: description in the list of keyboard shortcuts.
			(None, "Alt+F4", _("Close the window")),
		],
	)


def _globales() -> tuple[str, list[Entrada]]:
	return (
		# Translators: heading in the list of keyboard shortcuts: commands that work from anywhere.
		_("From anywhere"),
		[
			# Translators: description in the list of keyboard shortcuts.
			(("abrir_tablero",), "", _("Open the board: return to the game or start a new one")),
			# Translators: description in the list of keyboard shortcuts.
			(("aprender_a_jugar",), "", _("Open Learn to play")),
			# Translators: description in the list of keyboard shortcuts.
			(("retos",), "", _("Open Challenges")),
			# Translators: description in the list of keyboard shortcuts.
			(("estadisticas",), "", _("Show My statistics")),
		],
	)


def secciones(contexto: Contexto) -> list[tuple[str, list[Entrada]]]:
	lista = [_moverse()]
	if contexto is not Contexto.REPASO:
		lista.append(_mover_piezas(contexto))
	lista.append(_informacion(contexto))
	propias = _propias(contexto)
	if propias is not None:
		lista.append(propias)
	lista.append(_ventana(contexto))
	return lista


def teclas_asignadas(objeto: object) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
	"""Teclas de cada orden: (las del tablero de `objeto`, las globales del complemento).

	Se consultan a NVDA como en Gestos de entrada, incluidos los cambios de cada persona.
	"""
	tablero: dict[str, list[str]] = {}
	globales: dict[str, list[str]] = {}
	try:
		mapeos = inputCore.manager.getAllGestureMappings(obj=objeto, ancestors=[])
	except Exception:
		log.debugWarning("No se pudieron consultar los gestos", exc_info=True)
		return tablero, globales
	for categoria in mapeos.values():
		for info in categoria.values():
			nombre = info.scriptName
			if isinstance(objeto, info.cls):
				tablero.setdefault(nombre, []).extend(info.gestures)
			elif info.cls.__module__ == _PAQUETE:
				globales.setdefault(nombre, []).extend(info.gestures)
	return tablero, globales


def _texto_teclas(gestos: Iterable[str]) -> str:
	textos = []
	for gesto in gestos:
		try:
			texto = inputCore.getDisplayTextForGestureIdentifier(gesto)[1]
		except Exception:
			texto = gesto.split(":", 1)[-1]
		if texto not in textos:
			textos.append(texto)
	# Translators: shown in the list of keyboard shortcuts when a command has no key.
	return ", ".join(textos) if textos else _("no key assigned")


def _html_seccion(titulo: str, entradas: list[Entrada], teclas: dict[str, list[str]]) -> str:
	elementos = []
	for ordenes, fija, descripcion in entradas:
		if ordenes is None:
			linea = f"{fija}: {descripcion}" if fija else descripcion
		else:
			gestos = [g for orden in ordenes for g in teclas.get(orden, [])]
			linea = f"{_texto_teclas(gestos)}: {descripcion}"
		elementos.append(f"<li>{escape(linea)}.</li>")
	return f"<h2>{escape(titulo)}</h2><ul>{''.join(elementos)}</ul>"


def html_atajos(contextos: dict[Contexto, object]) -> str:
	"""La lista para uno o varios contextos. `contextos` asocia cada contexto con una casilla de su tablero."""
	# Translators: introduction of the list of keyboard shortcuts.
	intro = _(
		"You can change these keys in the NVDA menu, Preferences, Input gestures, "
		"category MiAjedrezAccesible (with the focus on the board for the board keys).",
	)
	partes = [f"<p>{escape(intro)}</p>"]
	vistas: set[str] = set()
	globales: dict[str, list[str]] = {}
	for contexto, objeto in contextos.items():
		teclas, globales = teclas_asignadas(objeto)
		for titulo, entradas in secciones(contexto):
			if len(contextos) > 1:
				# Varias ventanas: las secciones comunes solo una vez, y las demás con su ventana.
				if titulo in vistas:
					continue
				vistas.add(titulo)
			partes.append(_html_seccion(titulo, entradas, teclas))
	titulo, entradas = _globales()
	partes.append(_html_seccion(titulo, entradas, globales))
	return "".join(partes)


def mostrar(contextos: dict[Contexto, object]) -> None:
	ui.browseableMessage(
		html_atajos(contextos),
		# Translators: title of the window with the list of keyboard shortcuts.
		title=_("Keyboard shortcuts"),
		isHtml=True,
		closeButton=True,
		copyButton=True,
	)
