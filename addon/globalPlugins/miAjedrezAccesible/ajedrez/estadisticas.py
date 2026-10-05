# MiAjedrezAccesible: ajedrez accesible para NVDA.
# Copyright (C) 2026 Wilmer Rodríguez Vega <contacto@wilmer-rv.com>
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

"""Mis estadísticas: resultados de las partidas y resumen del curso y de los Retos.

Los resultados de las partidas se guardan en `partidas.json`. El curso y los Retos ya guardan
su propio progreso: aquí solo se resume.
"""

import json
import os

import chess

from .configuracion import ConfiguracionPartida
from .curso.modelo import Curso
from .curso.practica import TAMANO_RONDA
from .curso.progreso import Progreso
from .idioma import _, ngettext
from .partida import Motivo, Partida
from .retos import ProgresoRetos, Tema, nombre_tema

GANADAS, TABLAS, PERDIDAS = 0, 1, 2


class EstadisticasPartidas:
	VERSION = 1

	def __init__(self, ruta: str) -> None:
		self.ruta = ruta
		self._valores_iniciales()
		self.cargar()

	def _valores_iniciales(self) -> None:
		# Nivel de la computadora → [ganadas, tablas, perdidas].
		self.computadora: dict[int, list[int]] = {}
		self.dos_personas = 0
		self.perdidas_por_tiempo = 0

	def cargar(self) -> None:
		try:
			with open(self.ruta, encoding="utf-8") as archivo:
				datos = json.load(archivo)
		except (OSError, ValueError):
			return
		if not isinstance(datos, dict) or datos.get("version") != self.VERSION:
			return
		try:
			self.computadora = {
				int(nivel): [int(v) for v in valores][:3]
				for nivel, valores in datos.get("computadora", {}).items()
			}
			self.dos_personas = int(datos.get("dos_personas", 0))
			self.perdidas_por_tiempo = int(datos.get("perdidas_por_tiempo", 0))
		except (TypeError, ValueError, AttributeError):
			self._valores_iniciales()

	def guardar(self) -> None:
		os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
		temporal = self.ruta + ".tmp"
		with open(temporal, "w", encoding="utf-8") as archivo:
			json.dump(
				{
					"version": self.VERSION,
					"computadora": {str(n): v for n, v in sorted(self.computadora.items())},
					"dos_personas": self.dos_personas,
					"perdidas_por_tiempo": self.perdidas_por_tiempo,
				},
				archivo,
				indent=1,
			)
		os.replace(temporal, self.ruta)

	def registrar(
		self,
		partida: Partida,
		configuracion: ConfiguracionPartida,
		color_persona: chess.Color | None,
	) -> None:
		"""Anota una partida terminada."""
		resultado = partida.resultado_pgn
		if resultado == "*":
			return
		if color_persona is None:
			self.dos_personas += 1
			return
		if resultado == "1/2-1/2":
			indice = TABLAS
		elif (resultado == "1-0") == (color_persona == chess.WHITE):
			indice = GANADAS
		else:
			indice = PERDIDAS
		self.computadora.setdefault(configuracion.nivel, [0, 0, 0])[indice] += 1
		final = partida.final_acordado
		if indice == PERDIDAS and final is not None and final.motivo is Motivo.TIEMPO:
			self.perdidas_por_tiempo += 1

	@property
	def total_computadora(self) -> int:
		return sum(sum(v) for v in self.computadora.values())

	def nivel_mas_alto_ganado(self) -> int | None:
		ganados = [nivel for nivel, valores in self.computadora.items() if valores[GANADAS]]
		return max(ganados) if ganados else None


def _seccion_partidas(partidas: EstadisticasPartidas) -> list[str]:
	lineas = []
	total = partidas.total_computadora
	if total:
		ganadas, tablas, perdidas = (sum(v[i] for v in partidas.computadora.values()) for i in range(3))
		# Translators: summary of the games against the computer in the statistics.
		lineas.append(
			ngettext(
				"Against the computer: {n} game. Won {won}, drawn {drawn}, lost {lost}.",
				"Against the computer: {n} games. Won {won}, drawn {drawn}, lost {lost}.",
				total,
			).format(n=total, won=ganadas, drawn=tablas, lost=perdidas),
		)
		for nivel, (ganadas, tablas, perdidas) in sorted(partidas.computadora.items()):
			# Translators: results against one computer level in the statistics, for example
			# "Level 3: won 4, drawn 1, lost 2."
			lineas.append(
				_("Level {level}: won {won}, drawn {drawn}, lost {lost}.").format(
					level=nivel,
					won=ganadas,
					drawn=tablas,
					lost=perdidas,
				),
			)
		mejor = partidas.nivel_mas_alto_ganado()
		if mejor is not None:
			# Translators: in the statistics, the highest computer level beaten.
			lineas.append(_("Highest level you have beaten: {level}.").format(level=mejor))
		if partidas.perdidas_por_tiempo:
			# Translators: in the statistics, games lost on time against the computer.
			lineas.append(_("Lost on time: {n}.").format(n=partidas.perdidas_por_tiempo))
	if partidas.dos_personas:
		# Translators: in the statistics, finished games between two people.
		lineas.append(
			ngettext(
				"Between two people: {n} game.",
				"Between two people: {n} games.",
				partidas.dos_personas,
			).format(n=partidas.dos_personas),
		)
	if not lineas:
		# Translators: in the statistics, when no game has been finished yet.
		lineas.append(_("You have not finished any game yet."))
	return lineas


def _seccion_curso(curso: Curso, progreso: Progreso) -> list[str]:
	lecciones = [le for le in curso.lecciones if not le.extra]
	extras = [le for le in curso.lecciones if le.extra]
	completadas = [le for le in lecciones if progreso.leccion_completada(le)]
	lineas = [
		# Translators: in the statistics, lessons of the course completed, for example "Lessons completed: 15 of 23."
		_("Lessons completed: {done} of {total}.").format(done=len(completadas), total=len(lecciones)),
		# Translators: in the statistics, stars earned in the course, for example "Stars: 120 of 207."
		_("Stars: {stars} of {total}.").format(
			stars=sum(progreso.estrellas_de(le) for le in lecciones),
			total=sum(le.estrellas_posibles for le in lecciones),
		),
	]
	if extras:
		hechos = sum(1 for le in extras if progreso.leccion_completada(le))
		# Translators: in the statistics, extra lessons completed, for example "Extras completed: 1 of 1."
		lineas.append(_("Extras completed: {done} of {total}.").format(done=hechos, total=len(extras)))
	pendiente = next((le for le in lecciones if not progreso.leccion_completada(le)), None)
	if pendiente is None:
		# Translators: in the statistics, when the whole course is completed.
		lineas.append(_("You completed the whole course. Congratulations!"))
	else:
		# Translators: in the statistics, the next lesson to do, for example "Next lesson: 16, Checkmate."
		lineas.append(
			_("Next lesson: {number}, {title}.").format(number=pendiente.id, title=pendiente.titulo),
		)
	practicadas = [d["mejor"] for d in progreso.practica.values()]
	if practicadas:
		# Translators: in the statistics, how many lessons have been practiced and the best round, for example
		# "Lessons practiced: 5. Best practice round: 14 of 15 stars."
		lineas.append(
			_("Lessons practiced: {n}. Best practice round: {best} of {total} stars.").format(
				n=len(practicadas),
				best=max(practicadas),
				total=3 * TAMANO_RONDA,
			),
		)
	return lineas


def _seccion_retos(retos: ProgresoRetos) -> list[str]:
	if retos.nivel is None:
		# Translators: in the statistics, when the Challenges have not been started.
		return [_("You have not started the Challenges yet.")]
	lineas = [
		# Translators: in the statistics, the Challenges level, for example "Your level: 1050. Highest level: 1100."
		_("Your level: {level}. Highest level: {highest}.").format(
			level=retos.nivel,
			highest=retos.nivel_mas_alto,
		),
	]
	if retos.intentados:
		resueltos = min(len(retos.resueltos), retos.intentados)
		# Translators: in the statistics, puzzles solved at the first attempt, for example
		# "Puzzles solved at the first attempt: 30 of 40 (75%)."
		lineas.append(
			_("Puzzles solved at the first attempt: {solved} of {tried} ({percent}%).").format(
				solved=resueltos,
				tried=retos.intentados,
				percent=round(100 * resueltos / retos.intentados),
			),
		)
	for tema in Tema:
		resueltos_tema, intentados_tema = retos.temas.get(tema.value, [0, 0])
		if intentados_tema:
			# Translators: in the statistics, results of one puzzle theme, for example "Pin: 12 of 15."
			lineas.append(
				_("{theme}: {solved} of {tried}.").format(
					theme=nombre_tema(tema),
					solved=resueltos_tema,
					tried=intentados_tema,
				),
			)
	if retos.record_racha:
		# Translators: in the statistics, the best streak of puzzles in a row.
		lineas.append(_("Streak record: {n}.").format(n=retos.record_racha))
	if retos.mejor_dias_seguidos:
		# Translators: in the statistics, the best run of days with the daily challenge solved.
		lineas.append(
			ngettext(
				"Daily challenge: best run of {n} day in a row.",
				"Daily challenge: best run of {n} days in a row.",
				retos.mejor_dias_seguidos,
			).format(n=retos.mejor_dias_seguidos),
		)
	return lineas


def secciones(
	curso: Curso,
	progreso: Progreso,
	retos: ProgresoRetos,
	partidas: EstadisticasPartidas,
) -> list[tuple[str, list[str]]]:
	"""Las secciones de «Mis estadísticas»: (título, líneas)."""
	return [
		# Translators: heading of a section of the statistics.
		(_("Games"), _seccion_partidas(partidas)),
		# Translators: heading of a section of the statistics.
		(_("Learn to play"), _seccion_curso(curso, progreso)),
		# Translators: heading of a section of the statistics.
		(_("Challenges"), _seccion_retos(retos)),
	]
