from draughts.engines.dxp import DXPEngine
from draughts.engines.hub import HubEngine
from draughts.engines.checkerboard import CheckerBoardEngine
from typing import Optional, Union, Dict
from draughts.core.move import Move


class Limit:
    def __init__(self, time: Union[int, float, None] = None, inc: Union[int, float, None] = None, depth: Optional[int] = None, nodes: Optional[int] = None, movetime: Union[int, float, None] = None):
        assert time is not None or depth is not None or nodes is not None or movetime is not None
        self.time = time
        self.inc = inc
        self.depth = depth
        self.nodes = nodes
        self.movetime = movetime


class PlayResult:
    def __init__(self, move: Optional[Move] = None, ponder: Optional[Move] = None, info: Optional[Dict] = None, draw_offered: bool = False, resign: bool = False):
        self.move = move
        self.ponder = ponder
        self.info = info
        self.draw_offered = draw_offered
        self.resign = resign


__all__ = ['HubEngine', 'DXPEngine', 'CheckerBoardEngine', 'Limit', 'PlayResult']
