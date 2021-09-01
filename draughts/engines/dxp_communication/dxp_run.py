# This file is an adaptation of DXC100_draughts_client (https://github.com/akalverboer/DXC100_draughts_client) by akalverboer which is licensed under the MIT License.

import threading
import logging
from draughts.engines.dxp_communication.dxp_classes import DamExchange, MySocket, GameStatus, DXP_WHITE, DXP_BLACK

last_move = None
accepted = None

logger = logging.getLogger(__name__)


class ConsoleHandler:
    def __init__(self):
        self.isRunning = False  # not used

    def run_command(self, comm):

        global current, mySock, lock
        global accepted, last_move
        logger.debug(f'comm {comm}')

        if comm.startswith('q') or comm.startswith('ex'):  # quit/exit
            logger.debug(f"Command terminate program: {comm.strip()}")
            # os._exit(1)  # does no cleanups

        elif comm.startswith('setup'):
            if current.started:
                logger.debug("Game started; setup not allowed")
                return
            if len(comm.split()) == 1:
                # Setup starting position
                logger.debug(f"Command setup starting position: {comm.strip()}")
                current = GameStatus()  # State(Position(board), C.WHITE)
            elif len(comm.split()) == 2:
                # Setup position with fen string (!!! without apostrophes and no spaces !!!)
                _, fen = comm.split(' ', 1)  # strip first word
                logger.debug("Command setup position with FEN string")
                logger.debug(f"FEN: {fen.strip()}")
                color = DXP_BLACK if fen[0] == 'B' else DXP_WHITE
                current = GameStatus(fen=fen, myColor=color)  # State(pos, color)
            elif len(comm.split()) == 3:
                # Setup position with fen string (!!! without apostrophes and no spaces !!!)
                _, fen, variant = comm.split(' ', 2)  # strip first word
                logger.debug("Command setup position with FEN and variant string")
                logger.debug(f"FEN: {fen.strip()} Variant: {variant}")
                color = DXP_BLACK if fen[0] == 'B' else DXP_WHITE
                current = GameStatus(fen=fen, myColor=color, variant=variant)  # State(pos, color)
            else:
                return

        elif comm.startswith('sm'):
            if current.started and current.myColor != current.get_color():
                logger.debug("Move not allowed; server has to move")
                return
            logger.debug(f"Command step move piece: {comm.strip()}")
            steps = comm.strip().split()[1].split('-')
            steps = list(map(int, steps))

            lock.acquire()  # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK
            if current.started and current.myColor == current.get_color():
                timeSpend = 0  # time spend for this move (future)

                board = []
                for index in range(1, len(steps)):
                    board.append([steps[index - 1], steps[index]])
                all_moves, all_captures = current.pos.legal_moves()
                captures = all_captures[all_moves.index(board)]
                if captures[0] is None:
                    captures = []
                msg = dxp.msg_move(steps, captures, timeSpend)
                logger.debug(f'MOVE: {board}')

                try:
                    mySock.send(msg)
                    logger.debug(f"snd MOVE: {msg}")
                except Exception as err:
                    logger.debug(f"Error sending move: {err}")
                    return

                for move in board:
                    current.pos.move(move)
            lock.release()  # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK

        elif comm.startswith('conn'):
            if mySock.sock is not None:
                logger.debug("Already connected")
                return
            if current.started:
                logger.debug("Game marked as started. First exit to start a new game.")
                return
            host, port = '127.0.0.1', 27531  # default
            if len(comm.split()) == 2:
                _, host = comm.split()
            if len(comm.split()) == 3:
                _, host, port = comm.split()
            logger.debug(f"Command make connection with host {host} port {port}")
            try:
                mySock.open()
                mySock.connect(host, int(port))  # with timeout
                logger.debug(f"Successfully connected to remote host {host}, port {port}")
            except Exception as err:
                mySock.sock = None
                logger.debug(f"Error trying to connect: {err}")
                return

            if mySock.sock is not None:  # connected
                if not tReceiveHandler.isListening:
                    tReceiveHandler.start()

        elif comm.startswith('chat'):
            if len(comm.split()) == 1:
                return
            if len(comm.split()) > 1:
                _, txt = comm.split(' ', 1)  # strip first word
                txt = txt.strip()  # trim whitespace
                logger.debug(f"Command send chat message: {comm.strip()}")
                msg = dxp.msg_chat(txt)
                try:
                    mySock.send(msg)
                    logger.debug(f"snd CHAT: {msg}")
                except Exception as err:
                    logger.debug(f"Error sending chat message: {err}")
                    return

        elif comm.startswith('gamereq'):
            if current.started:
                logger.debug("Game already started; gamereq not allowed")
                return
            logger.debug(f"Command request new game: {comm.strip()}")
            last_move = None
            accepted = None
            myColor = "W"  # default
            gameTime = "120"  # default
            numMoves = "50"  # default
            if len(comm.split()) == 2:
                _, myColor = comm.split()
            if len(comm.split()) == 3:
                _, myColor, gameTime = comm.split()
            if len(comm.split()) == 4:
                _, myColor, gameTime, numMoves = comm.split()

            myColor = DXP_WHITE if myColor.upper().startswith('W') else DXP_BLACK
            current.myColor = myColor  # 0 or 1
            current.gameTime = gameTime
            current.numMoves = numMoves
            msg = dxp.msg_gamereq(myColor, gameTime, numMoves, current.pos, current.get_color())
            try:
                mySock.send(msg)
                logger.debug(f"snd GAMEREQ: {msg}")
            except Exception as err:
                logger.debug(f"Error sending game request: {err}")

        elif comm.startswith('gameend'):
            if not current.started:
                logger.debug("Game already finished; gameend not allowed")
                return
            logger.debug(f"Command finish game: {comm.strip()}")
            if current.started and current.myColor != current.get_color():
                logger.debug("Message gameend not allowed; wait until your turn")
                return
            if len(comm.split()) == 2:
                _, reason = comm.split()
            else:
                reason = "0"
            msg = dxp.msg_gameend(reason)

            try:
                mySock.send(msg)
                logger.debug(f"snd GAMEEND: {msg}")
            except Exception as err:
                logger.debug(f"Error sending gameend message: {err}")

        elif comm.startswith('backreq'):
            if not current.started:
                logger.debug("Game not started; backreq not allowed")
                return
            logger.debug("Not yet supported")

        else:
            logger.debug(f"Command unknown: {comm.strip()}")
            logger.debug(f"Unknown command, type h for help: {comm.strip()}")


class ReceiveHandler(threading.Thread):
    # Subslass of Thread to handle incoming messages from client.

    def __init__(self):
        threading.Thread.__init__(self)
        self.isListening = False

    def run(self):
        # Handling incoming messages from server.
        # Excutes when thread started. Overriding python threading.Thread.run()

        logger.debug("ReceiveHandler started")
        global current, mySock, lock
        global accepted, last_move
        self.isListening = True
        logger.debug("DXP Client starts listening")
        while True:
            try:
                message = mySock.receive()  # wait for message
            except Exception as err:
                logger.debug(f"Error {err}")
                break

            lock.acquire()  # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK
            message = message[0:127]  # DXP max length
            dxpData = dxp.parse(message)
            if dxpData["type"] == "C":
                logger.debug(f"rcv CHAT: {message}")
                logger.debug(f"\nChat message: {dxpData['text']}")

            elif dxpData["type"] == "A":
                logger.debug(f"rcv GAMEACC: {message}")
                if dxpData["accCode"] == "0":
                    current.started = True
                    current.myColor = current.myColor  # as requested
                    current.engineName = dxpData["engineName"]
                    logger.debug(f"\nGame request accepted by {dxpData['engineName']}")
                    accepted = True
                else:
                    current.started = False
                    logger.debug(f"\nGame request NOT accepted by {dxpData['engineName']} Reason: {dxpData['accCode']}")
                    accepted = False

            elif dxpData["type"] == "E":
                logger.debug(f"rcv GAMEEND: {message}")
                logger.debug(f"\nRequest end of game accepted. Reason: {dxpData['reason']} Stop: {dxpData['stop']}")
                # Confirm game end by sending message back (if not sent by me)
                if current.started:
                    current.started = False
                    current.result = dxpData["reason"]
                    msg = dxp.msg_gameend(dxpData["reason"])
                    mySock.send(msg)
                    logger.debug(f"snd GAMEEND: {msg}")

            elif dxpData["type"] == "M":
                logger.debug(f"rcv MOVE: {message}")
                steps = [dxpData['from'], dxpData['to']]
                nsteps = list(map(int, steps))
                ntakes = list(map(int, dxpData['captures']))
                board = None
                all_moves, all_captures = current.pos.legal_moves()
                if not ntakes:
                    ntakes = [None]
                for move, capture in zip(all_moves, all_captures):
                    if move[0][0] == nsteps[0] and move[-1][1] == nsteps[-1] and sorted(ntakes) == sorted(capture):
                        board = move

                if board is not None:
                    last_move = board
                    logger.debug(f"\nMove received: {board}")
                    for move in board:
                        current.pos.move(move)
                else:
                    logger.debug(f"Error: received move is illegal [{message}]")

            elif dxpData["type"] == "B":
                # For the time being do not confirm request from server: send message back.
                logger.debug(f"rcv BACKREQ: {message}")
                accCode = "1"  # 0: BACK YES; 1: BACK NO; 2: CONTINUE
                msg = dxp.msg_backacc(accCode)
                mySock.send(msg)
                logger.debug(f"snd BACKACC: {msg}")

            elif dxpData["type"] == "K":
                # Answer to my request to move back
                logger.debug(f"rcv BACKACC: {message}")
                logger.debug(f"rcv BACKACC: {message}")  # TEST
                accCode = dxpData['accCode']
                if accCode == "0":
                    # Actions to go back in history as specified in my request
                    raise NotImplementedError("Moving back is not implemented")

            else:
                logger.debug(f"rcv UNKNOWN: {message}")
                logger.debug(f"\nrcv Unknown message: {message}")

            lock.release()  # LOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCKLOCK

        self.isListening = False
        logger.error("Listening stopped; connection broken")
        logger.debug("Connection broken; receiveHandler stopped. ")
        logger.debug("Save your data and exit program to start again. ")
        return None


dxp = DamExchange()  # global, singleton
mySock = MySocket()  # global, singleton
current = GameStatus()  # global; use default parms
lock = threading.Lock()  # global

# use 1 thread to listen to incoming messages
tConsoleHandler = ConsoleHandler()  # Thread subclass instance
tReceiveHandler = ReceiveHandler()  # Thread subclass instance. Start when connected
