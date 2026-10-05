# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Retos: problemas de la base de datos de Lichess (dominio público), nivel y progreso.

Cada problema empieza en la posición ANTERIOR a la jugada del rival: la primera jugada es suya
y la solución empieza en la segunda. Los problemas se preparan con
`herramientas/preparar_problemas.py`.
"""

import datetime
import gzip
import json
import os
import random
from dataclasses import dataclass
from enum import StrEnum

import chess

from . import anunciador
from .curso.modelo import Ejercicio, TipoEjercicio
from .idioma import _, ngettext

RUTA_PROBLEMAS = os.path.join(
	os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
	"problemas",
	"problemas.jsonl.gz",
)
NIVEL_MINIMO = 400
NIVEL_MAXIMO = 2500
# Nivel inicial según la respuesta a «¿Cuánto sabes de ajedrez?».
NIVELES_INICIALES = (600, 1000, 1400)
# Dificultad del reto del día.
DIA_MINIMO = 800
DIA_MAXIMO = 1300
# La racha empieza con problemas muy fáciles y cada acierto sube la dificultad.
RACHA_INICIO = 500
RACHA_SUBIDA = 60


class Tema(StrEnum):
	"""Temas de Lichess que usa MiAjedrezAccesible, en el orden en que se muestran."""

	MATE_EN_UNO = "mateIn1"
	MATE_EN_DOS = "mateIn2"
	MATE_DEL_PASILLO = "backRankMate"
	PIEZA_SIN_DEFENDER = "hangingPiece"
	ATAQUE_DOBLE = "fork"
	CLAVADA = "pin"
	DESCUBIERTA = "discoveredAttack"
	CORONACION = "promotion"
	AL_PASO = "enPassant"


def nombre_tema(tema: Tema) -> str:
	nombres = {
		# Translators: name of a puzzle theme.
		Tema.MATE_EN_UNO: _("Mate in one"),
		# Translators: name of a puzzle theme.
		Tema.MATE_EN_DOS: _("Mate in two"),
		# Translators: name of a puzzle theme: checkmate on the first or last rank.
		Tema.MATE_DEL_PASILLO: _("Back rank mate"),
		# Translators: name of a puzzle theme.
		Tema.PIEZA_SIN_DEFENDER: _("Undefended piece"),
		# Translators: name of a puzzle theme.
		Tema.ATAQUE_DOBLE: _("Double attack"),
		# Translators: name of a puzzle theme.
		Tema.CLAVADA: _("Pin"),
		# Translators: name of a puzzle theme.
		Tema.DESCUBIERTA: _("Discovered attack"),
		# Translators: name of a puzzle theme.
		Tema.CORONACION: _("Promotion"),
		# Translators: name of a puzzle theme.
		Tema.AL_PASO: _("En passant"),
	}
	return nombres[tema]


def explicacion_tema(tema: Tema) -> str:
	explicaciones = {
		# Translators: explanation of a puzzle theme.
		Tema.MATE_EN_UNO: _(
			"Find the move that gives checkmate right away. Look at every check you can give: "
			"one of them leaves the king with no escape. You learned it in lesson 16.",
		),
		# Translators: explanation of a puzzle theme.
		Tema.MATE_EN_DOS: _(
			"Checkmate in two moves of yours. The first move usually forces the reply: a check, "
			"or a threat the opponent must answer. Then comes the mate. You learned it in lessons 16 and 17.",
		),
		# Translators: explanation of a puzzle theme.
		Tema.MATE_DEL_PASILLO: _(
			"The king is shut in on its first row, behind its own pawns, and cannot get out. "
			"A rook or a queen that reaches that row gives checkmate. Look for the open row and for "
			"pieces that can no longer defend it.",
		),
		# Translators: explanation of a puzzle theme.
		Tema.PIEZA_SIN_DEFENDER: _(
			"There is a piece that nobody defends, or that is badly defended. Capture it without losing "
			"yours. You learned it in lessons 12 and 13: check who attacks and who defends.",
		),
		# Translators: explanation of a puzzle theme.
		Tema.ATAQUE_DOBLE: _(
			"One move that attacks two things at once: two pieces, or the king and a piece. "
			"The opponent can only save one. The knight is the specialist. You learned it in lesson 18.",
		),
		# Translators: explanation of the pin, a theme not covered by the lessons.
		Tema.CLAVADA: _(
			"A piece is pinned when it cannot move, or should not move, because it would leave a more "
			"valuable piece behind it exposed, usually the king. If the piece behind is the king, the "
			"pinned piece cannot move at all. Bishops, rooks and queens pin along their lines. "
			"To take advantage of a pin, attack the pinned piece again: it cannot run away.",
		),
		# Translators: explanation of the discovered attack, a theme not covered by the lessons.
		Tema.DESCUBIERTA: _(
			"In a discovered attack you move a piece out of the way and uncover the attack of a bishop, "
			"rook or queen behind it. One move creates two threats: the piece that moves and the piece "
			"that is uncovered. If the uncovered piece gives check, it is a discovered check, and it is "
			"very strong.",
		),
		# Translators: explanation of a puzzle theme.
		Tema.CORONACION: _(
			"A pawn can reach the last row and become a queen. Sometimes you first have to clear the way "
			"or win a tempo. You learned it in lesson 9.",
		),
		# Translators: explanation of a puzzle theme.
		Tema.AL_PASO: _(
			"The opponent just moved a pawn two squares and it landed beside yours: you can capture it "
			"en passant, only now. You learned it in lesson 20.",
		),
	}
	return explicaciones[tema]


def objetivo_tema(tema: Tema) -> str:
	"""Lo que se pide en un problema elegido por tema."""
	objetivos = {
		# Translators: goal of a puzzle chosen by theme.
		Tema.MATE_EN_UNO: _("Give checkmate in one move."),
		# Translators: goal of a puzzle chosen by theme.
		Tema.MATE_EN_DOS: _("Give checkmate in two moves."),
		# Translators: goal of a puzzle chosen by theme.
		Tema.MATE_DEL_PASILLO: _("Give checkmate on the back rank."),
		# Translators: goal of a puzzle chosen by theme.
		Tema.PIEZA_SIN_DEFENDER: _("Win a piece that is not well defended."),
		# Translators: goal of a puzzle chosen by theme.
		Tema.ATAQUE_DOBLE: _("Make a double attack."),
		# Translators: goal of a puzzle chosen by theme.
		Tema.CLAVADA: _("Take advantage of a pin."),
		# Translators: goal of a puzzle chosen by theme.
		Tema.DESCUBIERTA: _("Make a discovered attack."),
		# Translators: goal of a puzzle chosen by theme.
		Tema.CORONACION: _("Promote a pawn, or make it unstoppable."),
		# Translators: goal of a puzzle chosen by theme.
		Tema.AL_PASO: _("Use the en passant capture."),
	}
	return objetivos[tema]


# Lecciones del curso tras las que se recomienda un tema de Retos.
TEMA_DE_LECCION = {
	"9": Tema.CORONACION,
	"12": Tema.PIEZA_SIN_DEFENDER,
	"16": Tema.MATE_EN_UNO,
	"17": Tema.MATE_EN_DOS,
	"18": Tema.ATAQUE_DOBLE,
	"20": Tema.AL_PASO,
}


def sugerencia_de_leccion(id_leccion: str) -> str:
	"""Al terminar ciertas lecciones, recomienda el tema de Retos que las practica con problemas reales."""
	tema = TEMA_DE_LECCION.get(id_leccion)
	if tema is None:
		return ""
	# Translators: said at the end of some lessons, for example
	# 'You can now solve real puzzles in Challenges, theme "Double attack".'
	return _('You can now solve real puzzles in Challenges, theme "{theme}".').format(theme=nombre_tema(tema))


@dataclass(frozen=True)
class Problema:
	id: str
	fen: str
	# Jugadas en UCI: la primera es del rival; luego alternan quien resuelve y el rival.
	jugadas: tuple[str, ...]
	dificultad: int
	temas: tuple[Tema, ...]

	@property
	def jugadas_propias(self) -> int:
		return len(self.jugadas) // 2

	def tablero(self) -> chess.Board:
		return chess.Board(self.fen)


def cargar_problemas(ruta: str = RUTA_PROBLEMAS) -> list[Problema]:
	problemas = []
	with gzip.open(ruta, "rt", encoding="utf-8") as archivo:
		for linea in archivo:
			datos = json.loads(linea)
			problemas.append(
				Problema(
					id=datos["id"],
					fen=datos["fen"],
					jugadas=tuple(datos["jugadas"].split()),
					dificultad=int(datos["dificultad"]),
					temas=tuple(Tema(t) for t in datos["temas"] if t in Tema._value2member_map_),
				),
			)
	return problemas


def texto_color(color: chess.Color) -> str:
	if color == chess.WHITE:
		# Translators: start of a puzzle when the learner has the white pieces.
		return _("You play white.")
	# Translators: start of a puzzle when the learner has the black pieces.
	return _("You play black.")


def ejercicio_de_problema(problema: Problema, tema: Tema | None = None, ver_jugada: bool = True) -> Ejercicio:
	"""Convierte un problema en un ejercicio. Con `tema`, la instrucción dice qué hay que buscar."""
	tablero = problema.tablero()
	previa = chess.Move.from_uci(problema.jugadas[0])
	color = not tablero.turn
	partes = [
		texto_color(color),
		# Translators: in a puzzle, the opponent's move that has just been played.
		_("Your opponent just played: {move}").format(move=anunciador.describir_jugada(tablero, previa)),
	]
	if tema is not None:
		partes.append(objetivo_tema(tema))
	else:
		# Translators: goal of a puzzle whose theme is not said.
		partes.append(_("Find the best move."))
	propias = problema.jugadas_propias
	if propias > 1:
		# Translators: length of a puzzle solution, for example "The solution has 2 moves of yours."
		partes.append(
			ngettext(
				"The solution has {n} move of yours.",
				"The solution has {n} moves of yours.",
				propias,
			).format(
				n=propias,
			),
		)
	tema_pista = tema or (problema.temas[0] if problema.temas else None)
	pistas: tuple[str, ...] = ()
	if tema_pista is not None:
		# Translators: first hint of a puzzle, for example "Theme: Double attack. One move that attacks…"
		pistas = (
			_("Theme: {theme}. {explanation}").format(
				theme=nombre_tema(tema_pista),
				explanation=explicacion_tema(tema_pista),
			),
		)
	resto = problema.jugadas[1:]
	guion = tuple((resto[i], resto[i + 1] if i + 1 < len(resto) else None) for i in range(0, len(resto), 2))
	posicion, turno, enroques, al_paso = problema.fen.split()[:4]
	return Ejercicio(
		id=f"reto-{problema.id}",
		tipo=TipoEjercicio.PROBLEMA,
		posicion=posicion,
		instruccion=" ".join(partes),
		pistas=pistas,
		inicio=previa.to_square,
		enroques=enroques,
		al_paso=al_paso,
		turno=turno,
		jugada_previa=previa.uci(),
		guion=guion,
		ver_jugada=ver_jugada,
	)


def nuevo_nivel(nivel: int, dificultad: int, resuelto: bool, intentados: int) -> int:
	"""Actualización tipo Elo: sube más al resolver problemas difíciles y baja más al fallar fáciles."""
	k = 40 if intentados < 20 else 24
	esperado = 1 / (1 + 10 ** ((dificultad - nivel) / 400))
	valor = nivel + k * ((1 if resuelto else 0) - esperado)
	return max(NIVEL_MINIMO, min(NIVEL_MAXIMO, round(valor)))


class Retos:
	"""Elige problemas: a tu nivel, por tema, el del día y los de la racha."""

	def __init__(self, problemas: list[Problema]) -> None:
		self.problemas = sorted(problemas, key=lambda p: (p.dificultad, p.id))
		self.por_tema: dict[Tema, list[Problema]] = {t: [] for t in Tema}
		for problema in self.problemas:
			for tema in problema.temas:
				self.por_tema[tema].append(problema)
		self._del_dia = [p for p in self.problemas if DIA_MINIMO <= p.dificultad <= DIA_MAXIMO]

	def cerca_de(
		self,
		nivel: int,
		excluir: set[str],
		azar: random.Random,
		tema: Tema | None = None,
		margen: int = 100,
	) -> Problema:
		"""Un problema de dificultad parecida al nivel; si no quedan, se amplía el margen."""
		candidatos = self.por_tema[tema] if tema is not None else self.problemas
		while margen < 4000:
			cerca = [p for p in candidatos if abs(p.dificultad - nivel) <= margen and p.id not in excluir]
			if cerca:
				return azar.choice(cerca)
			margen *= 2
		# Todos vistos: se repite el más cercano.
		return min(candidatos, key=lambda p: abs(p.dificultad - nivel))

	def del_dia(self, fecha: datetime.date) -> Problema:
		"""El mismo problema para todo el mundo en la misma fecha."""
		return random.Random(fecha.toordinal()).choice(self._del_dia)

	def para_racha(self, aciertos: int, excluir: set[str], azar: random.Random) -> Problema:
		return self.cerca_de(RACHA_INICIO + RACHA_SUBIDA * aciertos, excluir, azar, margen=50)


class ProgresoRetos:
	"""Nivel, problemas resueltos, récord de racha y días seguidos. Se guarda en `retos.json`."""

	VERSION = 1

	def __init__(self, ruta: str) -> None:
		self.ruta = ruta
		self._valores_iniciales()
		self.cargar()

	def _valores_iniciales(self) -> None:
		self.nivel: int | None = None
		self.intentados = 0
		self.resueltos: set[str] = set()
		self.record_racha = 0
		# Fecha (ISO) del último reto del día jugado, si se resolvió, y días seguidos resolviéndolo.
		self.dia = ""
		self.dia_resuelto = False
		self.ultimo_dia_resuelto = ""
		self.dias_seguidos = 0
		# Tema → [resueltos, intentados].
		self.temas: dict[str, list[int]] = {}
		# Para las estadísticas: el nivel más alto alcanzado y la mejor serie de días seguidos.
		self.nivel_maximo: int | None = None
		self.mejor_dias_seguidos = 0

	def cargar(self) -> None:
		try:
			with open(self.ruta, encoding="utf-8") as archivo:
				datos = json.load(archivo)
		except (OSError, ValueError):
			return
		if not isinstance(datos, dict) or datos.get("version") != self.VERSION:
			return
		try:
			nivel = datos.get("nivel")
			self.nivel = int(nivel) if nivel is not None else None
			self.intentados = int(datos.get("intentados", 0))
			self.resueltos = {str(i) for i in datos.get("resueltos", [])}
			self.record_racha = int(datos.get("record_racha", 0))
			self.dia = str(datos.get("dia", ""))
			self.dia_resuelto = bool(datos.get("dia_resuelto", False))
			self.ultimo_dia_resuelto = str(datos.get("ultimo_dia_resuelto", ""))
			self.dias_seguidos = int(datos.get("dias_seguidos", 0))
			self.temas = {str(k): [int(v[0]), int(v[1])] for k, v in datos.get("temas", {}).items()}
			maximo = datos.get("nivel_maximo")
			self.nivel_maximo = int(maximo) if maximo is not None else None
			self.mejor_dias_seguidos = int(datos.get("mejor_dias_seguidos", self.dias_seguidos))
		except (TypeError, ValueError, IndexError, AttributeError):
			# Un archivo dañado no impide jugar: se empieza de cero.
			self._valores_iniciales()

	def guardar(self) -> None:
		os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
		temporal = self.ruta + ".tmp"
		with open(temporal, "w", encoding="utf-8") as archivo:
			json.dump(
				{
					"version": self.VERSION,
					"nivel": self.nivel,
					"intentados": self.intentados,
					"resueltos": sorted(self.resueltos),
					"record_racha": self.record_racha,
					"dia": self.dia,
					"dia_resuelto": self.dia_resuelto,
					"ultimo_dia_resuelto": self.ultimo_dia_resuelto,
					"dias_seguidos": self.dias_seguidos,
					"temas": self.temas,
					"nivel_maximo": self.nivel_mas_alto,
					"mejor_dias_seguidos": self.mejor_dias_seguidos,
				},
				archivo,
				ensure_ascii=False,
				indent=1,
			)
		os.replace(temporal, self.ruta)

	def registrar(self, problema: Problema, resuelto: bool, cambia_nivel: bool = True) -> int | None:
		"""Anota un problema resuelto o fallado. Devuelve el nivel nuevo, o None si no cambia."""
		if resuelto:
			self.resueltos.add(problema.id)
		for tema in problema.temas:
			datos = self.temas.setdefault(tema.value, [0, 0])
			datos[1] += 1
			if resuelto:
				datos[0] += 1
		nuevo = None
		if cambia_nivel and self.nivel is not None:
			nuevo = nuevo_nivel(self.nivel, problema.dificultad, resuelto, self.intentados)
			self.nivel = nuevo
			self.nivel_maximo = max(nuevo, self.nivel_maximo or 0)
		self.intentados += 1
		return nuevo

	def resueltos_de(self, tema: Tema) -> int:
		return self.temas.get(tema.value, [0, 0])[0]

	# Reto del día.

	def dia_jugado(self, fecha: datetime.date) -> bool:
		return self.dia == fecha.isoformat()

	def registrar_dia(self, fecha: datetime.date, resuelto: bool) -> None:
		"""Anota el reto del día; si ya se jugó hoy, solo cuenta si ahora se resuelve."""
		if self.dia_jugado(fecha) and (self.dia_resuelto or not resuelto):
			return
		self.dia = fecha.isoformat()
		self.dia_resuelto = resuelto
		if not resuelto:
			return
		ayer = (fecha - datetime.timedelta(days=1)).isoformat()
		self.dias_seguidos = self.dias_seguidos + 1 if self.ultimo_dia_resuelto == ayer else 1
		self.mejor_dias_seguidos = max(self.mejor_dias_seguidos, self.dias_seguidos)
		self.ultimo_dia_resuelto = fecha.isoformat()

	def dias_seguidos_hasta(self, fecha: datetime.date) -> int:
		"""Días seguidos con el reto del día resuelto; se pierden si ayer no se resolvió."""
		ayer = (fecha - datetime.timedelta(days=1)).isoformat()
		if self.ultimo_dia_resuelto in (fecha.isoformat(), ayer):
			return self.dias_seguidos
		return 0

	# Racha.

	@property
	def nivel_mas_alto(self) -> int | None:
		niveles = [n for n in (self.nivel, self.nivel_maximo) if n is not None]
		return max(niveles) if niveles else None

	def registrar_racha(self, aciertos: int) -> bool:
		"""Devuelve True si es un récord nuevo."""
		if aciertos > self.record_racha:
			self.record_racha = aciertos
			return True
		return False
