import ctypes
import draughts
from draughts.engines.checkerboard_extra.get_checker_board import get_board

from msl.loadlib import Server32

DLL_name = ""


class Engine32Server(Server32):

    def __init__(self, host, port, **kwargs):
        super(Engine32Server, self).__init__(DLL_name, 'windll', host, port)

    def enginecommand(self, command):
        output = ctypes.create_string_buffer(b'', 1024)
        result = self.lib.enginecommand(ctypes.create_string_buffer(bytes(command.encode('ascii')), 256), output)
        return output.value, result

    def getmove(self, game, maxtime, increment, movetime, depth):

        # From CheckerBoard API:
        WHITE = 1
        BLACK = 2

        board = get_board(game)

        # Reversed color because red (black) starts first in Checkerboard and not white
        color = BLACK if game.whose_turn() == draughts.WHITE else WHITE
        if movetime:
            maxtime = ctypes.c_double(float(movetime))
        elif depth:
            maxtime = ctypes.c_double(float(depth))
        else:
            maxtime = ctypes.c_double(float(maxtime))
        output = ctypes.create_string_buffer(b'', 1024)
        playnow = ctypes.c_int(0)
        info = 0
        moreinfo = 0
        if movetime:
            info = info | (1 << 1)  # 2nd bit means the engine has to think for exactly maxtime seconds
        elif depth:
            info = info | (1 << 3)  # 4th bit means the engine has to search for exactly maxtime depth
        elif int(increment):
            info = info | (1 << 2)  # 3rd bit means the game has increment
            moreinfo = int(increment)

        class coor(ctypes.Structure):
            _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int)]

        class CBmove(ctypes.Structure):
            _fields_ = [("jumps", ctypes.c_int), ("newpiece", ctypes.c_int), ("oldpiece", ctypes.c_int), ("from", coor), ("to", coor), ("path", coor * 12), ("del", coor * 12), ("delpiece", ctypes.c_int * 12)]

        self.lib.getmove.argtypes = [((ctypes.c_int * 8) * 8), ctypes.c_int, ctypes.c_double, (ctypes.c_char * 1024), ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int, ctypes.POINTER(CBmove)]

        cbmove = CBmove()
        result = self.lib.getmove(board, color, maxtime, output, ctypes.byref(playnow), info, moreinfo, ctypes.byref(cbmove))

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
        return output.value, cbmove_output_2, result
