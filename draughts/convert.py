from math import ceil
import string
import re


def _rotate_move(internal_move, notation=None, variant=None):
    separators = ['-', 'x', ':']
    splitted_move = None
    correct_seperator = ''
    for separator in separators:
        splitted_move = internal_move.split(separator)
        if splitted_move[0] != internal_move:
            correct_seperator = separator
            break
    splitted_move = list(map(int, splitted_move))
    variant_to_notation = {'standard': 2, 'english': 1, 'italian': 2, 'russian': 0, 'brazilian': 0, 'turkish': 0, 'frisian': 2, 'frysk!': 2, 'antidraughts': 2, 'breakthrough': 2}
    value = variant_to_notation.get(variant, 2)
    if notation is None:
        notation = value

    def reverse_column(splitted_int_move):
        per_row = 5
        if variant in ['english', 'italian', 'russian', 'brazilian']:
            per_row = 4
        elif variant == 'turkish':
            per_row = 8
        for index, square in enumerate(splitted_int_move):
            square_in_row = square % per_row
            if square_in_row == 0:
                square_in_row += per_row
            splitted_int_move[index] = ((square - 1) // per_row) * per_row + (per_row - (square_in_row - 1))
        return splitted_int_move

    def reverse_row_and_column(splitted_int_move):
        if variant in ['brazilian', 'russian', 'english', 'italian']:
            squares = 32
        elif variant == 'turkish':
            squares = 64
        else:
            squares = 50
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


def _algebraic_to_number(algebraic_move, squares_per_letter=None, variant=None, every_other_square=None):
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
        squares_per_letter = 5
        if variant in ['english', 'italian', 'russian', 'brazilian']:
            squares_per_letter = 4
        elif variant == 'turkish':
            squares_per_letter = 8

    separators = ['-', 'x', ':']
    special_seperators = ['([a-zA-z]+\d+)']
    splitted_move = None
    correct_seperator = ''
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
        numeric_move.append(_algebraic_to_numeric_square(move, squares_per_letter, every_other_square=every_other_square))
    numeric_move = list(map(str, numeric_move))
    return correct_seperator.join(numeric_move)


def _algebraic_to_numeric_square(square, squares_per_letter, every_other_square=True):
    algebraic_notation = square[0] in string.ascii_letters
    if not algebraic_notation:
        return square
    if not every_other_square:
        return (int(square[1]) - 1) * squares_per_letter + string.ascii_lowercase.index(square[0]) + 1
    return (int(square[1]) - 1) * squares_per_letter + ceil(string.ascii_lowercase.index(square[0]) // 2) + 1


def _number_to_algebraic(number_move, width=None, variant=None, every_other_square=None):
    if every_other_square is None:
        if variant == 'turkish':
            every_other_square = False
        else:
            every_other_square = True
    algebraic_notation = number_move[0] in string.ascii_letters
    if algebraic_notation:
        return number_move
    if width is None:
        width = 5
        if variant in ['english', 'italian', 'russian', 'brazilian']:
            width = 4
        elif variant == 'turkish':
            width = 8

    separators = ['-', 'x', ':']
    special_seperators = ['([a-zA-z]+\d+)']
    splitted_move = None
    correct_seperator = ''
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
        algebraic_move.append(_numeric_to_algebraic_square(move, width, every_other_square=every_other_square))
    algebraic_move = list(map(str, algebraic_move))
    return correct_seperator.join(algebraic_move)


def _numeric_to_algebraic_square(square, width, every_other_square=True):
    algebraic_notation = square[0] in string.ascii_letters
    if algebraic_notation:
        return square
    square = int(square)
    row = ceil(square / width) - 1
    column = (square - 1) % width
    if every_other_square:
        column *= 2
        column += 1 if row % 2 == 1 else 0
    return string.ascii_lowercase[column] + str(row + 1)


def _change_fen_from_variant(li_fen, notation=None, squares_per_letter=5, every_other_square=True, variant=None):
    if variant in ['english', 'italian', 'russian', 'brazilian']:
        squares_per_letter = 4
    elif variant == 'turkish':
        squares_per_letter = 8
        every_other_square = False
    li_fen = li_fen.split(':')
    starts = li_fen[0]
    white_pieces = li_fen[1][1:].split(',')
    black_pieces = li_fen[2][1:].split(',')
    white_pieces_remove_hyphen = []
    for white_piece in white_pieces:
        if '-' in white_piece:
            start_end = white_piece.split('-')
            start, end = int(_algebraic_to_numeric_square(start_end[0], squares_per_letter, every_other_square)), int(_algebraic_to_numeric_square(start_end[1], squares_per_letter, every_other_square))
            for number in range(start, end + 1):
                white_pieces_remove_hyphen.append(_rotate_move(str(number), notation=notation, variant=variant))
        else:
            white_pieces_remove_hyphen.append(_rotate_move(white_piece, notation=notation, variant=variant))
    black_pieces_remove_hyphen = []
    for black_piece in black_pieces:
        if '-' in black_piece:
            start_end = black_piece.split('-')
            start, end = int(_algebraic_to_numeric_square(start_end[0], squares_per_letter, every_other_square)), int(_algebraic_to_numeric_square(start_end[1], squares_per_letter, every_other_square))
            for number in range(start, end + 1):
                black_pieces_remove_hyphen.append(_rotate_move(str(number), notation=notation, variant=variant))
        else:
            black_pieces_remove_hyphen.append(_rotate_move(black_piece, notation=notation, variant=variant))
    if variant == 'english':
        white_pieces_remove_hyphen, black_pieces_remove_hyphen = black_pieces_remove_hyphen, white_pieces_remove_hyphen
        starts = 'W' if starts == 'B' else 'B'
    white_pieces_remove_hyphen = list(map(lambda move: _algebraic_to_numeric_square(move, squares_per_letter) if move[0].lower() != 'k' else move, white_pieces_remove_hyphen))
    black_pieces_remove_hyphen = list(map(lambda move: _algebraic_to_numeric_square(move, squares_per_letter) if move[0].lower() != 'k' else move, black_pieces_remove_hyphen))
    white_pieces_remove_hyphen = list(map(int, white_pieces_remove_hyphen))
    black_pieces_remove_hyphen = list(map(int, black_pieces_remove_hyphen))
    white_pieces_remove_hyphen.sort()
    black_pieces_remove_hyphen.sort()
    white_pieces_remove_hyphen = list(map(str, white_pieces_remove_hyphen))
    black_pieces_remove_hyphen = list(map(str, black_pieces_remove_hyphen))
    return f'{starts}:W{",".join(white_pieces_remove_hyphen)}:B{",".join(black_pieces_remove_hyphen)}'


def fen_from_variant(fen, variant=None, notation=None, squares_per_letter=None, every_other_square=None):
    variant = variant.lower() if variant else variant
    fen = _change_fen_from_variant(fen, variant=variant, notation=notation, squares_per_letter=squares_per_letter, every_other_square=every_other_square)
    return fen


def fen_to_variant(fen, variant=None, notation=None, width=None, squares_per_letter=None, every_other_square=None, to_algebraic=None):
    variant = variant.lower() if variant else variant
    fen = _change_fen_from_variant(fen, variant=variant, notation=notation, squares_per_letter=squares_per_letter, every_other_square=every_other_square)
    if to_algebraic or variant in ['russian', 'brazilian', 'turkish']:
        new_white_pieces = []
        new_black_pieces = []
        white_pieces = fen.split(':')[1][1:]
        black_pieces = fen.split(':')[2][1:]
        for piece in white_pieces.split(','):
            add = ''
            if piece.lower().startswith('k'):
                add = 'K'
                piece = piece[1:]
            new_white_pieces.append(add + _number_to_algebraic(piece, variant=variant, width=width, every_other_square=every_other_square))
        for piece in black_pieces.split(','):
            add = ''
            if piece.lower().startswith('k'):
                add = 'K'
                piece = piece[1:]
            new_black_pieces.append(add + _number_to_algebraic(piece, variant=variant, width=width, every_other_square=every_other_square))
        fen = f'{fen[0]}:W{",".join(new_white_pieces)}:B{",".join(new_black_pieces)}'
    return fen


def move_from_variant(move, variant=None, notation=None, squares_per_letter=None, every_other_square=None):
    variant = variant.lower() if variant else variant
    move = _algebraic_to_number(move, variant=variant, squares_per_letter=squares_per_letter, every_other_square=every_other_square)
    move = _rotate_move(move, variant=variant, notation=notation)
    return move


def move_to_variant(move, variant=None, notation=None, width=None, every_other_square=None, to_algebraic=None):
    variant = variant.lower() if variant else variant
    move = _rotate_move(move, variant=variant, notation=notation)
    if to_algebraic or variant in ['russian', 'brazilian', 'turkish']:
        move = _number_to_algebraic(move, variant=variant, width=width, every_other_square=every_other_square)
    return move
