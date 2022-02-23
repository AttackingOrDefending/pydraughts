# This file is an adaptation of fishnet (https://github.com/lichess-org/fishnet/tree/ebd2a5e16d37135509cbfbff9998e0b798866ef5).

import subprocess
import os
import signal
import logging
import threading
import draughts
import draughts.engine
import re
import math

logger = logging.getLogger(__name__)


class HubEngine:
    def __init__(self, command, cwd=None, ENGINE=5):
        self.ENGINE = ENGINE
        self.info = {}
        self.id = {}
        self.options = set()
        self.variants = set()
        cwd = cwd or os.getcwd()
        cwd = os.path.realpath(os.path.expanduser(cwd))
        if type(command) == str:
            command = [command]
        command = list(filter(bool, command))
        command[0] = os.path.realpath(os.path.expanduser(command[0]))
        command[0] = '"' + command[0] + '"'
        command = ' '.join(command)
        self.p = self._open_process(command, cwd)
        self._last_sent = ""
        self.hub()

    def _open_process(self, command, cwd=None, shell=True, _popen_lock=threading.Lock()):
        kwargs = {
            "shell": shell,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "stdin": subprocess.PIPE,
            "bufsize": 1,  # Line buffered
            "universal_newlines": True,
        }

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
        try:
            # Windows
            self.p.send_signal(signal.CTRL_BREAK_EVENT)
        except AttributeError:
            # Unix
            os.killpg(self.p.pid, signal.SIGKILL)

        self.p.communicate()

    def send(self, line):
        if line == "ponder-hit":
            while self._last_sent != "go ponder":
                pass
        logger.debug(f"{self.ENGINE} %s << %s {self.p.pid} {line}")

        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()
        self._last_sent = line

    def recv(self):
        while True:
            line = self.p.stdout.readline()
            if line == "":
                raise EOFError()

            line = line.rstrip()

            logger.debug(f"{self.ENGINE} %s >> %s {self.p.pid} {line}")

            if line:
                return line

    def recv_hub(self):
        command_and_args = self.recv().split(None, 1)
        if len(command_and_args) == 1:
            return command_and_args[0], ""
        elif len(command_and_args) == 2:
            return command_and_args

    def hub(self):
        self.send("hub")

        engine_info = {}
        options = set()
        variants = set()

        while True:
            command, arg = self.recv_hub()

            if command == "wait":
                return engine_info, options, variants
            elif command == "id":
                args = re.split(r' +(?![^"]*"(?:(?:[^"]*"){2})*[^"]*$)', arg)
                args = list(map(lambda item: item.split("="), args))
                for key, value in args:
                    engine_info[key] = value
            elif command == "param":
                args = re.split(r' +(?![^"]*"(?:(?:[^"]*"){2})*[^"]*$)', arg)
                args = list(map(lambda item: item.split("="), args))
                is_variant = False
                for key, value in args:
                    if key == "name":
                        options.add(value)
                        if value == "variant":
                            is_variant = True
                    if key == "values" and is_variant:
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        for variant in value.split():
                            variants.add(variant)
            else:
                logger.warning("Unexpected engine response to hub: %s %s", command, arg)
            self.options = options
            self.variants = variants
            self.id = engine_info

    def init(self):
        self.send("init")
        while True:
            command, arg = self.recv_hub()
            if command == "ready":
                break
            elif command == "init":
                pass
            else:
                logger.warning("Unexpected engine response to init: %s %s", command, arg)

    def ping(self):
        self.send("ping")
        while True:
            command, arg = self.recv_hub()
            if command == "pong":
                break
            else:
                logger.warning("Unexpected engine response to ping: %s %s", command, arg)

    def setoption(self, name, value):
        if value is True:
            value = "true"
        elif value is False:
            value = "false"
        elif value is None:
            value = "none"

        if name == 'variant' and self.variants or name != 'variant':
            self.send("set-param name=%s value=%s" % (name, value))

    def go(self, fen, moves=None, my_time=None, inc=None, moves_left=None, movetime=None, depth=None, nodes=None, ponder=False):
        assert my_time or movetime or depth or nodes
        if moves:
            self.send(f'pos pos={fen} moves="{moves}"')
        else:
            self.send(f'pos pos={fen}')

        if my_time and inc and moves_left:
            self.send(f'level moves={moves_left} time={my_time} inc={inc}')
        elif my_time and inc:
            self.send(f'level time={my_time} inc={inc}')
        elif my_time and moves_left:
            self.send(f'level moves={moves_left} time={my_time}')
        elif my_time:
            self.send(f'level time={my_time}')
        elif movetime:
            self.send(f'level move-time={movetime}')
        elif depth:
            self.send(f'level depth={depth}')
        elif nodes:
            self.send(f'level nodes={nodes}')

        if ponder:
            self.send('go ponder')
        else:
            self.send('go think')

        self.info = {}
        while True:
            command, arg = self.recv_hub()
            if command == "done":
                args = arg.split()
                pondermove = None
                args = list(map(lambda item: item.split("="), args))
                bestmove = args[0][1]
                if len(args) == 2:
                    pondermove = args[1][1]
                return bestmove, pondermove
            elif command == "info":
                args = re.split(r' +(?![^"]*"(?:(?:[^"]*"){2})*[^"]*$)', arg)
                args = list(map(lambda item: item.split("="), args))
                for key, value in args:
                    if key in ["depth", "nodes"]:
                        value = int(value)
                    elif key in ["mean-depth", "time", "nps"]:
                        value = float(value)
                    elif key == "score":
                        score = int(float(value) * 100)
                        mate = None
                        if score > 9000:
                            mate = 10000 - score
                        elif score < -9000:
                            mate = -10000 - score
                        if mate:
                            value = {"win": math.ceil(mate / 2)}
                        else:
                            value = {"cp": score}
                    self.info[key] = value
            else:
                logger.warning("Unexpected engine response to go: %s %s", command, arg)

    def stop(self):
        self.send("stop")

    def ponderhit(self):
        self.send("ponder-hit")

    def quit(self):
        self.send("quit")

    def play(self, board, time_limit, ponder):
        time = time_limit.time
        inc = time_limit.inc
        depth = time_limit.depth
        nodes = time_limit.nodes
        movetime = time_limit.movetime
        hub_moves = board.move_stack
        hub_moves = list(map(lambda move: move.hub_move, hub_moves))
        bestmove, pondermove = self.go(board.initial_hub_fen, moves=' '.join(hub_moves), my_time=time, inc=inc, depth=depth, nodes=nodes, movetime=movetime, ponder=ponder)

        ponder_move = None
        if bestmove is None:
            return None, None
        ponder_board = board.copy()
        best_move = draughts.Move(ponder_board, hub_move=bestmove)
        if pondermove:
            for move in best_move.board_move:
                ponder_board.move(move)
            ponder_move = draughts.Move(ponder_board, hub_move=pondermove)

        return draughts.engine.PlayResult(best_move, ponder_move, self.info)
