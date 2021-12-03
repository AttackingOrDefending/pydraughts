# This file is an adaptation of DXC100_draughts_client (https://github.com/akalverboer/DXC100_draughts_client) by akalverboer which is licensed under the MIT License.

import socket
import logging
import draughts

logger = logging.getLogger(__name__)

DXP_WHITE = 0
DXP_BLACK = 1


class GameStatus:
    def __init__(self, fen='startpos', myColor=DXP_WHITE, started=False, variant='standard'):
        self.fen = fen
        self.myColor = myColor
        self.started = started
        self.variant = variant
        self.pos = draughts.Game(fen=fen, variant=variant)
        self.color = self.get_color()
        self.engineName = ''
        self.result = None

    def get_color(self):
        return DXP_WHITE if self.pos.whose_turn() == draughts.WHITE else DXP_BLACK


class MySocket:
    def __init__(self):
        self.sock = None

    def open(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception:
            self.sock = None
            raise Exception("socket exception: failed to open")
        return self

    def connect(self, host, port):
        self.sock.settimeout(10)  # timeout for connection
        try:
            self.sock.connect((host, port))
        except socket.error as msg:
            self.sock = None
            raise Exception("connection exception: failed to connect")
        if self.sock is not None:
            self.sock.settimeout(None)  # default
        return self

    def send(self, msg):
        try:
            self.sock.send(bytes(msg, 'utf-8') + b"\0")
        except Exception:
            raise Exception("send exception: no connection")
        return None

    def receive(self):
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

        logger.debug("final msg: " + msg)
        msg = msg.replace("\0", "")  # remove all null chars

        # Use strip to remove all whitespace at the start and end.
        # Including spaces, tabs, newlines and carriage returns.
        msg = msg.strip()
        return msg


class DamExchange:
    def parse(self, msg):
        # Parse incoming DXP message. Returns relevant items depending on mtype.
        result = {}
        mtype = msg[0:1]
        if mtype == "C":  # CHAT
            result['type'] = "C"
            result['text'] = msg[1:127]
        elif mtype == "R":  # GAMEREQ (only received by FOLLOWER)
            result['type'] = "R"
            result['name'] = msg[3:35].strip()  # initiator
            result['fColor'] = msg[35:36]  # color of follower
            result['gameTime'] = msg[36:40]
            result['numMoves'] = msg[40:44]
            result['posInd'] = msg[44:45]
            if result['posInd'] != "A":
                result['mColor'] = msg[45:46]  # color to move for position
                result['pos'] = msg[46:96]
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

    def msg_chat(self, str):
        # Generate CHAT message. Example: CWhat do you think about move 35?
        msg = "C" + str
        return msg

    def msg_gamereq(self, myColor, gameTime, numMoves, pos=None, colorToMove=None):
        # Generate GAMEREQ message. Example: R01Tornado voor Windows 4.0        W060065A
        gamereq = []
        gamereq.append("R")  # header
        gamereq.append("01")  # version

        gamereq.append("DXP Client".ljust(32)[:32])  # iName: fixed length padding spaces
        gamereq.append('Z' if myColor == DXP_WHITE else 'W')  # fColor: color of follower (server)
        gamereq.append(str(gameTime).zfill(3))  # gameTime: time limit of game (ex: 090)
        gamereq.append(str(numMoves).zfill(3))  # numMoves: number of moves of time limit (ex: 050)
        if pos is None or colorToMove is None:
            gamereq.append("A")  # posInd == A: use starting position
        else:
            gamereq.append("B")  # posInd == B: use parameters pos and colorToMove
            gamereq.append("W" if colorToMove == DXP_WHITE else "Z")  # mColor
            gamereq.append(pos.get_dxp_fen())  # board

        msg = ""
        for item in gamereq:
            msg = msg + item
        return msg

    def msg_move(self, steps, captures, timeSpend):
        # Generate MOVE message. Example: M001205250422122320
        # Parm rmove is a "two-color" move
        move = []
        move.append("M")  # header
        move.append(str(timeSpend % 10000).zfill(4))  # mTime: 0000 .. 9999
        move.append(str(steps[0] % 100).zfill(2))  # mFrom
        move.append(str(steps[-1] % 100).zfill(2))  # mTo
        move.append(str(len(captures) % 100).zfill(2))  # mNumCaptured: number of takes (captures)
        for k in captures:
            move.append(str(k % 100).zfill(2))  # mCaptures

        msg = ""
        for item in move:
            msg = msg + item
        return msg

    def msg_gameend(self, reason):
        # Generate GAMEEND message. Example: E00
        gameend = []
        gameend.append("E")  # header
        gameend.append(str(reason)[0])  # reason:  0 > unknown  1 > I lose  2 > draw  3 > I win
        gameend.append("1")  # stop code: 0 > next game preferred  1: > no next game
        msg = ""
        for item in gameend:
            msg = msg + item
        return msg

    def msg_backreq(self, moveId, colorToMove):
        # Generate BACKREQ message. Example: B005Z
        backreq = []
        backreq.append("B")
        backreq.append(str(moveId % 1000).zfill(3))  # moveId
        backreq.append("W" if colorToMove == DXP_WHITE else "Z")  # mColor
        msg = ""
        for item in backreq:
            msg = msg + item
        return msg

    def msg_backacc(self, accCode):
        # Generate BACKREQ message. Example: K1
        backreq = []
        backreq.append("K")
        backreq.append(str(accCode[0]))  # accCode
        msg = ""
        for item in backreq:
            msg = msg + item
        return msg
