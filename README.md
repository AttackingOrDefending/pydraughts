# pydraughts
[![PyPI version](https://badge.fury.io/py/pydraughts.svg)](https://badge.fury.io/py/pydraughts) [![Tests](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/tests.yml/badge.svg)](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/tests.yml) [![Build](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/build.yml/badge.svg)](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/build.yml) [![CodeQL](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/codeql-analysis.yml) [![codecov](https://codecov.io/gh/AttackingOrDefending/pydraughts/branch/main/graph/badge.svg?token=ZSPXIVSAWN)](https://codecov.io/gh/AttackingOrDefending/pydraughts)

pydraughts is a draughts library for Python with move generation, PDN reading and writing, engine communication and balloted openings. It is based on [ImparaAI/checkers](https://github.com/ImparaAI/checkers).

Installing
----------

Download and install the latest release:

    pip install pydraughts

## Features

**Variants:**
* Standard (International)
* Frisian
* frysk!
* Antidraughts
* Breakthrough
* Russian
* Brazilian
* English/American
* Italian
* Turkish

**Engine protocols:**
* Hub
* DXP
* CheckerBoard

**PDN Reading and Writing**
<br/></br>
* Import pydraughts
```python
from draughts import Board, Move, WHITE, BLACK
```
* Create a game
```python
board = Board(variant="standard", fen="startpos")
```
* Make a move
```python
move = Move(board, steps_move=[34, 30])
board.push(move)

# Multi-capture
board2 = Board(fen="W:WK40:B19,29")
board2.push(Move(board2, pdn_move='40x14'))
```
* Get a visual representation of the board
```python
print(board)

"""
   | b |   | b |   | b |   | b |   | b 
---------------------------------------
 b |   | b |   | b |   | b |   | b |   
---------------------------------------
   | b |   | b |   | b |   | b |   | b 
---------------------------------------
 b |   | b |   | b |   | b |   | b |   
---------------------------------------
   |   |   |   |   |   |   |   |   |   
---------------------------------------
   |   |   |   |   |   |   |   | w |   
---------------------------------------
   | w |   | w |   | w |   |   |   | w 
---------------------------------------
 w |   | w |   | w |   | w |   | w |   
---------------------------------------
   | w |   | w |   | w |   | w |   | w 
---------------------------------------
 w |   | w |   | w |   | w |   | w |   
"""
```
* Get legal moves
```python
moves = board.legal_moves()
```
* Detect wins and draws
```python
has_white_won = board.winner() == WHITE
is_draw = board.winner() == 0
winnner = board.winner()
is_game_over = board.is_over()
```
* Convert move to other types
```python
move = Move(board, board_move=moves[0].board_move).pdn_move
```
* Get fen
```python
fen = game.fen
```
* Communicate with engines
```python
from draughts.engine import HubEngine, Limit
engine = HubEngine(["scan.exe", "hub"])
engine.init()
limit = Limit(time=10)
engine_move = engine.play(board, limit, ponder=False)
```
* Read PDN games
```python
from draughts.PDN import PDNReader
games = PDNReader(filename=filepath)
game = games.games[0]
moves = game.moves
```
* Write PDN games
```python
from draughts.PDN import PDNWriter
games = PDNWriter(filename=filepath, board=board)
```
* Get a ballot
```python
from draughts.ballots import Ballots
ballots = Ballots('english')
ballot1 = ballots.get_ballot()
ballot2 = ballots.get_ballot()
```

## Acknowledgements
Thanks to [fishnet](https://github.com/lichess-org/fishnet/tree/ebd2a5e16d37135509cbfbff9998e0b798866ef5) which was modified to add support for Hub engines. Thanks to [akalverboer](https://github.com/akalverboer) for their [DXC100_draughts_client](https://github.com/akalverboer/DXC100_draughts_client) which was modified to add support for DXP engines.

## License
pydraughts is licensed under The MIT License. Check out `LICENSE` for the full text.
The licenses of the other projects that pydraughts uses are in the `other_licenses` folder.
