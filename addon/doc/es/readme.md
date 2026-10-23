# MiAjedrezAccesible

Ajedrez accesible para el lector de pantalla NVDA.

MiAjedrezAccesible permite a personas ciegas y con baja visión, de cualquier edad, aprender ajedrez desde cero, practicar con problemas reales y jugar contra la computadora o contra otra persona, con cada casilla del tablero disponible por voz y en braille.

Es un complemento nuevo para NVDA 2026.1 y posteriores, inspirado en [Chessmart](https://github.com/blindpandas/chessmart), de Blind Pandas, que ya no funciona con las versiones actuales de NVDA.

## Estado actual

Versión 1.0. Incluye:

* **Partidas** contra la computadora, con diez niveles de dificultad, y entre dos personas en el mismo equipo, con reloj opcional. Las partidas se pueden guardar, continuar y repasar.
* **Aprender a jugar:** un curso guiado de 23 lecciones, con práctica sin fin y una sección de Extras.
* **Retos:** 5.000 problemas reales que se adaptan a tu nivel.
* **Mis estadísticas** y un panel de configuración en las opciones de NVDA.

En próximas versiones se estudiará jugar por Internet contra otra persona.

## Por dónde empezar

Todo se abre desde el menú de NVDA (NVDA+N), Herramientas, MiAjedrezAccesible:

* Si nunca has jugado al ajedrez, empieza por **Aprender a jugar**, desde la lección 1.
* Si ya sabes mover las piezas, prueba los **Retos** o juega una **Nueva partida** en los niveles 1 a 4.
* Si juegas bien, sube el nivel de la computadora y prueba la **Racha** de los Retos.

El progreso del curso y de los Retos se guarda solo, en tu equipo. El complemento no necesita Internet ni envía ningún dato.

## Empezar una partida

1. Abre el menú de NVDA con NVDA+N.
2. Ve a Herramientas y luego a MiAjedrezAccesible.
3. Elige «Nueva partida».
4. En el diálogo, elige el modo (contra la computadora o dos personas en este equipo), con qué color juegas (blancas, negras o al azar), el nivel y el reloj (sin reloj, si no quieres jugar con tiempo). Pulsa Aceptar.

El diálogo recuerda lo que elegiste la última vez, así que normalmente basta con pulsar Intro.

Se abre el tablero con tus piezas abajo y el foco en tu rey. Si juegas con negras, la computadora hace la primera jugada.

También puedes asignar una tecla a la orden «Abre el tablero de ajedrez» en el diálogo Gestos de entrada de NVDA, dentro de la categoría MiAjedrezAccesible. Esa tecla vuelve a la partida en curso o, si no hay ninguna, empieza una nueva.

## Qué se oye

* Casilla vacía: su coordenada, por ejemplo «e4».
* Casilla con pieza: la pieza y la coordenada, por ejemplo «Caballo blanco, g1».
* Con una pieza tomada, las casillas a las que puede ir dicen «posible» y suena un tono agudo.
* Después de cada jugada: la jugada completa, el jaque si lo hay y a quién le toca. Por ejemplo: «Caballo blanco de g1 a f3. Juegan negras.»
* Al terminar la partida: el motivo y el resultado, por ejemplo «Jaque mate. Ganan las blancas.» o «Tablas por ahogado.»
* Un tono grave indica que no se puede avanzar en esa dirección o que la acción no es posible.

## Teclas del tablero

| Tecla | Acción |
|---|---|
| Flechas | Moverse por las casillas |
| Inicio / Fin | Primera o última casilla de la fila |
| 1 a 8 | Ir a esa fila sin cambiar de columna |
| Intro o Espacio | Tomar la pieza de la casilla; con una pieza tomada, soltarla aquí |
| R, D, T, A, C, P | Ir a tu siguiente pieza de ese tipo: rey, dama, torre, alfil, caballo, peón |
| Mayúsculas + R, D, T, A, C, P | Lo mismo con las piezas del bando rival |
| L | Ir a la casilla de destino de la última jugada |
| J | Escribir una jugada |
| X | Qué piezas atacan y defienden esta casilla |
| F1 | Tus piezas |
| Mayúsculas+F1 | Piezas del bando rival |
| F3 | Coordenada, color y contenido de la casilla |
| F4 | Planilla con todas las jugadas |
| F5 | A quién le toca, número de jugada y última jugada |
| F7 | Tiempo que queda en el reloj |
| Control+Z | Deshacer la última jugada; contra la computadora, tu jugada y su respuesta (pide confirmación) |
| Aplicaciones o Mayúsculas+F10 | Menú de la partida |
| Escape | Soltar la pieza tomada sin moverla |
| Alt+F4 | Cerrar el tablero (si la partida está en curso, pide confirmación) |

Entre dos personas, «tus piezas» son las del bando al que le toca mover.

Todas estas teclas se pueden cambiar en Gestos de entrada, en la categoría MiAjedrezAccesible, mientras el foco está en el tablero.

**¿No recuerdas una tecla?** Abre el menú de la ventana (tecla Aplicaciones) y elige «Atajos de teclado»: verás las teclas de esa ventana, por secciones (pulsa H para saltar entre ellas). La lista se lee de NVDA, así que muestra las teclas que tengas asignadas, también si las cambiaste. En Herramientas, MiAjedrezAccesible, «Atajos de teclado» muestra las de todas las ventanas. También puedes asignar una tecla a la orden «Muestra los atajos de teclado de esta ventana» en Gestos de entrada.

## Aprender a jugar

Un curso guiado para quien nunca ha jugado al ajedrez, pensado también para la infancia. Ábrelo desde Herramientas, MiAjedrezAccesible, «Aprender a jugar».

El curso también está en inglés: aparece en inglés cuando NVDA está en un idioma distinto del español. En ese caso, las teclas de las piezas y la notación usan las letras inglesas (K rey, Q dama, R torre, B alfil, N caballo). Con NVDA en español, todo funciona como se explica en este manual.

Tiene cinco bloques, con 23 lecciones:

* **Bloque A. Conocer el tablero:** filas, columnas y coordenadas; diagonales y el centro; la posición inicial.
* **Bloque B. Las piezas:** la torre, el alfil, la dama, el rey, el caballo, y el peón con la coronación.
* **Bloque C. Fundamentos:** capturar, proteger, capturar sin perder la pieza, el valor de las piezas, el jaque, salir del jaque, el jaque mate, el mate con dama y rey, y el ataque doble.
* **Bloque D. Reglas especiales:** el enroque, la captura al paso, y las tablas y el ahogado.
* **Bloque E. ¡A jugar!:** decir las jugadas en voz alta (notación algebraica, con la tecla J), la guerra de peones, un minijuego contra el propio complemento, y tu primera partida contra la computadora en el nivel 1.

Cada lección empieza con una explicación corta y sigue con ejercicios en el mismo tablero de las partidas, con las mismas teclas. Hay ejercicios para encontrar casillas, recoger manzanas con una pieza, capturar peones y coronar. En el bloque C también hay ejercicios de una jugada con un objetivo (dar jaque, proteger una pieza, capturar sin perderla…): si la jugada no sirve, NVDA explica por qué y la deshace para que lo intentes otra vez. Y hay mates en dos jugadas, en los que las negras se defienden con su mejor respuesta. En los ejercicios de manzanas puedes ganar hasta tres estrellas si usas pocas jugadas. Nunca se pierde: cada ejercicio siempre se puede terminar.

Teclas propias de las lecciones:

| Tecla | Acción |
|---|---|
| F2 | Repetir la instrucción del ejercicio |
| Mayúsculas+F2 | Repetir la explicación de la lección |
| F6 | Pista: la primera ayuda un poco, la segunda casi da la respuesta |
| M | Cuántas manzanas quedan y dónde |
| F5 | En qué ejercicio estás y qué hay que hacer |
| Intro | Cuando termines un ejercicio, pasar al siguiente |
| Aplicaciones | Menú: reiniciar ejercicio, saltar ejercicio, practicar más, volver a la lista, cerrar |

### Extras

Al final de la lista de lecciones está la sección **Extras**: contenidos opcionales para seguir practicando, que no forman parte del curso.

* **Extra 1. Jugar solo escribiendo:** todas las jugadas se escriben con la tecla J; si intentas tomar una pieza con Intro, te lo recuerda. Practica la coronación (e8=D), la jugada ambigua (Cbd2), la captura al paso (exd6) y el enroque largo escritos, un mate en dos, una partida corta escrita en la que te dicen con palabras qué mover y tú lo escribes en notación, y dos retos «sin mirar»: el tablero no dice qué pieza hay en cada casilla y tienes que imaginar la posición.

### Practicar más

Para reforzar lo aprendido, cada lección tiene práctica sin fin: elige la lección en la lista y pulsa el botón «Practicar», o abre el menú de la lección con la tecla Aplicaciones y elige «Practicar más».

* La práctica va en rondas de 5 ejercicios creados en el momento. Nunca se repiten.
* Hay 3 niveles. Si en una ronda ganas 13 estrellas o más (de 15), la siguiente sube de nivel; si ganas 8 o menos, baja un nivel para practicar con calma.
* En los ejercicios de casillas, las estrellas dependen de los fallos y de las pistas; en los de piezas, de las jugadas.
* «Otro ejercicio», en el menú, cambia el ejercicio actual por uno nuevo del mismo nivel.

El progreso se guarda solo. En la lista de lecciones verás cuáles están completadas y cuántas estrellas ganaste, y la próxima lección pendiente aparece seleccionada.

## Retos

Problemas reales de ajedrez para practicar lo aprendido (Herramientas, MiAjedrezAccesible, Retos). Son 5.000 problemas de partidas jugadas en Lichess, cortos (como mucho tres jugadas tuyas) y en su mayoría fáciles.

En cada problema, tu rival acaba de mover y te toca: encuentra la mejor jugada. Al empezar se dice con qué color juegas y qué jugó tu rival, y el foco queda en la casilla de esa jugada. Si juegas con negras, el tablero se ve desde el lado de las negras. Si la solución tiene varias jugadas, tu rival responde después de cada acierto.

La primera vez se pregunta **¿Cuánto sabes de ajedrez?**: «Estoy aprendiendo», «Sé jugar» o «Juego bien». Esa respuesta es tu nivel inicial; después de cada problema, tu nivel sube si lo resuelves a la primera y baja si fallas, y los problemas se adaptan a ti.

Hay cuatro modos:

* **Reto a tu nivel:** problemas de dificultad parecida a tu nivel, sin repetir los que ya resolviste.
* **Por tema:** mate en una, mate en dos, mate del pasillo, pieza sin defender, ataque doble, clavada, ataque a la descubierta, coronación y captura al paso. Antes de empezar se explica el tema. La clavada y el ataque a la descubierta no están en las lecciones: su explicación te los enseña.
* **Reto del día:** el mismo problema para todo el mundo cada día. Si lo resuelves varios días seguidos, se cuentan los días. Solo el primer intento del día cambia tu nivel.
* **Racha:** problemas seguidos, cada uno un poco más difícil, hasta el primer fallo. Se guarda tu récord. En la racha, la pista no dice la jugada.

En los Retos funcionan todas las teclas del tablero. Además:

| Tecla | Acción |
|---|---|
| F2 | Repetir el problema: color, jugada de tu rival y qué hay que buscar |
| Mayúsculas+F2 | Repetir la explicación (la del tema, si elegiste uno) |
| F6 | Pista: primero el tema, luego qué pieza mover y, por último, la jugada (entonces el problema cuenta como fallado) |
| F5 | Tu nivel y el problema actual |
| L | Ir a la casilla de la última jugada |
| Intro | Cuando termines un problema, pasar al siguiente |
| Aplicaciones | Menú: reiniciar problema, otro problema, volver a Retos, cerrar |

Si haces una jugada equivocada, se deshace y puedes volver a intentarlo, pero tu nivel ya no sube con ese problema. Cualquier jaque mate vale, aunque no sea la jugada de la solución. En el reto del día no hay «Otro problema», y en la racha, pedir otro problema la termina.

Al terminar algunas lecciones (la 9, la 12, la 16, la 17, la 18 y la 20) se recomienda el tema de Retos que las practica con problemas reales.

## Escribir una jugada

Pulsa J en el tablero, escribe la jugada y pulsa Intro. Si la jugada no es válida, el campo se queda abierto y NVDA explica el motivo.

Se aceptan:

* Notación algebraica en español: Cf3, Axf7, Dd1, Tfe1, exd5.
* Las letras inglesas N, B, Q y K: Nf3, Bxf7. La R siempre es el rey.
* Coordenadas de origen y destino: g1f3 o g1-f3.
* Enroques: O-O y O-O-O, también con ceros (0-0).
* Coronación: e8=D, e8D o e7e8d. Si no indicas la pieza, se pregunta.
* Si dos piezas iguales pueden ir a la misma casilla, añade la columna o la fila de origen: Cbd2.

## Contra la computadora

La computadora usa [Stockfish 19](https://stockfishchess.org). Los niveles van del 1 al 10:

| Nivel | Para quién |
|---|---|
| 1 y 2 | Aprender las reglas |
| 3 y 4 | Principiante |
| 5 y 6 | Intermedio |
| 7 y 8 | Avanzado |
| 9 y 10 | Máximo |

* En los niveles 1 a 4 la computadora comete errores a propósito, como alguien que está aprendiendo: deja piezas sin proteger o no aprovecha capturas. En el nivel 1 lo normal es que ganes tú.
* Su jugada se anuncia después de la tuya, empezando por «Computadora:». Pulsa L para ir a la casilla donde movió.
* Mientras piensa puedes recorrer el tablero, pero no mover.
* Si ofreces tablas, las acepta cuando no va ganando por más de medio peón.

## Reloj

En el diálogo de nueva partida puedes elegir un reloj: 30 minutos, 15 minutos + 10 segundos por jugada, 10 + 5 o 5 + 3. Los segundos por jugada se suman a tu tiempo cada vez que juegas. Por defecto, la partida no tiene reloj.

* Contra la computadora solo corre tu reloj: la computadora juega igual que siempre.
* Entre dos personas corren los dos relojes, cada uno en su turno.
* F7 dice el tiempo que queda.
* Cuando queda 1 minuto, 30 segundos y 10 segundos, suena un tono y NVDA lo avisa.
* El reloj se detiene mientras hay un menú o un diálogo abierto, también mientras escribes una jugada con la tecla J. Además, puedes pausarlo desde el menú de la partida; vuelve a correr cuando juegas o cuando eliges «Reanudar reloj». Al ocultar el tablero también se pausa, y sigue al volver.
* Si se acaba tu tiempo, pierdes la partida. Pero si a tu rival no le queda material para dar jaque mate, son tablas.

## Menú de la partida

Con la tecla Aplicaciones o Mayúsculas+F10:

* Girar tablero: pone las negras abajo, o vuelve a poner las blancas.
* Tablas por acuerdo (entre dos personas): termina la partida en tablas si ambas aceptan. Contra la computadora se llama «Ofrecer tablas».
* Abandonar: contra la computadora abandonas tú; entre dos personas, el bando que mueve.
* Pausar reloj o Reanudar reloj (solo en partidas con reloj).
* Guardar partida y Copiar partida (ver «Guardar, abrir y repasar partidas»).
* Nueva partida.
* Ocultar tablero.
* Cerrar tablero.

## Guardar, abrir y repasar partidas

Las partidas se guardan en formato PGN, el estándar de los programas de ajedrez, así que también puedes abrirlas en otros programas o en Lichess.

* **Guardar partida**, en el menú de la partida, propone la carpeta Documentos, MiAjedrezAccesible y un nombre con la fecha y la hora.
* **Copiar partida** la copia al portapapeles, para pegarla, por ejemplo, en el análisis de Lichess.
* **Abrir partida**, en Herramientas, MiAjedrezAccesible:
  * Una partida sin terminar guardada por MiAjedrezAccesible continúa donde quedó, con el mismo modo, nivel, color y tiempo de reloj.
  * Una partida terminada, o cualquier partida en PGN de otro programa, se abre para **repasarla**.

En el repaso, el tablero es de solo lectura y funcionan todas las teclas para recorrerlo. Además:

| Tecla | Acción |
|---|---|
| Alt+flecha derecha | Siguiente jugada |
| Alt+flecha izquierda | Retroceder una jugada |
| Alt+Inicio / Alt+Fin | Ir al principio o al final de la partida |
| F5 | Cuántas jugadas llevas, a quién le toca y la última jugada |
| F4 | Planilla con todas las jugadas, con la actual seleccionada |
| Aplicaciones | Menú: girar tablero, ir al principio, ir al final, copiar partida, cerrar repaso |

Si NVDA se cierra o se reinicia durante una partida, la partida se guarda sola. La próxima vez que empieces una partida, se te preguntará si quieres continuarla o empezar una nueva.

### Jugar a distancia, por correspondencia

Mientras no haya juego por Internet, puedes jugar con alguien que esté lejos intercambiando el archivo de la partida:

1. Empieza una partida «Dos personas en este equipo», haz tu jugada y elige «Guardar partida» en el menú.
2. Envía el archivo por correo o por mensajería.
3. La otra persona lo abre con «Abrir partida...», hace su jugada, la guarda y te la devuelve.

## Ocultar y volver

La opción «Ocultar tablero» del menú de la partida oculta el tablero sin perder la partida. Para volver, abre Herramientas, MiAjedrezAccesible, «Volver a la partida». Esta opción solo aparece cuando hay un tablero oculto.

## Mis estadísticas

En Herramientas, MiAjedrezAccesible, «Mis estadísticas» resume lo que has hecho:

* **Partidas:** contra la computadora, cuántas ganaste, empataste y perdiste en cada nivel, y el nivel más alto al que has ganado; las partidas entre dos personas y las perdidas por tiempo. Las partidas se cuentan desde la versión 0.9.0.
* **Aprender a jugar:** lecciones completadas, estrellas, extras, la siguiente lección pendiente y tu mejor ronda de práctica.
* **Retos:** tu nivel y el más alto que alcanzaste, los problemas resueltos a la primera, los aciertos por tema, el récord de la racha y tu mejor serie de días seguidos con el reto del día.

Se abre en modo exploración: pulsa H para saltar de una sección a otra. Con el botón Copiar puedes pegarlas en un correo, por ejemplo para compartirlas con tu familia o tu docente.

## Opciones

En el menú de NVDA, Preferencias, Opciones, categoría MiAjedrezAccesible:

* **Anunciar las jugadas:** con palabras («Caballo blanco de g1 a f3»), en notación («Cf3») o de las dos formas. Los enroques se dicen siempre con palabras.
* **Decir la casilla antes que la pieza:** al recorrer el tablero se oye «g1, caballo blanco» en lugar de «Caballo blanco, g1».
* **Reproducir sonidos:** los de las manzanas, los aciertos y las lecciones. Los tonos de aviso y de error suenan siempre.
* **Avisar cuando quede poco tiempo en el reloj.**
* **Borrar mi progreso y estadísticas:** borra el progreso del curso y de los Retos y las estadísticas de partidas, por ejemplo cuando el equipo pasa a otra persona. Pide confirmación y no se puede deshacer.

## Sobre cómo se hizo este complemento

MiAjedrezAccesible nació porque quería que las personas con discapacidad visual, y en especial niñas y niños que están aprendiendo, pudieran jugar ajedrez de forma plena con NVDA. La idea surgió tras probar diversas opciones existentes y notar que ninguna me satisfacía en materia de accesibilidad nativa ni en las características que considero indispensables en un juego accesible. Este es mi primer complemento publicado para NVDA.

Lo desarrollé con la asistencia de Claude, un modelo de inteligencia artificial de Anthropic. Claude escribió la mayor parte del código siguiendo mis indicaciones, consultó la documentación y el código de NVDA y me propuso soluciones técnicas. La dirección y el criterio fueron enteramente míos: el diseño funcional del complemento, la experiencia sonora, el comportamiento con el lector de pantalla, las mecánicas de juego y el descarte de características inviables.

Cada versión, función, atajo y respuesta de voz fue probada minuciosamente y validada por mí directamente con NVDA. Ninguna función llegó a la versión final sin mi revisión y aprobación.

Lo cuento porque creo que es lo honesto. Si encuentras un error, la responsabilidad es mía, y me ayudas mucho si me escribes para corregirlo.

## Autoría

Desarrollado con amor por Wilmer Rodríguez Vega ([wilmer-rv.com](https://wilmer-rv.com)).

Para reportar un error o proponer una mejora, escríbeme a contacto@wilmer-rv.com o abre un reporte en [la página de GitHub del complemento](https://github.com/WilmerRv1989/MiAjedrezAccesible/issues).

MiAjedrezAccesible se distribuye con la licencia GPL 2 o posterior.

Incluye:

* [python-chess](https://github.com/niklasf/python-chess), de Niklas Fiekas, con licencia GPL 3 o posterior.
* [Stockfish 19](https://stockfishchess.org), de los desarrolladores de Stockfish, con licencia GPL 3. Su código fuente está en [github.com/official-stockfish/Stockfish, versión sf_19](https://github.com/official-stockfish/Stockfish/tree/sf_19).
* Una selección de la [base de datos de problemas de Lichess](https://database.lichess.org/#puzzles), de dominio público (CC0). Gracias a Lichess y a sus jugadores.

Nosce te ipsum.
