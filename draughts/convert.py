from math import ceil
import string
import re
from typing import Tuple, Optional, List


def _get_squares(variant: Optional[str]) -> Tuple[int, int, int, bool]:
    """Returns the total squares, squares per row, squares per column and if every other square is playable."""
    # The default values are for International draughts.
    total_squares = 50
    squares_per_row = 5
    squares_per_column = 5
    every_other_square = True
    if variant in ['english', 'italian', 'russian', 'brazilian']:
        total_squares = 32
        squares_per_row = 4
        squares_per_column = 4
    elif variant in ['turkish']:
        total_squares = 64
        squares_per_row = 8
        squares_per_column = 8
        every_other_square = False
    return total_squares, squares_per_row, squares_per_column, every_other_square


def _rotate_move(internal_move: str, notation: Optional[int] = None, variant: Optional[str] = None) -> str:
    """Rotate the move."""
    separators = ['-', 'x', ':']
    split_move = []
    correct_seperator = ''
    for separator in separators:
        split_move = internal_move.split(separator)
        if split_move[0] != internal_move:
            correct_seperator = separator
            break
    int_move_parts = list(map(int, split_move))
    variant_to_notation = {'standard': 2, 'english': 1, 'italian': 2, 'russian': 0, 'brazilian': 0, 'turkish': 0, 'frisian': 2, 'frysk!': 2, 'antidraughts': 2, 'breakthrough': 2}
    if notation is None:
        notation = variant_to_notation.get(variant, 2)

    def reverse_column(split_int_move: List[int]) -> List[int]:
        per_row = _get_squares(variant)[1]
        for index, square in enumerate(split_int_move):
            square_in_row = square % per_row
            if square_in_row == 0:
                square_in_row += per_row
            split_int_move[index] = ((square - 1) // per_row) * per_row + (per_row - (square_in_row - 1))
        return split_int_move

    def reverse_row_and_column(split_int_move: List[int]) -> List[int]:
        squares = _get_squares(variant)[0]
        split_int_move = list(map(lambda square: squares + 1 - square, split_int_move))
        return split_int_move

    def reverse_row(split_int_move: List[int]) -> List[int]:
        return reverse_column(reverse_row_and_column(split_int_move))

    if notation == 0:
        rotated_move = reverse_row(int_move_parts)
    elif notation == 1:
        rotated_move = reverse_row_and_column(int_move_parts)
    elif notation == 2:
        rotated_move = int_move_parts
    else:  # notation == 3
        rotated_move = reverse_column(int_move_parts)

    rotated_str_move = list(map(str, rotated_move))
    return correct_seperator.join(rotated_str_move)


def _algebraic_to_number(algebraic_move: str, squares_per_letter: Optional[int] = None, variant: Optional[str] = None, every_other_square: Optional[bool] = None) -> str:
    """Convert an algebraic move to a numeric move."""
    if every_other_square is None:
        if variant == 'turkish':
            every_other_square = False
        else:
            every_other_square = True
    algebraic_notation = algebraic_move[0] in string.ascii_letters
    if not algebraic_notation:
        return algebraic_move
    algebraic_move = algebraic_move.lower()
    if squares_per_letter is None:
        squares_per_letter = _get_squares(variant)[2]

    separators = ['-', 'x', ':']
    special_seperators = [r'([a-zA-z]+\d+)']
    split_move = []
    correct_seperator = ''
    for separator in separators:
        split_move = list(filter(bool, re.split(separator, algebraic_move)))
        if split_move[0] != algebraic_move:
            correct_seperator = separator
            break

    if not correct_seperator:
        for separator in special_seperators:
            split_move = list(filter(bool, re.split(separator, algebraic_move)))
            if split_move[0] != algebraic_move:
                correct_seperator = '-'
                break

    numeric_move = []
    for move in split_move:
        numeric_move.append(_algebraic_to_numeric_square(move, squares_per_letter, every_other_square=every_other_square))
    numeric_str_move = list(map(str, numeric_move))
    return correct_seperator.join(numeric_str_move)


def _algebraic_to_numeric_square(square: str, squares_per_letter: int, every_other_square: bool = True) -> int:
    """Convert an algebraic square to a numeric square."""
    algebraic_notation = square[0] in string.ascii_letters
    if not algebraic_notation:
        return int(square)
    if not every_other_square:
        return (int(square[1]) - 1) * squares_per_letter + string.ascii_lowercase.index(square[0]) + 1
    return (int(square[1]) - 1) * squares_per_letter + ceil(string.ascii_lowercase.index(square[0]) // 2) + 1


def _number_to_algebraic(number_move: str, width: Optional[int] = None, variant: Optional[str] = None, every_other_square: Optional[bool] = None) -> str:
    """Convert a numeric move to an algebraic move."""
    if every_other_square is None:
        if variant == 'turkish':
            every_other_square = False
        else:
            every_other_square = True
    algebraic_notation = number_move[0] in string.ascii_letters
    if algebraic_notation:
        return number_move
    if width is None:
        width = _get_squares(variant)[1]

    separators = ['-', 'x', ':']
    split_move = []
    correct_seperator = ''
    for separator in separators:
        split_move = list(filter(bool, re.split(separator, number_move)))
        if split_move[0] != number_move:
            correct_seperator = separator
            break

    algebraic_move = []
    for move_part in split_move:
        algebraic_move.append(_numeric_to_algebraic_square(move_part, width, every_other_square=every_other_square))
    return correct_seperator.join(algebraic_move)


def _numeric_to_algebraic_square(square: str, width: int, every_other_square: Optional[bool] = True) -> str:
    """Convert a numeric square to an algebraic square."""
    algebraic_notation = square[0] in string.ascii_letters
    if algebraic_notation:
        return square
    int_square = int(square)
    row = ceil(int_square / width) - 1
    column = (int_square - 1) % width
    if every_other_square:
        column *= 2
        column += 1 if row % 2 == 1 else 0
    return string.ascii_lowercase[column] + str(row + 1)


def _change_fen_from_variant(li_fen: str, notation: Optional[int] = None, squares_per_letter: int = 5, every_other_square: bool = True, variant: Optional[str] = None) -> str:
    """Convert an internal fen to the correct fen for the variant."""
    if variant:
        _, _, squares_per_letter, every_other_square = _get_squares(variant)

    fen = li_fen.split(':')
    starts = fen[0]
    white_pieces = fen[1][1:].split(',')
    black_pieces = fen[2][1:].split(',')
    white_pieces = list(filter(bool, white_pieces))
    black_pieces = list(filter(bool, black_pieces))

    white_pieces_remove_hyphen = []
    for white_piece in white_pieces:
        if '-' in white_piece:
            start_end = white_piece.split('-')
            add_for_king = ''
            if start_end[0][0] == 'K':
                add_for_king = 'K'
                start_end[0] = start_end[0][1:]
            start, end = _algebraic_to_numeric_square(start_end[0], squares_per_letter, every_other_square), _algebraic_to_numeric_square(start_end[1], squares_per_letter, every_other_square)
            for number in range(start, end + 1):
                white_pieces_remove_hyphen.append(add_for_king + _rotate_move(str(number), notation=notation, variant=variant))
        else:
            add_for_king = ''
            if white_piece[0] == 'K':
                add_for_king = 'K'
                white_piece = white_piece[1:]
            white_pieces_remove_hyphen.append(add_for_king + _rotate_move(str(_algebraic_to_numeric_square(white_piece, squares_per_letter, every_other_square)), notation=notation, variant=variant))

    black_pieces_remove_hyphen = []
    for black_piece in black_pieces:
        if '-' in black_piece:
            start_end = black_piece.split('-')
            add_for_king = ''
            if start_end[0][0] == 'K':
                add_for_king = 'K'
                start_end[0] = start_end[0][1:]
            start, end = _algebraic_to_numeric_square(start_end[0], squares_per_letter, every_other_square), _algebraic_to_numeric_square(start_end[1], squares_per_letter, every_other_square)
            for number in range(start, end + 1):
                black_pieces_remove_hyphen.append(add_for_king + _rotate_move(str(number), notation=notation, variant=variant))
        else:
            add_for_king = ''
            if black_piece[0] == 'K':
                add_for_king = 'K'
                black_piece = black_piece[1:]
            black_pieces_remove_hyphen.append(add_for_king + _rotate_move(str(_algebraic_to_numeric_square(black_piece, squares_per_letter, every_other_square)), notation=notation, variant=variant))

    # Because in english black starts.
    white_starts = variant not in ['english']
    if not white_starts:
        white_pieces_remove_hyphen, black_pieces_remove_hyphen = black_pieces_remove_hyphen, white_pieces_remove_hyphen
        starts = 'W' if starts == 'B' else 'B'

    white_pieces_remove_hyphen.sort()
    black_pieces_remove_hyphen.sort()
    return f'{starts}:W{",".join(white_pieces_remove_hyphen)}:B{",".join(black_pieces_remove_hyphen)}'


def fen_from_variant(fen: str, variant: Optional[str] = None) -> str:
    """Convert variant fen to internal fen."""
    variant = variant.lower() if variant else variant
    fen = _change_fen_from_variant(fen, variant=variant)
    return fen


def fen_to_variant(fen: str, variant: Optional[str] = None, to_algebraic: Optional[bool] = None) -> str:
    """Convert internal fen to variant fen."""
    variant = variant.lower() if variant else variant
    fen = _change_fen_from_variant(fen, variant=variant)
    if to_algebraic or variant in ['russian', 'brazilian', 'turkish']:
        new_white_pieces = []
        new_black_pieces = []
        white_pieces = fen.split(':')[1][1:].split(',')
        black_pieces = fen.split(':')[2][1:].split(',')
        white_pieces = list(filter(bool, white_pieces))
        black_pieces = list(filter(bool, black_pieces))
        for piece in white_pieces:
            add = ''
            if piece.lower().startswith('k'):
                add = 'K'
                piece = piece[1:]
            new_white_pieces.append(add + _number_to_algebraic(piece, variant=variant))
        for piece in black_pieces:
            add = ''
            if piece.lower().startswith('k'):
                add = 'K'
                piece = piece[1:]
            new_black_pieces.append(add + _number_to_algebraic(piece, variant=variant))
        fen = f'{fen[0]}:W{",".join(new_white_pieces)}:B{",".join(new_black_pieces)}'
    return fen


def move_from_variant(move: str, variant: Optional[str] = None) -> str:
    """Convert variant PDN move to internal PDN move."""
    variant = variant.lower() if variant else variant
    move = _algebraic_to_number(move, variant=variant)
    move = _rotate_move(move, variant=variant)
    return move


def move_to_variant(move: str, variant: Optional[str] = None, to_algebraic: Optional[bool] = None) -> str:
    """Convert internal PDN move to variant PDN move."""
    variant = variant.lower() if variant else variant
    move = _rotate_move(move, variant=variant)
    if to_algebraic or variant in ['russian', 'brazilian', 'turkish']:
        move = _number_to_algebraic(move, variant=variant)
    return move
