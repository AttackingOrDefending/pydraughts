from __future__ import annotations
from draughts.core.board import Board
from draughts.core.move import StandardMove
import pickle
from math import ceil
from draughts.convert import _algebraic_to_numeric_square, _get_squares, fen_to_variant
from typing import List, Union, Tuple, Optional

WHITE = 2
BLACK = 1


def _convert_variant_names(variant: str) -> str:
    if variant == 'from position':
        return 'standard'
    if variant == 'american':
        return 'english'
    elif variant == 'frysk':
        return 'frysk!'
    return variant


class Game:

    def __init__(self, variant: str = 'standard', fen: str = 'startpos') -> None:
        self.variant = _convert_variant_names(variant)
        if fen == 'startpos' or ':' in fen:  # Li fen
            self.initial_fen = self.startpos_to_fen(fen)
            self.initial_hub_fen = self.li_fen_to_hub_fen(self.initial_fen)
            self.board = Board(self.variant, self.initial_hub_fen)
        else:  # Hub fen
            self.initial_hub_fen = fen
            self.board = Board(self.variant, self.initial_hub_fen)
            self.initial_fen = self.get_li_fen()
        self.initial_dxp_fen = self.get_dxp_fen()
        self.last_non_reversible_fen = fen_to_variant(self.initial_fen, self.variant)

        # moves has every move of a multi-capture as a separate move.
        self.moves: List[List[int]] = []

        # move_stack contains the moves played but a multi-capture is only considered as one move.
        # move_stack is preferred to moves.
        self.move_stack: List[StandardMove] = []
        self.capture_stack: List[List[int]] = []

        # _not_added_move and _not_added_capture contain the moves that are part of a multi-capture.
        # that hasn't been completed yet.
        self._not_added_move: List[List[int]] = []
        self._not_added_capture: List[int] = []

        # reversible_moves contains the moves since the last capture or move of a man.
        # (so it only contains non-capture king moves).
        self.reversible_moves: List[StandardMove] = []

        # fens stores the Hub fen of each position to detect threefold repetition.
        self.fens = [self.initial_hub_fen]
        self.moves_since_last_capture = 0
        self.consecutive_noncapture_king_moves = 0

        # save data for pop()
        self.last_non_reversible_fen_history = [self.last_non_reversible_fen]
        self.moves_since_last_capture_history = [self.moves_since_last_capture]
        self.consecutive_noncapture_king_moves_history = [self.consecutive_noncapture_king_moves]

    def copy(self) -> Game:
        """Copy the board (transfers all data)."""
        # At least 6 times faster than deepcopy.
        return pickle.loads(pickle.dumps(self, -1))

    def copy_fast(self) -> Game:
        """Copy the board (doesn't transfer all the data but is faster)."""
        # More than 10x faster than .copy() but it doesn't transfer all the data.
        game = Game(self.variant, self.get_fen())
        game._not_added_move = self._not_added_move.copy()
        game._not_added_capture = self._not_added_capture.copy()
        return game

    def pop(self) -> None:
        """Undo the last move."""
        # Removes the whole capture sequence in case of a multi-capture.
        if self.moves:
            if self._not_added_move:
                self._not_added_move = []
                self._not_added_capture = []
            else:
                # The fen and other data is only added after the whole capture sequence is complete.
                self.fens.pop()
                self.move_stack.pop()
                last_captures = self.capture_stack.pop()
                if self.reversible_moves:
                    self.reversible_moves.pop()
                for _ in range(max(1, len(last_captures))):
                    self.moves.pop()

                self.last_non_reversible_fen_history.pop()
                self.moves_since_last_capture_history.pop()
                self.consecutive_noncapture_king_moves_history.pop()

            self.board = Board(self.variant, self.fens[-1])

    def move(self, move: List[int], return_captured: bool = False, include_pdn=False) -> Union[Game, Tuple[Game, Optional[int]]]:
        """Make a move. Plays only one jump in case of a multi-capture and not the whole sequence."""
        # [0, 0] is a null move.
        is_null_move = move == [0, 0]
        if move not in self.get_possible_moves() and not is_null_move:
            raise ValueError('The provided move is not possible')
        turn = self.whose_turn()
        was_king = False
        old_board = self.copy_fast() if include_pdn else None

        if is_null_move:
            self.board.switch_turn()
            enemy_position = None
        else:
            was_king = self.board.searcher.get_piece_by_position(move[0]).king
            self.board, enemy_position = self.board.push_move(move, len(self.move_stack) + 1, self._not_added_capture)
        self.moves.append(move)

        if self.whose_turn() == turn:
            self._not_added_move.append(move)
            self._not_added_capture.append(enemy_position)
        else:
            captures = self._not_added_capture + [enemy_position]
            if captures[0] is None:
                captures = []
            move_to_add_board = self._not_added_move + [move]
            move_to_add_hub = self.make_len_2(move_to_add_board[0][0]) + self.make_len_2(move_to_add_board[-1][1]) + self.sort_captures(captures)
            if include_pdn:
                move_to_add = StandardMove(board=old_board, board_move=move_to_add_board)
            else:
                move_to_add = StandardMove(board_move=move_to_add_board, hub_position_move=move_to_add_hub, has_captures=bool(captures), hub_to_pdn_pseudolegal=True)
            self.move_stack.append(move_to_add)
            self.capture_stack.append(captures)
            self._not_added_move = []
            self._not_added_capture = []

            self.moves_since_last_capture = 0 if self.board.previous_move_was_capture else self.moves_since_last_capture + 1
            if was_king and not captures:
                self.reversible_moves.append(move_to_add)
                self.consecutive_noncapture_king_moves += 1
            else:
                self.last_non_reversible_fen = fen_to_variant(self.get_li_fen(), self.variant)
                self.reversible_moves = []
                self.consecutive_noncapture_king_moves = 0
            self.last_non_reversible_fen_history.append(self.last_non_reversible_fen)
            self.moves_since_last_capture_history.append(self.moves_since_last_capture)
            self.consecutive_noncapture_king_moves_history.append(self.consecutive_noncapture_king_moves)
            self.fens.append(self.get_fen())

        if return_captured:
            return self, enemy_position
        else:
            return self

    def push(self, move: Union[List[List[int]], List[int]], return_captured: bool = False, include_pdn=False) -> Union[Game, Tuple[Game, List[int]]]:
        """Make a move. Plays the whole move sequence in case of a capture."""
        if type(move[0]) == int:
            move = [move]
        enemy_positions = []
        for move_part in move:
            enemy_positions.append(self.move(move_part, return_captured, include_pdn))
        if return_captured:
            enemy_positions = list(map(lambda game_enemy_position: game_enemy_position[1], enemy_positions))
            return self, enemy_positions
        else:
            return self

    def null(self) -> Game:
        """Play a null move."""
        self.move([0, 0])
        return self

    def has_player_won(self, player: int = WHITE) -> bool:
        """Get if a given player has won."""
        turn = self.whose_turn()
        opponent_color = WHITE if player == BLACK else BLACK
        if self.variant == 'breakthrough':
            for piece in self.board.searcher.player_pieces[player]:
                if piece.king:
                    # Player wins if they have a king.
                    return True
        elif self.variant == 'antidraughts':
            # Player wins if they have no available move.
            # Can only check if it is the player's turn.
            if turn == player and not self.board.count_movable_player_pieces(player, self._not_added_capture):
                return True
        if self.variant != 'antidraughts':
            # Player wins if the opponent has no available move.
            # Can only check if it is the opponent's turn.
            if turn == opponent_color and not self.board.count_movable_player_pieces(opponent_color, self._not_added_capture):
                return True
        return False

    def is_threefold(self) -> bool:
        """Get if the current position has occurred at least three times."""
        return bool(self.fens and self.fens.count(self.fens[-1]) >= 3)

    def is_draw(self) -> bool:
        """Get if the game is a draw."""
        # long_diagonal contains all the squares in the long diagonal of an 8x8 board.
        long_diagonal = [4, 8, 11, 15, 18, 22, 25, 29]
        white_pieces = 0
        black_pieces = 0
        white_kings = 0
        black_kings = 0
        white_piece_in_long_diagonal = False
        black_piece_in_long_diagonal = False
        for piece in self.board.searcher.uncaptured_pieces:
            loc = piece.position
            if piece is not None:
                if piece.player == WHITE:
                    if loc in long_diagonal:
                        white_piece_in_long_diagonal = True
                    white_pieces += 1
                    if piece.king:
                        white_kings += 1
                else:
                    if loc in long_diagonal:
                        black_piece_in_long_diagonal = True
                    black_pieces += 1
                    if piece.king:
                        black_kings += 1
        if self.variant == 'standard':
            # 25 consecutive non-capture king moves.
            if self.consecutive_noncapture_king_moves >= 50:
                return True
            # 1 king vs 3 pieces (with at least 1 king) and 16 moves made.
            if white_pieces == white_kings == 1 and black_pieces == 3 and black_kings >= 1 and self.consecutive_noncapture_king_moves >= 32:
                return True
            if black_pieces == black_kings == 1 and white_pieces == 3 and white_kings >= 1 and self.consecutive_noncapture_king_moves >= 32:
                return True
            # 1 king vs 2 or fewer pieces (with at least 1 king) and 5 moves made.
            if white_pieces == white_kings == 1 and black_pieces <= 2 and black_kings >= 1 and self.consecutive_noncapture_king_moves >= 10:
                return True
            if black_pieces == black_kings == 1 and white_pieces <= 2 and white_kings >= 1 and self.consecutive_noncapture_king_moves >= 10:
                return True
            return self.is_threefold()
        elif self.variant in ['frisian', 'frysk!']:
            # 2 kings vs 1 king and 7 moves made.
            if white_pieces == white_kings == 1 and black_pieces == black_kings == 2 and self.consecutive_noncapture_king_moves >= 14:
                return True
            if white_pieces == white_kings == 2 and black_pieces == black_kings == 1 and self.consecutive_noncapture_king_moves >= 14:
                return True
            # 1 king vs 1 king and 2 moves made (officially immediately if there can't be a forced capture).
            # but we don't detect if there is a forced capture.
            if white_pieces == white_kings == black_pieces == black_kings == 1 and self.consecutive_noncapture_king_moves >= 4:
                return True
        elif self.variant == 'antidraughts':
            # Only way to draw is threefold.
            return self.is_threefold()
        elif self.variant == 'breakthrough':
            # There is no draw.
            return False
        elif self.variant in ['russian', 'brazilian']:
            # 3 or more kings vs 1 king and 15 moves made.
            if white_pieces == white_kings == 1 and black_pieces == black_kings >= 3 and self.consecutive_noncapture_king_moves >= 30:
                return True
            if white_pieces == white_kings >= 3 and black_pieces == black_kings == 1 and self.consecutive_noncapture_king_moves >= 30:
                return True
            # 15 consecutive non-capture king moves.
            if self.consecutive_noncapture_king_moves >= 30:
                return True
            # Same number of kings, same number of pieces, 4 or 5 pieces per side and 30 moves made.
            if white_kings == black_kings >= 1 and white_pieces == black_pieces and white_pieces in [4, 5] and self.moves_since_last_capture >= 60:
                return True
            # Same number of kings, same number of pieces, 6 or 7 pieces per side and 60 moves made.
            if white_kings == black_kings >= 1 and white_pieces == black_pieces and white_pieces in [6, 7] and self.moves_since_last_capture >= 120:
                return True
            # 3 pieces (with at least 1 king) vs 1 king on the long diagonal and 5 moves made.
            if white_pieces == 3 and white_kings >= 1 and black_pieces == black_kings == 1 and not white_piece_in_long_diagonal and black_piece_in_long_diagonal and self.moves_since_last_capture >= 10:
                return True
            if white_pieces == white_kings == 1 and black_pieces == 3 and black_kings >= 1 and white_piece_in_long_diagonal and not black_piece_in_long_diagonal and self.moves_since_last_capture >= 10:
                return True
            # 2 pieces (with at least 1 king) vs 1 king and 5 moves made.
            if white_pieces == 2 and white_kings >= 1 and black_pieces == black_kings == 1 and self.moves_since_last_capture >= 10:
                return True
            if white_pieces == white_kings == 1 and black_pieces == 2 and black_kings >= 1 and self.moves_since_last_capture >= 10:
                return True
            return self.is_threefold()
        elif self.variant in ['english', 'italian']:
            # 40 non-capture king moves.
            if self.consecutive_noncapture_king_moves >= 80:
                return True
            return self.is_threefold()
        elif self.variant == 'turkish':
            # 1 piece (king or not) vs 1 piece (king or not) and 2 moves made (officially immediately if there can't be
            # a forced capture) but we don't detect if there is a forced capture.
            if white_pieces == black_pieces == 1 and self.moves_since_last_capture >= 4:
                return True
            return self.is_threefold()
        return False

    def is_over(self) -> bool:
        """Get if the game is over."""
        return self.has_player_won(WHITE) or self.has_player_won(BLACK) or self.is_draw()

    def get_winner(self) -> Optional[int]:
        """
        Get the player who won.
        :returns: WHITE if white won, BLACK if black won, 0 if it is a draw, and None if the game hasn't ended.
        """
        if self.has_player_won(WHITE):
            return WHITE
        elif self.has_player_won(BLACK):
            return BLACK
        elif self.is_draw():
            return 0
        return None

    def get_possible_moves(self) -> List[List[int]]:
        """
        Get all possible moves. Doesn't return the whole capture sequence.
        It only returns the first move of a multi-capture, so the moves are pseudo-legal.
        """
        return self.board.get_possible_moves(self._not_added_capture)

    def whose_turn(self) -> int:
        """Get whose turn it is."""
        return self.board.player_turn

    def get_fen(self) -> str:
        """Get the Hub fen of the position."""
        playing = 'W' if self.board.player_turn == WHITE else 'B'
        fen = ''

        for loc in range(1, self.board.position_count + 1):
            letter = 'e'
            if loc in self.board.searcher.filled_positions:
                piece = self.board.searcher.get_piece_by_position(loc)
                if piece.player == WHITE:
                    letter = 'w'
                else:
                    letter = 'b'
                if piece.king:
                    letter = letter.capitalize()
            fen += letter

        final_fen = playing + fen
        return final_fen

    def get_li_fen(self) -> str:
        """Get the fen of the position."""
        playing = 'W' if self.board.player_turn == WHITE else 'B'
        white_pieces = []
        black_pieces = []

        for piece in self.board.searcher.uncaptured_pieces:
            letter = str(piece.position)
            if piece.king:
                letter = 'K' + letter
            if piece.player == WHITE:
                white_pieces.append(letter)
            else:
                black_pieces.append(letter)

        final_fen = f"{playing}:W{','.join(white_pieces)}:B{','.join(black_pieces)}"
        return final_fen

    def get_dxp_fen(self) -> str:
        """Get the DXP fen of the position."""
        fen = ''

        for loc in range(1, self.board.position_count + 1):
            letter = 'e'
            if loc in self.board.searcher.filled_positions:
                piece = self.board.searcher.get_piece_by_position(loc)
                if piece.player == WHITE:
                    letter = 'w'
                else:
                    letter = 'z'
                if piece.king:
                    letter = letter.capitalize()
            fen += letter

        return fen

    def get_moves(self) -> Tuple[List[List[List[int]]], List[List[Optional[int]]]]:
        """
        Get the moves for a position. It returns the whole multi-capture,
        but it doesn't check the rules of each variant for which multi-capture to choose, so the moves are pseudo-legal.
        Use legal_moves for legal moves.
        """
        turn = self.whose_turn()
        moves = []
        captured_pieces = []
        # get_possible_moves returns only the first jump in a multi-capture sequence,
        # so we use it again after the first jump to check if there are any further moves.
        for move in self.get_possible_moves():
            game_2 = self.copy_fast()
            _, captures = game_2.move(move, return_captured=True)
            if game_2.whose_turn() == turn:
                more_moves, more_captures = game_2.get_moves()
                for semi_move, semi_capture in zip(more_moves, more_captures):
                    moves.append([move] + semi_move)
                    captured_pieces.append([captures] + semi_capture)
            else:
                moves.append([move])
                captured_pieces.append([captures])
        return moves, captured_pieces

    def legal_moves(self) -> Tuple[List[List[List[int]]], List[List[Optional[int]]]]:
        """Get the legal moves for the current position."""

        moves, captures = self.get_moves()
        if not moves:
            return moves, captures

        if self.variant in ['frisian', 'frysk!']:
            # Kings are worth 1.5 and men 1. The kings here are worth 1.501 because if we have a choice between 3 men or 2 kings (both are worth 3) we must capture the kings.

            # We have to choose the path that is worth the most.
            king_value = 1.501
            man_value = 1

            values = []
            for capture in captures:
                value = 0.
                for position in capture:
                    if position is None:
                        continue
                    piece = self.board.searcher.get_piece_by_position(position)
                    value += king_value if piece.king else man_value
                values.append(value)
            max_value = max(values)
            moves_pseudo_legal = []
            captures_pseudo_legal = []
            for move, capture, value in zip(moves, captures, values):
                if value == max_value:
                    moves_pseudo_legal.append(move)
                    captures_pseudo_legal.append(capture)

            # If a man and a king can play a capture sequence of equal value, it is forced play the capture sequence with the king.
            move_with_king = bool(list(filter(lambda move: self.board.searcher.get_piece_by_position(move[0][0]).king, moves_pseudo_legal)))
            if move_with_king:
                moves_pseudo_legal_2 = []
                captures_pseudo_legal_2 = []
                for move, capture in zip(moves_pseudo_legal, captures_pseudo_legal):
                    if self.board.searcher.get_piece_by_position(move[0][0]).king and capture[0] is not None or capture[0] is None:
                        moves_pseudo_legal_2.append(move)
                        captures_pseudo_legal_2.append(capture)
            else:
                moves_pseudo_legal_2 = moves_pseudo_legal
                captures_pseudo_legal_2 = captures_pseudo_legal

            # The same king can't make more than 3 non-capturing moves in a row, if the player has men left.
            has_man = False
            for piece in self.board.searcher.uncaptured_pieces:
                if piece and not piece.king and piece.player == self.whose_turn():
                    has_man = True

            if has_man and len(self.move_stack) >= 6:
                last_3_move_stack_moves = [self.move_stack[-6], self.move_stack[-4], self.move_stack[-2]]
                last_3_moves = list(map(lambda move: move.li_one_move, last_3_move_stack_moves))
                last_3_moves_same_piece = last_3_moves[0][-2:] == last_3_moves[1][:2] and last_3_moves[1][-2:] == last_3_moves[2][:2]
                was_a_capture = bool(list(filter(bool, [self.capture_stack[-6], self.capture_stack[-4], self.capture_stack[-2]])))
                loc = int(last_3_moves[-1][-2:])
                if loc in self.board.searcher.open_positions:
                    is_king = False
                    is_king_for_at_least_3_moves = True
                else:
                    piece = self.board.searcher.get_piece_by_position(loc)
                    is_king = piece.king
                    is_king_for_at_least_3_moves = len(self.move_stack) - piece.became_king >= 6
                if is_king and last_3_moves_same_piece and not was_a_capture and is_king_for_at_least_3_moves:
                    piece_not_allowed = int(last_3_moves[2][-2:])
                    moves_legal = []
                    captures_legal = []
                    for move, capture in zip(moves_pseudo_legal_2, captures_pseudo_legal_2):
                        if move[0][0] != piece_not_allowed or capture[0] is not None:
                            moves_legal.append(move)
                            captures_legal.append(capture)
                else:
                    moves_legal = moves_pseudo_legal_2
                    captures_legal = captures_pseudo_legal_2
            else:
                moves_legal = moves_pseudo_legal_2
                captures_legal = captures_pseudo_legal_2

        elif self.variant == 'italian':
            # The move that captures the most pieces has to be played.
            max_len_key = max(list(map(len, moves)))
            moves_pseudo_legal = []
            captures_pseudo_legal = []
            for move, capture in zip(moves, captures):
                if len(move) == max_len_key:
                    moves_pseudo_legal.append(move)
                    captures_pseudo_legal.append(capture)

            # If a man and a king can play a capture the same number of pieces, it is forced play the capture sequence with the king.
            move_with_king = bool(list(filter(lambda move: self.board.searcher.get_piece_by_position(move[0][0]).king, moves_pseudo_legal)))
            if move_with_king:
                moves_pseudo_legal_2 = []
                captures_pseudo_legal_2 = []
                for move, capture in zip(moves_pseudo_legal, captures_pseudo_legal):
                    if self.board.searcher.get_piece_by_position(move[0][0]).king and capture[0] is not None or capture[0] is None:
                        moves_pseudo_legal_2.append(move)
                        captures_pseudo_legal_2.append(capture)
            else:
                moves_pseudo_legal_2 = moves_pseudo_legal
                captures_pseudo_legal_2 = captures_pseudo_legal

            # The capture sequence that captures the most kings has to be played.
            max_kings = 0
            for move, capture in zip(moves_pseudo_legal_2, captures_pseudo_legal_2):
                kings = 0
                for piece_loc in capture:
                    if piece_loc is not None and self.board.searcher.get_piece_by_position(piece_loc).king:
                        kings += 1
                max_kings = max(max_kings, kings)
            moves_pseudo_legal_3 = []
            captures_pseudo_legal_3 = []
            for move, capture in zip(moves_pseudo_legal_2, captures_pseudo_legal_2):
                kings = 0
                for piece_loc in capture:
                    if piece_loc is not None and self.board.searcher.get_piece_by_position(piece_loc).king:
                        kings += 1
                if kings == max_kings:
                    moves_pseudo_legal_3.append(move)
                    captures_pseudo_legal_3.append(capture)

            # The capture sequence where the king occurs first has to be played.
            earliest_king = 100
            king_in_capture_sequence = False
            for move, capture in zip(moves_pseudo_legal_3, captures_pseudo_legal_3):
                if capture[0] is not None:
                    for index, piece_loc in enumerate(capture):
                        if self.board.searcher.get_piece_by_position(piece_loc).king:
                            king_in_capture_sequence = True
                            earliest_king = min(earliest_king, index)
                            break
            moves_pseudo_legal_4 = []
            captures_pseudo_legal_4 = []
            if king_in_capture_sequence:
                for move, capture in zip(moves_pseudo_legal_3, captures_pseudo_legal_3):
                    for index, piece_loc in enumerate(capture):
                        if index > earliest_king:
                            break
                        elif self.board.searcher.get_piece_by_position(piece_loc).king:
                            if index == earliest_king:
                                moves_pseudo_legal_4.append(move)
                                captures_pseudo_legal_4.append(capture)
                            break
            else:
                moves_pseudo_legal_4 = moves_pseudo_legal_3
                captures_pseudo_legal_4 = captures_pseudo_legal_3
            moves_legal = moves_pseudo_legal_4
            captures_legal = captures_pseudo_legal_4

        elif self.variant == 'russian':
            # We have to finish the capture sequence that we choose, so we check if another move by the same piece
            # captures more pieces and starts with the same captures.
            # For example:
            # move_1_captures = [28, 18], move_2_captures = [28, 18, 6]
            # move_2_captures ([28, 18, ...]) starts with the captures in move_1_captures ([28, 18]) and
            # captures more pieces, so move_1 doesn't finish the capture sequence.
            moves_legal = []
            captures_legal = []
            for move, capture in zip(moves, captures):
                for possible_move, possible_capture in zip(moves, captures):
                    if move[0][0] == possible_move[0][0] and capture == possible_capture[:len(capture)] and len(possible_capture) > len(capture):
                        break
                else:
                    moves_legal.append(move)
                    captures_legal.append(capture)

        elif self.variant == 'english':
            # No restriction. The player can choose, whichever move they prefer.
            # They only have to complete the multi-capture.
            return moves, captures
        else:
            # Turkish also goes in this category (together with international etc.) because the rule that prohibits a piece from turning 180 degrees is accounted for in get_position_behind_enemy.

            # The move that captures the most pieces has to be played.
            max_len_key = max(list(map(len, moves)))
            moves_legal = []
            captures_legal = []
            for move, capture in zip(moves, captures):
                if len(move) == max_len_key:
                    moves_legal.append(move)
                    captures_legal.append(capture)
        return moves_legal, captures_legal

    def make_len_2(self, move: Union[str, int]) -> str:
        """
        Add a 0 in the front of the square if it is only 1 digit.
        e.g. The move 5 will be turned to 05 but the move 23 will be left the same.
        """
        return f'0{move}' if len(str(move)) == 1 else str(move)

    def push_str_move(self, move: str) -> None:
        """
        Make a move, given a string. Plays only one jump in case of a multi-capture and not the whole sequence.
        e.g. 0523 will mean move the piece at square 5 to square 23.
        """
        self.move([int(move[:2]), int(move[2:4])])

    def sort_captures(self, captures: List[int]) -> str:
        """
        Sort the captures from the smallest number to the highest.
        e.g. [10, 30, 19] will change to '101930'.
        This function exists because hub engines return the captures in alphabetical order
        (e.g. for the move 231201 scan returns 23x01x07x18 instead of 23x01x18x07).
        """
        return ''.join(list(sorted(map(self.make_len_2, captures))))

    def li_fen_to_hub_fen(self, li_fen: str) -> str:
        """Convert a fen to a Hub fen."""
        _, _, squares_per_letter, every_other_square = _get_squares(self.variant)
        fen = ''
        split_li_fen = li_fen.split(':')
        fen += split_li_fen[0]
        white_pieces = split_li_fen[1][1:].split(',')
        black_pieces = split_li_fen[2][1:].split(',')
        white_pieces = list(filter(bool, white_pieces))
        black_pieces = list(filter(bool, black_pieces))

        # Fens sometimes contain hyphens to denote that the player has pieces from one square until another.
        # e.g. 5-10 is the same as 5,6,7,8,9,10.
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
                    white_pieces_remove_hyphen.append(add_for_king + str(number))
            else:
                add_for_king = ''
                if white_piece[0] == 'K':
                    add_for_king = 'K'
                    white_piece = white_piece[1:]
                white_pieces_remove_hyphen.append(add_for_king + str(_algebraic_to_numeric_square(white_piece, squares_per_letter, every_other_square)))

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
                    black_pieces_remove_hyphen.append(add_for_king + str(number))
            else:
                add_for_king = ''
                if black_piece[0] == 'K':
                    add_for_king = 'K'
                    black_piece = black_piece[1:]
                black_pieces_remove_hyphen.append(add_for_king + str(_algebraic_to_numeric_square(black_piece, squares_per_letter, every_other_square)))

        position_count = _get_squares(self.variant)[0]

        for index in range(1, position_count + 1):
            str_index = str(index)
            if str_index in white_pieces_remove_hyphen:
                fen += 'w'
            elif 'K' + str_index in white_pieces_remove_hyphen:
                fen += 'W'
            elif str_index in black_pieces_remove_hyphen:
                fen += 'b'
            elif 'K' + str_index in black_pieces_remove_hyphen:
                fen += 'B'
            else:
                fen += 'e'
        return fen

    def startpos_to_fen(self, fen: str) -> str:
        """Get the starting fen."""
        if fen != 'startpos':
            return fen
        if self.variant == 'frysk!':
            return 'W:W46,47,48,49,50:B1,2,3,4,5'
        elif self.variant == 'turkish':
            return 'W:W41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56:B9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24'
        elif self.variant in ['brazilian', 'russian', 'english', 'italian']:
            return 'W:W21,22,23,24,25,26,27,28,29,30,31,32:B1,2,3,4,5,6,7,8,9,10,11,12'
        else:
            return 'W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20'

    def __repr__(self) -> str:
        """Get a visual representation of the board."""
        # From get_checker_board.get_board

        # In most draughts variants only the dark squares are playable.
        half_of_the_squares_are_playable = self.variant not in ['turkish']
        # The bottom left square isn't a playing square in italian draughts.
        bottom_left_square_isnt_playable = self.variant in ['italian']

        squares_per_row = self.board.width
        columns = 8 if self.variant in ['russian', 'brazilian', 'english', 'italian', 'turkish'] else 10
        rows = self.board.height

        board = [[" " for col in range(columns)] for _ in range(rows)]

        for loc in range(1, self.board.position_count + 1):
            row_number = ceil(loc / squares_per_row) - 1  # From get_row_from_position

            column = (loc - 1) % squares_per_row  # From get_column

            if not half_of_the_squares_are_playable:
                pass
            elif row_number % 2 == 0:
                column = (column + 1) * 2 - (2 if bottom_left_square_isnt_playable else 1)  # To account for the always empty white squares
            else:
                column = (column + 1) * 2 - (1 if bottom_left_square_isnt_playable else 2)  # To account for the always empty white squares

            piece_symbol = " "
            if loc in self.board.searcher.filled_positions:
                piece = self.board.searcher.get_piece_by_position(loc)
                piece_symbol = "w" if piece.player == WHITE else "b"
                piece_symbol = piece_symbol.upper() if piece.king else piece_symbol
            board[row_number][column] = piece_symbol

        str_board = ""
        divider = (4 * columns - 1) * "-" + "\n"
        for row_index, row in enumerate(board):
            str_row = ""
            for str_piece in row:
                str_row += f" {str_piece} |"
            str_row = str_row[:-1] + "\n"
            str_board += str_row
            if row_index != rows - 1:
                str_board += divider
        str_board = str_board[:-1]
        return str_board
