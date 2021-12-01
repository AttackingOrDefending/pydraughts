import string
import re
from math import ceil


class Move:
    def __init__(self, board=None, board_move=None, hub_move=None, hub_position_move=None, pdn_move=None, pdn_position_move=None, steps_move=None, li_api_move=None, li_one_move=None, has_captures=None, possible_moves=None, possible_captures=None, hub_to_pdn_pseudolegal=False, variant=None, notation=2, squares_per_letter=4):
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
                self.to_board()
                self.captures = self.possible_captures[self.possible_moves.index(self.board_move)]
                self.captures = [] if self.captures[0] is None else self.captures
                self.has_captures = bool(self.captures)
                self.from_board()
            else:
                self.no_board()

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
            self.pdn_move = algebraic_to_number(self.pdn_move, variant=self.variant, squares_per_letter=self.squares_per_letter)
            self.pdn_move = rotate_move(self.pdn_move, notation=self.notation, variant=self.variant)

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
            self.ambiguous = starts_endings.count(self.make_len_2(self.board_move[0][0]) + self.make_len_2(self.board_move[-1][1])) >= 2
            if self.ambiguous:
                self.pdn_position_move = "".join(list(map(self.make_len_2, self.steps_move)))
            else:
                self.pdn_position_move = self.make_len_2(self.board_move[0][0]) + self.make_len_2(self.board_move[-1][1])

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

    def no_board(self):
        """
        Makes as many conversions as possible without the board.
        """

        # Board related moves

        if self.steps_move:
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
                    li_api_move.append(self.make_len_2(move[0]) + self.make_len_2(move[1]))
                self.li_api_move = li_api_move

            # li_one_move
            if not self.li_one_move:
                self.li_one_move = "".join(list(map(self.make_len_2, self.steps_move)))

        # Hub related moves

        if self.hub_move:
            if "-" in self.hub_move:
                self.has_captures = False
                self.hub_position_move = "".join(list(map(self.make_len_2, self.hub_move.split("-"))))
            else:
                self.has_captures = True
                self.hub_position_move = "".join(list(map(self.make_len_2, self.hub_move.split("x"))))
        elif self.hub_position_move:
            positions = [self.hub_position_move[i:i + 2] for i in range(0, len(self.hub_position_move), 2)]
            separator = "x" if self.has_captures else "-"
            self.hub_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        if self.hub_to_pdn_pseudolegal:
            self.pdn_position_move = self.hub_position_move[:4]
            separator = "x" if self.has_captures else "-"
            self.pdn_move = self.pdn_position_move[:2] + separator + self.pdn_position_move[2:]

        # PDN related moves

        if self.pdn_move:
            self.pdn_move = algebraic_to_number(self.pdn_move, variant=self.variant, squares_per_letter=self.squares_per_letter)
            self.pdn_move = rotate_move(self.pdn_move, notation=self.notation, variant=self.variant)

            if "-" in self.pdn_move:
                self.has_captures = False
                self.pdn_position_move = "".join(list(map(self.make_len_2, self.pdn_move.split("-"))))
            else:
                self.has_captures = True
                self.pdn_position_move = "".join(list(map(self.make_len_2, self.pdn_move.split("x"))))
        elif self.pdn_position_move:
            positions = [self.pdn_position_move[i:i + 2] for i in range(0, len(self.pdn_position_move), 2)]
            separator = "x" if self.has_captures else "-"
            self.pdn_move = separator.join(list(map(lambda position: str(int(position)), positions)))

        if self.pdn_position_move:
            self.ambiguous = not (len(self.pdn_position_move) == 4)


def rotate_move(internal_move, notation=None, variant=None):
    separators = ['-', 'x', ':']
    splitted_move = None
    correct_seperator = None
    for separator in separators:
        splitted_move = internal_move.split(separator)
        if splitted_move[0] != internal_move:
            correct_seperator = separator
            break
    splitted_move = list(map(int, splitted_move))
    variant_to_notation = {'standard': 2, 'english': 0, 'italian': 2, 'russian': 0, 'brazilian': 0, 'frisian': 2, 'frysk!': 2, 'antidraughts': 2, 'breakthrough': 2}
    value = variant_to_notation.get(variant, 2)
    if notation is None:
        notation = value

    def reverse_column(splitted_int_move):
        per_row = 4 if variant in ['english', 'italian', 'russian', 'brazilian'] else 5
        for index, square in enumerate(splitted_int_move):
            square_in_row = square % per_row
            if square_in_row == 0:
                square_in_row += per_row
            splitted_int_move[index] = ((square - 1) // per_row) * per_row + (per_row - (square_in_row - 1))
        return splitted_int_move

    def reverse_row_and_column(splitted_int_move):
        squares = 32 if variant in ['english', 'italian', 'russian', 'brazilian'] else 50
        splitted_int_move = list(map(lambda square: squares + 1 - square, splitted_int_move))
        return splitted_int_move

    def reverse_row(splitted_int_move):
        return reverse_column(reverse_row_and_column(splitted_int_move))

    rotated_move = None
    if notation == 0:
        rotated_move = reverse_row(splitted_move)
    elif notation == 1:
        rotated_move = reverse_row_and_column(splitted_move)
    elif notation == 2:
        rotated_move = splitted_move
    elif notation == 3:
        rotated_move = reverse_column(splitted_move)

    rotated_move = list(map(str, rotated_move))
    return correct_seperator.join(rotated_move)


def algebraic_to_number(algebraic_move, squares_per_letter=None, variant=None):
    algebraic_notation = algebraic_move[0] in string.ascii_letters
    if not algebraic_notation:
        return algebraic_move
    algebraic_move = algebraic_move.lower()
    if squares_per_letter is None:
        squares_per_letter = 4 if variant in ['english', 'italian', 'russian', 'brazilian'] else 5

    separators = ['-', 'x', ':']
    special_seperators = ['([a-zA-z]+\d+)']
    splitted_move = None
    correct_seperator = None
    for separator in separators:
        splitted_move = list(filter(bool, re.split(separator, algebraic_move)))
        if splitted_move[0] != algebraic_move:
            correct_seperator = separator
            break

    if not correct_seperator:
        for separator in special_seperators:
            splitted_move = list(filter(bool, re.split(separator, algebraic_move)))
            if splitted_move[0] != algebraic_move:
                correct_seperator = '-'
                break

    numeric_move = []
    for move in splitted_move:
        numeric_move.append(algebraic_to_numeric_square(move, squares_per_letter))
    numeric_move = list(map(str, numeric_move))
    return correct_seperator.join(numeric_move)


def algebraic_to_numeric_square(square, squares_per_letter):
    algebraic_notation = square[0] in string.ascii_letters
    if not algebraic_notation:
        return square
    return (int(square[1]) - 1) * squares_per_letter + ceil(string.ascii_lowercase.index(square[0]) // 2) + 1


def number_to_algebraic(number_move, width=None, variant=None):
    algebraic_notation = number_move[0] in string.ascii_letters
    if algebraic_notation:
        return number_move
    if width is None:
        width = 4 if variant in ['english', 'italian', 'russian', 'brazilian'] else 5

    separators = ['-', 'x', ':']
    special_seperators = ['([a-zA-z]+\d+)']
    splitted_move = None
    correct_seperator = None
    for separator in separators:
        splitted_move = list(filter(bool, re.split(separator, number_move)))
        if splitted_move[0] != number_move:
            correct_seperator = separator
            break

    if not correct_seperator:
        for separator in special_seperators:
            splitted_move = list(filter(bool, re.split(separator, number_move)))
            if splitted_move[0] != number_move:
                correct_seperator = '-'
                break

    algebraic_move = []
    for move in splitted_move:
        algebraic_move.append(numeric_to_algebraic_square(move, width))
    algebraic_move = list(map(str, algebraic_move))
    return correct_seperator.join(algebraic_move)


def numeric_to_algebraic_square(square, width):
    algebraic_notation = square[0] in string.ascii_letters
    if algebraic_notation:
        return square
    square = int(square)
    row = ceil(square / width) - 1
    column = (square - 1) % width
    column *= 2
    column += 1 if row % 2 == 1 else 0
    return string.ascii_lowercase[column] + str(row + 1)
