from draughts.convert import move_from_variant
from typing import List, Optional, Any, Union


class Move:
    def __init__(self, board: Any = None, board_move: Optional[List[List[int]]] = None, hub_move: Optional[str] = None, hub_position_move: Optional[str] = None, pdn_move: Optional[str] = None, pdn_position_move: Optional[str] = None, steps_move: Optional[List[int]] = None, li_api_move: Optional[List[str]] = None, li_one_move: Optional[str] = None, has_captures: Optional[bool] = None, possible_moves: Optional[List[List[List[int]]]] = None, possible_captures: Optional[List[List[Optional[int]]]] = None, hub_to_pdn_pseudolegal: bool = False, variant: Optional[str] = None, is_null: Optional[bool] = None) -> None:
        self.ambiguous: Optional[bool] = None
        self.captures = None
        self.has_captures = has_captures
        if (possible_moves is None or possible_captures is None) and board:
            self.possible_moves, self.possible_captures = board.legal_moves()
        else:
            self.possible_moves = possible_moves
            self.possible_captures = possible_captures
        self.hub_to_pdn_pseudolegal = hub_to_pdn_pseudolegal
        self.variant = variant
        self.original_pdn_move = pdn_move
        self.is_null = is_null

        if self.is_null is None:
            self.is_null = board_move == [[0, 0]] or hub_move == '0-0' or hub_position_move == '0000' or pdn_move == '0-0' or pdn_position_move == '0000' or steps_move == [0, 0] or li_api_move == ['0000'] or li_one_move == '0000'

        if (board_move or hub_move or hub_position_move or pdn_move or pdn_position_move or steps_move or li_api_move or li_one_move) and not self.is_null:
            if self.possible_moves:
                self.board_move = self._to_board(board_move, hub_move, hub_position_move, pdn_move, pdn_position_move, steps_move, li_api_move, li_one_move)
                self.captures = self.possible_captures[self.possible_moves.index(self.board_move)]
                self.captures = [] if self.captures[0] is None else self.captures
                self.has_captures = bool(self.captures)
                self._from_board(hub_move, hub_position_move, pdn_move, pdn_position_move, steps_move, li_api_move, li_one_move)
            else:
                self._no_board(board_move, hub_move, hub_position_move, pdn_move, pdn_position_move, steps_move, li_api_move, li_one_move)
        elif self.is_null:
            self.board_move = [[0, 0]]
            self.hub_move = '0-0'
            self.hub_position_move = '0000'
            self.pdn_move = '0-0'
            self.pdn_position_move = '0000'
            self.steps_move = [0, 0]
            self.li_api_move = ['0000']
            self.li_one_move = '0000'

    def _make_len_2(self, move: Union[str, int]) -> str:
        """
        Add a 0 in the front of the square if it is only 1 digit.
        e.g. The move 5 will be turned to 05 but the move 23 will be left the same.
        """
        return f'0{move}' if len(str(move)) == 1 else str(move)

    def _sort_captures(self, captures: List[Optional[int]]) -> str:
        """
        Sort the captures from the smallest number to the highest.
        e.g. [10, 30, 19] will change to '101930'.
        This function exists because hub engines return the captures in alphabetical order
        (e.g. for the move 231201 scan returns 23x01x07x18 instead of 23x01x18x07)
        """
        if captures and captures[0] is None:
            captures = []
        return ''.join(list(sorted(map(self._make_len_2, captures))))

    def _to_board(self, board_move_given: Optional[List[List[int]]] = None, hub_move: Optional[str] = None, hub_position_move: Optional[str] = None, pdn_move: Optional[str] = None, pdn_position_move: Optional[str] = None, steps_move: Optional[List[int]] = None, li_api_move: Optional[List[str]] = None, li_one_move: Optional[str] = None) -> List[List[int]]:
        """Convert the move to a board_move. Requires a Game() object to make the conversions."""

        board_move = [] if board_move_given is None else board_move_given
        # Hub related move

        if hub_move:
            # Hub move
            if "-" in hub_move:
                hub_position_move = "".join(list(map(self._make_len_2, hub_move.split("-"))))
            else:
                hub_position_move = "".join(list(map(self._make_len_2, hub_move.split("x"))))

        # PDN related move

        if pdn_move:
            # PDN move
            pdn_move = move_from_variant(pdn_move, variant=self.variant)

            if "-" in pdn_move:
                pdn_position_move = "".join(list(map(self._make_len_2, pdn_move.split("-"))))
            else:
                pdn_position_move = "".join(list(map(self._make_len_2, pdn_move.split("x"))))

        # Hub related move

        if hub_position_move:
            # Hub position move
            moves_li_board = {}
            for possible_move, possible_capture in zip(self.possible_moves, self.possible_captures):
                li_move = self._make_len_2(possible_move[0][0]) + self._make_len_2(possible_move[-1][1]) + self._sort_captures(possible_capture)
                moves_li_board[li_move] = possible_move
            board_move = moves_li_board[hub_position_move]

        # PDN related move

        elif pdn_position_move:
            # PDN position move
            moves_li_board = {}
            if len(pdn_position_move) == 4:
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
            board_move = moves_li_board[pdn_position_move]

        # Board related moves

        elif steps_move:
            # steps_move
            board_move = []
            for index in range(1, len(steps_move)):
                board_move.append([steps_move[index - 1], steps_move[index]])

        elif li_api_move:
            # li_api_move
            board_move = []
            for move in li_api_move:
                board_move.append([int(move[:2]), int(move[2:])])

        elif li_one_move:
            # li_one_move
            steps = [int(li_one_move[i:i + 2]) for i in range(0, len(li_one_move), 2)]
            board_move = []
            for index in range(1, len(steps)):
                board_move.append([steps[index - 1], steps[index]])

        return board_move

    def _from_board(self, hub_move: Optional[str] = None, hub_position_move: Optional[str] = None, pdn_move: Optional[str] = None, pdn_position_move: Optional[str] = None, steps_move: Optional[List[int]] = None, li_api_move: Optional[List[str]] = None, li_one_move: Optional[str] = None) -> None:
        """Convert the move to all other move types. Requires a Game() object to make the conversions."""

        hub_move = "" if hub_move is None else hub_move
        hub_position_move = "" if hub_position_move is None else hub_position_move
        pdn_move = "" if pdn_move is None else pdn_move
        pdn_position_move = "" if pdn_position_move is None else pdn_position_move
        steps_move = [] if steps_move is None else steps_move
        li_api_move = [] if li_api_move is None else li_api_move
        li_one_move = "" if li_one_move is None else li_one_move

        # Board related move

        if not steps_move:
            # steps_move
            steps = [self.board_move[0][0]]
            for move in self.board_move:
                steps.append(move[1])
            steps_move = steps

        # Hub related moves

        if not hub_position_move:
            # Hub position move
            hub_position_move = self._make_len_2(self.board_move[0][0]) + self._make_len_2(self.board_move[-1][1])
            if self.captures:
                sorted_captures = self._sort_captures(self.captures)
                sorted_captures_list = [sorted_captures[i:i + 2] for i in range(0, len(sorted_captures), 2)]
                hub_position_move += "".join(list(map(self._make_len_2, sorted_captures_list)))

        if not hub_move:
            # Hub move
            positions = [hub_position_move[i:i + 2] for i in range(0, len(hub_position_move), 2)]
            separator = "x" if self.captures else "-"
            hub_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        # PDN related moves

        if not pdn_position_move:
            # starts_endings contains the start position and the end position of every possible move.
            # It is used to detect ambiguous PDN moves, so we know when we have to expand the PDN move.
            # e.g. Use 3x14x23 instead of 3x23.

            # PDN position move

            start_end = self._make_len_2(self.board_move[0][0]) + self._make_len_2(self.board_move[-1][1])
            same_start_ends = 0
            moves_with_same_start_end_and_captures = []
            for possible_move, possible_captures in zip(self.possible_moves, self.possible_captures):
                possible_start_end = self._make_len_2(possible_move[0][0]) + self._make_len_2(possible_move[-1][1])
                if possible_start_end == start_end:
                    same_start_ends += 1
                    possible_steps_move = [possible_move[0][0]]
                    for semi_move in possible_move:
                        possible_steps_move.append(semi_move[1])
                    moves_with_same_start_end_and_captures.append(possible_steps_move)
            self.ambiguous = same_start_ends >= 2
            if self.ambiguous:
                # From FMJD (https://pdn.fmjd.org/grammar.html#pdn-3-0-grammar):
                # Disambiguated capture sequences have to specify a complete sequence of intermediate squares
                # along the path of the capture. If there is a change in direction, an intermediate square is
                # the square where a turn in direction was made. If there was not a change in direction,
                # the intermediate square is the square immediately behind a captured piece.
                #
                # This means that if we continue going in the same direction,
                # the intermediate square is the square immediately behind the captured piece.
                # pydraughts supports providing a square not immediately behind the captured piece, but when we
                # convert it to a PDN move, we have to change it to the square immediately behind the captured piece.
                correct_start_ends = []
                for index in range(1, len(steps_move) - 1):
                    closest_distance = 1000

                    for steps_move in moves_with_same_start_end_and_captures:
                        distance = abs(steps_move[index - 1] - steps_move[index])

                        # New closest square
                        if distance < closest_distance:
                            closest_distance = distance
                            correct_start_ends = [steps_move]
                        # The same intermediate square.
                        # This means that the difference is in a later intermediate square.
                        elif distance == closest_distance:
                            correct_start_ends.append(steps_move)
                        moves_with_same_start_end_and_captures = correct_start_ends

                correct_move = correct_start_ends[0]

                pdn_position_move = "".join(list(map(self._make_len_2, correct_move)))
            else:
                pdn_position_move = self._make_len_2(self.board_move[0][0]) + self._make_len_2(self.board_move[-1][1])

        if not pdn_move:
            # PDN move
            positions = [pdn_position_move[i:i + 2] for i in range(0, len(pdn_position_move), 2)]
            separator = "x" if self.captures else "-"
            pdn_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        # Board related moves

        if not li_api_move:
            # li_api_move
            li_api_move = []
            for move in self.board_move:
                li_api_move.append(self._make_len_2(move[0]) + self._make_len_2(move[1]))

        if not li_one_move:
            # li_one_move
            li_one_move = "".join(list(map(self._make_len_2, steps_move)))

        self.hub_move = hub_move
        self.hub_position_move = hub_position_move
        self.pdn_move = pdn_move
        self.pdn_position_move = pdn_position_move
        self.steps_move = steps_move
        self.li_api_move = li_api_move
        self.li_one_move = li_one_move

    def _no_board(self, board_move_given: Optional[List[List[int]]] = None, hub_move: Optional[str] = None, hub_position_move: Optional[str] = None, pdn_move: Optional[str] = None, pdn_position_move: Optional[str] = None, steps_move: Optional[List[int]] = None, li_api_move: Optional[List[str]] = None, li_one_move: Optional[str] = None) -> None:
        """Makes as many conversions as possible if the board was not given."""

        board_move = [] if board_move_given is None else board_move_given
        hub_move = "" if hub_move is None else hub_move
        hub_position_move = "" if hub_position_move is None else hub_position_move
        pdn_move = "" if pdn_move is None else pdn_move
        pdn_position_move = "" if pdn_position_move is None else pdn_position_move
        steps_move = [] if steps_move is None else steps_move
        li_api_move = [] if li_api_move is None else li_api_move
        li_one_move = "" if li_one_move is None else li_one_move

        # Board related moves

        if steps_move:
            # steps_move
            board_move = []
            for index in range(1, len(steps_move)):
                board_move.append([steps_move[index - 1], steps_move[index]])

        elif li_api_move:
            # li_api_move
            board_move = []
            for move in li_api_move:
                board_move.append([int(move[:2]), int(move[2:])])

        elif li_one_move:
            # li_one_move
            steps = [int(li_one_move[i:i + 2]) for i in range(0, len(li_one_move), 2)]
            board_move = []
            for index in range(1, len(steps)):
                board_move.append([steps[index - 1], steps[index]])

        if board_move:
            # steps_move
            steps = [board_move[0][0]]
            for move in board_move:
                steps.append(move[1])
            steps_move = steps

            # li_api_move
            li_api_move = []
            for move in board_move:
                move_part = self._make_len_2(move[0]) + self._make_len_2(move[1])
                li_api_move.append(move_part)

            # li_one_move
            li_one_move = "".join(list(map(self._make_len_2, steps_move)))

        # Hub related moves

        if hub_move:
            # Hub move
            if "-" in hub_move:
                self.has_captures = False
                hub_position_move = "".join(list(map(self._make_len_2, hub_move.split("-"))))
            else:
                self.has_captures = True
                hub_position_move = "".join(list(map(self._make_len_2, hub_move.split("x"))))
        elif hub_position_move:
            # Hub position move
            positions = [hub_position_move[i:i + 2] for i in range(0, len(hub_position_move), 2)]
            separator = "x" if self.has_captures else "-"
            hub_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        if self.hub_to_pdn_pseudolegal:
            # Pseudo-legal PDN move
            pdn_position_move = hub_position_move[:4]
            separator = "x" if self.has_captures else "-"
            pdn_move = pdn_position_move[:2] + separator + pdn_position_move[2:]

        # PDN related moves

        if pdn_move:
            # PDN move
            pdn_move = move_from_variant(pdn_move, variant=self.variant)

            if "-" in pdn_move:
                self.has_captures = False
                pdn_position_move = "".join(list(map(self._make_len_2, pdn_move.split("-"))))
            else:
                self.has_captures = True
                pdn_position_move = "".join(list(map(self._make_len_2, pdn_move.split("x"))))
        elif pdn_position_move:
            # PDN position move
            positions = [pdn_position_move[i:i + 2] for i in range(0, len(pdn_position_move), 2)]
            separator = "x" if self.has_captures else "-"
            pdn_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        if pdn_position_move:
            # Get if the move is ambiguous.
            self.ambiguous = not (len(pdn_position_move) == 4)

        self.board_move = board_move
        self.hub_move = hub_move
        self.hub_position_move = hub_position_move
        self.pdn_move = pdn_move
        self.pdn_position_move = pdn_position_move
        self.steps_move = steps_move
        self.li_api_move = li_api_move
        self.li_one_move = li_one_move
