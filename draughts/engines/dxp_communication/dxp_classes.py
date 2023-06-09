# This file is an adaptation of DXC100_draughts_client (https://github.com/akalverboer/DXC100_draughts_client) by akalverboer.

from __future__ import annotations
import socket
import logging
import draughts
from typing import Dict, Optional, List, Union

logger = logging.getLogger("pydraughts")

DXP_WHITE = 0
DXP_BLACK = 1


class GameStatus:
    def __init__(self, fen: str = 'startpos', my_color: int = DXP_WHITE, started: bool = False, variant: str = 'standard') -> None:
        self.fen = fen
        self.my_color = my_color
        self.started = started
        self.variant = variant
        self.pos = draughts.Board(fen=fen, variant=variant)
        self.color = self.get_color()
        self.engineName = ''
        self.result = None

    def get_color(self) -> int:
        """Get the color of the playing side."""
        return DXP_WHITE if self.pos.turn == draughts.WHITE else DXP_BLACK


class MySocket:
    def __init__(self) -> None:
        self.sock = None
        self.closed = False

    def open(self) -> MySocket:
        """Open the socket."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.closed = False
        except Exception:
            self.sock = None
            raise Exception("socket exception: failed to open")
        return self

    def connect(self, host: str, port: int) -> MySocket:
        """Connect to the engine."""
        self.sock.settimeout(10)  # timeout for connection
        try:
            self.sock.connect((host, port))
        except socket.error as msg:
            self.sock = None
            raise Exception(f"connection exception: failed to connect ({msg}).")
        if self.sock is not None:
            self.sock.settimeout(None)  # default
        return self

    def send(self, msg: str) -> None:
        """Send a message to the engine."""
        try:
            logger.debug(f"socket send: {msg}")
            self.sock.send(bytes(msg, 'utf-8') + b"\0")
        except Exception:
            raise Exception("send exception: no connection")
        return None

    def receive(self) -> str:
        """Receive a message from the engine."""
        msg = ""
        while True:
            # Collect message chunks until null character found
            try:
                chunk = self.sock.recv(1024)
            except Exception:
                raise Exception("receive exception: no connection")

            if chunk == "":
                raise Exception("receive exception: socket connection broken")
            msg += chunk.decode()
            if msg.find("\0") > -1:
                break
            if len(msg) > 128:
                break  # too long, no null char

        logger.debug(f"socket receive: {msg}")
        msg = msg.replace("\0", "")  # remove all null chars

        # Use strip to remove all whitespace at the start and end.
        # Including spaces, tabs, newlines and carriage returns.
        msg = msg.strip()
        return msg

    def close(self):
        if self.sock and not self.closed:
            self.closed = True
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.sock = None

    def __del__(self):
        self.close()


class DamExchange:
    def parse(self, msg: str) -> Dict[str, Union[str, List[str]]]:
        """Parse an incoming DXP message."""
        # Parse incoming DXP message. Returns relevant items depending on mtype.
        result: Dict[str, Union[str, List[str]]] = {}
        mtype = msg[0:1]
        if mtype == "C":  # CHAT
            result['type'] = "C"
            result['text'] = msg[1:127]
        elif mtype == "R":  # GAMEREQ (only received by FOLLOWER)
            result['type'] = "R"
            result['name'] = msg[3:35].strip()  # initiator
            result['fColor'] = msg[35:36]  # color of follower
            result['gameTime'] = msg[36:39]
            result['numMoves'] = msg[39:42]
            result['posInd'] = msg[42:43]
            if result['posInd'] != "A":
                result['mColor'] = msg[43:44]  # color to move for position
                result['pos'] = msg[44:94]
        elif mtype == "A":  # GAMEACC
            result['type'] = "A"
            result['engineName'] = msg[1:33].strip()  # follower name
            result['accCode'] = msg[33:34]
        elif mtype == "M":  # MOVE
            result['type'] = "M"
            result['time'] = msg[1:5]
            result['from'] = msg[5:7]
            result['to'] = msg[7:9]
            result['nCaptured'] = msg[9:11]
            result['captures'] = []
            for i in range(int(result['nCaptured'])):
                s = i * 2
                result['captures'].append(msg[11 + s:13 + s])
        elif mtype == "E":  # GAMEEND
            result['type'] = "E"
            result['reason'] = msg[1:2]
            result['stop'] = msg[2:3]
        elif mtype == "B":  # BACKREQ
            result['type'] = "B"
            result['moveId'] = msg[1:4]
            result['mColor'] = msg[4:5]
        elif mtype == "K":  # BACKACC
            result['type'] = "K"
            result['accCode'] = msg[1:2]
        else:
            result['type'] = "?"
        return result

    def msg_chat(self, msg: str) -> str:
        """Generate a CHAT message."""
        # Generate CHAT message. Example: CWhat do you think about move 35?
        msg = "C" + msg
        return msg

    def msg_gamereq(self, my_color: int, game_time: int, num_moves: int, pos: Optional[draughts.Board] = None, color_to_move: Optional[int] = None) -> str:
        """Generate a GAMEREQ message."""
        # Generate GAMEREQ message. Example: R01Tornado voor Windows 4.0        W060065A
        gamereq = []
        gamereq.append("R")  # header
        gamereq.append("01")  # version

        gamereq.append("DXP Client".ljust(32)[:32])  # iName: fixed length padding spaces
        gamereq.append('Z' if my_color == DXP_WHITE else 'W')  # fColor: color of follower (server)
        gamereq.append(str(game_time).zfill(3))  # game_time: time limit of game (ex: 090)
        gamereq.append(str(num_moves).zfill(3))  # num_moves: number of moves of time limit (ex: 050)
        if pos is None or color_to_move is None:
            gamereq.append("A")  # posInd == A: use starting position
        else:
            gamereq.append("B")  # posInd == B: use parameters pos and color_to_move
            gamereq.append("W" if color_to_move == DXP_WHITE else "Z")  # mColor
            gamereq.append(pos._game.get_dxp_fen())  # board

        msg = ""
        for item in gamereq:
            msg = msg + item
        return msg

    def msg_move(self, steps: List[int], captures: List[int], time_spent: int) -> str:
        """Generate a MOVE message."""
        # Generate MOVE message. Example: M001205250422122320
        # Parm rmove is a "two-color" move
        move = []
        move.append("M")  # header
        move.append(str(time_spent % 10000).zfill(4))  # mTime: 0000 .. 9999
        move.append(str(steps[0] % 100).zfill(2))  # mFrom
        move.append(str(steps[-1] % 100).zfill(2))  # mTo
        move.append(str(len(captures) % 100).zfill(2))  # mNumCaptured: number of takes (captures)
        for k in captures:
            move.append(str(k % 100).zfill(2))  # mCaptures

        msg = ""
        for item in move:
            msg = msg + item
        return msg

    def msg_gameend(self, reason: str) -> str:
        """Generate a GAMEEND message."""
        # Generate GAMEEND message. Example: E00
        gameend = []
        gameend.append("E")  # header
        gameend.append(str(reason)[0])  # reason:  0 > unknown  1 > I lose  2 > draw  3 > I win
        gameend.append("1")  # stop code: 0 > next game preferred  1: > no next game
        msg = ""
        for item in gameend:
            msg = msg + item
        return msg

    def msg_backreq(self, moveId: int, color_to_move: int) -> str:
        """Generate a BACKREQ message."""
        # Generate BACKREQ message. Example: B005Z
        backreq = []
        backreq.append("B")
        backreq.append(str(moveId % 1000).zfill(3))  # moveId
        backreq.append("W" if color_to_move == DXP_WHITE else "Z")  # mColor
        msg = ""
        for item in backreq:
            msg = msg + item
        return msg

    def msg_backacc(self, accCode: str) -> str:
        """Generate the response to a BACKREQ request."""
        # Generate BACKREQ message. Example: K1
        backreq = []
        backreq.append("K")
        backreq.append(str(accCode[0]))  # accCode
        msg = ""
        for item in backreq:
            msg = msg + item
        return msg
