from draughts import Game, Move
from draughts.PDN import PDNReader, PDNWriter

import requests
import zipfile
import os
import sys
import shutil
import logging
platform = sys.platform
file_extension = '.exe' if platform == 'win32' else ''

logger = logging.getLogger(__name__)


def download_games():
    response = requests.get('https://pdn.fmjd.org/_downloads/games.zip', allow_redirects=True)
    with open('./TEMP/games.zip', 'wb') as file:
        file.write(response.content)
    with zipfile.ZipFile('./TEMP/games.zip', 'r') as zip_ref:
        zip_ref.extractall('./games/')


if os.path.exists('TEMP'):
    shutil.rmtree('TEMP')
os.mkdir('TEMP')
download_games()


def test_pdn_reading():
    files = os.listdir('games/succeed')
    for file in files:
        filepath = os.path.realpath(f'games/succeed/{file}')
        games = PDNReader(filename=filepath)


def test_pdn_writing():
    filepath = os.path.realpath('games/succeed/mrcd2000kval.pdn')
    games = PDNReader(filename=filepath)
    one_game = games.games[1]
    moves = one_game.moves
    game = Game(variant='russian')
    for move in moves:
        for semi_move in Move(pdn_move=move, board=game, notation=0, variant=game.variant).board_move:
            game.move(semi_move)

    PDNWriter('pdn_writer.pdn', game, game_ending=one_game.game_ending)

    with open('pdn_writer.pdn') as file:
        data = file.read().split('\n')
    data = list(filter(lambda line: bool(line) and not line.startswith('['), data))
    moves = data[0]

    correct_moves = '1. c3-d4 f6-e5 2. d4xf6 g7xe5 3. b2-c3 h8-g7 4. g3-f4 e5xg3 5. h2xf4 g7-f6 6. a1-b2 b6-a5 7. e3-d4 d6-e5 8. f4xd6 c7xe5 9. d4-c5 b8-c7 10. d2-e3 e5-f4 11. e3xg5 h6xf4 12. c3-d4 c7-b6 13. c1-d2 f6-e5 14. d4xf6 e7xg5 15. f2-e3 b6xf2 16. e1xe5 a7-b6 17. e5-d6 f8-e7 18. d6xf8 b6-c5 19. f8xb4 a5xe1 20. g1-f2 e1xg3 0-1'
    assert moves == correct_moves
