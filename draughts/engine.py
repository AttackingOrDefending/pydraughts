from draughts.engines.dxp import DXPEngine
from draughts.engines.hub import HubEngine
from draughts.engines.checkerboard import CheckerBoardEngine


class Limit:
    def __init__(self, time=None, inc=None, depth=None, nodes=None, movetime=None):
        assert time is not None or depth is not None or nodes is not None or movetime is not None
        self.time = time
        self.inc = inc
        self.depth = depth
        self.nodes = nodes
        self.movetime = movetime
