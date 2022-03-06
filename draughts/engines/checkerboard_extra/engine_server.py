import ctypes
import draughts
from draughts.engines.checkerboard_extra.get_checker_board import get_board, from_board
import os
from typing import Tuple, Optional, Union, Dict, Any

from msl.loadlib import Server32

with open(os.path.join(os.path.dirname(__file__), 'engine_name.txt')) as file:
    DLL_name = file.read()


class Engine32Server(Server32):

    def __init__(self, host: str, port: int, **kwargs: Any) -> None:
        super(Engine32Server, self).__init__(DLL_name, 'windll', host, port)

    def enginecommand(self, command: str) -> Tuple[bytes, int]:
        """Send an enginecommand to the engine."""
        output = ctypes.create_string_buffer(b'', 1024)
        result = self.lib.enginecommand(ctypes.create_string_buffer(bytes(command.encode('ascii')), 256), output)
        return output.value, result

    def getmove(self, game: draughts.Game, maxtime: Union[int, float, None] = None, time: Union[int, float, None] = None, increment: Union[int, float, None] = None, movetime: Union[int, float, None] = None) -> Tuple[Optional[str], bytes, Dict[str, Any], int]:
        """Send a getmove to the engine."""

        # From CheckerBoard API:
        WHITE = 1
        BLACK = 2

        board = get_board(game)

        # Reversed color because red (black) starts first and not white in english checkers in Checkerboard.
        color = BLACK if game.whose_turn() == draughts.WHITE else WHITE
        white_starts = game.variant not in ['english']
        if white_starts:
            color = 3 - color

        info = 0
        moreinfo = 0
        if movetime:
            info = info | (1 << 1)  # 2nd bit means the engine has to think for exactly maxtime seconds
        elif time:
            if time / .01 > 2 ** 15 - 1 or increment / .01 > 2 ** 15 - 1:
                info = info | (1 << 3)  # 0.1 seconds
                info = info | (1 << 4)  # 0.1 seconds
                time = int(time / .1)
                increment = int(increment / .1)
            elif time / .001 > 2 ** 15 - 1 or increment / .001 > 2 ** 15 - 1:
                info = info | (1 << 3)  # 0.01 seconds
                time = int(time / .01)
                increment = int(increment / .01)
            else:
                info = info | (1 << 4)  # 0.001 seconds
                time = int(time / .001)
                increment = int(increment / .001)
            bin_time = bin(time)[2:].zfill(16)
            if len(bin_time) > 16:
                bin_time = '1' * 16
            bin_inc = bin(increment)[2:].zfill(16)
            if len(bin_inc) > 16:
                bin_inc = '1' * 16
            moreinfo = eval('0b' + bin_time + bin_inc)

        if movetime:
            maxtime = ctypes.c_double(float(movetime))
        else:
            maxtime = ctypes.c_double(float(maxtime))
        output = ctypes.create_string_buffer(b'', 1024)
        playnow = ctypes.c_int(0)

        class coor(ctypes.Structure):
            _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int)]

        class CBmove(ctypes.Structure):
            _fields_ = [("jumps", ctypes.c_int), ("newpiece", ctypes.c_int), ("oldpiece", ctypes.c_int), ("from", coor), ("to", coor), ("path", coor * 12), ("del", coor * 12), ("delpiece", ctypes.c_int * 12)]

        self.lib.getmove.argtypes = [((ctypes.c_int * 8) * 8), ctypes.c_int, ctypes.c_double, (ctypes.c_char * 1024), ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int, ctypes.POINTER(CBmove)]

        cbmove = CBmove()

        result = self.lib.getmove(board, color, maxtime, output, ctypes.byref(playnow), info, moreinfo, ctypes.byref(cbmove))

        old_fen = game.get_fen()
        new_fen = from_board(board, game)
        our_pieces, opponents_pieces = (['w', 'W'], ['b', 'B']) if old_fen[0] == 'W' else (['b', 'B'], ['w', 'W'])
        captures = []
        start_pos, end_pos = None, None
        for index in range(1, len(old_fen)):
            if old_fen[index] in our_pieces and new_fen[index] == 'e':
                start_pos = index
            elif new_fen[index] in our_pieces and old_fen[index] == 'e':
                end_pos = index
            elif old_fen[index] in opponents_pieces and new_fen[index] == 'e':
                captures.append(index)
        if start_pos and end_pos:
            hub_pos_move = game.make_len_2(start_pos) + game.make_len_2(end_pos) + game.sort_captures(captures)
        else:
            hub_pos_move = None

        cbmove_output_2 = {}
        cbmove_output_2['jumps'] = cbmove.jumps
        cbmove_output_2['oldpiece'] = cbmove.oldpiece
        cbmove_output_2['newpiece'] = cbmove.newpiece
        cbmove_output_2['to'] = cbmove.to.x, cbmove.to.y
        cbmove.to = getattr(cbmove, 'from')
        cbmove_output_2['from'] = cbmove.to.x, cbmove.to.y
        cbmove_output_2['path'] = [(cbmove.path[i].x, cbmove.path[i].y) for i in range(12)]
        cbmove.path = getattr(cbmove, 'del')
        cbmove_output_2['del'] = [(cbmove.path[i].x, cbmove.path[i].y) for i in range(12)]
        cbmove_output_2['delpiece'] = [cbmove.delpiece[i] for i in range(12)]
        return hub_pos_move, output.value, cbmove_output_2, result
