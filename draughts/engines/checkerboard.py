from draughts.engines.checkerboard_extra.engine_64 import Engine64
from draughts.engines.checkerboard_extra.engine_client import Engine32
import os
import draughts


class CheckerBoardEngine:
    def __init__(self, command, divide_time_by=40, ENGINE=5):
        self.cwd = os.path.realpath(os.path.expanduser("."))
        if type(command) == str:
            command = [command]
        command = list(filter(bool, command))
        command = " ".join(command)
        self.command = os.path.join(self.cwd, command)
        self.ENGINE = ENGINE
        self.engine = None
        self.info = None
        self.id = {}
        self.result = None
        self.divide_time_by = divide_time_by
        self.sent_variant = False
        self.bits = self.open_engine()
        self.id["name"] = self.engine.enginecommand('name')[0].decode()

    def open_engine(self):
        try:
            self.engine = Engine64(self.command, self.cwd)
            return 64
        except:
            self.engine = Engine32(self.command)  # I will see what I will do with it
            return 32

    def setoption(self, name, value):
        if name == 'divide-time-by':
            self.divide_time_by = value
        else:
            self.engine.enginecommand(f"set {name} {value}")

    def kill_process(self):
        if self.bits == 32:
            self.engine.shutdown_server32()
        else:
            self.engine.kill_process()

    def play(self, board, time_limit):
        time = time_limit.time
        inc = time_limit.inc
        depth = time_limit.depth
        nodes = time_limit.nodes
        movetime = time_limit.movetime

        if not self.sent_variant:
            if board.variant == 'russian':
                self.engine.enginecommand('set gametype 25')
            elif board.variant == 'brazilian':
                self.engine.enginecommand('set gametype 26')
            elif board.variant == 'italian':
                self.engine.enginecommand('set gametype 22')
            elif board.variant == 'english':
                self.engine.enginecommand('set gametype 21')
            self.sent_variant = True
        
        if time:
            time /= self.divide_time_by

        hub_pos_move, info, cbmove, result = self.engine.getmove(board, time, inc, movetime, depth)

        if hub_pos_move:
            bestmove = draughts.Move(board, hub_position_move=hub_pos_move)
        else:
            steps = []
            positions = [cbmove['from']]
            jumps = max(cbmove['jumps'], 1)
            for pos in cbmove['path'][1:jumps]:
                positions.append(pos)
            positions.append(cbmove['to'])
            for pos in positions:
                steps.append(
                    self.row_col_to_num(board, pos[1], pos[0]))  # Checkerboard returns first the column, then the row

            bestmove = draughts.Move(board, steps_move=steps)

        self.info = info.decode()
        self.result = result
        return bestmove, None

    def row_col_to_num(self, board, row, col):
        if row % 2 == 0:
            col = ((col + 2) / 2) - 1
        else:
            col = ((col + 1) / 2) - 1
        row = (board.board.height - 1) - row
        loc = board.board.position_layout.get(row, {}).get(col)
        return loc
