import ctypes
import draughts
from math import ceil


def get_board(board):
    row = (ctypes.c_int * 8)
    checkerboard_board = (row * 8)()

    # From CheckerBoard API:
    WHITE = 1
    BLACK = 2
    MAN = 4
    KING = 8
    FREE = 0

    for loc in range(1, board.board.position_count + 1):
        piece = board.board.searcher.get_piece_by_position(loc)
        row = ceil(loc / board.board.width) - 1  # From get_row_from_position
        if board.variant == 'english':
            row = (board.board.height - 1) - row
        column = (loc - 1) % board.board.width  # From get_column
        if board.variant not in ['english', 'italian']:
            column = board.board.width - 1 - column
        if row % 2 == 0:
            column = (column + 1) * 2 - 2  # To account for the always empty white squares
        else:
            column = (column + 1) * 2 - 1  # To account for the always empty white squares
        number = FREE
        if piece:
            # In Checkerboard black starts first, so the colors are reversed
            if piece.player == draughts.WHITE and not piece.king:
                number = (WHITE if board.variant != 'english' else BLACK) + MAN
            elif piece.player == draughts.BLACK and not piece.king:
                number = (BLACK if board.variant != 'english' else WHITE) + MAN
            elif piece.player == draughts.WHITE and piece.king:
                number = (WHITE if board.variant != 'english' else BLACK) + KING
            elif piece.player == draughts.BLACK and piece.king:
                number = (BLACK if board.variant != 'english' else WHITE) + KING
        checkerboard_board[column][row] = number

    return checkerboard_board


def from_board(checker_board, old_board):
    # board_numbers = [[square for square in column] for column in checker_board]
    fen = 'B' if old_board.whose_turn() == draughts.WHITE else 'W'  # switch turns

    # From CheckerBoard API:
    WHITE = 1
    BLACK = 2
    MAN = 4
    KING = 8
    FREE = 0

    for loc in range(1, old_board.board.position_count + 1):
        row = ceil(loc / old_board.board.width) - 1  # From get_row_from_position
        if old_board.variant == 'english':
            row = (old_board.board.height - 1) - row
        column = (loc - 1) % old_board.board.width  # From get_column
        if old_board.variant not in ['english', 'italian']:
            column = old_board.board.width - 1 - column
        if row % 2 == 0:
            column = (column + 1) * 2 - 2  # To account for the always empty white squares
        else:
            column = (column + 1) * 2 - 1  # To account for the always empty white squares
        # In Checkerboard black starts first, so the colors are reversed
        if checker_board[column][row] == FREE:
            fen += 'e'
        elif checker_board[column][row] == (BLACK if old_board.variant != 'english' else WHITE) + MAN:
            fen += 'b'
        elif checker_board[column][row] == (WHITE if old_board.variant != 'english' else BLACK) + MAN:
            fen += 'w'
        elif checker_board[column][row] == (BLACK if old_board.variant != 'english' else WHITE) + KING:
            fen += 'B'
        elif checker_board[column][row] == (WHITE if old_board.variant != 'english' else BLACK) + KING:
            fen += 'W'
    return fen
