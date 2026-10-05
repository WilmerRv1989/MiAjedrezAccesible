# MiAjedrezAccesible

Accessible chess for the NVDA screen reader.

MiAjedrezAccesible lets blind and visually impaired people of any age learn chess from scratch, practice with real puzzles and play against the computer or against another person, with every square of the board readable by speech and braille.

Manual en español: [addon/doc/es/readme.md](addon/doc/es/readme.md).

It is a new add-on for NVDA 2026.1 and later, inspired by [Chessmart](https://github.com/blindpandas/chessmart) by Blind Pandas, which no longer works with current NVDA versions.

## Current state

Version 1.0. It includes:

* **Games** against the computer, with ten difficulty levels, and between two people on the same computer, with an optional clock. Games can be saved, continued and reviewed.
* **Learn to play:** a guided course of 23 lessons, with endless practice and an Extras section. The course is currently available in Spanish only.
* **Challenges:** 5,000 real puzzles that adapt to your level.
* **My statistics** and a settings panel in NVDA's options.

Playing against another person over the Internet will be studied for future versions.

## Where to start

Everything opens from the NVDA menu (NVDA+N), Tools, MiAjedrezAccesible:

* If you have never played chess, start with **Learn to play**, from lesson 1.
* If you already know how the pieces move, try the **Challenges** or play a **New game** on levels 1 to 4.
* If you play well, raise the computer level and try the **Streak** in Challenges.

Progress in the course and in Challenges is saved automatically on your computer. The add-on does not need the Internet and does not send any data.

## Starting a game

1. Open the NVDA menu with NVDA+N.
2. Go to Tools, then MiAjedrezAccesible.
3. Choose "New game".
4. In the dialog, choose the mode (against the computer or two people on this computer), your color (white, black or random), the level and the clock.

The dialog remembers your last choices. The board opens with your pieces at the bottom and the focus on your king. If you play black, the computer moves first.

You can also assign a key to the "Opens the chess board" command in NVDA's Input gestures dialog, under the MiAjedrezAccesible category.

## Board keys

The piece letters follow the Spanish names: R king (rey), D queen (dama), T rook (torre), A bishop (alfil), C knight (caballo), P pawn (peón).

| Key | Action |
|---|---|
| Arrows | Move between squares |
| Home / End | First or last square of the row |
| 1 to 8 | Go to that rank, keeping the file |
| Enter or Space | Pick up the piece on the square; with a piece picked up, drop it here |
| R, D, T, A, C, P | Your next piece of that type |
| Shift + R, D, T, A, C, P | Same with the opponent's pieces |
| L | Go to the destination square of the last move |
| J | Type a move |
| X | Which pieces attack and defend this square |
| F1 / Shift+F1 | Your pieces / the opponent's pieces |
| F3 | Coordinate, color and content of the square |
| F4 | Score sheet |
| F5 | Whose turn it is, move number and last move |
| F7 | Time left on the clock |
| Control+Z | Undo the last move; against the computer, your move and its reply (asks for confirmation) |
| Applications or Shift+F10 | Game menu: flip board, draw by agreement, resign, pause clock, save game, copy game, new game, hide, close |
| Escape | Drop the selected piece without moving it |
| Alt+F4 | Close the board (asks for confirmation during a game) |

Between two people, "your pieces" are those of the side to move.

Can't remember a key? Choose Keyboard shortcuts in the menu of any board window (Applications key): it lists the keys of that window by section, as they are assigned in NVDA, including your changes in Input gestures. Tools, MiAjedrezAccesible, Keyboard shortcuts lists them all.

## Against the computer

The computer uses [Stockfish 19](https://stockfishchess.org), with levels 1 to 10: 1-2 learning the rules, 3-4 beginner, 5-6 intermediate, 7-8 advanced, 9-10 maximum. On levels 1 to 4 it makes human-like mistakes on purpose, so beginners can win. Its move is announced after yours, starting with "Computer:". It accepts a draw offer when it is not winning by more than half a pawn.

## Clock

The New game dialog offers an optional clock: 30 minutes, 15 minutes + 10 seconds per move, 10 + 5 or 5 + 3. Against the computer only your clock runs; between two people both do. F7 tells the time left, and a tone and a warning come at 1 minute, 30 seconds and 10 seconds. The clock stops while a menu or a dialog is open (including typing a move with J), and the game menu can pause it; it runs again when you move or resume it. Running out of time loses the game, or draws if the opponent cannot checkmate.

## Saving, opening and reviewing games

Save game and Copy game, in the game menu, use the standard PGN format; games are saved in Documents, MiAjedrezAccesible. Open game, in Tools, MiAjedrezAccesible, continues an unfinished game of the add-on with the same mode, level, color and clock, or opens a finished game, or any PGN game from elsewhere, for review: the board is read-only, Alt+Right and Alt+Left arrows move forward and back, Alt+Home and Alt+End go to the start or the end, and F4 shows the score sheet. If NVDA closes during a game, it is saved automatically, and the next time you start a game you are asked whether to continue it.

To play with someone far away in the meantime, play by correspondence: start a game between two people, make your move, save the game and send the file; the other person opens it with Open game, moves, saves and sends it back.

## My statistics

Tools, MiAjedrezAccesible, My statistics summarizes your games against the computer by level (counted from version 0.9.0), games between two people and games lost on time; your lessons, stars and next lesson; and your Challenges level, puzzles solved at the first attempt, results by theme, streak record and best run of days. It opens in browse mode (press H to jump between sections) and has Copy and Close buttons.

## Settings

In NVDA's menu, Preferences, Options, MiAjedrezAccesible: announce moves in words, in notation or both (castling is always said in words); say the square before the piece; play sounds; warn when little time is left on the clock; and delete your progress and statistics (asks for confirmation).

## Learn to play

A guided course for people who have never played chess, also designed for children (Tools, MiAjedrezAccesible, Learn to play). Block A teaches the board and the coordinates; block B, how each piece moves; block C, the fundamentals: capturing, protecting, piece values, check, checkmate and double attacks; block D, castling, en passant and draws; and block E, saying moves aloud, the pawn war mini-game and your first game against the computer. Lesson keys: F2 repeats the instruction, Shift+F2 the explanation, F6 gives a hint, M lists the apples left, F5 says which exercise you are on, Enter continues after an exercise, and Applications opens the lesson menu (restart exercise, skip exercise, practice more, back to the list, close). An Extras section at the end of the list holds optional content: Extra 1, Play only by typing, practices notation, a written game and blindfold mate challenges. Progress is saved automatically. The Practice button (or Practice more in the lesson menu) starts endless practice: rounds of 5 exercises created on the fly, with three levels that adapt to your results.

## Challenges

Real puzzles to practice (Tools, MiAjedrezAccesible, Challenges): 5,000 short puzzles from the Lichess puzzle database, mostly easy. Your opponent has just moved; find the best move, playing white or black. The first time, a question (I am learning, I know how to play, I play well) sets your starting level, which then goes up or down after each puzzle. Modes: Challenge at your level; By theme (mate in one, mate in two, back rank mate, undefended piece, double attack, pin, discovered attack, promotion, en passant), each with a short explanation; Daily challenge, with days in a row; and Streak, harder and harder puzzles until the first mistake. All board keys work in Challenges. Also:

| Key | Action |
|---|---|
| F2 | Repeat the puzzle: your color, your opponent's move and what to look for |
| Shift+F2 | Repeat the explanation (of the theme, if you chose one) |
| F6 | Hint: first the theme, then which piece to move, and finally the move (the puzzle then counts as failed) |
| F5 | Your level and the current puzzle |
| L | Go to the square of the last move |
| Enter | After solving a puzzle, go to the next one |
| Applications | Menu: restart puzzle, another puzzle, back to Challenges, close |

A wrong move is taken back and you can try again, but your level no longer goes up with that puzzle. Any checkmate is accepted, even if it is not the move of the solution. The daily challenge has no "Another puzzle", and in a streak, asking for another puzzle ends it.

## Typing moves

Press J on the board. Accepted: Spanish algebraic notation (Cf3, Axf7), the English letters N, B, Q and K (Nf3), coordinates (g1f3), castling (O-O, 0-0-0) and promotion (e8=D, e7e8d).

## How this add-on was made

MiAjedrezAccesible was born because I wanted people with visual impairments, and especially children who are learning, to be able to fully enjoy chess with NVDA. The idea came after trying several existing options and finding that none of them satisfied me in terms of native accessibility or the features I consider essential in an accessible game. This is my first published add-on for NVDA.

I developed it with the assistance of Claude, an artificial intelligence model by Anthropic. Claude wrote most of the code following my instructions, consulted the NVDA documentation and code, and suggested technical solutions. The direction and judgment were entirely mine: the functional design of the add-on, the sound experience, the behavior with the screen reader, the game mechanics and the dropping of unfeasible features.

Every version, feature, shortcut and spoken response was thoroughly tested and validated by me directly with NVDA. No feature made it into the final version without my review and approval.

I share this because I believe it is the honest thing to do. If you find a mistake, it is my responsibility, and writing to me helps me a lot to fix it.

## Author

Developed with love by Wilmer Rodríguez Vega ([wilmer-rv.com](https://wilmer-rv.com)).

To report a bug or suggest an improvement, write to contacto@wilmer-rv.com or open an issue on [the add-on's GitHub page](https://github.com/WilmerRv1989/MiAjedrezAccesible/issues).

MiAjedrezAccesible is licensed under the GPL 2 or later.

Includes:

* [python-chess](https://github.com/niklasf/python-chess) by Niklas Fiekas, licensed under the GPL 3 or later.
* [Stockfish 19](https://stockfishchess.org) by the Stockfish developers, licensed under the GPL 3. Source code: [github.com/official-stockfish/Stockfish, tag sf_19](https://github.com/official-stockfish/Stockfish/tree/sf_19).
* A selection of the [Lichess puzzle database](https://database.lichess.org/#puzzles), public domain (CC0). Prepared with `herramientas/preparar_problemas.py`.

## Building

Stockfish is not stored in git (the executable is larger than GitHub's 100 MB limit). Before building, run:

```
uv run python herramientas/obtener_stockfish.py
uv run scons
```

Nosce te ipsum.
