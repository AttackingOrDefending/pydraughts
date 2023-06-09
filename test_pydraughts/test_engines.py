import draughts
from draughts.engine import HubEngine, DXPEngine, CheckerBoardEngine, Limit, PlayResult

import pytest
import requests
import zipfile
import shutil
import os
import stat
import sys
import threading
import random
import time
import logging
platform = sys.platform
file_extension = '.exe' if platform == 'win32' else ''

logging.basicConfig()
logger = logging.getLogger("pydraughts")
logger.setLevel(logging.DEBUG)


def random_move_engine(game):
    return PlayResult(move=random.choice(game.legal_moves()))


def download_scan():
    windows_linux_mac = ''
    if platform == 'linux':
        windows_linux_mac = '_linux'
    elif platform == 'darwin':
        windows_linux_mac = '_mac'
    response = requests.get('https://hjetten.home.xs4all.nl/scan/scan_31.zip', allow_redirects=True)
    with open('./TEMP/scan_zip.zip', 'wb') as file:
        file.write(response.content)
    with zipfile.ZipFile('./TEMP/scan_zip.zip', 'r') as zip_ref:
        zip_ref.extractall('./TEMP/')
    shutil.copyfile(f'./TEMP/scan_31/scan{windows_linux_mac}{file_extension}', f'scan{file_extension}')
    shutil.copyfile('./TEMP/scan_31/scan.ini', 'scan.ini')
    with open('scan.ini') as file:
        options = file.read()
    options = options.replace('book = true', 'book = false')
    with open('scan.ini', 'w') as file:
        file.write(options)
    if os.path.exists('data'):
        shutil.rmtree('data')
    shutil.copytree('./TEMP/scan_31/data', 'data')
    if windows_linux_mac != "":
        st = os.stat(f'scan{file_extension}')
        os.chmod(f'scan{file_extension}', st.st_mode | stat.S_IEXEC)


def download_kr():
    headers = {'User-Agent': 'User Agent', 'From': 'mail@mail.com'}
    response = requests.get('http://edgilbert.org/InternationalDraughts/downloads/kr_hub_163.zip', headers=headers, allow_redirects=True)
    with open('./TEMP/kr_zip.zip', 'wb') as file:
        file.write(response.content)
    with zipfile.ZipFile('./TEMP/kr_zip.zip', 'r') as zip_ref:
        zip_ref.extractall('./TEMP/')
    shutil.copyfile('./TEMP/kr_hub.exe', 'kr_hub.exe')
    shutil.copyfile('./TEMP/kr_hub.ini', 'kr_hub.ini')
    shutil.copyfile('./TEMP/KingsRow.odb', 'KingsRow.odb')
    shutil.copyfile('./TEMP/weights.bin', 'weights.bin')


def download_cake():
    headers = {'User-Agent': 'User Agent', 'From': 'mail@mail.com'}
    response = requests.get('http://www.fierz.ch/cake_189f.zip', headers=headers)
    with open('./TEMP/cake_zip.zip', 'wb') as file:
        file.write(response.content)
    with zipfile.ZipFile('./TEMP/cake_zip.zip', 'r') as zip_ref:
        zip_ref.extractall('./TEMP/')
    shutil.copyfile('./TEMP/cake_189f.dll', 'cake_189f.dll')
    shutil.copyfile('./TEMP/egdb64.dll', 'egdb64.dll')
    shutil.copyfile('./TEMP/book.bin', 'book.bin')


def download_saltare():
    headers = {'User-Agent': 'User Agent', 'From': 'mail@mail.com'}
    response = requests.get('http://www.fierz.ch/saltare.zip', headers=headers)
    with open('./TEMP/saltare_zip.zip', 'wb') as file:
        file.write(response.content)
    with zipfile.ZipFile('./TEMP/saltare_zip.zip', 'r') as zip_ref:
        zip_ref.extractall('./TEMP/')
    shutil.copyfile('./TEMP/saltare.dll', 'saltare.dll')


def download_kestog():
    headers = {'User-Agent': 'User Agent', 'From': 'mail@mail.com'}
    response = requests.get('http://www.fierz.ch/KestoG.zip', headers=headers)
    with open('./TEMP/kestog_zip.zip', 'wb') as file:
        file.write(response.content)
    with zipfile.ZipFile('./TEMP/kestog_zip.zip', 'r') as zip_ref:
        zip_ref.extractall('./TEMP/')
    shutil.copyfile('./TEMP/KestoG.dll', 'kestog.dll')


if os.path.exists('TEMP'):
    shutil.rmtree('TEMP')
os.mkdir('TEMP')
download_functions = [download_scan, download_kr, download_cake, download_saltare, download_kestog]
for downloader in download_functions:
    try:
        downloader()
    except Exception:
        downloader()  # Attempt to download twice if there are problems.


@pytest.mark.timeout(300, method="thread")
def test_hub_engines():
    if platform not in ['win32', 'linux', 'darwin']:
        assert True
        return
    hub = HubEngine([f'scan{file_extension}', 'hub'])
    hub.init()
    limit = Limit(5, 0.2)
    game = draughts.Board()
    logger.info('Starting game 1')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move1: {len(game.move_stack)}')
        best_move = hub.play(game, limit, False)
        if best_move.move:
            game.push(best_move.move)
        else:
            break
    logger.info('Finished playing 1')
    hub.quit()
    logger.info('Quited hub 1')
    hub.kill_process()
    logger.info('Killed hub 1')

    hub = HubEngine([f'scan{file_extension}', 'hub'])
    hub.init()
    limit = Limit(5)
    game = draughts.Board()
    logger.info('Starting game 2')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move2: {len(game.move_stack)}')
        best_move = hub.play(game, limit, False)
        if best_move.move:
            game.push(best_move.move)
        else:
            break
    logger.info('Finished playing 2')
    hub.quit()
    logger.info('Quited hub 2')
    hub.kill_process()
    logger.info('Killed hub 2')


@pytest.mark.timeout(300, method="thread")
def test_dxp_engines():
    if platform not in ['win32', 'linux']:
        assert True
        return
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False, 'ip': '127.0.0.1', 'port': 27531, 'wait-to-open-time': 10, 'max-moves': 100, 'initial-time': 30})
    game = draughts.Board()
    logger.info('Starting game 1')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move1: {len(game.move_stack)}')
        if len(game.move_stack) % 2 == 0:
            best_move = dxp.play(game)
        else:
            best_move = random_move_engine(game)
        if best_move.move:
            game.push(best_move.move)
        else:
            break
    logger.info('Finished playing 1')
    dxp.quit()
    logger.info('Quited dxp 1')
    dxp.kill_process()
    logger.info('Killed dxp 1')

    time.sleep(20)

    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    game = draughts.Board()
    logger.info('Starting game 2')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move2: {len(game.move_stack)}')
        if len(game.move_stack) % 2 == 1:
            best_move = dxp.play(game)
        else:
            best_move = random_move_engine(game)
        if best_move.move:
            game.push(best_move.move)
        else:
            break
    logger.info('Finished playing 2')
    dxp.quit()
    logger.info('Quited dxp 2')
    dxp.kill_process()
    logger.info('Killed dxp 2')


@pytest.mark.timeout(300, method="thread")
def test_checkerboard_engines():
    if platform != 'win32':
        assert True
        return
    checkerboard = CheckerBoardEngine('cake_189f.dll')
    limit = Limit(10, 2)
    game = draughts.Board(variant='english')
    logger.info('Starting game 1')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move1: {len(game.move_stack)}')
        best_move = checkerboard.play(game, limit)
        if best_move.move:
            game.push(best_move.move)
        else:
            break
    logger.info('Finished playing 1')
    checkerboard.kill_process()

    checkerboard = CheckerBoardEngine('cake_189f.dll')
    limit = Limit(10)
    game = draughts.Board(variant='english')
    logger.info('Starting game 2')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move2: {len(game.move_stack)}')
        best_move = checkerboard.play(game, limit)
        if best_move.move:
            game.push(best_move.move)
        else:
            break
    logger.info('Finished playing 2')
    checkerboard.kill_process()


@pytest.mark.timeout(300, method="thread")
def test_russian_checkerboard_engines():
    if platform != 'win32':
        assert True
        return
    checkerboard = CheckerBoardEngine('kestog.dll')
    limit = Limit(10, 2)
    game = draughts.Board(variant='russian')
    logger.info('Starting game 1')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move1: {len(game.move_stack)}')
        best_move = checkerboard.play(game, limit)
        if best_move.move:
            game.push(best_move.move)
        else:
            break
    logger.info('Finished playing 1')
    checkerboard.kill_process()

    checkerboard = CheckerBoardEngine('kestog.dll')
    limit = Limit(10)
    game = draughts.Board(variant='russian')
    logger.info('Starting game 2')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move2: {len(game.move_stack)}')
        best_move = checkerboard.play(game, limit)
        if best_move.move:
            game.push(best_move.move)
        else:
            break
    logger.info('Finished playing 2')
    checkerboard.kill_process()


@pytest.mark.timeout(300, method="thread")
def test_engines():
    # Test ping and setoption
    hub = HubEngine([f'scan{file_extension}', 'hub'])
    hub.init()
    hub.ping()
    hub.configure({'book': True})
    hub.setoption('book', False)

    # Test searching and pondering
    thr = threading.Thread(target=hub.play, args=(draughts.Board(), Limit(time=1), True))
    thr.start()
    hub.ponderhit()
    thr.join()

    hub.go('W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20', '35-30', my_time=30, inc=2, moves_left=40)
    hub.go('W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20', '35-30', my_time=30, moves_left=40)
    hub.play(draughts.Board(fen='W:W22:B9,18'), Limit(movetime=10), False)
    hub.play(draughts.Board(fen='B:W22:B18'), Limit(nodes=10000), False)
    hub.play(draughts.Board(fen='B:W22:B18'), Limit(depth=15), False)
    hub.stop()
    hub.play(draughts.Board(fen='W:WK34:B9,18'), Limit(time=10), False)
    hub.play(draughts.Board(fen='B:WK34:B9,18'), Limit(time=10), False)
    hub.quit()
    hub.kill_process()

    # options is None
    dxp = DXPEngine(None, None, initial_time=30)
    dxp.sender.chat("chat")
    try:
        dxp.sender.backreq()
        assert False
    except NotImplementedError:
        assert True
    dxp.quit()

    if platform != 'win32':
        assert True
        return

    # Test movetime
    checkerboard = CheckerBoardEngine('cake_189f.dll')
    limit = Limit(movetime=2)
    game = draughts.Board(variant='english')
    checkerboard.play(game, limit)

    # Test setoption
    checkerboard.configure({'divide-time-by': 20})
    checkerboard.setoption('book', 2)
    checkerboard.kill_process()

    # Test send variant
    for variant in ('russian', 'brazilian', 'italian', 'english'):
        checkerboard = CheckerBoardEngine('cake_189f.dll')
        limit = Limit(movetime=2)
        game = draughts.Board(variant=variant)
        checkerboard.play(game, limit)
        checkerboard.kill_process()

    # Test time handling
    checkerboard = CheckerBoardEngine('cake_189f.dll')
    limit = Limit(time=-1, inc=-1)
    game = draughts.Board(variant='english')
    checkerboard.play(game, limit)
    limit = Limit(time=-1, inc=2)
    game = draughts.Board(variant='english')
    checkerboard.play(game, limit)
    limit = Limit(time=2, inc=-1)
    game = draughts.Board(variant='english')
    checkerboard.play(game, limit)
    limit = Limit(time=328)
    game = draughts.Board(variant='english')
    checkerboard.play(game, limit)
    limit = Limit(time=1, inc=33)
    game = draughts.Board(variant='english')
    checkerboard.play(game, limit)
    limit = Limit(time=6555, inc=6555)
    game = draughts.Board(variant='english')
    checkerboard.play(game, limit)
    checkerboard.kill_process()

    checkerboard = CheckerBoardEngine('./cake_189f.dll', checkerboard_timing=True)
    limit = Limit(time=0.1, inc=1)
    game = draughts.Board(variant='english')
    checkerboard.play(game, limit)
    limit = Limit(time=0.9, inc=1)
    game = draughts.Board(variant='english')
    checkerboard.play(game, limit)
    limit = Limit(time=2, inc=1)
    game = draughts.Board(variant='english')
    checkerboard.play(game, limit)

    # gamehist longer than 256 characters
    game = draughts.Board('english', 'W:WK30:BK4')
    for _ in range(65):
        game.push(draughts.Move(steps_move=[30, 26]))
        game.push(draughts.Move(steps_move=[4, 8]))
        game.push(draughts.Move(steps_move=[26, 30]))
        game.push(draughts.Move(steps_move=[8, 4]))
    limit = Limit(time=10)
    checkerboard.play(game, limit)

    # Test CheckerBoardEngine()._row_col_to_num()
    game = draughts.Board('english')
    assert checkerboard._row_col_to_num(game, 0, 2) == 30
    game = draughts.Board('russian')
    assert checkerboard._row_col_to_num(game, 1, 5) == 6
    checkerboard.kill_process()
