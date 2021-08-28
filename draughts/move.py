class Move:
    def __init__(self, board, board_move=None, hub_move=None, hub_position_move=None, pdn_move=None,
                 pdn_position_move=None, steps_move=None, li_api_move=None, li_one_move=None):
        assert board_move or hub_move or hub_position_move or pdn_move or pdn_position_move or steps_move or li_api_move or li_one_move

        self.board_move = board_move
        self.hub_move = hub_move
        self.hub_position_move = hub_position_move
        self.pdn_move = pdn_move
        self.pdn_position_move = pdn_position_move
        self.steps_move = steps_move
        self.li_api_move = li_api_move
        self.li_one_move = li_one_move
        self.ambiguous = None

        self.possible_moves, self.possible_captures = board.legal_moves()
        self.to_board()
        self.captures = self.possible_captures[self.possible_moves.index(self.board_move)]
        self.captures = [] if self.captures[0] is None else self.captures
        self.from_board()

    def make_len_2(self, move):
        return f'0{move}' if len(str(move)) == 1 else str(move)

    def sort_captures(self, captures):
        """
        This function is because hub engines returns the captures in alphabetical order
        (e.g. for the move 231201 scan returns 23x01x07x18 instead of 23x01x18x07)
        """
        if captures and captures[0] is None:
            captures = []
        captures = list(map(self.make_len_2, captures))
        captures.sort()
        captures = ''.join(captures)
        return captures

    def to_board(self):
        if self.hub_move:
            if "-" in self.hub_move:
                self.hub_position_move = "".join(list(map(self.make_len_2, self.hub_move.split("-"))))
            else:
                self.hub_position_move = "".join(list(map(self.make_len_2, self.hub_move.split("x"))))
        if self.pdn_move:
            if "-" in self.pdn_move:
                self.pdn_position_move = "".join(list(map(self.make_len_2, self.pdn_move.split("-"))))
            else:
                self.pdn_position_move = "".join(list(map(self.make_len_2, self.pdn_move.split("x"))))

        if self.hub_position_move:
            moves_li_board = {}
            for possible_move, possible_capture in zip(self.possible_moves, self.possible_captures):
                li_move = self.make_len_2(possible_move[0][0]) + self.make_len_2(
                    possible_move[-1][1]) + self.sort_captures(possible_capture)
                moves_li_board[li_move] = possible_move
            board_move = moves_li_board[self.hub_position_move]
            self.board_move = board_move

        elif self.pdn_position_move:
            moves_li_board = {}
            if len(self.pdn_position_move) == 4:
                self.ambiguous = False
                for possible_move, possible_capture in zip(self.possible_moves, self.possible_captures):
                    li_move = self.make_len_2(possible_move[0][0]) + self.make_len_2(possible_move[-1][1])
                    moves_li_board[li_move] = possible_move
            else:
                self.ambiguous = True
                for possible_move, possible_capture in zip(self.possible_moves, self.possible_captures):
                    steps = [possible_move[0][0]]
                    for move in possible_move:
                        steps.append(move[1])
                    li_move = "".join(list(map(self.make_len_2, steps)))
                    moves_li_board[li_move] = possible_move
            board_move = moves_li_board[self.pdn_position_move]
            self.board_move = board_move

        elif self.steps_move:
            board_move = []
            for index in range(1, len(self.steps_move)):
                board_move.append([self.steps_move[index - 1], self.steps_move[index]])
            self.board_move = board_move

        elif self.li_api_move:
            board_move = []
            for move in self.li_api_move:
                board_move.append([int(move[:2]), int(move[2:])])
            self.board_move = board_move

        elif self.li_one_move:
            steps = [int(self.li_one_move[i:i + 2]) for i in range(0, len(self.li_one_move), 2)]
            board_move = []
            for index in range(1, len(steps)):
                board_move.append([steps[index - 1], steps[index]])
            self.board_move = board_move

    def from_board(self):
        if not self.steps_move:
            steps = [self.board_move[0][0]]
            for move in self.board_move:
                steps.append(move[1])
            self.steps_move = steps

        if not self.hub_position_move:
            self.hub_position_move = self.make_len_2(self.board_move[0][0]) + self.make_len_2(self.board_move[-1][1])
            if self.captures:
                sorted_captures = self.sort_captures(self.captures)
                sorted_captures = [sorted_captures[i:i + 2] for i in range(0, len(sorted_captures), 2)]
                self.hub_position_move += "".join(list(map(self.make_len_2, sorted_captures)))

        if not self.hub_move:
            positions = [self.hub_position_move[i:i + 2] for i in range(0, len(self.hub_position_move), 2)]
            separator = "x" if self.captures else "-"
            self.hub_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        if not self.pdn_position_move:
            starts_endings = []
            for possible_move in self.possible_moves:
                starts_endings.append(self.make_len_2(possible_move[0][0]) + self.make_len_2(possible_move[-1][1]))
            self.ambiguous = starts_endings.count(
                self.make_len_2(self.board_move[0][0]) + self.make_len_2(self.board_move[-1][1])) >= 2
            if self.ambiguous:
                self.pdn_position_move = "".join(list(map(self.make_len_2, self.steps_move)))
            else:
                self.pdn_position_move = self.make_len_2(self.board_move[0][0]) + self.make_len_2(
                    self.board_move[-1][1])

        if not self.pdn_move:
            positions = [self.pdn_position_move[i:i + 2] for i in range(0, len(self.pdn_position_move), 2)]
            separator = "x" if self.captures else "-"
            self.pdn_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        if not self.li_api_move:
            li_api_move = []
            for move in self.board_move:
                li_api_move.append(self.make_len_2(move[0]) + self.make_len_2(move[1]))
            self.li_api_move = li_api_move

        if not self.li_one_move:
            self.li_one_move = "".join(list(map(self.make_len_2, self.steps_move)))
