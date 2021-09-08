import ctypes
from ctypes import wintypes
import os
import draughts
from draughts.engines.checkerboard_extra.get_checker_board import get_board, from_board


class Engine64:
    def __init__(self, command, cwd=None):
        if cwd is None:
            cwd = os.path.realpath(os.path.expanduser("."))
        os.add_dll_directory(cwd)
        self.engine = ctypes.windll.LoadLibrary(command)

    def kill_process(self):
        handle = self.engine._handle
        try:
            ctypes.windll.kernel32.FreeLibrary.argtypes = [wintypes.HMODULE]
            ctypes.windll.kernel32.FreeLibrary(handle)
        except:
            self.engine.dlcose(handle)

    def enginecommand(self, command):
        output = ctypes.create_string_buffer(b'', 1024)
        result = self.engine.enginecommand(ctypes.create_string_buffer(bytes(command.encode('ascii')), 256), output)
        return output.value, result

    def getmove(self, game, maxtime=None, increment=None, movetime=None, depth=None):
        assert maxtime is not None or movetime is not None or depth is not None

        # From CheckerBoard API:
        WHITE = 1
        BLACK = 2

        board = get_board(game)

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

        self.engine.argtypes = [((ctypes.c_int * 8) * 8), ctypes.c_int, ctypes.c_double, (ctypes.c_char * 1024), ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int, ctypes.POINTER(CBmove)]

        cbmove = CBmove()

        result = self.engine.getmove(board, color, maxtime, output, ctypes.byref(playnow), info, moreinfo,  ctypes.byref(cbmove))

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
