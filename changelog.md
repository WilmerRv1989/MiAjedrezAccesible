## 1.0.0

First stable version. Everything from the beta versions, reviewed and tested on several computers:

* Games against the computer (Stockfish, 10 levels) and between two people, with an optional clock, saved and reviewed in PGN format.
* Learn to play: a guided course of 23 lessons, also designed for children, with endless practice and Extras.
* Challenges: 5,000 real puzzles from Lichess that adapt to your level.
* My statistics, a settings panel in NVDA's options and a list of keyboard shortcuts in every window.

Thanks to everyone who tested the beta versions.

## 0.9.1

* Keyboard shortcuts: a new item in the menu of the game, lesson, Challenges and review windows shows the keys of that window, with headings by section. Tools, MiAjedrezAccesible, Keyboard shortcuts shows all of them. The keys are read from NVDA, so the list includes your changes in Input gestures, and says when a command has no key.
* The command "Shows the keyboard shortcuts of this window" can be given a key in Input gestures.

## 0.9.0

* My statistics (Tools, MiAjedrezAccesible): games against the computer by level, games between two people and games lost on time; lessons completed, stars, next lesson and best practice round; Challenges level and highest level, puzzles solved at the first attempt, results by theme, streak record and best run of days. It opens in browse mode: press H to jump between sections, and it has Copy and Close buttons. Game results are counted from this version on.
* New panel in NVDA's settings (Preferences, Options, MiAjedrezAccesible): announce moves in words, in notation or both; say the square before the piece; play sounds; clock warnings; and delete your progress and statistics.

## 0.8.0

* Optional clock in the New game dialog: 30 minutes, 15 + 10, 10 + 5 or 5 + 3. Against the computer only your clock runs. F7 tells the time left, and warnings sound at 1 minute, 30 and 10 seconds. The clock stops while a menu or a dialog is open (including typing a move), and the game menu can pause it. Running out of time loses the game, or draws if the opponent cannot checkmate.
* Save game and Copy game in the game menu, in PGN format, the standard for chess programs. Games are saved in Documents, MiAjedrezAccesible.
* Open game in the add-on menu: an unfinished game of the add-on continues where it was left; a finished game, or any PGN game from elsewhere, opens for review, moving with Alt+Left and Alt+Right arrows, and Alt+Home and Alt+End.
* If NVDA closes during a game, the next time you start a game you are asked whether to continue it.

## 0.7.1

* Updated manual for the first test version: what the add-on includes and what is still missing, a new "Where to start" section, the Challenges keys in a table, and the full lesson menu.
* Neutral language in the Spanish manual.

## 0.7.0

* New Challenges (Tools, MiAjedrezAccesible, Challenges): 5,000 real puzzles from the Lichess puzzle database, short (at most three moves of yours) and mostly easy.
* The first time, a question sets your starting level (I am learning, I know how to play, I play well). After each puzzle your level goes up or down, like a rating.
* Four modes: Challenge at your level; By theme (mate in one, mate in two, back rank mate, undefended piece, double attack, pin, discovered attack, promotion and en passant), each with a short explanation; Daily challenge, the same for everyone each day, with days in a row; and Streak, puzzles in a row that get harder until the first mistake.
* Puzzles are played with white or black: with black, the board is seen from black's side.
* Hints with F6: the theme, then which piece to move, then the move (the puzzle then counts as failed). Any checkmate is accepted, even if it is not the move of the solution.
* Some lessons (9, 12, 16, 17, 18 and 20) now suggest the matching Challenges theme when finished.

## 0.6.1

* New "Extras" section at the end of the list of lessons, for optional content to keep practicing.
* Extra 1, "Play only by typing": every move is typed with J. Promotion (e8=Q), ambiguous moves (Nbd2), en passant (exd6), queenside castling, a mate in two, a short written game, and two blindfold mate challenges where the board does not tell which piece is on each square. Endless practice included.
* Lessons 22 and 23 now remind you that a whole game can be played by typing with J.

## 0.6.0

* The Learn to play course is complete: 23 lessons and 113 exercises in 5 blocks.
* Block D (Special rules): castling, en passant, and draws and stalemate.
* Block E (Let's play!): saying moves aloud in algebraic notation, the pawn war mini-game against the add-on itself, and your first game against the computer on level 1.
* Practice for every lesson of blocks D and E.

## 0.5.0

* Learn to play, block C (Fundamentals): 9 new lessons and 45 exercises about capturing, protecting, capturing safely, piece values, check, getting out of check, checkmate, mate with queen and king, and double attacks.
* New exercise types: one move with a goal (wrong moves are explained and taken back) and mate in two, where black defends with its best reply.
* Practice for every lesson of block C, generated and checked on the fly.

## 0.4.1

* "Practice" in the Learn to play course: rounds of 5 exercises created on the fly for every lesson, never repeated, with three levels that adapt to how well you do.
* Every practice exercise is solved before it is shown, so it is always possible and the stars are fair.

## 0.4.0

* New "Learn to play" course (Tools, MiAjedrezAccesible, Learn to play): 9 guided lessons and 47 exercises about the board and the pieces.
* Exercises to find squares, collect apples with a piece, capture pieces and promote, with hints (F6), up to three stars, and progress saved between sessions.
* Sounds generated by the add-on itself (no third-party audio).

## 0.3.1

* Levels 1 to 4 now make human-like mistakes on purpose, so beginners can win: against a simulated beginner the computer scores about 30 % on level 1, 55 % on level 2, 70 % on level 3 and almost 100 % on level 4.
* New tool herramientas/medir_niveles.py to measure the levels without playing.

## 0.3.0

* Play against the computer with Stockfish 19 and ten difficulty levels.
* New game dialog: mode, color (white, black or random) and level; it remembers the last choices.
* When playing black, the board is flipped and the computer opens the game.
* The computer's move is announced after yours, without cutting it off.
* L moves to the destination square of the last move.
* Control+Z against the computer undoes your move and its reply.
* Draw offers: the computer accepts when it is not winning by more than half a pawn.

## 0.2.1

* Escape only drops the selected piece; hiding the board is done from the game menu.

## 0.2.0

* Chess board for two people on the same computer, readable by speech and braille.
* Navigation with arrows, Home, End and rank numbers; jumps to pieces with the Spanish piece letters.
* Pick up and drop pieces, or type the move (Spanish or English algebraic notation, or coordinates).
* All chess rules: castling, en passant, promotion, check, checkmate and every kind of draw.
* Information keys: attackers and defenders, pieces of each side, square details, score sheet and game status.
* Game menu: flip board, draw by agreement, resign, new game, hide and close.
* Undo the last move.

## 0.1.0

* First development build: the MiAjedrezAccesible submenu is available under NVDA's Tools menu.
