from draughts.convert import move_from_variant
from typing import List, Optional, Any


class Move:
    def __init__(self, board: Any = None, board_move: List[List[int]] = None, hub_move: str = None, hub_position_move: str = None, pdn_move: str = None, pdn_position_move: str = None, steps_move: List[int] = None, li_api_move: str = None, li_one_move: str = None, has_captures: Optional[bool] = None, possible_moves: List[List[List[int]]] = None, possible_captures: List[List[Optional[int]]] = None, hub_to_pdn_pseudolegal: bool = False, variant: Optional[str] = None, notation: int = 2, squares_per_letter: int = 4) -> None:
        self.board_move = board_move
        self.hub_move = hub_move
        self.hub_position_move = hub_position_move
        self.pdn_move = pdn_move
        self.pdn_position_move = pdn_position_move
        self.steps_move = steps_move
        self.li_api_move = li_api_move
        self.li_one_move = li_one_move
        self.ambiguous = None
        self.captures = None
        self.has_captures = has_captures
        self.possible_moves = possible_moves
        self.possible_captures = possible_captures
        self.hub_to_pdn_pseudolegal = hub_to_pdn_pseudolegal
        self.variant = variant
        self.original_pdn_move = self.pdn_move
        self.notation = notation
        self.squares_per_letter = squares_per_letter

        if board_move or hub_move or hub_position_move or pdn_move or pdn_position_move or steps_move or li_api_move or li_one_move:
            if board or possible_moves and possible_captures:
                if not possible_moves or not possible_captures:
                    self.possible_moves, self.possible_captures = board.legal_moves()
                self._to_board()
                self.captures = self.possible_captures[self.possible_moves.index(self.board_move)]
                self.captures = [] if self.captures[0] is None else self.captures
                self.has_captures = bool(self.captures)
                self._from_board()
            else:
                self._no_board()

    def _make_len_2(self, move):
        """
        Add a 0 in the front of the square if it is only 1 digit.
        e.g. The move 5 will be turned to 05 but the move 23 will be left the same.
        """
        return f'0{move}' if len(str(move)) == 1 else str(move)

    def _sort_captures(self, captures):
        """
        Sort the captures from the smallest number to the highest.
        e.g. [10, 30, 19] will change to '101930'.
        This function exists because hub engines return the captures in alphabetical order
        (e.g. for the move 231201 scan returns 23x01x07x18 instead of 23x01x18x07)
        """
        if captures and captures[0] is None:
            captures = []
        captures = list(map(self._make_len_2, captures))
        captures.sort()
        captures = ''.join(captures)
        return captures

    def _to_board(self) -> None:
        """Convert the move to all other move types. Requires a Game() object to make the conversions."""

        # Hub related move

        if self.hub_move:
            # Hub move
            if "-" in self.hub_move:
                self.hub_position_move = "".join(list(map(self._make_len_2, self.hub_move.split("-"))))
            else:
                self.hub_position_move = "".join(list(map(self._make_len_2, self.hub_move.split("x"))))

        # PDN related move

        if self.pdn_move:
            # PDN move
            self.pdn_move = move_from_variant(self.pdn_move, variant=self.variant, notation=self.notation, squares_per_letter=self.squares_per_letter)

            if "-" in self.pdn_move:
                self.pdn_position_move = "".join(list(map(self._make_len_2, self.pdn_move.split("-"))))
            else:
                self.pdn_position_move = "".join(list(map(self._make_len_2, self.pdn_move.split("x"))))

        # Hub related move

        if self.hub_position_move:
            # Hub position move
            moves_li_board = {}
            for possible_move, possible_capture in zip(self.possible_moves, self.possible_captures):
                li_move = self._make_len_2(possible_move[0][0]) + self._make_len_2(
                    possible_move[-1][1]) + self._sort_captures(possible_capture)
                moves_li_board[li_move] = possible_move
            board_move = moves_li_board[self.hub_position_move]
            self.board_move = board_move

        # PDN related move

        elif self.pdn_position_move:
            # PDN position move
            moves_li_board = {}
            if len(self.pdn_position_move) == 4:
                self.ambiguous = False
                for possible_move, possible_capture in zip(self.possible_moves, self.possible_captures):
                    li_move = self._make_len_2(possible_move[0][0]) + self._make_len_2(possible_move[-1][1])
                    moves_li_board[li_move] = possible_move
            else:
                self.ambiguous = True
                for possible_move, possible_capture in zip(self.possible_moves, self.possible_captures):
                    steps = [possible_move[0][0]]
                    for move in possible_move:
                        steps.append(move[1])
                    li_move = "".join(list(map(self._make_len_2, steps)))
                    moves_li_board[li_move] = possible_move
            board_move = moves_li_board[self.pdn_position_move]
            self.board_move = board_move

        # Board related moves

        elif self.steps_move:
            # steps_move
            board_move = []
            for index in range(1, len(self.steps_move)):
                board_move.append([self.steps_move[index - 1], self.steps_move[index]])
            self.board_move = board_move

        elif self.li_api_move:
            # li_api_move
            board_move = []
            for move in self.li_api_move:
                board_move.append([int(move[:2]), int(move[2:])])
            self.board_move = board_move

        elif self.li_one_move:
            # li_one_move
            steps = [int(self.li_one_move[i:i + 2]) for i in range(0, len(self.li_one_move), 2)]
            board_move = []
            for index in range(1, len(steps)):
                board_move.append([steps[index - 1], steps[index]])
            self.board_move = board_move

    def _from_board(self) -> None:
        """Convert the move to a board_move. Requires a Game() object to make the conversions."""

        # Board related move

        if not self.steps_move:
            # steps_move
            steps = [self.board_move[0][0]]
            for move in self.board_move:
                steps.append(move[1])
            self.steps_move = steps

        # Hub related moves

        if not self.hub_position_move:
            # Hub position move
            self.hub_position_move = self._make_len_2(self.board_move[0][0]) + self._make_len_2(self.board_move[-1][1])
            if self.captures:
                sorted_captures = self._sort_captures(self.captures)
                sorted_captures = [sorted_captures[i:i + 2] for i in range(0, len(sorted_captures), 2)]
                self.hub_position_move += "".join(list(map(self._make_len_2, sorted_captures)))

        if not self.hub_move:
            # Hub move
            positions = [self.hub_position_move[i:i + 2] for i in range(0, len(self.hub_position_move), 2)]
            separator = "x" if self.captures else "-"
            self.hub_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        # PDN related moves

        if not self.pdn_position_move:
            # starts_endings contains the start position and the end position of every possible move.
            # It is used to detect ambiguous PDN moves, so we know when we have to expand the PDN move.
            # e.g. Use 3x14x23 instead of 3x23.

            # PDN position move

            starts_endings = []
            for possible_move in self.possible_moves:
                starts_endings.append(self._make_len_2(possible_move[0][0]) + self._make_len_2(possible_move[-1][1]))
            self.ambiguous = starts_endings.count(self._make_len_2(self.board_move[0][0]) + self._make_len_2(self.board_move[-1][1])) >= 2
            if self.ambiguous:
                self.pdn_position_move = "".join(list(map(self._make_len_2, self.steps_move)))
            else:
                self.pdn_position_move = self._make_len_2(self.board_move[0][0]) + self._make_len_2(self.board_move[-1][1])

        if not self.pdn_move:
            # PDN move
            positions = [self.pdn_position_move[i:i + 2] for i in range(0, len(self.pdn_position_move), 2)]
            separator = "x" if self.captures else "-"
            self.pdn_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        # Board related moves

        if not self.li_api_move:
            # li_api_move
            li_api_move = []
            for move in self.board_move:
                li_api_move.append(self._make_len_2(move[0]) + self._make_len_2(move[1]))
            self.li_api_move = li_api_move

        if not self.li_one_move:
            # li_one_move
            self.li_one_move = "".join(list(map(self._make_len_2, self.steps_move)))

    def _no_board(self) -> None:
        """Makes as many conversions as possible if the board was not given."""

        # Board related moves

        if self.steps_move:
            # steps_move
            board_move = []
            for index in range(1, len(self.steps_move)):
                board_move.append([self.steps_move[index - 1], self.steps_move[index]])
            self.board_move = board_move

        elif self.li_api_move:
            # li_api_move
            board_move = []
            for move in self.li_api_move:
                board_move.append([int(move[:2]), int(move[2:])])
            self.board_move = board_move

        elif self.li_one_move:
            # li_one_move
            steps = [int(self.li_one_move[i:i + 2]) for i in range(0, len(self.li_one_move), 2)]
            board_move = []
            for index in range(1, len(steps)):
                board_move.append([steps[index - 1], steps[index]])
            self.board_move = board_move

        if self.board_move:
            # steps_move
            if not self.steps_move:
                steps = [self.board_move[0][0]]
                for move in self.board_move:
                    steps.append(move[1])
                self.steps_move = steps

            # li_api_move
            if not self.li_api_move:
                li_api_move = []
                for move in self.board_move:
                    li_api_move.append(self._make_len_2(move[0]) + self._make_len_2(move[1]))
                self.li_api_move = li_api_move

            # li_one_move
            if not self.li_one_move:
                self.li_one_move = "".join(list(map(self._make_len_2, self.steps_move)))

        # Hub related moves

        if self.hub_move:
            # Hub move
            if "-" in self.hub_move:
                self.has_captures = False
                self.hub_position_move = "".join(list(map(self._make_len_2, self.hub_move.split("-"))))
            else:
                self.has_captures = True
                self.hub_position_move = "".join(list(map(self._make_len_2, self.hub_move.split("x"))))
        elif self.hub_position_move:
            # Hub position move
            positions = [self.hub_position_move[i:i + 2] for i in range(0, len(self.hub_position_move), 2)]
            separator = "x" if self.has_captures else "-"
            self.hub_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        if self.hub_to_pdn_pseudolegal:
            # Pseudo-legal PDN move
            self.pdn_position_move = self.hub_position_move[:4]
            separator = "x" if self.has_captures else "-"
            self.pdn_move = self.pdn_position_move[:2] + separator + self.pdn_position_move[2:]

        # PDN related moves

        if self.pdn_move:
            # PDN move
            self.pdn_move = move_from_variant(self.pdn_move, variant=self.variant, notation=self.notation, squares_per_letter=self.squares_per_letter)

            if "-" in self.pdn_move:
                self.has_captures = False
                self.pdn_position_move = "".join(list(map(self._make_len_2, self.pdn_move.split("-"))))
            else:
                self.has_captures = True
                self.pdn_position_move = "".join(list(map(self._make_len_2, self.pdn_move.split("x"))))
        elif self.pdn_position_move:
            # PDN position move
            positions = [self.pdn_position_move[i:i + 2] for i in range(0, len(self.pdn_position_move), 2)]
            separator = "x" if self.has_captures else "-"
            self.pdn_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        if self.pdn_position_move:
            # Get if the move is ambiguous.
            self.ambiguous = not (len(self.pdn_position_move) == 4)
