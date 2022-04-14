import draughts
from draughts.engine import HubEngine, DXPEngine, CheckerBoardEngine, Limit, PlayResult

import pytest
import requests
import zipfile
import shutil
import os
import stat
import sys
import subprocess
import threading
import time
import random
from typing import Any, Optional
import logging
platform = sys.platform
file_extension = '.exe' if platform == 'win32' else ''

logger = logging.getLogger("pydraughts")
logger.setLevel(logging.DEBUG)


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
download_scan()
download_kr()
download_cake()
download_saltare()
download_kestog()


@pytest.mark.timeout(300, method="thread")
def test_hub_engines():
    if platform not in ['win32', 'linux', 'darwin']:
        assert True
        return
    hub = HubEngine([f'scan{file_extension}', 'hub'])
    hub.init()
    limit = Limit(10)
    game = draughts.Game()
    logger.info('Starting game 1')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move1: {len(game.move_stack)}')
        best_move = hub.play(game, limit, False)
        if best_move.move:
            game.push(best_move.move.board_move)
        else:
            break
    logger.info('Finished playing 1')
    hub.quit()
    logger.info('Quited hub 1')
    hub.kill_process()
    logger.info('Killed hub 1')
    
    hub = HubEngine([f'scan{file_extension}', 'hub'])
    hub.init()
    limit = Limit(10)
    game = draughts.Game()
    logger.info('Starting game 2')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move2: {len(game.move_stack)}')
        best_move = hub.play(game, limit, False)
        if best_move.move:
            game.push(best_move.move.board_move)
        else:
            break
    logger.info('Finished playing 2')
    hub.quit()
    logger.info('Quited hub 2')
    hub.kill_process()
    logger.info('Killed hub 2')


def _open_process(command: str, cwd: Optional[str] = None, shell: bool = True, _popen_lock: Any = threading.Lock()) -> subprocess.Popen:
    """Open the engine process."""
    kwargs = {
        "shell": shell,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "stdin": subprocess.PIPE,
        "bufsize": 1,  # Line buffered
        "universal_newlines": True,
    }
    logger.debug(f'command: {command}, cwd: {cwd}')

    if cwd is not None:
        kwargs["cwd"] = cwd

    # Prevent signal propagation from parent process
    try:
        # Windows
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    except AttributeError:
        # Unix
        kwargs["preexec_fn"] = os.setpgrp

    with _popen_lock:  # Work around Python 2 Popen race condition
        return subprocess.Popen(command, **kwargs)


@pytest.mark.timeout(300, method="thread")
def test_dxp_engines():
    if platform not in ['win32', 'linux', 'darwin']:
        assert True
        return
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False, 'ip': '127.0.0.1', 'port': 27531, 'wait_to_open_time': 10, 'max-moves': 100, 'initial-time': 30})
    game = draughts.Game()
    logger.info('Starting game 1')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move1: {len(game.move_stack)}')
        if len(game.move_stack) % 2 == 0:
            best_move = dxp.play(game)
        else:
            best_move = PlayResult(move=draughts.Move(board_move=random.choice(game.legal_moves()[0])))
        if best_move.move:
            game.push(best_move.move.board_move)
        else:
            break
    logger.info('Finished playing 1')
    dxp.quit()
    logger.info('Quited dxp 1')
    dxp.kill_process()
    logger.info('Killed dxp 1')

    engine = _open_process('"' + os.path.realpath(os.path.expanduser(f'scan{file_extension}')) + '" dxp', os.getcwd())
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': True}, initial_time=30)
    game = draughts.Game()
    logger.info('Starting game 2')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move2: {len(game.move_stack)}')
        if len(game.move_stack) % 2 == 1:
            best_move = dxp.play(game)
        else:
            best_move = PlayResult(move=draughts.Move(board_move=random.choice(game.legal_moves()[0])))
        if best_move.move:
            game.push(best_move.move.board_move)
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
    game = draughts.Game(variant='english')
    logger.info('Starting game 1')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move1: {len(game.move_stack)}')
        best_move = checkerboard.play(game, limit)
        if best_move.move:
            game.push(best_move.move.board_move)
        else:
            break
    logger.info('Finished playing 1')
    checkerboard.kill_process()

    checkerboard = CheckerBoardEngine('cake_189f.dll')
    limit = Limit(10)
    game = draughts.Game(variant='english')
    logger.info('Starting game 2')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move2: {len(game.move_stack)}')
        best_move = checkerboard.play(game, limit)
        if best_move.move:
            game.push(best_move.move.board_move)
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
    game = draughts.Game(variant='russian')
    logger.info('Starting game 1')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move1: {len(game.move_stack)}')
        best_move = checkerboard.play(game, limit)
        if best_move.move:
            game.push(best_move.move.board_move)
        else:
            break
    logger.info('Finished playing 1')
    checkerboard.kill_process()

    checkerboard = CheckerBoardEngine('kestog.dll')
    limit = Limit(10)
    game = draughts.Game(variant='russian')
    logger.info('Starting game 2')
    while not game.is_over() and len(game.move_stack) < 100:
        logger.info(f'move2: {len(game.move_stack)}')
        best_move = checkerboard.play(game, limit)
        if best_move.move:
            game.push(best_move.move.board_move)
        else:
            break
    logger.info('Finished playing 2')
    checkerboard.kill_process()


def test_engines():
    # Test ping and setoption
    hub = HubEngine([f'scan{file_extension}', 'hub'])
    hub.init()
    hub.ping()
    hub.setoption('book', True)
    hub.setoption('book', False)

    # Test searching and pondering
    thr = threading.Thread(target=hub.play, args=(draughts.Game(), Limit(time=1), True))
    thr.start()
    hub.ponderhit()
    thr.join()

    hub.go('startpos', '35-30', my_time=30, inc=2, moves_left=40)
    hub.go('startpos', '35-30', my_time=30, moves_left=40)
    hub.play(draughts.Game(fen='W:W22:B9,18'), Limit(depth=15, nodes=10000, movetime=10), False)
    time.sleep(0.01)
    hub.stop()
    hub.play(draughts.Game(fen='B:W22:B18'), Limit(depth=15, nodes=10000, movetime=10), False)
    hub.kill_process()
    
    if platform != 'win32':
        assert True
        return
    
    # Test movetime
    checkerboard = CheckerBoardEngine('cake_189f.dll')
    limit = Limit(movetime=2)
    game = draughts.Game(variant='english')
    checkerboard.play(game, limit)

    # Test setoption
    checkerboard.setoption('divide-time-by', 20)
    checkerboard.setoption('book', 2)
    checkerboard.kill_process()

    # Test send variant
    for variant in ('russian', 'brazilian', 'italian', 'english'):
        checkerboard = CheckerBoardEngine('cake_189f.dll')
        limit = Limit(movetime=2)
        game = draughts.Game(variant=variant)
        checkerboard.play(game, limit)
        checkerboard.kill_process()

    # Test time handling
    checkerboard = CheckerBoardEngine('cake_189f.dll')
    limit = Limit(time=-1, inc=-1)
    game = draughts.Game(variant=variant)
    checkerboard.play(game, limit)
    limit = Limit(time=-1, inc=2)
    game = draughts.Game(variant=variant)
    checkerboard.play(game, limit)
    limit = Limit(time=2, inc=-1)
    game = draughts.Game(variant=variant)
    checkerboard.play(game, limit)
    limit = Limit(time=328)
    game = draughts.Game(variant=variant)
    checkerboard.play(game, limit)
    limit = Limit(time=1, inc=33)
    game = draughts.Game(variant=variant)
    checkerboard.play(game, limit)
    limit = Limit(time=3277, inc=3277)
    game = draughts.Game(variant=variant)
    checkerboard.play(game, limit)
    checkerboard.kill_process()

    checkerboard = CheckerBoardEngine('./cake_189f.dll', checkerboard_timing=True)
    limit = Limit(time=0.1, inc=1)
    game = draughts.Game(variant=variant)
    checkerboard.play(game, limit)
    limit = Limit(time=0.9, inc=1)
    game = draughts.Game(variant=variant)
    checkerboard.play(game, limit)
    limit = Limit(time=2, inc=1)
    game = draughts.Game(variant=variant)
    checkerboard.play(game, limit)
    checkerboard.kill_process()
