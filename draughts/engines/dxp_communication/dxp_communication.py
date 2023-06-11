# This file is an adaptation of DXC100_draughts_client (https://github.com/akalverboer/DXC100_draughts_client) by akalverboer.

from __future__ import annotations
import threading
import logging
from draughts.engines.dxp_communication.dxp_classes import DamExchange, MySocket, GameStatus, DXP_WHITE, DXP_BLACK
from draughts import Move, WHITE
from typing import Optional

logger = logging.getLogger("pydraughts")


class Receiver:
    def __init__(self, sender: Sender) -> None:
        self.sender = sender
        self.accepted: Optional[bool] = None
        self.gameend_sent = False
        self.last_move: Optional[Move] = None
        self.last_move_changed = False
        self.listening = False
        self.receive_thread_started = False
        self.backreq_accepted: Optional[bool] = None
        self.takeback_in_progress = False
        self.receive_thread = threading.Thread(target=self.receive)

    def start(self) -> None:
        self.receive_thread_started = True
        self.receive_thread.start()

    def close(self) -> None:
        if self.receive_thread_started:
            self.receive_thread.join()

    def receive(self) -> None:
        logger.debug("DXP Client starts listening")
        self.listening = True
        while True:
            try:
                message = self.sender.socket.receive()  # wait for message
            except Exception as err:
                logger.debug(f"Error {err}")
                self.sender.socket.close()
                break

            message = message[0:127]  # DXP max length
            dxp_data = self.sender.dxp.parse(message)
            if dxp_data["type"] == "C":
                logger.debug(f"rcv CHAT: {message}")
                logger.debug(f"\nChat message: {dxp_data['text']}")

            elif dxp_data["type"] == "A":
                logger.debug(f"rcv GAMEACC: {message}")
                if dxp_data["accCode"] == "0":
                    self.sender.current.engine_color = self.sender.current.engine_color  # as requested
                    self.sender.current.engineName = dxp_data["engineName"]
                    logger.debug(f"\nGame request accepted by {dxp_data['engineName']}")
                    self.accepted = True
                    self.gameend_sent = False
                    self.sender.current.started = True
                else:
                    logger.debug(f"\nGame request NOT accepted by {dxp_data['engineName']} Reason: {dxp_data['accCode']}")
                    self.accepted = False
                    self.sender.current.started = False

            elif dxp_data["type"] == "E":
                logger.debug(f"rcv GAMEEND: {message}")
                logger.debug(f"\nRequest end of game accepted. Reason: {dxp_data['reason']} Stop: {dxp_data['stop']}")
                # Confirm game end by sending message back (if not sent by me)
                if self.sender.current.started and not self.gameend_sent:
                    self.sender.current.result = dxp_data["reason"]
                    msg = self.sender.dxp.msg_gameend(str(dxp_data["reason"]))  # `str` is there only for mypy.
                    self.sender.socket.send(msg)
                    logger.debug(f"snd GAMEEND: {msg}")
                    self.gameend_sent = True
                    self.sender.current.started = False

            elif dxp_data["type"] == "M":
                logger.debug(f"rcv MOVE: {message}")
                steps = [dxp_data['from'], dxp_data['to']]
                nsteps = list(map(int, steps))
                ntakes_int = list(map(int, dxp_data['captures']))
                ntakes = list(map(lambda pos: str(pos).zfill(2), sorted(ntakes_int)))
                logger.debug(f"FEN: {self.sender.current.pos.fen}, Steps: {nsteps}, Takes: {ntakes}")
                correct_move = None
                while True:
                    if not self.takeback_in_progress:
                        break
                for move in self.sender.current.pos.legal_moves():
                    if move.hub_position_move == f"{str(nsteps[0]).zfill(2)}{str(nsteps[-1]).zfill(2)}{''.join(ntakes)}":
                        correct_move = move

                if correct_move is not None:
                    self.sender.current.pos.push(correct_move)
                    self.last_move = correct_move
                    logger.debug(f"Move received: {correct_move.steps_move}")
                    self.last_move_changed = True
                else:
                    move_history = list(map(lambda old_move: old_move.steps_move, self.sender.current.pos.move_stack))
                    logger.debug(f"Error: received move is illegal [{message}]\nMove history: {move_history}")

            elif dxp_data["type"] == "B":
                # For the time being do not confirm request from server: send message back.
                logger.debug(f"rcv BACKREQ: {message}")
                acc_code = "1"  # 0: BACK YES; 1: BACK NO; 2: CONTINUE
                msg = self.sender.dxp.msg_backacc(acc_code)
                self.sender.socket.send(msg)
                logger.debug(f"snd BACKACC: {msg}")

            elif dxp_data["type"] == "K":
                # Answer to my request to move back
                logger.debug(f"rcv BACKACC: {message}")
                logger.debug(f"rcv BACKACC: {message}")  # TEST
                acc_code = dxp_data['accCode']
                if acc_code == "0":
                    # Actions to go back in history as specified in my request
                    self.backreq_accepted = True
                elif acc_code == "1":
                    logger.debug("Engine doesn't support going back.")
                    self.backreq_accepted = False
                else:
                    logger.debug("Engine wants to continue the game.")
                    self.backreq_accepted = False

            else:
                logger.debug(f"rcv UNKNOWN: {message}")
                logger.debug(f"\nrcv Unknown message: {message}")

        self.listening = False


class Sender:
    def __init__(self) -> None:
        self.dxp = DamExchange()
        self.socket = MySocket()
        self.current = GameStatus("W")
        self.receiver = Receiver(self)

    def setup(self, fen: str, variant: str) -> None:
        logger.debug(f"FEN: {fen.strip()}, Variant: {variant}")
        engine_color = DXP_BLACK if fen[0] == 'B' else DXP_WHITE
        self.current = GameStatus(fen=fen, engine_color=engine_color, variant=variant)

    def send_move(self, move: Move) -> None:
        logger.debug(f"FEN: {self.current.pos.fen}, Steps: {move.steps_move}, Captures: {move.captures}")
        time_spent = 0
        self.receiver.last_move_changed = False
        self.current.pos.push(move)
        msg = self.dxp.msg_move(move.steps_move, move.captures, time_spent)
        try:
            self.socket.send(msg)
            logger.debug(f"snd MOVE: {msg}")
        except Exception as err:
            logger.debug(f"Error sending move: {err}")
            return

    def connect(self, host: str, port: int) -> None:
        logger.debug(f"Host: {host}, Port: {port}")
        try:
            self.socket.open()
            self.socket.connect(host, int(port))  # with timeout
            logger.debug(f"Successfully connected to remote host {host}, port {port}")
        except Exception as err:
            self.socket.sock = None
            logger.debug(f"Error trying to connect: {err}")
            return
        self.receiver.start()

    def disconnect(self) -> None:
        logger.debug("Attempting to disconnect.")
        try:
            self.socket.close()
            logger.debug("Successfully closed socket.")
        except Exception as err:
            self.socket.sock = None
            logger.debug(f"Error trying to close socket: {err}")
        self.receiver.close()

    def chat(self, text: str) -> None:
        text = text.strip()  # trim whitespace
        logger.debug(f"Text: {text}")
        msg = self.dxp.msg_chat(text)
        try:
            self.socket.send(msg)
            logger.debug(f"snd CHAT: {msg}")
        except Exception as err:
            logger.debug(f"Error sending chat message: {err}")

    def gamereq(self, engine_color: str, time: int, max_moves: int) -> None:
        logger.debug(f"Engine color: {engine_color}, Time: {time}, Max moves: {max_moves}")
        dxp_color = DXP_WHITE if engine_color.upper().startswith('W') else DXP_BLACK
        msg = self.dxp.msg_gamereq(dxp_color, time, max_moves, self.current.pos, self.current.get_color())
        try:
            self.socket.send(msg)
            logger.debug(f"snd GAMEREQ: {msg}")
        except Exception as err:
            logger.debug(f"Error sending game request: {err}")

    def gameend(self) -> None:
        logger.debug("Attempting to send a gameend.")
        reason = "0"
        msg = self.dxp.msg_gameend(reason)
        self.receiver.gameend_sent = True
        try:
            self.socket.send(msg)
            logger.debug(f"snd GAMEEND: {msg}")
        except Exception as err:
            logger.debug(f"Error sending gameend message: {err}")

    def backreq(self, move: int, color: int) -> None:
        logger.debug(f"Request to return to {move}th move with {'WHITE' if color == WHITE else 'BLACK'} to move.")
        msg = self.dxp.msg_backreq(move, DXP_WHITE if color == WHITE else DXP_BLACK)
        self.receiver.last_move_changed = False
        self.receiver.takeback_in_progress = True
        try:
            self.socket.send(msg)
            logger.debug(f"snd BACKREQ: {msg}")
        except Exception as err:
            logger.debug(f"Error sending backreq request: {err}")
