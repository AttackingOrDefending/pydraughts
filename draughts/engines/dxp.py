import draughts.engines.dxp_communication.dxp_communication as dxp_communication
import draughts
import draughts.engine
import subprocess
import os
import signal
import threading
import time
import logging
from typing import Optional, Dict, Union, List, Any

logger = logging.getLogger("pydraughts")


class DXPEngine:
    def __init__(self, command: Union[List[str], str, None] = None, options: Optional[Dict[str, Union[str, int, bool]]] = None, initial_time: int = 0, cwd: Optional[str] = None, ENGINE: int = 5) -> None:
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
        self.info: Dict[str, Any] = {}
        self.id: Dict[str, str] = {}
        self.sender = dxp_communication.Sender()
        self.receiver = self.sender.receiver
        self.game_started = False
        self.exit = False

        self.configure(options)

        if not self.engine_opened:
            cwd = cwd or os.getcwd()
            cwd = os.path.realpath(os.path.expanduser(cwd))
            if type(command) == str:
                command = [command]
            command = list(filter(bool, command))
            command[0] = os.path.realpath(os.path.expanduser(command[0]))
            command[0] = '"' + command[0] + '"'
            command = ' '.join(command)
            self.command = command
            self.p = self._open_process(command, cwd)
            self.engine_receive_thread = threading.Thread(target=self._recv)
            self.engine_receive_thread.start()

        self.start_time = time.perf_counter_ns()
        self.quit_time = 0

    def setoption(self, name: str, value: Union[str, int, bool]) -> None:
        """Set a DXP option."""
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

    def configure(self, options: Dict[str, Union[str, int, bool]]) -> None:
        """Configure many options at once."""
        for name, value in options.items():
            self.setoption(name, value)

    def _open_process(self, command: str, cwd: Optional[str] = None, shell: bool = True, _popen_lock: Any = threading.Lock()) -> subprocess.Popen:
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

    def kill_process(self) -> None:
        """Kill the engine process."""
        if not self.engine_opened:
            wait_time = self.quit_time / 1e9 + 10 - time.perf_counter_ns() / 1e9
            logger.debug(f'wait time before killing: {wait_time}')
            if wait_time > 0:
                time.sleep(wait_time)
            self.exit = True
            try:
                # Windows
                logger.debug("Killing Windows.")
                self.p.send_signal(signal.CTRL_BREAK_EVENT)
            except AttributeError:
                # Unix
                logger.debug("Killing UNIX.")
                os.killpg(self.p.pid, signal.SIGKILL)

            self.p.communicate()
            self.engine_receive_thread.join()

    def _connect(self) -> None:
        """Connect to the engine."""
        if not self.engine_opened:
            wait_time = self.start_time / 1e9 + self.wait_to_open_time - time.perf_counter_ns() / 1e9
            logger.debug(f'wait time before connecting: {wait_time}')
            if wait_time > 0:
                time.sleep(wait_time)
        self.sender.connect(self.ip, int(self.port))

    def _start(self, board: draughts.Board, game_time: int) -> None:
        """Start the game."""
        self._connect()
        color = 'B' if board.turn == draughts.WHITE else 'W'
        game_time = int(round(game_time // 60))
        moves = self.max_moves
        self.sender.setup(board.initial_fen, board.variant)
        self.sender.gamereq(color, game_time, moves)
        accepted = self._recv_accept()
        logger.debug(f'Aceepted: {accepted}')
        self.id["name"] = self.sender.current.engineName

    def _recv(self) -> None:
        """Receive a line from the engine, if the engine is opened by pydraughts."""
        # The engine doesn't work otherwise.
        while True:
            try:
                line = self.p.stdout.readline()

                line = line.rstrip()

                if line:
                    logger.debug(f"{self.ENGINE} %s >> %s {self.p.pid} {line}")
            except ValueError as err:
                if self.exit:
                    break
                else:
                    raise err

    def _recv_accept(self) -> bool:
        """Get if the game was accepted."""
        while True:
            if self.receiver.accepted is not None:
                return self.receiver.accepted

    def _recv_move(self) -> Optional[List[List[int]]]:
        """Receive the engine move."""
        while True:
            if not self.receiver.listening:
                break
            if self.receiver.last_move_changed:
                logger.debug(f'new last move: {self.receiver.last_move.board_move}')
                return self.receiver.last_move

    def play(self, board: draughts.Board) -> Any:
        """Engine search."""
        if not self.game_started:
            self._start(board, self.initial_time)
            self.game_started = True
        if board.move_stack:
            self.sender.send_move(board.move_stack[-1])
        best_move = self._recv_move()
        return draughts.engine.PlayResult(best_move, None, {})

    def quit(self) -> None:
        """Quit the engine."""
        self.sender.gameend()
        self.sender.disconnect()
        self.quit_time = time.perf_counter_ns()
