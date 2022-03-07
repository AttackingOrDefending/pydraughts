from draughts.core.piece import Piece
from typing import Any

WHITE = 2
BLACK = 1


class BoardInitializer:

    def __init__(self, board: Any, fen: str = 'startpos') -> None:
        self.board = board
        self.fen = fen

    def initialize(self) -> None:
        """Initialize the board."""
        self.build_position_layout()
        self.set_starting_pieces()

    def build_position_layout(self) -> None:
        """Build the position layout."""
        self.board.position_layout = {}
        position = 1

        for row in range(self.board.height):
            self.board.position_layout[row] = {}

            for column in range(self.board.width):
                self.board.position_layout[row][column] = position
                position += 1

    def set_starting_pieces(self) -> None:
        """Create the pieces."""
        pieces = []
        if self.fen != 'startpos':  # Hub fen
            # starting = self.fen[0]
            board = self.fen[1:]
            for index, position in enumerate(board):
                piece = None
                if position.lower() == 'w':
                    # Index + 1 because enumerate returns 0-49 while the board takes 1-50.
                    piece = self.create_piece(2, index + 1)
                elif position.lower() == 'b':
                    piece = self.create_piece(1, index + 1)
                if position == 'W' or position == 'B':
                    piece.king = True
                if piece:
                    pieces.append(piece)
        else:  # Not used, but it isn't removed, because it may be needed in the future
            starting_piece_count = self.board.width * self.board.rows_per_user_with_pieces
            player_starting_positions = {
                1: list(range(1, starting_piece_count + 1)),
                2: list(range(self.board.position_count - starting_piece_count + 1, self.board.position_count + 1))
            }

            for key, row in self.board.position_layout.items():
                for key, position in row.items():
                    player_number = 1 if position in player_starting_positions[1] else 2 if position in player_starting_positions[2] else None

                    if player_number:
                        pieces.append(self.create_piece(player_number, position))

        self.board.pieces = pieces

    def create_piece(self, player_number: int, position: int) -> Piece:
        """Create a piece."""
        piece = Piece(variant=self.board.variant)
        piece.player = player_number
        piece.position = position
        piece.board = self.board

        return piece
