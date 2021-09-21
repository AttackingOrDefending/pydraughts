from draughts.core.board import Board
from draughts.core.move import Move
import pickle

WHITE = 2
BLACK = 1


class Game:

    def __init__(self, variant='standard', fen='startpos'):
        self.variant = variant
        if self.variant == 'from position':
            self.variant = 'standard'
        if self.variant == 'american':
            self.variant = 'english'
        elif self.variant == 'frysk':
            self.variant = 'frysk!'
        if fen == 'startpos' or ':' in fen:  # Li fen
            self.initial_fen = self.startpos_to_fen(fen)
            self.initial_hub_fen = self.li_fen_to_hub_fen(self.initial_fen)
            self.board = Board(self.variant, self.initial_hub_fen)
        else:  # Hub fen
            self.initial_hub_fen = fen
            self.board = Board(self.variant, self.initial_hub_fen)
            self.initial_fen = self.get_li_fen()
        self.initial_dxp_fen = self.get_dxp_fen()
        self.last_non_reversible_fen = self.initial_fen
        self.moves = []
        self.move_stack = []
        self.capture_stack = []
        self.not_added_move = []
        self.not_added_capture = []
        self.non_reversible_moves = []
        self.consecutive_noncapture_move_limit = 1000  # The original was 40
        self.moves_since_last_capture = 0

    def copy(self):
        # At least 6 times faster than deepcopy
        return pickle.loads(pickle.dumps(self, -1))

    def move(self, move, return_captured=False):
        if move not in self.get_possible_moves():
            raise ValueError('The provided move is not possible')
        turn = self.whose_turn()

        self.board, enemy_position = self.board.create_new_board_from_move(move, len(self.move_stack) + 1, self.not_added_capture, return_captured=True)
        self.moves.append(move)
        self.moves_since_last_capture = 0 if self.board.previous_move_was_capture else self.moves_since_last_capture + 1

        if self.whose_turn() == turn:
            self.not_added_move.append(move)
            self.not_added_capture.append(enemy_position)
        else:
            captures = self.not_added_capture + [enemy_position]
            if captures[0] is None:
                captures = []
            move_to_add_board = self.not_added_move + [move]
            move_to_add_hub = self.make_len_2(move_to_add_board[0][0]) + self.make_len_2(move_to_add_board[-1][1]) + self.sort_captures(captures)
            move_to_add = Move(board_move=move_to_add_board, hub_position_move=move_to_add_hub, has_captures=bool(captures), hub_to_pdn_pseudolegal=True)
            self.move_stack.append(move_to_add)
            self.capture_stack.append(captures)
            self.not_added_move = []
            self.not_added_capture = []

            piece = self.board.searcher.get_piece_by_position(move[1])
            if piece.king and not captures:
                self.non_reversible_moves.append(move_to_add)
            else:
                self.last_non_reversible_fen = self.get_li_fen()
                self.non_reversible_moves = []

        if return_captured:
            return self, enemy_position
        else:
            return self

    def move_limit_reached(self):
        return self.moves_since_last_capture >= self.consecutive_noncapture_move_limit

    def is_over(self):
        if self.variant == 'breakthrough':
            has_king = False
            for loc in range(1, self.board.position_count + 1):
                piece = self.board.searcher.get_piece_by_position(loc)
                if piece is not None:
                    if piece.king:
                        has_king = True
            return self.move_limit_reached() or not self.legal_moves()[0] or has_king
        return self.move_limit_reached() or not self.legal_moves()[0]

    def get_winner(self):
        if self.whose_turn() == BLACK and not self.board.count_movable_player_pieces(BLACK, self.not_added_capture):
            return WHITE
        elif self.whose_turn() == WHITE and not self.board.count_movable_player_pieces(WHITE, self.not_added_capture):
            return BLACK
        elif self.variant == 'breakthrough':
            for loc in range(1, self.board.position_count + 1):
                piece = self.board.searcher.get_piece_by_position(loc)
                if piece is not None:
                    if piece.player == WHITE and piece.king:
                        return WHITE
                    elif piece.player == BLACK and piece.king:
                        return BLACK

    def get_possible_moves(self):
        return self.board.get_possible_moves(self.not_added_capture)

    def whose_turn(self):
        return self.board.player_turn

    def get_fen(self):
        playing = 'W' if self.board.player_turn == WHITE else 'B'
        fen = ''

        for loc in range(1, self.board.position_count + 1):
            piece = self.board.searcher.get_piece_by_position(loc)
            letter = 'e'
            if piece is not None:
                if piece.player == WHITE:
                    letter = 'w'
                else:
                    letter = 'b'
                if piece.king:
                    letter = letter.capitalize()
            fen += letter

        final_fen = playing + fen
        return final_fen

    def get_li_fen(self):
        playing = 'W' if self.board.player_turn == WHITE else 'B'
        white_pieces = []
        black_pieces = []

        for loc in range(1, self.board.position_count + 1):
            piece = self.board.searcher.get_piece_by_position(loc)
            if piece is not None:
                letter = str(loc)
                if piece.king:
                    letter = 'K' + letter
                if piece.player == WHITE:
                    white_pieces.append(letter)
                else:
                    black_pieces.append(letter)

        final_fen = f"{playing}:W{','.join(white_pieces)}:B{','.join(black_pieces)}"
        return final_fen

    def get_dxp_fen(self):
        fen = ''

        for loc in range(1, self.board.position_count + 1):
            piece = self.board.searcher.get_piece_by_position(loc)
            letter = 'e'
            if piece is not None:
                if piece.player == WHITE:
                    letter = 'w'
                else:
                    letter = 'z'
                if piece.king:
                    letter = letter.capitalize()
            fen += letter

        return fen

    def get_moves(self):
        """
        Moves are only pseudo-legal. Use legal_moves for legal moves.
        """
        turn = self.whose_turn()
        moves = []
        captured_pieces = []
        for move in self.get_possible_moves():
            game_2 = self.copy()
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

    def legal_moves(self):
        if self.variant == 'frisian' or self.variant == 'frysk!':
            king_value = 1.501
            man_value = 1
            moves, captures = self.get_moves()
            if not moves:
                return moves, captures
            values = []
            for capture in captures:
                value = 0
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

            has_man = False
            for loc in range(1, self.board.position_count + 1):
                piece = self.board.searcher.get_piece_by_position(loc)
                if piece and not piece.king and piece.player == self.whose_turn():
                    has_man = True

            if has_man and len(self.move_stack) >= 6:
                last_3_moves = [self.move_stack[-6], self.move_stack[-4], self.move_stack[-2]]
                last_3_moves = list(map(lambda move: move.li_one_move, last_3_moves))
                last_3_moves_same_piece = last_3_moves[0][-2:] == last_3_moves[1][:2] and last_3_moves[1][-2:] == last_3_moves[2][:2]
                was_a_capture = bool(list(filter(lambda captures: captures[0] is not None, [self.capture_stack[-6], self.capture_stack[-4], self.capture_stack[-2]])))
                piece = self.board.searcher.get_piece_by_position(int(last_3_moves[-1][-2:]))
                if piece is None:  # It is None when the piece was captured
                    is_king = False
                    is_king_for_at_least_3_moves = True
                else:
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
            moves, captures = self.get_moves()
            if not moves:
                return moves, captures
            max_len_key = max(list(map(len, moves)))
            moves_pseudo_legal = []
            captures_pseudo_legal = []
            for move, capture in zip(moves, captures):
                if len(move) == max_len_key:
                    moves_pseudo_legal.append(move)
                    captures_pseudo_legal.append(capture)

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

            earliest_king = 100
            for move, capture in zip(moves_pseudo_legal_3, captures_pseudo_legal_3):
                if capture[0] is not None:
                    for index, piece_loc in enumerate(capture):
                        if self.board.searcher.get_piece_by_position(piece_loc).king:
                            earliest_king = min(earliest_king, index)
                            break
            moves_pseudo_legal_4 = []
            captures_pseudo_legal_4 = []
            for move, capture in zip(moves_pseudo_legal_3, captures_pseudo_legal_3):
                if capture[0] is not None:
                    for index, piece_loc in enumerate(capture):
                        if index > earliest_king:
                            break
                        elif self.board.searcher.get_piece_by_position(piece_loc).king:
                            if index == earliest_king:
                                moves_pseudo_legal_4.append(move)
                                captures_pseudo_legal_4.append(capture)
                            break
                else:
                    moves_pseudo_legal_4.append(move)
                    captures_pseudo_legal_4.append(capture)
            moves_legal = moves_pseudo_legal_4
            captures_legal = captures_pseudo_legal_4

        elif self.variant in ['russian', 'english']:
            return self.get_moves()
        else:
            moves, captures = self.get_moves()
            if not moves:
                return moves, captures
            max_len_key = max(list(map(len, moves)))
            moves_legal = []
            captures_legal = []
            for move, capture in zip(moves, captures):
                if len(move) == max_len_key:
                    moves_legal.append(move)
                    captures_legal.append(capture)
        return moves_legal, captures_legal

    def make_len_2(self, move):
        return f'0{move}' if len(str(move)) == 1 else str(move)

    def push_move(self, move):
        self.move([int(move[:2]), int(move[2:4])])

    def sort_captures(self, captures):
        """
        This function is because hub engines returns the captures in alphabetical order
        (e.g. for the move 231201 scan returns 23x01x07x18 instead of 23x01x18x07)
        """
        captures = list(map(self.make_len_2, captures))
        captures.sort()
        captures = ''.join(captures)
        return captures

    def li_fen_to_hub_fen(self, li_fen):
        fen = ''
        li_fen = li_fen.split(':')
        fen += li_fen[0]
        white_pieces = li_fen[1][1:].split(',')
        black_pieces = li_fen[2][1:].split(',')

        if self.variant in ['brazilian', 'russian', 'english', 'italian']:
            position_count = 32
        else:
            position_count = 50

        for index in range(1, position_count + 1):
            str_index = str(index)
            if str_index in white_pieces:
                fen += 'w'
            elif 'K' + str_index in white_pieces:
                fen += 'W'
            elif str_index in black_pieces:
                fen += 'b'
            elif 'K' + str_index in black_pieces:
                fen += 'B'
            else:
                fen += 'e'
        return fen

    def startpos_to_fen(self, fen):
        if fen != 'startpos':
            return fen
        if self.variant == 'frysk!':
            return 'W:W46,47,48,49,50:B1,2,3,4,5'
        elif self.variant in ['brazilian', 'russian', 'english', 'italian']:
            return 'W:W21,22,23,24,25,26,27,28,29,30,31,32:B1,2,3,4,5,6,7,8,9,10,11,12'
        else:
            return 'W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20'
