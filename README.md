# pydraughts
[![PyPI version](https://badge.fury.io/py/pydraughts.svg)](https://badge.fury.io/py/pydraughts) [![Tests](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/tests.yml/badge.svg)](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/tests.yml) [![Build](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/build.yml/badge.svg)](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/build.yml) [![CodeQL](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/AttackingOrDefending/pydraughts/actions/workflows/codeql-analysis.yml)

pydraughts is a draughts library for Python with move generation and engine communication. It is based on [ImparaAI/checkers](https://github.com/ImparaAI/checkers).

## Features

Note: White always starts. Black always has the squares starting from 1 (e.g. 1-20 in international draughts).

Variants:
* Standard (International)
* Frisian
* frysk!
* Antidraughts
* Breakthrough
* Russian
* Brazilian
* English/American
* Italian

Engine protocols:
* Hub
* DXP
* CheckerBoard
<br/></br>
* Import library
```python
from draughts import Game, Move
```
* Create a game
```python
game = Game(variant="standard", fen="startpos")
```
* Make a move
```python
game.move([34, 30])
```
* Get legal moves
```python
moves, captures = game.legal_moves()
```
* Convert move to other types
```python
move = Move(game, board_move=moves[0]).pdn_move
```
* Get fen
```python
fen = game.get_li_fen()
```
* Communicate with engines
```python
from draughts.engine import HubEngine, Limit
engine = HubEngine("scan.exe hub")
enigne.hub()
engine.init()
limit = Limit(time=10)
engine_move = engine.play(game, limit, ponder=False)
```

## Acknowledgements
Thanks to [RoepStoep](https://github.com/RoepStoep) for his [draughtsnet](https://github.com/RoepStoep/draughtsnet) which was modified to add support for Hub engines. Thanks to [akalverboer](https://github.com/akalverboer) for their [DXC100_draughts_client](https://github.com/akalverboer/DXC100_draughts_client) which was modified to add support for DXP engines.

## License
pydraughts is licensed under the GPL 3 (or any later version at your option). Check out LICENSE.txt for the full text.
The license of [ImparaAI/checkers](https://github.com/ImparaAI/checkers) is also present [here](ImparaAI%20checkers%20LICENSE).
