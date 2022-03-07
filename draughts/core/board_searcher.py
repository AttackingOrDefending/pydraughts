from __future__ import annotations
from functools import reduce
from typing import List, Optional
from draughts.core.piece import Piece

WHITE = 2
BLACK = 1


class BoardSearcher:

    def build(self, board) -> None:
        """Build the searcher."""
        self.board = board
        self.uncaptured_pieces = list(filter(lambda piece: not piece.captured, board.pieces))
        self.open_positions = []
        self.filled_positions = []
        self.player_positions = {}
        self.player_pieces = {}
        self.position_pieces = {}

        self.build_filled_positions()
        self.build_open_positions()
        self.build_player_positions()
        self.build_player_pieces()
        self.build_position_pieces()

    def build_filled_positions(self) -> None:
        """Find the filled positions (squares which have a piece)."""
        self.filled_positions = reduce((lambda open_positions, piece: open_positions + [piece.position]), self.uncaptured_pieces, [])

    def build_open_positions(self) -> None:
        """Find the open positions (empty squares)."""
        self.open_positions = list(set(range(1, self.board.position_count)).difference(self.filled_positions))

    def build_player_positions(self) -> None:
        """Find the positions where each player has a piece."""
        self.player_positions = {
            1: reduce((lambda positions, piece: positions + ([piece.position] if piece.player == BLACK else [])), self.uncaptured_pieces, []),
            2: reduce((lambda positions, piece: positions + ([piece.position] if piece.player == WHITE else [])), self.uncaptured_pieces, [])
        }

    def build_player_pieces(self) -> None:
        """Find all the pieces of both players."""
        self.player_pieces = {
            1: reduce((lambda pieces, piece: pieces + ([piece] if piece.player == BLACK else [])), self.uncaptured_pieces, []),
            2: reduce((lambda pieces, piece: pieces + ([piece] if piece.player == WHITE else [])), self.uncaptured_pieces, [])
        }

    def build_position_pieces(self) -> None:
        """Make a dict where the key is the square and the value is the piece in this square."""
        self.position_pieces = {piece.position: piece for piece in self.uncaptured_pieces}

    def get_pieces_by_player(self, player_number: int) -> List[Piece]:
        """Get all the pieces of one player."""
        return self.player_pieces[player_number]

    def get_positions_by_player(self, player_number: int) -> List[int]:
        """Get the positions of one player's pieces."""
        return self.player_positions[player_number]

    def get_pieces_in_play(self) -> List[Piece]:
        """
        Get pieces in play. They are: All the pieces of the player playing now except when a piece is
        in the middle of a multi-capture, so it has already captured one or more pieces, but it can capture more,
        where we only return the piece that is in the middle of the multi-capture.
        """
        return self.player_pieces[self.board.player_turn] if not self.board.piece_requiring_further_capture_moves else [self.board.piece_requiring_further_capture_moves]

    def get_piece_by_position(self, position: int) -> Optional[Piece]:
        """Get the piece given its position."""
        return self.position_pieces.get(position)
