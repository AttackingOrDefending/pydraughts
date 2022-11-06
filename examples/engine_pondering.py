from draughts.engine import HubEngine, Limit
from draughts import Board
import threading
import time

game = Board()
engine = HubEngine(["scan.exe", "hub"])
engine.init()
limit = Limit(time=10)
move = None


def ponder_result(game, limit):
    global move
    move = engine.play(game, limit, True)


thr = threading.Thread(target=ponder_result, args=(game, limit))
thr.start()
time.sleep(2)  # Opponent thinking
engine.ponderhit()
thr.join()

print(move.move.pdn_move)
