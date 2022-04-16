from draughts.engines.dxp_communication import dxp_run
from draughts.engines.dxp_communication.dxp_classes import DamExchange
from draughts.engine import DXPEngine
from importlib import reload
from draughts import Game
import time
import sys
import logging
platform = sys.platform
file_extension = '.exe' if platform == 'win32' else ''

logging.basicConfig()
logger = logging.getLogger("pydraughts")
logger.setLevel(logging.DEBUG)


def test_console_handler():
    global dxp_run

    dxp_run = reload(dxp_run)
    tConsoleHandler = dxp_run.ConsoleHandler()
    # conn (number of commands = 2) & Error trying to connect: connection exception: failed to connect
    tConsoleHandler.run_command('conn 127.0.0.1')
    # chat (number of commands > 1) & Error sending chat message: send exception: no connection
    tConsoleHandler.run_command('chat message')
    # gamereq (number of commands = 2) & Error sending game request: send exception: no connection
    tConsoleHandler.run_command('gamereq W')


def test_console_handler_with_dxp_engine():
    if platform not in ['win32', 'linux', 'darwin']:
        assert True
        return
    # BACKREQ Not yet supported
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    game = Game()
    dxp.play(game)
    dxp.console.run_command('backreq')
    # Game started; setup not allowed
    dxp.console.run_command('setup')
    # Game already started; gamereq not allowed
    dxp.console.run_command('gamereq')
    # GAMEEND (number of commands = 1)
    dxp.console.run_command('gameend')
    # Already connected
    dxp.console.run_command('conn')
    # CHAT
    dxp.console.run_command('chat MESSAGE')
    # BACKREQ
    dxp.console.run_command('backreq')
    dxp.quit()
    dxp.kill_process()

    # terminate program (doesn't do anything) & setup (number of commands = 1)
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    dxp.console.run_command('setup')
    dxp.console.run_command('q')
    dxp.quit()
    dxp.kill_process()

    # setup (number of commands = 2)
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    dxp.console.run_command(f'setup {Game().get_dxp_fen()}')
    dxp.quit()
    dxp.kill_process()

    # setup (number of commands > 3)
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    dxp.console.run_command(f'setup {Game().get_dxp_fen()} {Game().variant} extra')
    dxp.quit()
    dxp.kill_process()

    # conn (number of commands = 2)
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    dxp.console.run_command('conn 127.0.0.1')
    dxp.quit()
    dxp.kill_process()

    # conn (number of commands = 1)
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    dxp.console.run_command('conn')
    # chat (number of commands = 1)
    dxp.console.run_command('chat')
    # chat (number of commands > 1)
    dxp.console.run_command('chat message')
    dxp.quit()
    dxp.kill_process()

    # gamereq (number of commands = 2)
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    dxp.console.run_command('conn')
    dxp.console.run_command('gamereq W')
    dxp.quit()
    dxp.kill_process()

    # gamereq (number of commands = 3)
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    dxp.console.run_command('conn')
    dxp.console.run_command('gamereq B 100')
    dxp.quit()
    dxp.kill_process()

    # gamereq (number of commands = 3)
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    dxp.console.run_command('conn')
    dxp.console.run_command('gamereq W 100')
    # Game already finished; gameend not allowed
    time.sleep(2)
    dxp.console.run_command('gameend')
    dxp.console.run_command('gameend')
    dxp.quit()
    dxp.kill_process()

    # Game not started; backreq not allowed
    dxp = DXPEngine([f'scan{file_extension}', 'dxp'], {'engine-opened': False}, initial_time=30)
    dxp.console.run_command('backreq')
    # Command unknown
    dxp.console.run_command('random-command')
    dxp.quit()
    dxp.kill_process()


def test_dam_exchange():
    dam_exchange = DamExchange()

    assert dam_exchange.parse('CMESSAGE') == {'type': 'C', 'text': 'MESSAGE'}  # CHAT
    assert dam_exchange.parse('B001W') == {'type': 'B', 'moveId': '001', 'mColor': 'W'}  # BACKREQ
    assert dam_exchange.parse('K1') == {'type': 'K', 'accCode': '1'}  # BACKACC
    assert dam_exchange.parse('P0') == {'type': '?'}  # Unknown
    assert dam_exchange.parse('E11') == {'type': 'E', 'reason': '1', 'stop': '1'}  # GAMEEND
    assert dam_exchange.parse('ANAME                            1') == {'type': 'A', 'engineName': 'NAME', 'accCode': '1'}  # GAMEACC
    assert dam_exchange.parse('M000135240130') == {'type': 'M', 'time': '0001', 'from': '35', 'to': '24', 'nCaptured': '01', 'captures': ['30']}  # MOVE
    assert dam_exchange.parse(f'R01NAME                            Z010100BW{Game().get_dxp_fen()}') == {'type': 'R', 'name': 'NAME', 'fColor': 'Z', 'gameTime': '010', 'numMoves': '100', 'posInd': 'B', 'mColor': 'W', 'pos': 'zzzzzzzzzzzzzzzzzzzzeeeeeeeeeewwwwwwwwwwwwwwwwwwww'}  # GAMEREQ

    assert dam_exchange.parse(dam_exchange.msg_gamereq(0, 100, 100, Game(), 0)) == {'type': 'R', 'name': 'DXP Client', 'fColor': 'Z', 'gameTime': '100', 'numMoves': '100', 'posInd': 'B', 'mColor': 'W', 'pos': 'zzzzzzzzzzzzzzzzzzzzeeeeeeeeeewwwwwwwwwwwwwwwwwwww'}  # GAMEREQ
    assert dam_exchange.msg_gamereq(0, 100, 100) == 'R01DXP Client                      Z100100A'  # GAMEREQ
    assert dam_exchange.parse(dam_exchange.msg_backreq(1, 1)) == {'type': 'B', 'moveId': '001', 'mColor': 'Z'}  # BACKREQ
    assert dam_exchange.msg_backreq(1, 0) == 'B001W'  # BACKREQ
    assert dam_exchange.parse(dam_exchange.msg_backacc('1')) == {'type': 'K', 'accCode': '1'}  # BACKACC
    assert dam_exchange.msg_backacc('0') == 'K0'  # BACKACC