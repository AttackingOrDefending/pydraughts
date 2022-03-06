from __future__ import annotations
from draughts.core.board_searcher import BoardSearcher
from draughts.core.board_initializer import BoardInitializer
from functools import reduce
import pickle
from typing import Optional, List, Tuple, Any

WHITE = 2
BLACK = 1


class Board:

    def __init__(self, variant: str = 'standard', fen: str = 'startpos') -> None:
        if fen != 'startpos':
            self.player_turn = WHITE if fen[0].lower() == 'w' else BLACK
        else:
            self.player_turn = WHITE

        if variant in ['brazilian', 'russian', 'english', 'italian']:
            self.width = 4
            self.height = 8
        elif variant == 'turkish':
            self.width = 8
            self.height = 8
        else:
            self.width = 5
            self.height = 10

        if variant == 'frysk!':
            self.rows_per_user_with_pieces = 1
        elif variant == 'turkish':
            self.rows_per_user_with_pieces = 2
        elif variant in ['brazilian', 'russian', 'english', 'italian']:
            self.rows_per_user_with_pieces = 3
        else:
            self.rows_per_user_with_pieces = 4

        self.position_count = self.width * self.height
        self.position_layout = {}
        self.piece_requiring_further_capture_moves = None
        self.previous_move_was_capture = False
        self.variant = variant
        self.fen = fen
        self.searcher = BoardSearcher()
        BoardInitializer(self, self.fen).initialize()

        self.pieces_promote_and_stop_capturing = self.variant in ['english', 'italian']
        self.pieces_promote_and_continue_capturing = self.variant in ['russian']

    def count_movable_player_pieces(self, player_number: int = 1, captures: Optional[List[int]] = None) -> int:
        """Count the pieces of one player that can be moved."""
        if captures is None:
            captures = []
        return reduce((lambda count, piece: count + (1 if piece.is_movable(captures) else 0)), self.searcher.get_pieces_by_player(player_number), 0)

    def get_possible_moves(self, captures: List[int]) -> List[List[int]]:
        """Get all possible moves."""
        capture_moves = self.get_possible_capture_moves(captures)

        return capture_moves if capture_moves else self.get_possible_positional_moves()

    def get_possible_capture_moves(self, captures: List[int]) -> List[List[int]]:
        """Get all possible capture moves (not positional moves)."""
        return reduce((lambda moves, piece: moves + piece.get_possible_capture_moves(captures)), self.searcher.get_pieces_in_play(), [])

    def get_possible_positional_moves(self) -> List[List[int]]:
        """Get all possible positional moves (not capture moves)."""
        return reduce((lambda moves, piece: moves + piece.get_possible_positional_moves()), self.searcher.get_pieces_in_play(), [])

    def position_is_open(self, position: int) -> bool:
        """Get if the position is open (a piece is not in the given square)."""
        return not self.searcher.get_piece_by_position(position)

    def create_new_board_from_move(self, move: List[int], move_number: int, captures: List[int]) -> Tuple[Board, Optional[int]]:
        """Create a new board and play the move given."""
        new_board = pickle.loads(pickle.dumps(self, -1))  # A lot faster that deepcopy.
        enemy_position = None

        if move in self.get_possible_capture_moves(captures):
            enemy_position = new_board.perform_capture_move(move, move_number, captures)
        else:
            new_board.perform_positional_move(move, move_number)

        return new_board, enemy_position

    def push_move(self, move: List[int], move_number: int, captures: List[int]) -> Tuple[Board, Optional[int]]:
        """Play the move given without creating a new board."""
        # It takes 40% less time than create_new_board_from_move (60% faster).
        enemy_position = None

        if move in self.get_possible_capture_moves(captures):
            enemy_position = self.perform_capture_move(move, move_number, captures)
        else:
            self.perform_positional_move(move, move_number)

        return self, enemy_position

    def perform_capture_move(self, move: List[int], move_number: int, captures: List[int]) -> Optional[int]:
        """Make a capture move."""
        self.previous_move_was_capture = True
        piece = self.searcher.get_piece_by_position(move[0])
        originally_was_king = piece.king
        enemy_piece = piece.capture_move_enemies[move[1]]
        enemy_position = enemy_piece.position
        enemy_piece.capture()
        self.move_piece(move, move_number)
        if not originally_was_king and piece.king and self.pieces_promote_and_stop_capturing:
            further_capture_moves_for_piece = []
        elif not originally_was_king and not self.pieces_promote_and_continue_capturing:
            was_king = piece.king
            piece.king = False
            further_capture_moves_for_piece = [capture_move for capture_move in self.get_possible_capture_moves(captures + [enemy_position]) if move[1] == capture_move[0]]
            if not further_capture_moves_for_piece and was_king:
                piece.king = True
        else:
            further_capture_moves_for_piece = [capture_move for capture_move in self.get_possible_capture_moves(captures + [enemy_position]) if move[1] == capture_move[0]]

        if further_capture_moves_for_piece:
            self.piece_requiring_further_capture_moves = self.searcher.get_piece_by_position(move[1])
        else:
            self.piece_requiring_further_capture_moves = None
            self.switch_turn()
        return enemy_position

    def perform_positional_move(self, move: List[int], move_number: int) -> None:
        """Make a positional move."""
        self.previous_move_was_capture = False
        self.move_piece(move, move_number)
        self.switch_turn()

    def switch_turn(self) -> None:
        """Switch the turn."""
        self.player_turn = BLACK if self.player_turn == WHITE else WHITE

    def move_piece(self, move: List[int], move_number: int) -> None:
        """Move a piece."""
        self.searcher.get_piece_by_position(move[0]).move(move[1], move_number)
        self.pieces = sorted(self.pieces, key=lambda piece: piece.position if piece.position else 0)

    def is_valid_row_and_column(self, row: int, column: int) -> bool:
        """Get if the given row and column is inside the board."""
        if row < 0 or row >= self.height:
            return False

        if column < 0 or column >= self.width:
            return False

        return True

    def __setattr__(self, name: str, value: Any) -> None:
        super(Board, self).__setattr__(name, value)

        if name == 'pieces':
            [piece.reset_for_new_board() for piece in self.pieces]

            self.searcher.build(self)
