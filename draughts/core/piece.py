from math import ceil

WHITE = 2
BLACK = 1


class Piece:

    def __init__(self, variant='standard'):
        self.player = None
        self.other_player = None
        self.king = False
        self.captured = False
        self.position = None
        self.board = None
        self.became_king = -100
        self.capture_move_enemies = {}
        self.variant = variant
        self.reset_for_new_board()

    def reset_for_new_board(self):
        self.possible_capture_moves = None
        self.possible_positional_moves = None

    def is_movable(self, captures):
        return (self.get_possible_capture_moves(captures) or self.get_possible_positional_moves()) and not self.captured

    def capture(self):
        self.captured = True
        self.position = None

    def move(self, new_position, move_number):
        self.position = new_position
        was_king = self.king
        self.king = self.king or self.is_on_enemy_home_row()
        if self.king != was_king:
            self.became_king = move_number

    def get_possible_capture_moves(self, captures):
        if self.possible_capture_moves is None:
            self.possible_capture_moves = self.build_possible_capture_moves(captures)

        return self.possible_capture_moves

    def build_possible_capture_moves(self, captures):
        adjacent_enemy_positions = list(filter((lambda position: position in self.board.searcher.get_positions_by_player(self.other_player)), self.get_adjacent_positions(capture=True)))
        capture_move_positions = []
        for enemy_position in adjacent_enemy_positions:
            enemy_piece = self.board.searcher.get_piece_by_position(enemy_position)
            if self.variant == 'italian' and not self.king and enemy_piece.king:
                # Men can't capture kings in italian draughts
                continue
            positions_behind_enemy = self.get_position_behind_enemy(enemy_piece, captures)
            for position_behind_enemy in positions_behind_enemy:

                if (position_behind_enemy is not None) and self.board.position_is_open(position_behind_enemy):
                    capture_move_positions.append(position_behind_enemy)
                    self.capture_move_enemies[position_behind_enemy] = enemy_piece

        return self.create_moves_from_new_positions(capture_move_positions)

    def get_position_behind_enemy(self, enemy_piece, captures):
        """
        Gets the positions the piece can land after capturing the enemy piece.
        :param captures: it contains all the positions of the pieces that this piece has captured during this multi-capture,
        because kings in multi-captures can't go over a piece they have captured in that move sequence in most variants
        """
        if not self.king:
            current_row = self.get_row()
            current_column = self.get_column()
            enemy_column = enemy_piece.get_column()
            enemy_row = enemy_piece.get_row()
            if self.variant in ['frisian', 'frysk!', 'turkish']:  # Orthogonal captures
                row_difference = current_row - enemy_row
                column_difference = current_column - enemy_column
                if (column_difference == 0 or row_difference == 0) and (row_difference % 2 == 0 if self.variant in ['frisian', 'frysk!'] else True):
                    next_row = enemy_row - row_difference
                    next_column = enemy_column - column_difference
                    return [self.board.position_layout.get(next_row, {}).get(next_column)]

            column_adjustment = -1 if current_row % 2 == 0 else 1
            column_behind_enemy = current_column + column_adjustment if current_column == enemy_column else enemy_column
            row_behind_enemy = enemy_row + (enemy_row - current_row)

            return [self.board.position_layout.get(row_behind_enemy, {}).get(column_behind_enemy)]
        else:
            positions = []
            current_row = self.get_row()
            current_column = self.get_column()
            enemy_column = enemy_piece.get_column()
            enemy_row = enemy_piece.get_row()
            if self.variant in ['frisian', 'frysk!', 'turkish']:  # Orthogonal captures
                positions_to_check = []
                row_difference = current_row - enemy_row
                column_difference = current_column - enemy_column
                add_row = 0
                if row_difference < 0:
                    add_row = -1
                elif row_difference > 0:
                    add_row = 1
                add_column = 0
                if column_difference < 0:
                    add_column = -1
                elif column_difference > 0:
                    add_column = 1
                if (column_difference == 0 or row_difference == 0) and (row_difference % 2 == 0 if self.variant in ['frisian', 'frysk!'] else True):
                    for multiplier in range(1, max(self.board.width, self.board.height)):
                        if multiplier % 2 == 1 and self.variant in ['frisian', 'frysk!']:
                            continue
                        next_row = current_row - multiplier * add_row
                        next_column = current_column - multiplier * add_column
                        if next_row in self.board.position_layout and next_column in self.board.position_layout[next_row]:
                            positions_to_check.append(self.board.position_layout.get(next_row, {}).get(next_column))
                        next_row = enemy_row - multiplier * add_row
                        next_column = enemy_column - multiplier * add_column
                        if next_row in self.board.position_layout and next_column in self.board.position_layout[next_row]:
                            positions.append(self.board.position_layout.get(next_row, {}).get(next_column))

                    new_positions = []
                    for index, position in enumerate(positions_to_check):
                        enemy_piece_found = False
                        for semi_position in positions_to_check[:index + 1]:
                            piece = self.board.searcher.get_piece_by_position(semi_position)
                            if piece is not None:
                                if piece.player == self.player or enemy_piece_found:  # It stops if it meets a piece of the same color or another opponent piece
                                    break
                                else:
                                    enemy_piece_found = True
                            elif semi_position in ([captures[-1]] if self.variant == 'turkish' and captures else captures):
                                # Kings in multi-captures can't go over a piece they have captured in that move sequence in frisian and frysk!
                                # In turkish they can but we use the last capture, so we prevent the piece from turning 180 degrees, which is not allowed
                                break
                        else:
                            if position in positions:
                                new_positions.append(position)
                            continue
                        break
                    positions = new_positions

                    return positions
            elif self.variant == 'english' or self.variant == 'italian':
                # Same as if it is not a king
                column_adjustment = -1 if current_row % 2 == 0 else 1
                column_behind_enemy = current_column + column_adjustment if current_column == enemy_column else enemy_column
                row_behind_enemy = enemy_row + (enemy_row - current_row)

                return [self.board.position_layout.get(row_behind_enemy, {}).get(column_behind_enemy)]
            adjacent_positions = self.get_adjacent_positions(capture=True)
            down_direction = enemy_row > current_row
            left_direction = enemy_column < current_column if current_row % 2 == 1 else enemy_column <= current_column

            legal_adjacent_positions = []
            was_king = enemy_piece.king
            enemy_piece.king = True
            for position in enemy_piece.get_adjacent_positions(capture=True):
                column = (position - 1) % self.board.width
                row = self.get_row_from_position(position)
                down_direction_possible = row > enemy_row
                left_direction_possible = column < enemy_column if enemy_row % 2 == 1 else column <= enemy_column
                # Checks if the captured piece square is between the starting square and the landing square
                # For example, if the captured piece square is to the left and down of the starting square, we check if the landing square is to the left and down of the captured piece square
                # It also checks if the position is in a pseudolegal list of legal moves (because we can have landing squares that aren't in the same diagonal as the staring square (e.g. if the piece is in 28, 31 isn't a possible landing square))
                if down_direction_possible == down_direction and left_direction_possible == left_direction and position in adjacent_positions:
                    legal_adjacent_positions.append(self.board.position_layout.get(row, {}).get(column))
            enemy_piece.king = was_king
            adjacent_positions = legal_adjacent_positions

            positions_to_check = []
            row_to_check = current_row
            position_to_check = self.position
            subtract_for_variant = 1 if self.variant == 'brazilian' or self.variant == 'russian' else 0
            for add in range(1, self.board.height):
                if down_direction and not left_direction and row_to_check % 2 == 1:
                    position_to_check += 5 - subtract_for_variant
                    row_to_check += 1
                elif down_direction and not left_direction and row_to_check % 2 == 0:
                    position_to_check += 6 - subtract_for_variant
                    row_to_check += 1
                elif down_direction and left_direction and row_to_check % 2 == 1:
                    position_to_check += 4 - subtract_for_variant
                    row_to_check += 1
                elif down_direction and left_direction and row_to_check % 2 == 0:
                    position_to_check += 5 - subtract_for_variant
                    row_to_check += 1
                elif not down_direction and not left_direction and row_to_check % 2 == 1:
                    position_to_check -= 5 - subtract_for_variant
                    row_to_check -= 1
                elif not down_direction and not left_direction and row_to_check % 2 == 0:
                    position_to_check -= 4 - subtract_for_variant
                    row_to_check -= 1
                elif not down_direction and left_direction and row_to_check % 2 == 1:
                    position_to_check -= 6 - subtract_for_variant
                    row_to_check -= 1
                elif not down_direction and left_direction and row_to_check % 2 == 0:
                    position_to_check -= 5 - subtract_for_variant
                    row_to_check -= 1
                if self.get_row_from_position(position_to_check) == row_to_check:
                    positions_to_check.append(position_to_check)
                else:
                    break

            for index, position in enumerate(positions_to_check):  # Checks if the piece will encounter any other piece in its path
                enemy_piece_found = False
                for semi_position in positions_to_check[:index + 1]:
                    piece = self.board.searcher.get_piece_by_position(semi_position)
                    if piece is not None:
                        if piece.player == self.player or enemy_piece_found:  # It stops if it meets a piece of the same color or another opponent piece
                            break
                        else:
                            enemy_piece_found = True
                    elif semi_position in captures:  # Kings in multi-captures can't go over a piece they have captured in that move sequence in most variants
                        break
                else:
                    if position in adjacent_positions:
                        positions.append(position)
                    continue
                break
            return positions

    def get_possible_positional_moves(self):
        if self.possible_positional_moves is None:
            self.possible_positional_moves = self.build_possible_positional_moves()

        return self.possible_positional_moves

    def build_possible_positional_moves(self):
        new_positions = list(filter((lambda position: self.board.position_is_open(position)), self.get_adjacent_positions()))

        return self.create_moves_from_new_positions(new_positions)

    def create_moves_from_new_positions(self, new_positions):
        return [[self.position, new_position] for new_position in new_positions]

    def get_adjacent_positions(self, capture=False):
        criteria = bool(self.king) if self.variant in ['english', 'italian', 'turkish'] else bool(capture or self.king)  # In english, italian and turkish men can't capture backwards
        return self.get_directional_adjacent_positions(forward=True, capture=capture) + (self.get_directional_adjacent_positions(forward=False, capture=capture) if criteria else [])

    def get_column(self):
        return (self.position - 1) % self.board.width

    def get_row(self):
        return self.get_row_from_position(self.position)

    def is_on_enemy_home_row(self):
        return self.get_row() == self.get_row_from_position(1 if self.other_player == BLACK else self.board.position_count)

    def get_row_from_position(self, position):
        return ceil(position / self.board.width) - 1

    def get_directional_adjacent_positions(self, forward, capture=False):
        # In frisian, forward=True includes left and up and forward=False includes right and down
        # e.g. If the piece is at 33, square 32 will be considered in forward=True and square 34 will be considered in forward=False
        # In turkish, if the piece is a king, forward=True includes left and up and forward=False includes right and down
        # if it isn't a king forward=True, calculates up, left and right
        if not self.king:
            if self.variant == 'turkish':
                positions = []
                current_row = self.get_row()
                current_column = self.get_column()
                next_row = current_row + (1 if self.player == BLACK else -1)
                if next_row in self.board.position_layout:
                    positions.append(self.board.position_layout[next_row][current_column])
                next_column = current_column - 1
                if next_column in self.board.position_layout[current_row]:
                    positions.append(self.board.position_layout[current_row][next_column])
                next_column = current_column + 1
                if next_column in self.board.position_layout[current_row]:
                    positions.append(self.board.position_layout[current_row][next_column])
                return positions
            if (self.variant == 'frisian' or self.variant == 'frysk!') and capture:
                positions = []
                current_row = self.get_row()
                current_column = self.get_column()
                next_row = current_row + ((2 if self.player == BLACK else -2) * (1 if forward else -1))
                next_column = current_column + ((1 if self.player == BLACK else -1) * (1 if forward else -1))

                # Orthogonal squares (only in frisian and frysk!)
                if next_row not in self.board.position_layout:
                    pass
                else:
                    positions.append(self.board.position_layout[next_row][current_column])
                if next_column not in self.board.position_layout[current_row]:
                    pass
                else:
                    positions.append(self.board.position_layout[current_row][next_column])

                # Diagonal squares (as in standard draughts)
                next_row = current_row + ((1 if self.player == BLACK else -1) * (1 if forward else -1))

                if next_row not in self.board.position_layout:
                    pass
                else:

                    next_column_indexes = self.get_next_column_indexes(current_row, self.get_column())

                    positions += [self.board.position_layout[next_row][column_index] for column_index in next_column_indexes]
                return positions
            else:
                current_row = self.get_row()
                next_row = current_row + ((1 if self.player == BLACK else -1) * (1 if forward else -1))

                if next_row not in self.board.position_layout:
                    return []

                next_column_indexes = self.get_next_column_indexes(current_row, self.get_column())

                return [self.board.position_layout[next_row][column_index] for column_index in next_column_indexes]
        else:
            positions = []
            current_row = self.get_row()
            current_column = self.get_column()
            if self.variant == 'turkish':
                for multiplier in range(1, self.board.height):
                    next_row = current_row + multiplier * (1 if self.player == BLACK else -1) * (1 if forward else -1)
                    if next_row in self.board.position_layout:
                        positions.append(self.board.position_layout[next_row][current_column])
                for multiplier in range(1, self.board.width):
                    next_column = current_column + multiplier * (1 if self.player == BLACK else -1) * (1 if forward else -1)
                    if next_column in self.board.position_layout[current_row]:
                        positions.append(self.board.position_layout[current_row][next_column])
                return positions
            if (self.variant == 'frisian' or self.variant == 'frysk!') and capture:
                # Orthogonal squares
                for add_column in range(1, self.board.width):
                    next_column = current_column + ((add_column if self.player == BLACK else -add_column) * (1 if forward else -1))
                    if next_column not in self.board.position_layout[current_row]:
                        positions += []
                        continue
                    positions += [self.board.position_layout[current_row][next_column]]
                for add_row in range(2, self.board.height, 2):
                    next_row = current_row + ((add_row if self.player == BLACK else -add_row) * (1 if forward else -1))
                    if next_row not in self.board.position_layout:
                        positions += []
                        continue
                    positions += [self.board.position_layout[next_row][current_column]]
            elif self.variant == 'english' or self.variant == 'italian':
                # Same as if it is not a king
                next_row = current_row + ((1 if self.player == BLACK else -1) * (1 if forward else -1))

                if next_row not in self.board.position_layout:
                    return []

                next_column_indexes = self.get_next_column_indexes(current_row, self.get_column())

                return [self.board.position_layout[next_row][column_index] for column_index in next_column_indexes]

            # Diagonal squares
            positions_diagonal_1 = []
            positions_diagonal_2 = []
            for i in range(1, self.board.height):
                next_row = current_row + ((i if self.player == BLACK else -i) * (1 if forward else -1))

                if next_row not in self.board.position_layout:
                    positions += []
                    continue

                next_column_indexes = self.get_next_column_indexes(current_row, current_column, i, True)
                if 0 <= next_column_indexes[0] < self.board.width:
                    positions_diagonal_1.append(self.board.position_layout[next_row][next_column_indexes[0]])
                if 0 <= next_column_indexes[1] < self.board.width:
                    positions_diagonal_2.append(self.board.position_layout[next_row][next_column_indexes[1]])

            for index, position in enumerate(positions_diagonal_1):
                for semi_position in positions_diagonal_1[:index + 1]:
                    piece = self.board.searcher.get_piece_by_position(semi_position)
                    if piece is not None and not capture:
                        # If we encounter a piece, and we are searching for a positional move not a capture move, we break the loop
                        break
                else:
                    positions.append(position)
                    continue
                break

            for index, position in enumerate(positions_diagonal_2):
                for semi_position in positions_diagonal_2[:index + 1]:
                    piece = self.board.searcher.get_piece_by_position(semi_position)
                    if piece is not None and not capture:
                        # If we encounter a piece, and we are searching for a positional move not a capture move, we break the loop
                        break
                else:
                    positions.append(position)
                    continue
                break

            return positions

    def get_next_column_indexes(self, current_row, current_column, i=1, unfiltered=False):
        """
        Get the index of the next column.
        It isn't as simple as finding the next row (where we only add or subtract 1) but the column index only changes
        once every 2 rows.
        e.g. Square 32 and 27 are both in the second row, but 27 and 31 are not.
        :param i: current_row ± i is the row we should search (the columns for current_row + i are the same as current_row - i). e.g if current row=3 and i=2, we will return the 2 possible columns for row 5 (which will be the same for row 1)
        """
        column_indexes = [0, 0]
        start_right = True if current_row % 2 == 0 else False
        for semi_i in range(1, i + 1):
            if start_right and semi_i % 2 == 1 or not start_right and semi_i % 2 == 0:
                column_indexes[1] += 1
            else:
                column_indexes[0] -= 1

        column_indexes = list(map(lambda value: value + current_column, column_indexes))

        if unfiltered:
            return column_indexes
        else:
            return filter((lambda column_index: 0 <= column_index < self.board.width), column_indexes)

    def __setattr__(self, name, value):
        super(Piece, self).__setattr__(name, value)

        if name == 'player':
            self.other_player = BLACK if value == WHITE else WHITE
