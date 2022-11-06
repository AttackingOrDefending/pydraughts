import ctypes
import draughts
from math import ceil


# From CheckerBoard API:
WHITE = 1
BLACK = 2
MAN = 4
KING = 8
FREE = 0


def get_board(board: draughts.Board) -> ctypes.Array:
    """Get a CheckerBoard board (for use in CheckerBoard engines) from a Board() object."""

    one_column = (ctypes.c_int * 8)
    checkerboard_board = (one_column * 8)()

    white_starts = board.variant not in ['english']
    flip_column = board.variant not in ['english', 'italian']

    for loc in range(1, board._game.board.position_count + 1):
        row = ceil(loc / board._game.board.width) - 1  # From get_row_from_position

        # Because in english black starts
        if not white_starts:
            row = (board._game.board.height - 1) - row

        column = (loc - 1) % board._game.board.width  # From get_column

        # Because:
        # 1. In italian the bottom-left square isn't playable, so in CheckerBoard the board is flipped vertically.
        # 2. In most variants the bottom-left square for the starting side (usually white) is in column a,
        # while in english black starts, so the bottom-left square for the starting side (black) is in row h.
        if flip_column:
            column = board._game.board.width - 1 - column

        if row % 2 == 0:
            column = (column + 1) * 2 - 2  # To account for the always empty white squares
        else:
            column = (column + 1) * 2 - 1  # To account for the always empty white squares

        number = FREE
        if loc in board._game.board.searcher.filled_positions:
            piece = board._game.board.searcher.get_piece_by_position(loc)
            # In Checkerboard black starts first, so the colors are reversed
            if piece.player == draughts.WHITE and not piece.king:
                number = (WHITE if white_starts else BLACK) + MAN
            elif piece.player == draughts.BLACK and not piece.king:
                number = (BLACK if white_starts else WHITE) + MAN
            elif piece.player == draughts.WHITE and piece.king:
                number = (WHITE if white_starts else BLACK) + KING
            elif piece.player == draughts.BLACK and piece.king:
                number = (BLACK if white_starts else WHITE) + KING
        checkerboard_board[column][row] = number

    return checkerboard_board


def from_board(checker_board: ctypes.Array, old_board: draughts.Board) -> str:
    """Get the Hub fen from a CheckerBoard board."""

    # board_numbers = [[square for square in column] for column in checker_board]
    fen = 'B' if old_board.turn == draughts.WHITE else 'W'  # switch turns

    white_starts = old_board.variant not in ['english']
    flip_column = old_board.variant not in ['english', 'italian']

    for loc in range(1, old_board._game.board.position_count + 1):
        row = ceil(loc / old_board._game.board.width) - 1  # From get_row_from_position
        if not white_starts:
            row = (old_board._game.board.height - 1) - row
        column = (loc - 1) % old_board._game.board.width  # From get_column

        # Because:
        # 1. In italian the bottom-left square isn't playable, so in CheckerBoard the board is flipped vertically.
        # 2. In most variants the bottom-left square for the starting side (usually white) is in column a,
        # while in english black starts, so the bottom-left square for the starting side (black) is in row h.
        if flip_column:
            column = old_board._game.board.width - 1 - column

        if row % 2 == 0:
            column = (column + 1) * 2 - 2  # To account for the always empty white squares
        else:
            column = (column + 1) * 2 - 1  # To account for the always empty white squares

        # In Checkerboard black starts first, so the colors are reversed
        if checker_board[column][row] == FREE:
            fen += 'e'
        elif checker_board[column][row] == (BLACK if white_starts else WHITE) + MAN:
            fen += 'b'
        elif checker_board[column][row] == (WHITE if white_starts else BLACK) + MAN:
            fen += 'w'
        elif checker_board[column][row] == (BLACK if white_starts else WHITE) + KING:
            fen += 'B'
        elif checker_board[column][row] == (WHITE if white_starts else BLACK) + KING:
            fen += 'W'
    return fen
