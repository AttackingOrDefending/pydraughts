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
        if not self.king:
            current_row = self.get_row()
            current_column = self.get_column()
            enemy_column = enemy_piece.get_column()
            enemy_row = enemy_piece.get_row()
            if self.variant == 'frisian' or self.variant == 'frysk!':
                if current_row - enemy_row == 2 and current_column - enemy_column == 0:
                    next_row = enemy_row - 2
                    if next_row not in self.board.position_layout:
                        pass
                    else:
                        return [self.board.position_layout.get(next_row, {}).get(current_column)]
                elif current_row - enemy_row == -2 and current_column - enemy_column == 0:
                    next_row = enemy_row + 2
                    if next_row not in self.board.position_layout:
                        pass
                    else:
                        return [self.board.position_layout.get(next_row, {}).get(current_column)]
                elif current_row - enemy_row == 0 and current_column - enemy_column == 1:
                    next_column = enemy_column - 1
                    if next_column not in self.board.position_layout[current_row]:
                        pass
                    else:
                        return [self.board.position_layout.get(current_row, {}).get(next_column)]
                elif current_row - enemy_row == 0 and current_column - enemy_column == -1:
                    next_column = enemy_column + 1
                    if next_column not in self.board.position_layout[current_row]:
                        pass
                    else:
                        return [self.board.position_layout.get(current_row, {}).get(next_column)]

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
            if self.variant == 'frisian' or self.variant == 'frysk!':
                same_row = current_row == enemy_row
                same_column = current_column == enemy_column and (current_row - enemy_row) % 2 == 0
                positions_to_check = []
                if same_row:
                    if current_column > enemy_column:
                        for add_column in range(1, self.board.width):
                            next_column = enemy_column - add_column
                            if next_column not in self.board.position_layout[current_row]:
                                pass
                            else:
                                positions.append(self.board.position_layout.get(current_row, {}).get(next_column))
                            position_to_check = current_column - add_column
                            if position_to_check not in self.board.position_layout[current_row]:
                                pass
                            else:
                                positions_to_check.append(self.board.position_layout.get(current_row, {}).get(position_to_check))
                    else:
                        for add_column in range(1, self.board.width):
                            next_column = enemy_column + add_column
                            if next_column not in self.board.position_layout[current_row]:
                                pass
                            else:
                                positions.append(self.board.position_layout.get(current_row, {}).get(next_column))
                            position_to_check = current_column + add_column
                            if position_to_check not in self.board.position_layout[current_row]:
                                pass
                            else:
                                positions_to_check.append(self.board.position_layout.get(current_row, {}).get(position_to_check))

                    new_positions = []
                    for index, position in enumerate(positions_to_check):
                        enemy_piece_found = False
                        for semi_position in positions_to_check[:index + 1]:
                            piece = self.board.searcher.get_piece_by_position(semi_position)
                            if piece is not None:
                                if piece.player == self.player or enemy_piece_found:
                                    break
                                else:
                                    enemy_piece_found = True
                            elif semi_position in captures:
                                break
                        else:
                            if position in positions:
                                new_positions.append(position)
                            continue
                        break
                    positions = new_positions

                    return positions
                elif same_column:
                    if current_row > enemy_row:
                        for add_row in range(2, self.board.height, 2):
                            next_row = enemy_row - add_row
                            if next_row not in self.board.position_layout:
                                pass
                            else:
                                positions.append(self.board.position_layout.get(next_row, {}).get(current_column))
                            position_to_check = current_row - add_row
                            if position_to_check not in self.board.position_layout:
                                pass
                            else:
                                positions_to_check.append(self.board.position_layout.get(position_to_check, {}).get(current_column))
                    else:
                        for add_row in range(2, self.board.height, 2):
                            next_row = enemy_row + add_row
                            if next_row not in self.board.position_layout:
                                pass
                            else:
                                positions.append(self.board.position_layout.get(next_row, {}).get(current_column))
                            position_to_check = current_row + add_row
                            if position_to_check not in self.board.position_layout:
                                pass
                            else:
                                positions_to_check.append(self.board.position_layout.get(position_to_check, {}).get(current_column))

                    new_positions = []
                    for index, position in enumerate(positions_to_check):
                        enemy_piece_found = False
                        for semi_position in positions_to_check[:index + 1]:
                            piece = self.board.searcher.get_piece_by_position(semi_position)
                            if piece is not None:
                                if piece.player == self.player or enemy_piece_found:
                                    break
                                else:
                                    enemy_piece_found = True
                            elif semi_position in captures:
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

            for index, position in enumerate(positions_to_check):
                enemy_piece_found = False
                for semi_position in positions_to_check[:index + 1]:
                    piece = self.board.searcher.get_piece_by_position(semi_position)
                    if piece is not None:
                        if piece.player == self.player or enemy_piece_found:
                            break
                        else:
                            enemy_piece_found = True
                    elif semi_position in captures:
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
        criteria = bool(self.king) if self.variant == 'english' or self.variant == 'italian' else bool(capture or self.king)
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
        if not self.king:
            if (self.variant == 'frisian' or self.variant == 'frysk!') and capture:
                # forward=True includes left and up and forward=False includes right and down
                positions = []
                current_row = self.get_row()
                current_column = self.get_column()
                next_row = current_row + ((2 if self.player == BLACK else -2) * (1 if forward else -1))
                next_column = current_column + ((1 if self.player == BLACK else -1) * (1 if forward else -1))
                if next_row not in self.board.position_layout:
                    pass
                else:
                    positions.append(self.board.position_layout[next_row][current_column])
                if next_column not in self.board.position_layout[current_row]:
                    pass
                else:
                    positions.append(self.board.position_layout[current_row][next_column])

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
            if (self.variant == 'frisian' or self.variant == 'frysk!') and capture:
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
                        break
                else:
                    positions.append(position)
                    continue
                break

            for index, position in enumerate(positions_diagonal_2):
                for semi_position in positions_diagonal_2[:index + 1]:
                    piece = self.board.searcher.get_piece_by_position(semi_position)
                    if piece is not None and not capture:
                        break
                else:
                    positions.append(position)
                    continue
                break

            return positions

    def get_next_column_indexes(self, current_row, current_column, i=1, unfiltered=False):
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
