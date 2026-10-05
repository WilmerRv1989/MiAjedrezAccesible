# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""«Practicar más»: ejercicios creados al momento y rondas con dificultad que se adapta.

Cada ejercicio de piezas se resuelve antes de mostrarse: si no tiene solución o es demasiado
largo, se descarta y se crea otro. Así nunca aparece un ejercicio imposible, y las estrellas
se calculan con el mínimo real de jugadas.
"""

import random
from dataclasses import replace

import chess

from .. import anunciador
from ..idioma import _, ngettext
from . import resolver
from .modelo import POSICIONES, Ejercicio, TipoEjercicio
from .practica_jugadas import GeneradorJugadas
from .sesion import texto_direcciones

TAMANO_RONDA = 5
NIVEL_MINIMO = 1
NIVEL_MAXIMO = 3
# Estrellas de una ronda (de 15) para subir o bajar de nivel.
SUBIR_CON = 13
BAJAR_CON = 8

LECCIONES_CON_PRACTICA = frozenset([*(str(n) for n in range(1, 24)), "x1"])
_PIEZA_DE_LECCION = {"4": chess.ROOK, "5": chess.BISHOP, "6": chess.QUEEN, "7": chess.KING, "8": chess.KNIGHT}
# Jugadas máximas de la solución según el nivel, para que nada sea demasiado largo.
_MAXIMO_JUGADAS = {1: 3, 2: 5, 3: 6}
_INTENTOS = 300
# Teclas para saltar a cada tipo de pieza (las del tablero, en español).
_TECLA_PIEZA = {
	chess.KING: "R",
	chess.QUEEN: "D",
	chess.ROOK: "T",
	chess.BISHOP: "A",
	chess.KNIGHT: "C",
	chess.PAWN: "P",
}


def tiene_practica(id_leccion: str) -> bool:
	return id_leccion in LECCIONES_CON_PRACTICA


def _nombres(casillas) -> str:
	return anunciador.unir_lista([chess.square_name(c) for c in casillas])


def _misma_paridad(a: chess.Square, b: chess.Square) -> bool:
	return anunciador.es_casilla_oscura(a) == anunciador.es_casilla_oscura(b)


class GeneradorPractica:
	def __init__(self, azar: random.Random | None = None) -> None:
		self.azar = azar or random.Random()
		self._contador = 0
		self._jugadas = GeneradorJugadas(self.azar)

	def generar(self, id_leccion: str, nivel: int) -> Ejercicio:
		nivel = max(NIVEL_MINIMO, min(NIVEL_MAXIMO, nivel))
		self._contador += 1
		if id_leccion == "1":
			ejercicio = self._coordenadas(nivel)
		elif id_leccion == "2":
			ejercicio = self._diagonales(nivel)
		elif id_leccion == "3":
			ejercicio = self._posicion_inicial(nivel)
		elif id_leccion in _PIEZA_DE_LECCION:
			ejercicio = self._pieza(_PIEZA_DE_LECCION[id_leccion], nivel)
		elif id_leccion == "9":
			ejercicio = self._peon(nivel)
		elif id_leccion == "10":
			tipo = self.azar.choice([chess.ROOK, chess.BISHOP, chess.QUEEN, chess.KNIGHT])
			ejercicio = self._pieza(
				tipo,
				nivel,
				tipos_negros=(chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK),
				solo_capturas=True,
			)
		elif id_leccion == "11":
			ejercicio = self._jugadas.proteger(nivel)
		elif id_leccion == "12":
			ejercicio = self._jugadas.captura_segura(nivel)
		elif id_leccion == "13":
			ejercicio = self._jugadas.mejor_captura(nivel)
		elif id_leccion == "14":
			ejercicio = self._jugadas.jaque(nivel)
		elif id_leccion == "15":
			ejercicio = self._jugadas.salir_jaque(nivel)
		elif id_leccion == "16":
			ejercicio = self._jugadas.mate(nivel)
		elif id_leccion == "17":
			ejercicio = (
				self._jugadas.mate_en_dos() if nivel == 3 else self._jugadas.mate(nivel, solo_dama=True)
			)
		elif id_leccion == "18":
			ejercicio = self._jugadas.ataque_doble(nivel)
		elif id_leccion == "19":
			ejercicio = self._jugadas.enroque(nivel)
		elif id_leccion == "20":
			ejercicio = self._jugadas.al_paso(nivel)
		elif id_leccion == "21":
			ejercicio = self._jugadas.tablas(nivel)
		elif id_leccion == "22":
			ejercicio = self._jugadas.notacion(nivel)
		elif id_leccion == "23":
			ejercicio = self._jugadas.guerra_peones(nivel)
		elif id_leccion == "x1":
			ejercicio = self._jugadas.solo_escribiendo(nivel)
		else:
			raise ValueError(f"La lección {id_leccion} no tiene práctica")
		return replace(ejercicio, id=f"practica-{id_leccion}-{self._contador}", practica=True)

	def _casilla(self, excluir=()) -> chess.Square:
		while True:
			casilla = self.azar.randrange(64)
			if casilla not in excluir:
				return casilla

	# Lección 1: coordenadas.

	def _coordenadas(self, nivel: int) -> Ejercicio:
		inicio = self._casilla()
		if nivel == 3:
			casillas = []
			while len(casillas) < 3:
				casillas.append(self._casilla(excluir=[inicio, *casillas]))
			return Ejercicio(
				id="",
				tipo=TipoEjercicio.VISITAR,
				posicion=POSICIONES["vacio"],
				inicio=inicio,
				respuestas=frozenset(casillas),
				# Translators: practice instruction; {squares} is a list like "c3, f6 and h2".
				instruccion=_("You are on {start}. Visit {squares} and press Enter on each one.").format(
					start=chess.square_name(inicio),
					squares=_nombres(casillas),
				),
				pistas=(
					# Translators: practice hint.
					_("The number keys take you to a row without changing the column."),
					# Translators: practice hint; {faltan} is replaced by the squares still to visit.
					_("You still have to visit: {faltan}."),
				),
			)
		while True:
			objetivo = self._casilla(excluir=[inicio])
			if nivel == 2 or chess.square_distance(inicio, objetivo) <= 2:
				break
		return Ejercicio(
			id="",
			tipo=TipoEjercicio.IR_A,
			posicion=POSICIONES["vacio"],
			inicio=inicio,
			respuestas=frozenset([objetivo]),
			# Translators: practice instruction to go to a square.
			instruccion=_("You are on {start}. Go to {target} and press Enter.").format(
				start=chess.square_name(inicio),
				target=chess.square_name(objetivo),
			),
			pistas=(
				# Translators: practice hint; {file} is a letter and {rank} a number.
				_("First find the column {file}, then the row {rank}.").format(
					file=chess.FILE_NAMES[chess.square_file(objetivo)],
					rank=chess.square_rank(objetivo) + 1,
				),
				# Translators: practice hint, for example "From a1, e4 is four columns to the right and three rows up."
				_("From {start}, {target} is {directions}.").format(
					start=chess.square_name(inicio),
					target=chess.square_name(objetivo),
					directions=texto_direcciones(inicio, objetivo),
				),
			),
		)

	# Lección 2: diagonales.

	def _diagonales(self, nivel: int) -> Ejercicio:
		direcciones = [
			# Translators: direction of a diagonal, used in practice exercises.
			(1, 1, _("up to the right"), _("up"), _("right")),
			# Translators: direction of a diagonal, used in practice exercises.
			(-1, 1, _("up to the left"), _("up"), _("left")),
			# Translators: direction of a diagonal, used in practice exercises.
			(1, -1, _("down to the right"), _("down"), _("right")),
			# Translators: direction of a diagonal, used in practice exercises.
			(-1, -1, _("down to the left"), _("down"), _("left")),
		]
		largo_minimo = {1: 1, 2: 3, 3: 2}[nivel]
		while True:
			inicio = self._casilla()
			paso_columna, paso_fila, direccion, vertical, horizontal = self.azar.choice(direcciones)
			camino = []
			columna, fila = chess.square_file(inicio), chess.square_rank(inicio)
			while 0 <= columna + paso_columna <= 7 and 0 <= fila + paso_fila <= 7:
				columna, fila = columna + paso_columna, fila + paso_fila
				camino.append(chess.square(columna, fila))
			if len(camino) >= largo_minimo:
				break
		datos = {"start": chess.square_name(inicio), "direction": direccion}
		if nivel == 1:
			objetivo = camino[0]
			# Translators: practice instruction about diagonals.
			instruccion = _(
				"You are on {start}. Go to the next square of the diagonal that goes {direction}, and press Enter.",
			)
		elif nivel == 2:
			objetivo = self.azar.choice(camino[1:])
			# Translators: practice instruction about diagonals; {rank} is a row number.
			instruccion = _(
				"You are on {start}. Follow the diagonal that goes {direction} to row {rank}, and press Enter.",
			)
			datos["rank"] = str(chess.square_rank(objetivo) + 1)
		else:
			objetivo = camino[-1]
			# Translators: practice instruction about diagonals.
			instruccion = _(
				"You are on {start}. Go to the end of the diagonal that goes {direction}, and press Enter.",
			)
		return Ejercicio(
			id="",
			tipo=TipoEjercicio.IR_A,
			posicion=POSICIONES["vacio"],
			inicio=inicio,
			respuestas=frozenset([objetivo]),
			instruccion=instruccion.format(**datos),
			pistas=(
				# Translators: practice hint about moving diagonally with the arrow keys.
				_("For each step, press the {vertical} arrow and the {horizontal} arrow.").format(
					vertical=vertical,
					horizontal=horizontal,
				),
				# Translators: practice hint that gives the answer.
				_("It is {target}.").format(target=chess.square_name(objetivo)),
			),
		)

	# Lección 3: la posición inicial.

	def _descripcion_pieza(self, tipo: chess.PieceType, color: chess.Color) -> tuple[str, chess.Square]:
		"""Una pieza concreta de la posición inicial, descrita para encontrarla, y su casilla."""
		casillas = sorted(chess.Board().pieces(tipo, color))
		nombre = anunciador.nombre_pieza_con_articulo(chess.Piece(tipo, color))
		if len(casillas) == 1:
			return nombre, casillas[0]
		if tipo == chess.PAWN:
			casilla = self.azar.choice(casillas)
			# Translators: a pawn described by its file, for example "the white pawn of the c file".
			texto = _("{piece} of the {file} file").format(
				piece=nombre,
				file=chess.FILE_NAMES[chess.square_file(casilla)],
			)
			return texto, casilla
		lado_rey = self.azar.random() < 0.5
		casilla = casillas[1] if lado_rey else casillas[0]
		if lado_rey:
			# Translators: a piece described by its side, for example "the white rook on the king's side".
			return _("{piece} on the king's side").format(piece=nombre), casilla
		# Translators: a piece described by its side, for example "the white rook on the queen's side".
		return _("{piece} on the queen's side").format(piece=nombre), casilla

	def _posicion_inicial(self, nivel: int) -> Ejercicio:
		color = self.azar.choice([chess.WHITE, chess.BLACK])
		tipos = list(_TECLA_PIEZA)
		if nivel == 3:
			tipos.remove(chess.PAWN)
		tipo = self.azar.choice(tipos)
		tecla = _TECLA_PIEZA[tipo]
		if color == chess.WHITE:
			# Translators: practice hint; {key} is a letter like T.
			pista_tecla = _("Press {key} to jump to your pieces of that type.").format(key=tecla)
		else:
			# Translators: practice hint; {key} is a letter like T.
			pista_tecla = _("Press Shift+{key} to jump to your opponent's pieces of that type.").format(
				key=tecla,
			)
		if tipo == chess.PAWN:
			# Translators: practice hint about where the pawns start.
			pista_fila = _("The white pawns start on row 2, and the black pawns on row 7.")
		else:
			# Translators: practice hint about the initial position.
			pista_fila = _(
				"Remember the first row: rook, knight, bishop, queen, king, bishop, knight and rook.",
			)
		if nivel == 1:
			respuestas = frozenset(chess.Board().pieces(tipo, color))
			pieza = anunciador.nombre_pieza(chess.Piece(tipo, color))
			# Translators: practice instruction; {piece} is a piece like "white knight".
			instruccion = _("Find a square with a {piece} and press Enter.").format(piece=pieza)
			pistas = (pista_fila, pista_tecla)
		elif nivel == 2:
			descripcion, casilla = self._descripcion_pieza(tipo, color)
			respuestas = frozenset([casilla])
			# Translators: practice instruction; {piece} is a description like "the white rook on the king's side".
			instruccion = _("Find {piece} and press Enter.").format(piece=descripcion)
			pistas = (pista_fila, pista_tecla)
		else:
			descripcion, casilla = self._descripcion_pieza(tipo, color)
			delante = casilla + 8 if color == chess.WHITE else casilla - 8
			respuestas = frozenset([delante])
			# Translators: practice instruction; {piece} is a description like "the black king".
			instruccion = _(
				"Find {piece}. Then go to the square right in front of it, from its side, and press Enter.",
			).format(piece=descripcion)
			pistas = (pista_tecla, _("It is {target}.").format(target=chess.square_name(delante)))
		return Ejercicio(
			id="",
			tipo=TipoEjercicio.IR_A,
			posicion=POSICIONES["inicial"],
			inicio=chess.E1,
			respuestas=respuestas,
			instruccion=instruccion,
			pistas=pistas,
		)

	# Lecciones 4 a 8: cada pieza.

	def _pieza(
		self,
		tipo: chess.PieceType,
		nivel: int,
		tipos_negros: tuple[chess.PieceType, ...] = (chess.PAWN,),
		solo_capturas: bool = False,
	) -> Ejercicio:
		for _intento in range(_INTENTOS):
			tablero = chess.Board(None)
			origen = self._casilla()
			tablero.set_piece_at(origen, chess.Piece(tipo, chess.WHITE))
			ocupadas = {origen}

			def libre(color_igual: bool = False, filas=range(8)) -> chess.Square:
				while True:
					casilla = self._casilla(excluir=ocupadas)
					if chess.square_rank(casilla) not in filas:
						continue
					if color_igual and not _misma_paridad(casilla, origen):
						continue
					ocupadas.add(casilla)
					return casilla

			solo_su_color = tipo == chess.BISHOP
			objetivos = self.azar.choice([1, 2]) if nivel == 1 else 3
			peones = 0 if nivel == 1 else self.azar.choice([1, 2])
			if solo_capturas:
				objetivos = peones = nivel
			obstaculos = [libre(filas=range(1, 7)) for _o in range(2 if nivel == 3 else 0)]
			for casilla in obstaculos:
				tablero.set_piece_at(casilla, chess.Piece(chess.PAWN, chess.WHITE))
			negros = [libre(solo_su_color, filas=range(1, 7)) for _p in range(peones)]
			for casilla in negros:
				tablero.set_piece_at(casilla, chess.Piece(self.azar.choice(tipos_negros), chess.BLACK))
			manzanas = [libre(solo_su_color) for _m in range(objetivos - peones)]
			ejercicio = Ejercicio(
				id="",
				tipo=TipoEjercicio.MANZANAS,
				posicion=tablero.board_fen(),
				inicio=origen,
				manzanas=frozenset(manzanas),
				capturar=frozenset(negros) or None,
				instruccion="",
				pistas=(),
			)
			if ejercicio.tablero().is_check():
				# El rey no empieza atacado por un peón: sería confuso.
				continue
			solucion = resolver.resolver(ejercicio, limite=_MAXIMO_JUGADAS[nivel], solo_desde=origen)
			if solucion:
				return self._completar_pieza(ejercicio, solucion, origen, manzanas, negros, obstaculos)
		raise RuntimeError("No se pudo crear un ejercicio de práctica")

	def _completar_pieza(
		self,
		ejercicio: Ejercicio,
		solucion: list[chess.Move],
		origen: chess.Square,
		manzanas: list[chess.Square],
		negros: list[chess.Square],
		obstaculos: list[chess.Square],
		bloqueo: chess.Square | None = None,
	) -> Ejercicio:
		pieza = ejercicio.tablero().piece_at(origen)
		assert pieza is not None
		partes = [
			# Translators: start of a practice instruction, for example "Your white rook is on d4."
			_("Your {piece} is on {square}.").format(
				piece=anunciador.nombre_pieza(pieza),
				square=chess.square_name(origen),
			),
		]
		if bloqueo is not None:
			# Translators: practice instruction when a black pawn blocks the way.
			partes.append(
				_("The black pawn on {square} blocks your way.").format(square=chess.square_name(bloqueo)),
			)
		if manzanas:
			partes.append(
				# Translators: practice instruction; {squares} is a list of squares.
				ngettext(
					"Collect the apple on {squares}.",
					"Collect the apples on {squares}.",
					len(manzanas),
				).format(
					squares=_nombres(manzanas),
				),
			)
		tablero = ejercicio.tablero()
		if negros and all(tablero.piece_type_at(c) == chess.PAWN for c in negros):
			partes.append(
				# Translators: practice instruction; {squares} is a list of squares.
				ngettext(
					"Capture the black pawn on {squares}.",
					"Capture the black pawns on {squares}.",
					len(negros),
				).format(squares=_nombres(negros)),
			)
		elif negros:
			piezas = anunciador.unir_lista(
				[anunciador.pieza_en_casilla(tablero.piece_at(c), c) for c in negros],
			)
			# Translators: practice instruction; {pieces} is a list like "black knight on c5 and black rook on e7".
			partes.append(_("Capture: {pieces}.").format(pieces=piezas))
		if obstaculos:
			partes.append(
				# Translators: practice instruction about own pawns that block the way.
				ngettext(
					"Your pawn on {squares} is in the way.",
					"Your pawns on {squares} are in the way.",
					len(obstaculos),
				).format(squares=_nombres(obstaculos)),
			)
		objetivos = set(manzanas) | set(negros)
		primero = next((j.to_square for j in solucion if j.to_square in objetivos), solucion[0].to_square)
		pistas = (
			# Translators: practice hint; {square} is the first target to go for.
			_("Start with {square}.").format(square=chess.square_name(primero)),
			# Translators: practice hint; {squares} lists the destination of each move of a solution.
			_("For example, move to {squares}.").format(squares=_nombres([j.to_square for j in solucion])),
		)
		return replace(ejercicio, minimo=len(solucion), instruccion=" ".join(partes), pistas=pistas)

	# Lección 9: el peón.

	def _peon(self, nivel: int) -> Ejercicio:
		for _intento in range(_INTENTOS):
			tablero = chess.Board(None)
			columna = self.azar.randrange(1, 7)
			manzanas: list[chess.Square] = []
			negros: list[chess.Square] = []
			bloqueo = None
			if nivel == 1:
				origen = chess.square(columna, 1)
				manzanas = [chess.square(columna, self.azar.randrange(2, 5))]
			elif nivel == 2:
				fila = self.azar.randrange(2, 5)
				origen = chess.square(columna, fila)
				bloqueo = chess.square(columna, fila + 1)
				negros = [chess.square(columna + self.azar.choice([-1, 1]), fila + 1)]
				tablero.set_piece_at(bloqueo, chess.Piece(chess.PAWN, chess.BLACK))
				for casilla in negros:
					tablero.set_piece_at(casilla, chess.Piece(chess.PAWN, chess.BLACK))
			else:
				return self._coronar(columna)
			tablero.set_piece_at(origen, chess.Piece(chess.PAWN, chess.WHITE))
			ejercicio = Ejercicio(
				id="",
				tipo=TipoEjercicio.MANZANAS,
				posicion=tablero.board_fen(),
				inicio=origen,
				manzanas=frozenset(manzanas),
				capturar=frozenset(negros) or None,
				instruccion="",
				pistas=(),
			)
			solucion = resolver.resolver(ejercicio, limite=_MAXIMO_JUGADAS[nivel], solo_desde=origen)
			if solucion:
				return self._completar_pieza(ejercicio, solucion, origen, manzanas, negros, [], bloqueo)
		raise RuntimeError("No se pudo crear un ejercicio de práctica")

	def _coronar(self, columna: int) -> Ejercicio:
		tablero = chess.Board(None)
		origen = chess.square(columna, self.azar.choice([5, 6]))
		tablero.set_piece_at(origen, chess.Piece(chess.PAWN, chess.WHITE))
		con_bloqueo = chess.square_rank(origen) == 6 and self.azar.random() < 0.5
		partes = [
			_("Your {piece} is on {square}.").format(
				piece=anunciador.nombre_pieza(chess.Piece(chess.PAWN, chess.WHITE)),
				square=chess.square_name(origen),
			),
		]
		if con_bloqueo:
			delante = chess.square(columna, 7)
			lado = chess.square(columna + self.azar.choice([-1, 1]), 7)
			tablero.set_piece_at(delante, chess.Piece(chess.BISHOP, chess.BLACK))
			tablero.set_piece_at(lado, chess.Piece(chess.ROOK, chess.BLACK))
			partes.append(
				# Translators: practice instruction for a capture that promotes.
				_(
					"A black bishop blocks the last row, but you can capture the rook on {square} and promote.",
				).format(
					square=chess.square_name(lado),
				),
			)
			pistas = (
				# Translators: practice hint.
				_("The pawn captures diagonally forward."),
				_("For example, move to {squares}.").format(squares=chess.square_name(lado)),
			)
			minimo = 1
		else:
			# Translators: practice instruction to promote a pawn.
			partes.append(_("Take it to the last row and promote it."))
			pasos = [chess.square(columna, fila) for fila in range(chess.square_rank(origen) + 1, 8)]
			pistas = (
				# Translators: practice hint.
				_("The pawn moves forward one square at a time."),
				_("For example, move to {squares}.").format(squares=_nombres(pasos)),
			)
			minimo = len(pasos)
		return Ejercicio(
			id="",
			tipo=TipoEjercicio.CORONAR,
			posicion=tablero.board_fen(),
			inicio=origen,
			minimo=minimo,
			instruccion=" ".join(partes),
			pistas=pistas,
			# Translators: said when a pawn is promoted to a queen in a practice exercise.
			corona_dama=_("You promoted!"),
			# Translators: said when a pawn is promoted to another piece in a practice exercise.
			corona_otra=_("You promoted! The queen is almost always the best choice."),
		)


class RondaPractica:
	"""Una ronda de ejercicios generados. Al terminar, propone el nivel de la siguiente."""

	def __init__(
		self,
		id_leccion: str,
		nivel: int,
		generador: GeneradorPractica,
		tamano: int = TAMANO_RONDA,
	) -> None:
		self.id_leccion = id_leccion
		self.nivel = nivel
		self.tamano = tamano
		self._generador = generador
		self._ejercicios: list[Ejercicio] = []
		self.estrellas: list[int] = []

	def ejercicio(self, indice: int) -> Ejercicio:
		while len(self._ejercicios) <= indice:
			self._ejercicios.append(self._generador.generar(self.id_leccion, self.nivel))
		return self._ejercicios[indice]

	def cambiar(self, indice: int) -> Ejercicio:
		"""Sustituye un ejercicio por otro nuevo del mismo nivel (al saltarlo)."""
		self.ejercicio(indice)
		self._ejercicios[indice] = self._generador.generar(self.id_leccion, self.nivel)
		return self._ejercicios[indice]

	def registrar(self, estrellas: int | None) -> None:
		self.estrellas.append(estrellas or 0)

	@property
	def ganadas(self) -> int:
		return sum(self.estrellas)

	@property
	def posibles(self) -> int:
		return 3 * self.tamano

	def nivel_siguiente(self) -> int:
		if self.ganadas >= SUBIR_CON:
			return min(NIVEL_MAXIMO, self.nivel + 1)
		if self.ganadas <= BAJAR_CON:
			return max(NIVEL_MINIMO, self.nivel - 1)
		return self.nivel

	def texto_final(self) -> str:
		# Translators: said at the end of a practice round.
		partes = [
			_("Round completed! You earned {stars} of {total} stars.").format(
				stars=self.ganadas,
				total=self.posibles,
			),
		]
		siguiente = self.nivel_siguiente()
		if siguiente > self.nivel:
			# Translators: said when the practice level goes up.
			partes.append(_("Great! Next round, level {level}.").format(level=siguiente))
		elif siguiente < self.nivel:
			# Translators: said when the practice level goes down.
			partes.append(_("Next round, level {level}, to practice calmly.").format(level=siguiente))
		else:
			# Translators: said when the practice level stays the same.
			partes.append(_("Next round, again level {level}.").format(level=siguiente))
		return " ".join(partes)
