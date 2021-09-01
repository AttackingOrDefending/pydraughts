# This file is an adaptation of draughtsnet (https://github.com/RoepStoep/draughtsnet) by RoepStoep.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
import os
import signal
import logging
import threading
import time
import draughts

logger = logging.getLogger(__name__)


class HubEngine:
    def __init__(self, command, ENGINE=5):
        if type(command) == str:
            command = [command]
        self.ENGINE = ENGINE
        self.info = {}
        self.id = {}
        cwd = os.path.realpath(os.path.expanduser("."))
        command = list(filter(bool, command))
        command = " ".join(command)
        self.p = self.open_process(command, cwd)
        self.last_sent = ""

    def open_process(self, command, cwd=None, shell=True, _popen_lock=threading.Lock()):
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
            while self.last_sent != "go ponder":
                pass
        logging.debug(f"{self.ENGINE} %s << %s {self.p.pid} {line}")

        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()
        self.last_sent = line

    def recv(self):
        while True:
            line = self.p.stdout.readline()
            if line == "":
                raise EOFError()

            line = line.rstrip()

            logging.debug(f"{self.ENGINE} %s >> %s {self.p.pid} {line}")

            if line:
                return line

    def recv_uci(self):
        command_and_args = self.recv().split(None, 1)
        if len(command_and_args) == 1:
            return command_and_args[0], ""
        elif len(command_and_args) == 2:
            return command_and_args

    def uci(self):
        self.send("hub")

        engine_info = {}
        variants = set()

        while True:
            command, arg = self.recv_uci()

            if command == "wait":
                return engine_info, variants
            elif command == "id":
                parts = arg.split()
                i = 0
                while i < len(parts):
                    name_and_value = parts[i].split("=", 1)
                    if len(name_and_value) == 2:
                        value = name_and_value[1]
                        if value.startswith("\""):
                            value = value[1:]
                            i += 1
                            while i < len(parts) and not parts[i].endswith("\""):
                                value += " " + parts[i]
                                i += 1
                            value += " " + parts[i][:-1]
                        engine_info[name_and_value[0]] = value
                    i += 1
            elif command == "param":
                if arg.startswith("name=variant") and arg.find("type=enum") != -1:
                    argvalues = arg.split("=")[-1].replace("\"", "")
                    for variant in argvalues.split():
                        variants.add(variant)
            else:
                logging.warning("Unexpected engine response to uci: %s %s", command, arg)
            self.variants = variants
            self.id = engine_info

    def init(self):
        self.send("init")
        while True:
            command, arg = self.recv_uci()
            if command == "ready":
                break
            elif command == "init":
                pass
            else:
                logging.warning("Unexpected engine response to init: %s %s", command, arg)

    def ping(self):
        self.send("ping")
        while True:
            command, arg = self.recv_uci()
            if command == "pong":
                break
            else:
                logging.warning("Unexpected engine response to ping: %s %s", command, arg)

    def setoption(self, name, value):
        if value is True:
            value = "true"
        elif value is False:
            value = "false"
        elif value is None:
            value = "none"

        if name == 'variant' and self.variants or name != 'variant':
            self.send("set-param name=%s value=%s" % (name, value))

    def go(self, position, my_time=None, inc=None, movetime=None, clock=None, depth=None, analysisnodes=None, handicap=None, pst=None,
           searchnodes=None, bookply=None, bookmargin=None, ply=None, moves=None, ponder=False):
        if moves is None:
            moves = ''
        if moves and len(moves) != 0:
            self.send("pos pos=%s moves=\"%s\"" % (position, moves))
        else:
            self.send("pos pos=%s" % position)

        if handicap is not None and handicap > 0:
            self.send("level handicap=%s" % str(handicap))
        if ply is not None and ply > 0:
            self.send("level ply=%s" % str(ply))
        if searchnodes is not None and searchnodes > 0:
            self.send("level nodes=%s" % str(searchnodes))

        if movetime is not None and clock is not None:
            if position[0] == 'B':
                timeleft = clock["btime"] / 100.0
            else:
                timeleft = clock["wtime"] / 100.0
            increment = clock["inc"]
            if increment == 0 and timeleft < 50.0:
                movetime *= (timeleft / 50.0)
            elif increment == 1 and timeleft < 6.0:
                movetime *= (timeleft / 6.0)

        # if analysisnodes is not None and movetime is None:
        #     movetime = 4  # If no movetime is specified, allow 4 seconds to reach the required amount of nodes

        if depth is not None and depth > 0:
            self.send("level depth=%s" % str(depth))
        if movetime is not None:
            self.send("level move-time=%s" % str(movetime))

        if depth is None and movetime is None and clock is None and searchnodes is None:
            if inc:
                my_time -= inc  # Hub engines first add the increment
                self.send("level time={} inc={}".format(my_time, inc))
            else:
                self.send("level time={}".format(my_time))

        if analysisnodes is not None:
            self.send("level nodes=%s" % str(analysisnodes))
        if ponder:
            self.send("go ponder")
        else:
            self.send("go think")

        info = {}
        info["bestmove"] = None
        info["pondermove"] = None
        info["taken"] = ""
        info["pondertaken"] = ""

        start = time.time()
        while True:
            command, arg = self.recv_uci()
            arg_split = arg.split()

            forcestop = False
            if command == "done":
                if len(arg) == 0:
                    # info["bestmove"] = ""
                    # info["taken"] = ""
                    # info["score"] = {"win": 0}
                    # return info
                    return None, None, None, None
                bestmoveval = arg_split[0]
                if bestmoveval and bestmoveval.find("=") != -1:
                    bestmove = bestmoveval.split("=")[1]
                    if bestmove.find("x") != -1:
                        fields = bestmove.split("x")
                        origdest = fields[:2]
                        taken = fields[2:]
                    else:
                        origdest = bestmove.split("-")[:2]
                        taken = []
                    if len(origdest) == 2:
                        info["bestmove"] = "%02d%02d" % (int(origdest[0]), int(origdest[1]))
                    alltaken = ""
                    for t in taken:
                        alltaken += "%02d" % int(t)
                    info["taken"] = alltaken
                if len(arg_split) >= 2:
                    pondermoveval = arg_split[1]
                    if pondermoveval and pondermoveval.find("=") != -1:
                        pondermove = pondermoveval.split("=")[1]
                        if pondermove.find("x") != -1:
                            fields = pondermove.split("x")
                            origdest = fields[:2]
                            taken = fields[2:]
                        else:
                            origdest = pondermove.split("-")[:2]
                            taken = []
                        if len(origdest) == 2:
                            info["pondermove"] = "%02d%02d" % (int(origdest[0]), int(origdest[1]))
                        alltaken = ""
                        for t in taken:
                            alltaken += "%02d" % int(t)
                        info["pondertaken"] = alltaken
                return info["bestmove"], info["pondermove"], info["taken"], info["pondertaken"]
            elif command == "info":
                arg = arg or ""

                # Parse all other parameters
                cur_nodes = 0
                cur_depth = 0
                parts = arg.split()
                i = 0
                while i < len(parts):
                    name_and_value = parts[i].split("=", 1)
                    if len(name_and_value) == 2:
                        value = name_and_value[1]
                        if value.startswith("\""):
                            value = value[1:]
                            i += 1
                            while i < len(parts) and not parts[i].endswith("\""):
                                value += " " + parts[i]
                                i += 1
                            value += " " + parts[i][:-1]
                        if name_and_value[0] in ["nodes", "depth"]:
                            info[name_and_value[0]] = int(value)
                        elif name_and_value[0] == "score":
                            score = int(float(value) * 100)
                            if abs(score) > 9000:
                                if score > 0:
                                    plies = 10000 - score
                                    moves = int((plies + plies % 2) / 2)
                                else:
                                    plies = -(10000 + score)
                                    moves = int((plies - plies % 2) / 2)
                                info["score"] = {"win": moves}
                            elif abs(score) > 8000:
                                if score > 0:
                                    plies = 9000 - score
                                    moves = int((plies + plies % 2) / 2)
                                else:
                                    plies = -(9000 + score)
                                    moves = int((plies - plies % 2) / 2)
                                info["score"] = {"win": moves}
                            else:
                                info["score"] = {"cp": score}
                        elif name_and_value[0] == "time":
                            info["time"] = int(float(value) * 1000)
                        elif name_and_value[0] == "nps":
                            info["nps"] = round(float(value))
                        elif name_and_value[0] != "mean-depth":
                            info[name_and_value[0]] = value
                        if name_and_value[0] == "nodes":
                            cur_nodes = int(value)
                        if name_and_value[0] == "depth":
                            cur_depth = int(value)
                    i += 1
                    self.info = info

                # Check if we have reached the node count for analysis
                if analysisnodes is not None and (cur_nodes > analysisnodes or cur_depth > 50):
                    forcestop = True
            else:
                logging.warning("Unexpected engine response to go: %s %s", command, arg)

            # Force play if movetime is exceeded (not exact as we only reach this point after the engine produces output)
            if forcestop or (movetime is not None and time.time() - start > movetime):
                self.send("stop")

    def known_variant(self, variant):
        return self.parse_variant(variant) in ["normal", "bt", "frisian", "losing"]

    def parse_variant(self, variant):
        variant = variant.lower()

        if variant in ["standard", "fromposition"]:
            return "normal"
        elif variant == "breakthrough":
            return "bt"
        elif variant == "antidraughts":
            return "losing"
        elif variant == "frysk":
            return "frisian"
        else:
            return variant

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
        bestmove, pondermove, taken, pondertaken = self.go(board.initial_hub_fen, moves=' '.join(hub_moves), my_time=time, inc=inc, depth=depth, analysisnodes=nodes, movetime=movetime, ponder=ponder)

        ponder_move = None
        if bestmove is None:
            return None, None
        ponder_board = board.copy()
        best_move = draughts.Move(ponder_board, hub_position_move=bestmove + taken)
        if pondermove:
            for move in best_move.board_move:
                ponder_board.move(move)
            ponder_move = draughts.Move(ponder_board, hub_position_move=pondermove + pondertaken)

        return best_move, ponder_move
