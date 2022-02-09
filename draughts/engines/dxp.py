import draughts.engines.dxp_communication.dxp_run as dxp
import draughts
import draughts.engine
import subprocess
import os
import signal
import threading
import time
import logging
from importlib import reload

logger = logging.getLogger(__name__)


class DXPEngine:
    def __init__(self, command=None, options=None, initial_time=0, ENGINE=5):
        global dxp
        dxp = reload(dxp)
        if options is None:
            options = {}
        self.initial_time = initial_time
        self.max_moves = 0
        self.ip = '127.0.0.1'
        self.port = '27531'
        self.command = command
        self.engine_opened = True  # Whether the engine is already open or pydraughts should open it
        self.wait_to_open_time = 10
        self.ENGINE = ENGINE
        self.info = {}
        self.id = {}
        self.console = dxp.tConsoleHandler
        self.receiver = dxp.tReceiveHandler
        self.game_started = False
        self._last_move = None

        for name, value in options.items():
            self.setoption(name, value)

        if not self.engine_opened:
            cwd = os.getcwd()
            cwd = os.path.realpath(os.path.expanduser(cwd))
            if type(command) == str:
                command = [command]
                command = list(filter(bool, command))
            else:
                command = list(filter(bool, command))
                command[0] = os.path.realpath(os.path.expanduser(command[0]))
                command[0] = '"' + command[0] + '"'
            command = ' '.join(command)
            self.command = command
            self.p = self._open_process(command, cwd)
            self.thr = threading.Thread(target=self._recv)
            self.thr.start()

        self.start_time = time.perf_counter_ns()

    def setoption(self, name, value):
        if name == 'engine-opened':
            self.engine_opened = value
        elif name == 'ip':
            self.ip = str(value)
        elif name == 'port':
            self.port = str(value)
        elif name == 'wait-to-open-time':
            self.wait_to_open_time = int(value)
        elif name == 'max-moves':
            self.max_moves = 0
        elif name == 'initial-time':
            self.initial_time = 0

    def _open_process(self, command, cwd=None, shell=True, _popen_lock=threading.Lock()):
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

    def kill_process(self):
        if not self.engine_opened:
            try:
                # Windows
                self.p.send_signal(signal.CTRL_BREAK_EVENT)
            except AttributeError:
                # Unix
                os.killpg(self.p.pid, signal.SIGKILL)

            self.p.communicate()

    def _connect(self):
        if not self.engine_opened:
            wait_time = self.start_time / 1e9 + self.wait_to_open_time - time.perf_counter_ns() / 1e9
            logger.debug(f'wait time: {wait_time}')
            if wait_time > 0:
                time.sleep(wait_time)
        self.console.run_command(f'connect {self.ip} {self.port}')

    def _start(self, board, time):
        self._connect()
        color = 'B' if board.whose_turn() == draughts.WHITE else 'W'
        time = str(round(time // 60))
        moves = self.max_moves
        self.console.run_command(f'setup {board.initial_fen} {board.variant}')
        self.console.run_command(f'gamereq {color} {time} {moves}')
        accepted = self._recv_accept()
        logger.debug(f'Aceepted: {accepted}')
        self.id["name"] = dxp.current.engineName

    def _recv(self):
        while True:
            line = self.p.stdout.readline()

            line = line.rstrip()

            if line:
                logging.debug(f"{self.ENGINE} %s >> %s {self.p.pid} {line}")

    def _recv_accept(self):
        while True:
            if dxp.accepted is not None:
                return dxp.accepted

    def _recv_move(self):
        while True:
            if not dxp.tReceiveHandler.isListening:
                break
            if self._last_move != dxp.last_move:
                self._last_move = dxp.last_move
                logger.debug(f'new last move: {self._last_move}')
                return self._last_move

    def play(self, board):
        if not self.game_started:
            self._start(board, self.initial_time)
            self.game_started = True
        if board.move_stack:
            move = board.move_stack[-1].li_one_move
            move = [move[i:i+2] for i in range(0, len(move), 2)]
            move = '-'.join(move)
            self.console.run_command(f'sm {move}')
        best_move = self._recv_move()
        if best_move:
            best_move = draughts.Move(board, best_move)
        return draughts.engine.PlayResult(best_move, None)

    def quit(self):
        self.console.run_command('gameend 0')
