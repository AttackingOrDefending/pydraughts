from draughts.engines.checkerboard_extra.engine_64 import Engine64
from draughts.engines.checkerboard_extra.engine_client import Engine32
import os
import draughts
import draughts.engine
import logging
from draughts.convert import move_to_variant
from typing import Union, List, Any, Dict, Tuple

logger = logging.getLogger("pydraughts")


class CheckerBoardEngine:
    def __init__(self, command: Union[List[str], str], divide_time_by: int = 40, checkerboard_timing: bool = False, ENGINE: int = 5) -> None:
        if type(command) == str:
            command = [command]
        command = list(filter(bool, command))
        command = " ".join(command)
        if "\\" not in command and "/" not in command:
            self.cwd = os.path.realpath(os.path.expanduser("."))
            self.command = os.path.join(self.cwd, command)
        else:
            self.command = command
        self.ENGINE = ENGINE
        self.info = None
        self.id = {}
        self.result = None
        self.divide_time_by = divide_time_by
        self.checkerboard_timing = checkerboard_timing
        self._sent_variant = False
        self.engine, self.bits = self._open_engine()
        self.id["name"] = self.engine.enginecommand('name')[0].decode()

    def _open_engine(self) -> Union[Tuple[Engine64, int], Tuple[Engine32, int]]:
        """Open the engine process."""
        try:
            return Engine64(self.command), 64
        except Exception:
            return Engine32(self.command), 32

    def setoption(self, name: str, value: Union[str, int]) -> None:
        """Set an engine option."""
        if name == 'divide-time-by':
            self.divide_time_by = value
        else:
            self.engine.enginecommand(f"set {name} {value}")

    def configure(self, options: Dict[str, Union[str, int]]) -> None:
        """Configure many options at once."""
        for name, value in options.items():
            self.setoption(name, value)

    def kill_process(self) -> None:
        """Kill the engine process."""
        if self.bits == 32:
            self.engine.shutdown_server32()
        else:
            self.engine.kill_process()

    def play(self, board: draughts.Board, time_limit: Any) -> Any:
        """Engine search."""
        time = time_limit.time
        inc = time_limit.inc
        depth = time_limit.depth
        nodes = time_limit.nodes
        movetime = time_limit.movetime

        if not inc:
            inc = 0

        if not self._sent_variant:
            if board.variant == 'russian':
                self.engine.enginecommand('set gametype 25')
            elif board.variant == 'brazilian':
                self.engine.enginecommand('set gametype 26')
            elif board.variant == 'italian':
                self.engine.enginecommand('set gametype 22')
            elif board.variant == 'english':
                self.engine.enginecommand('set gametype 21')
            self._sent_variant = True

        if board.move_stack:
            gamehist = f'set gamehist {board._last_non_reversible_fen} {" ".join(list(map(lambda move: move.pdn_move, board._reversible_moves)))}'
            if len(gamehist) > 256:
                gamehist = " ".join(gamehist[-256:].split()[1:])
            self.engine.enginecommand(gamehist)

        time_to_use = None
        if time:

            if time < 0 and inc < 0:
                time = 0
                inc = 0
            elif time < 0:
                inc = max(inc + time, 0)
                time = 0
            elif inc < 0:
                time = max(time + inc, 0)
                inc = 0

            if self.checkerboard_timing:
                if time < inc * .4:
                    time_to_use = inc * .4
                elif time < inc:
                    time_to_use = time
                else:
                    time_to_use = inc + (time - inc) / 2.5
            else:
                time_to_use = time / self.divide_time_by

        logger.debug(f"Fen: {board.fen}, Time to use: {time_to_use}, Time: {time}, Inc: {inc}, Movetime: {movetime}")

        hub_pos_move, info, cbmove, result = self.engine.getmove(board, time_to_use, time, inc, movetime)

        logger.debug(f"Hub Pos Move: {hub_pos_move}, CBMove: {cbmove}, Info: {info}, Result: {result}")

        if hub_pos_move:
            hub_move = '-'.join([hub_pos_move[i:i+2] for i in range(0, len(hub_pos_move), 2)])
            bestmove = draughts.Move(board, hub_move=move_to_variant(hub_move, board.variant, to_algebraic=False))
        else:
            steps = []
            positions = [cbmove['from']]
            jumps = max(cbmove['jumps'], 1)
            for pos in cbmove['path'][1:jumps]:
                positions.append(pos)
            positions.append(cbmove['to'])
            for pos in positions:
                steps.append(self._row_col_to_num(board, pos[1], pos[0]))  # Checkerboard returns first the column, then the row

            steps = list(map(lambda step: int(move_to_variant(str(step), board.variant, to_algebraic=False)), steps))
            bestmove = draughts.Move(board, steps_move=steps)

        self.info = info.decode()
        self.result = result
        return draughts.engine.PlayResult(bestmove, None, {'info': self.info, 'result': self.result})

    def _row_col_to_num(self, board: draughts.Board, row: int, col: int) -> int:
        """Get the square from the row and column."""
        if row % 2 == 0:
            col = ((col + 2) / 2) - 1
        else:
            col = ((col + 1) / 2) - 1
        # Because:
        # 1. In italian the bottom-left square isn't playable, so in CheckerBoard the board is flipped vertically.
        # 2. In most variants the bottom-left square for the starting side (usually white) is in column a,
        # while in english black starts, so the bottom-left square for the starting side (black) is in row h.
        flip_column = board.variant not in ['english', 'italian']
        if flip_column:
            col = board._game.board.width - 1 - col
        # Because in english black starts
        white_starts = board.variant not in ['english']
        if not white_starts:
            row = (board._game.board.height - 1) - row
        loc = board._game.board.position_layout.get(row, {}).get(col)
        return loc
