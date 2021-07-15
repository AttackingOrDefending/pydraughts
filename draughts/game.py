from draughts.board import Board
import pickle

WHITE = 2
BLACK = 1


class Game:

    def __init__(self, variant='standard', fen='startpos'):
        self.variant = variant
        self.initial_fen = fen
        self.initial_hub_fen = self.li_fen_to_hub_fen(self.initial_fen)
        self.board = Board(self.variant, self.initial_hub_fen)
        self.moves = []
        self.move_stack = []
        self.capture_stack = []
        self.not_added_move = []
        self.not_added_capture = []
        self.hub_move_stack = []
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
            li_move = self.board_to_li(self.not_added_move + [move])
            self.move_stack.append(li_move)
            self.capture_stack.append(self.not_added_capture + [enemy_position])
            self.hub_move_stack.append(self.li_to_hub(li_move, self.not_added_capture + [enemy_position]))
            self.not_added_move = []
            self.not_added_capture = []

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
            return self.move_limit_reached() or not self.legal_moves() or has_king
        return self.move_limit_reached() or not self.legal_moves()

    def get_winner(self):
        if self.whose_turn() == BLACK and not self.board.count_movable_player_pieces(BLACK, self.not_added_capture):
            return WHITE
        elif self.whose_turn() == WHITE and not self.board.count_movable_player_pieces(WHITE, self.not_added_capture):
            return BLACK
        else:
            if self.variant == 'breakthrough':
                for loc in range(1, self.board.position_count + 1):
                    piece = self.board.searcher.get_piece_by_position(loc)
                    if piece is not None:
                        if piece.player == WHITE and piece.king:
                            return WHITE
                        elif piece.player == BLACK and piece.king:
                            return BLACK
                return None
            else:
                return None

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
        elif self.variant == 'russian':
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

    def make_len_4(self, move1, move2):
        return self.make_len_2(move1) + self.make_len_2(move2)

    def board_to_li_old(self, move):
        return self.make_len_4(move[0][0], move[-1][1])

    def board_to_li(self, move):
        final_move = self.make_len_2(move[0][0])
        for semi_move in move:
            final_move += self.make_len_2(semi_move[1])
        return final_move

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

    def hub_to_li_board(self, move):
        possible_moves, possible_captures = self.legal_moves()
        moves_li_board = {}
        for possible_move, possible_capture in zip(possible_moves, possible_captures):
            if possible_capture[0] is None:
                possible_capture = []
            li_move = self.board_to_li_old(possible_move) + self.sort_captures(possible_capture)
            moves_li_board[li_move] = possible_move
        board_move = moves_li_board[move]
        api_move = []
        for semi_move in board_move:
            api_move.append(self.board_to_li([semi_move]))
        return api_move, board_move

    def li_to_hub(self, move, captures):
        if captures[0] is None:
            captures = []
        hub_move = move[:2] + move[-2:] + self.sort_captures(captures)
        if captures:
            hub_move = 'x'.join([hub_move[i:i + 2] for i in range(0, len(hub_move), 2)])
        else:
            hub_move = hub_move[:2] + '-' + hub_move[2:]
        return hub_move

    def board_to_li_api(self, move):
        moves = []
        for semi_move in move:
            moves.append(self.make_len_4(semi_move[0], semi_move[1]))
        return moves

    def li_api_to_li_one(self, move):
        new_move = move[0][:2]
        for semi_move in move:
            new_move += semi_move[2:]
        return new_move

    def board_to_pdn(self, move):
        possible_moves, possible_captures = self.legal_moves()
        starts_endings = []
        for possible_move in possible_moves:
            starts_endings.append(self.make_len_4(possible_move[0][0], possible_move[-1][1]))
        if starts_endings.count(self.make_len_4(move[0][0], move[-1][1])) == 1:
            index = possible_moves.index(move)
            captures = possible_captures[index]
            if captures[0] is not None:
                return self.make_len_2(str(move[0][0])) + 'x' + self.make_len_2(str(move[-1][1]))
            else:
                return self.make_len_2(str(move[0][0])) + '-' + self.make_len_2(str(move[-1][1]))
        else:
            li_move = self.board_to_li(move)
            li_move = [li_move[i:i + 2] for i in range(0, len(li_move), 2)]
            return 'x'.join(li_move)

    def board_to_hub(self, move):
        possible_moves, possible_captures = self.legal_moves()
        li_move = self.board_to_li(move)
        moves_to_captures = {}
        for possible_move, possible_capture in zip(possible_moves, possible_captures):
            moves_to_captures[self.board_to_li(possible_move)] = possible_capture
        captures = moves_to_captures[li_move]
        return self.li_to_hub(li_move, captures)

    def li_fen_to_hub_fen(self, li_fen):
        if li_fen == 'startpos' and self.variant == 'frysk!':
            return 'Wbbbbbeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeewwwww'
        elif li_fen == 'startpos' and (self.variant == 'brazilian' or self.variant == 'russian'):
            return 'Wbbbbbbbbbbbbeeeeeeeewwwwwwwwwwww'
        elif li_fen == 'startpos':
            return 'Wbbbbbbbbbbbbbbbbbbbbeeeeeeeeeewwwwwwwwwwwwwwwwwwww'
        fen = ''
        li_fen = li_fen.split(':')
        fen += li_fen[0]
        white_pieces = li_fen[1][1:].split(',')
        black_pieces = li_fen[2][1:].split(',')

        if self.variant == 'brazilian' or self.variant == 'russian':
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
