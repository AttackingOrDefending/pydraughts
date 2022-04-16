from draughts.engines.dxp_communication import dxp_run
from importlib import reload
from draughts import Game
import logging

logging.basicConfig()
logger = logging.getLogger("pydraughts")
logger.setLevel(logging.DEBUG)


def test_console_handler():
    global dxp_run

    # terminate program (doesn't do anything)
    dxp_run = reload(dxp_run)
    tConsoleHandler = dxp_run.ConsoleHandler()
    tConsoleHandler.run_command('setup')
    tConsoleHandler.run_command('q')

    # setup (number of commands = 2)
    dxp_run = reload(dxp_run)
    tConsoleHandler = dxp_run.ConsoleHandler()
    tConsoleHandler.run_command(f'setup {Game().get_dxp_fen()}')

    # setup (number of commands > 3)
    dxp_run = reload(dxp_run)
    tConsoleHandler = dxp_run.ConsoleHandler()
    tConsoleHandler.run_command(f'setup {Game().get_dxp_fen()} {Game().variant} extra')

    dxp_run = reload(dxp_run)
    tConsoleHandler = dxp_run.ConsoleHandler()
    # conn (number of commands = 2) & Error trying to connect: connection exception: failed to connect
    tConsoleHandler.run_command('conn 127.0.0.1')
    # conn (number of commands = 1) & Error trying to connect: connection exception: failed to connect
    tConsoleHandler.run_command('conn')
    # chat (number of commands = 1)
    tConsoleHandler.run_command('chat')
    # chat (number of commands > 1) & Error sending chat message: send exception: no connection
    tConsoleHandler.run_command('chat message')
    # gamereq (number of commands = 2) & Error sending game request: send exception: no connection
    tConsoleHandler.run_command('gamereq W')

    dxp_run = reload(dxp_run)
    tConsoleHandler = dxp_run.ConsoleHandler()
    # gamereq (number of commands = 3) & Error sending game request: send exception: no connection
    tConsoleHandler.run_command('gamereq B 100')
    # Game already finished; gameend not allowed
    tConsoleHandler.run_command('gameend')

    dxp_run = reload(dxp_run)
    tConsoleHandler = dxp_run.ConsoleHandler()
    # Game not started; backreq not allowed
    tConsoleHandler.run_command('backreq')
    # Command unknown
    tConsoleHandler.run_command('random-command')


test_console_handler()
