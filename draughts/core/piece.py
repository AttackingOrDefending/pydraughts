from __future__ import annotations
from math import ceil
from typing import List

WHITE = 2
BLACK = 1


class Piece:

    def __init__(self, variant: str = 'standard') -> None:
        self.player = None
        self.king = False
        self.captured = False
        self.position = None
        self.board = None
        self.became_king = -100
        self.capture_move_enemies = {}
        self.variant = variant
        self.reset_for_new_board()

        self.diagonal_moves = self.variant not in ['turkish']
        self.orthogonal_moves = self.variant in ['turkish']
        self.orthogonal_captures = self.variant in ['frisian', 'frysk!', 'turkish']
        # In most draughts variants only the dark squares are playable.
        self.half_of_the_squares_are_playable = self.variant not in ['turkish']
        # The bottom left square isn't a playing square in italian draughts.
        self.bottom_left_square_is_playable = self.variant in ['italian']
        # Men can't capture kings in italian draughts.
        self.man_can_capture_king = self.variant not in ['italian']
        # There are three possible values for squares_per_row (4, 5, 8), which is why two lines are needed.
        self.squares_per_row = 4 if self.variant in ['russian', 'brazilian', 'english', 'italian'] else 5
        self.squares_per_row = 8 if self.variant in ['turkish'] else self.squares_per_row
        self.kings_can_move_more_than_one_square = self.variant not in ['english', 'italian']
        self.men_can_capture_backwards = self.variant not in ['english', 'italian', 'turkish']
        self.kings_can_jump_over_an_already_captured_piece = self.variant in ['turkish']
        self.kings_can_turn_180_degrees_in_multicapture = False  # No variant supports it for now.

    def reset_for_new_board(self) -> None:
        """Reset possible moves to None."""
        self.possible_capture_moves = None
        self.possible_positional_moves = None

    def get_square(self, row: int, column: int) -> int:
        """Get the square given the row and column."""
        return self.board.position_layout.get(row, {}).get(column)

    def is_movable(self, captures: List[int]) -> bool:
        """Get if the piece can move."""
        return bool((self.get_possible_capture_moves(captures) or self.get_possible_positional_moves()) and not self.captured)

    def capture(self) -> None:
        """Flag the piece as captured."""
        self.captured = True
        self.position = None

    def move(self, new_position: int, move_number: int) -> None:
        """Move the piece to a new position."""
        self.position = new_position
        was_king = self.king
        self.king = self.king or self.is_on_enemy_home_row()
        if self.king != was_king:
            self.became_king = move_number

    def get_possible_capture_moves(self, captures: List[int]) -> List[List[int]]:
        """Get all possible capture moves (not positional moves) for this piece."""
        if self.possible_capture_moves is None:
            self.possible_capture_moves = self.build_possible_capture_moves(captures)

        return self.possible_capture_moves

    def build_possible_capture_moves(self, captures: List[int]) -> List[List[int]]:
        """Build all possible capture moves (not positional moves) for this piece."""
        adjacent_enemy_positions = list(filter((lambda position: position in self.board.searcher.get_positions_by_player(self.other_player)), self.get_adjacent_positions(capture=True)))
        capture_move_positions = []

        for enemy_position in adjacent_enemy_positions:
            enemy_piece = self.board.searcher.get_piece_by_position(enemy_position)

            if not self.man_can_capture_king and not self.king and enemy_piece.king:
                continue

            positions_behind_enemy = self.get_position_behind_enemy(enemy_piece, captures)
            for position_behind_enemy in positions_behind_enemy:

                if (position_behind_enemy is not None) and self.board.position_is_open(position_behind_enemy):
                    capture_move_positions.append(position_behind_enemy)
                    self.capture_move_enemies[position_behind_enemy] = enemy_piece

        return self.create_moves_from_new_positions(capture_move_positions)

    def get_diagonal_one_square_behind_enemy(self, enemy_piece: Piece) -> List[int]:
        """
        Get the diagonal square directly behind the enemy piece if the piece can move only one square
        (usually men, but in some variants kings can also only move one square).
        """
        # Diagonal captures
        current_row = self.get_row()
        current_column = self.get_column()
        enemy_column = enemy_piece.get_column()
        enemy_row = enemy_piece.get_row()

        # Orthogonal, not diagonal
        if current_row == enemy_row or current_column == enemy_column and (current_row - enemy_row) % 2 == 0:
            return []

        column_adjustment = -1 if current_row % 2 == int(self.bottom_left_square_is_playable) else 1
        column_behind_enemy = current_column + column_adjustment if current_column == enemy_column else enemy_column
        row_behind_enemy = enemy_row + (enemy_row - current_row)

        return [self.get_square(row_behind_enemy, column_behind_enemy)]

    def get_orthogonal_one_square_behind_enemy(self, enemy_piece: Piece) -> List[int]:
        """
        Get the orthogonal square directly behind the enemy piece if the piece can move only one square
        (usually men, but in some variants kings can also only move one square).
        """
        # Orthogonal captures
        current_row = self.get_row()
        current_column = self.get_column()
        enemy_column = enemy_piece.get_column()
        enemy_row = enemy_piece.get_row()

        row_difference = current_row - enemy_row
        column_difference = current_column - enemy_column

        # Check if the pieces are on the same row or column

        # If half_of_the_squares_are_playable the square in the front is not playable
        # (e.g. a1 is playable but a2 isn't, so the square directly in front of it is a3)
        if (column_difference == 0 or row_difference == 0) and (row_difference % 2 == 0 if self.half_of_the_squares_are_playable else True):
            next_row = enemy_row - row_difference
            next_column = enemy_column - column_difference
            return [self.get_square(next_row, next_column)]
        return []

    def get_diagonal_multiple_squares_behind_enemy(self, enemy_piece: Piece, captures: List[int]) -> List[int]:
        """Get the diagonal squares behind the enemy piece if the piece can move more than one square (kings)."""
        positions = []
        current_row = self.get_row()
        current_column = self.get_column()
        enemy_column = enemy_piece.get_column()
        enemy_row = enemy_piece.get_row()

        # Orthogonal, not diagonal
        if current_row == enemy_row or current_column == enemy_column and (current_row - enemy_row) % 2 == 0:
            return []

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
                legal_adjacent_positions.append(self.get_square(row, column))

        enemy_piece.king = was_king
        adjacent_positions = legal_adjacent_positions

        positions_to_check = []
        row_to_check = current_row
        position_to_check = self.position

        for multiplier in range(1, self.board.height):
            row_change = 1 if down_direction else -1
            add = self.squares_per_row
            add *= row_change

            # Because only half the squares are playable

            # Add 1 square if the piece is moving diagonally to the right
            add += int(not left_direction)
            # Remove 1 square if the row the piece is in, is an odd 4
            add -= int(row_to_check % 2 == 1)
            # e.g. From 30 to 25: We start with add=5 because variant="standard".
            # The piece is going to the right (from white's perspective always), so we add 1 to add.
            # The piece is in an odd row (square 30 is in row 5) so we subtract 1 from add.
            # We end with add=5, which is the correct result.

            position_to_check += add
            row_to_check += row_change

            # Checks if position is in the correct row.
            # e.g. If a piece is at square 35 it can't go to the right, but when we subtract 6, we get 29, which would
            # be correct if we could go to the right. To prevent this we check that the expected row matches the actual
            # row. In this example we expect row=5, but we get row=4, so we know that this isn't correct.
            if self.get_row_from_position(position_to_check) == row_to_check:
                positions_to_check.append(position_to_check)
            else:
                break

        # Checks if the piece will encounter any other piece in its path
        for index, position in enumerate(positions_to_check):
            enemy_piece_found = False
            for semi_position in positions_to_check[:index + 1]:
                piece = self.board.searcher.get_piece_by_position(semi_position)
                if piece is not None:
                    # It stops if it meets a piece of the same color or another opponent piece
                    if piece.player == self.player or enemy_piece_found:
                        break
                    else:
                        enemy_piece_found = True
                # Kings in multi-captures can't go over a piece they have captured in that move sequence in most
                # variants. They can in turkish, but pieces in turkish draughts can't move diagonally.
                elif semi_position in captures:
                    break
            else:
                if position in adjacent_positions:
                    positions.append(position)
                continue
            break
        return positions

    def get_orthogonal_multiple_squares_behind_enemy(self, enemy_piece: Piece, captures: List[int]) -> List[int]:
        """Get the orthogonal squares behind the enemy piece if the piece can move more than one square (kings)."""
        positions = []
        current_row = self.get_row()
        current_column = self.get_column()
        enemy_column = enemy_piece.get_column()
        enemy_row = enemy_piece.get_row()

        positions_to_check = []
        row_difference = current_row - enemy_row
        column_difference = current_column - enemy_column

        # Get direction of row change
        add_row = 0
        if row_difference < 0:
            add_row = -1
        elif row_difference > 0:
            add_row = 1

        # Get direction of column change
        add_column = 0
        if column_difference < 0:
            add_column = -1
        elif column_difference > 0:
            add_column = 1

        # Check if the pieces are on the same row or column
        if (column_difference == 0 or row_difference == 0) and (row_difference % 2 == 0 if self.half_of_the_squares_are_playable else True):
            for multiplier in range(1, max(self.board.width, self.board.height)):
                # In frisian, the square directly in front, behind, on the left and on the right
                # of the piece isn't playable.
                if multiplier % 2 == 1 and self.half_of_the_squares_are_playable:
                    continue

                next_row = current_row - multiplier * add_row
                next_column = current_column - multiplier * add_column
                if next_row in self.board.position_layout and next_column in self.board.position_layout[next_row]:
                    positions_to_check.append(self.get_square(next_row, next_column))

                next_row = enemy_row - multiplier * add_row
                next_column = enemy_column - multiplier * add_column
                if next_row in self.board.position_layout and next_column in self.board.position_layout[next_row]:
                    positions.append(self.get_square(next_row, next_column))

            # Kings in multi-captures can't go over a piece they have captured in that move sequence in
            # frisian and frysk!. In turkish they can, but we use the last capture to prevent the piece from
            # turning 180 degrees, which is not allowed.
            if self.kings_can_turn_180_degrees_in_multicapture:
                captures = []
            elif self.kings_can_jump_over_an_already_captured_piece and captures:
                captures = [captures[-1]]

            new_positions = []
            for index, position in enumerate(positions_to_check):
                enemy_piece_found = False
                for semi_position in positions_to_check[:index + 1]:
                    piece = self.board.searcher.get_piece_by_position(semi_position)
                    if piece is not None:
                        # It stops if it meets a piece of the same color or another opponent piece.
                        if piece.player == self.player or enemy_piece_found:
                            break
                        else:
                            enemy_piece_found = True
                    elif semi_position in captures:
                        # Kings in multi-captures can't go over a piece they have captured in that move sequence in
                        # frisian and frysk!. In turkish they can, but we use the last capture to prevent the piece from
                        # turning 180 degrees, which is not allowed.
                        break
                else:
                    if position in positions:
                        new_positions.append(position)
                    continue
                break

            positions = new_positions

        return positions

    def get_position_behind_enemy(self, enemy_piece: Piece, captures: List[int]) -> List[int]:
        """
        Gets the positions the piece can land after capturing the enemy piece.
        :param captures: it contains all the positions of the pieces that this piece has captured during this multi-capture,
        because kings in multi-captures can't go over a piece they have captured in that move sequence in most variants
        """
        positions = []
        if not self.king:
            if self.orthogonal_captures or self.orthogonal_moves:
                positions += self.get_orthogonal_one_square_behind_enemy(enemy_piece)
            if not positions and self.diagonal_moves:
                positions += self.get_diagonal_one_square_behind_enemy(enemy_piece)
        else:
            if self.kings_can_move_more_than_one_square:
                if self.orthogonal_captures or self.orthogonal_moves:
                    positions += self.get_orthogonal_multiple_squares_behind_enemy(enemy_piece, captures)
                if not positions and self.diagonal_moves:
                    positions += self.get_diagonal_multiple_squares_behind_enemy(enemy_piece, captures)
            else:
                if self.orthogonal_captures or self.orthogonal_moves:
                    positions += self.get_orthogonal_one_square_behind_enemy(enemy_piece)
                if not positions and self.diagonal_moves:
                    positions += self.get_diagonal_one_square_behind_enemy(enemy_piece)
        return positions

    def get_possible_positional_moves(self) -> List[List[int]]:
        """Get all possible positional moves (not capture moves) for this piece."""
        if self.possible_positional_moves is None:
            self.possible_positional_moves = self.build_possible_positional_moves()

        return self.possible_positional_moves

    def build_possible_positional_moves(self) -> List[List[int]]:
        """Build all possible positional moves (not capture moves) for this piece."""
        new_positions = list(filter((lambda position: self.board.position_is_open(position)), self.get_adjacent_positions()))

        return self.create_moves_from_new_positions(new_positions)

    def create_moves_from_new_positions(self, new_positions: List[int]) -> List[List[int]]:
        """Create moves ([[cur_pos, end_pos1], [cur_pos, end_pos2]]) given the ending square ([end_pos1, end_pos2])."""
        return [[self.position, new_position] for new_position in new_positions]

    def get_adjacent_positions(self, capture: bool = False) -> List[int]:
        """Get all adjacent positions of the piece."""
        # In some variants men can't capture backwards
        criteria = bool(capture or self.king) if self.men_can_capture_backwards else bool(self.king)
        return self.get_directional_adjacent_positions(forward=True, capture=capture) + (self.get_directional_adjacent_positions(forward=False, capture=capture) if criteria else [])

    def get_column(self) -> int:
        """Get the piece's column."""
        return (self.position - 1) % self.board.width

    def get_row(self) -> int:
        """Get the piece's row."""
        return self.get_row_from_position(self.position)

    def is_on_enemy_home_row(self) -> bool:
        """Get if the piece is on the enemy's home row (used for promotions)."""
        return self.get_row() == self.get_row_from_position(1 if self.other_player == BLACK else self.board.position_count)

    def get_row_from_position(self, position: int) -> int:
        """Get the piece's row, given its square."""
        return ceil(position / self.board.width) - 1

    def get_directional_diagonal_one_square_adjacent_positions(self, forward: bool) -> List[int]:
        """
        Get the diagonal directional adjacent positions if the piece can move only one square
        (usually men, but in some variants kings can also only move one square).
        """
        current_row = self.get_row()
        next_row = current_row + ((1 if self.player == BLACK else -1) * (1 if forward else -1))

        if next_row not in self.board.position_layout:
            return []

        next_column_indexes = self.get_next_column_indexes(current_row, self.get_column())

        return [self.board.position_layout[next_row][column_index] for column_index in next_column_indexes]

    def get_directional_orthogonal_one_square_adjacent_positions(self, forward: bool, capture: bool) -> List[int]:
        """
        Get the orthogonal directional adjacent positions if the piece can move only one square
        (usually men, but in some variants kings can also only move one square).
        """
        positions = []
        current_row = self.get_row()
        current_column = self.get_column()

        # If only half_of_the_squares_are_playable, the first square directly in front is 2 rows away,
        # while if all the squares are playable, it is only 1 row away.
        row_in_front = 2 if self.half_of_the_squares_are_playable else 1

        if self.orthogonal_moves or self.orthogonal_captures and self.men_can_capture_backwards and capture:
            # If self.orthogonal_moves is False:
            # With forward=True we will calculate left and up and with forward=False we will calculate right and down.
            # e.g. If the piece is at 33, square 32 will be considered in forward=True and
            # square 34 will be considered in forward=False.
            # So we will use both forward=True and forward=False, to get all 4 directions.
            # This is used for example in frisian.
            #
            # if self.orthogonal_moves is True:
            # With forward=True we will calculate left, right and up.
            # forward=False will return the same as forward=True because it is not meant to be used when
            # self.orthogonal_moves is True.
            # This is used for example in turkish.

            next_row = current_row + ((row_in_front if self.player == BLACK else -row_in_front) * (1 if forward else -1))
            next_column = current_column + ((1 if self.player == BLACK else -1) * (1 if forward else -1))

            if next_row in self.board.position_layout:
                positions.append(self.board.position_layout[next_row][current_column])
            if next_column in self.board.position_layout[current_row]:
                positions.append(self.board.position_layout[current_row][next_column])

            if self.orthogonal_moves:
                next_column = current_column - ((1 if self.player == BLACK else -1) * (1 if forward else -1))
                if next_column in self.board.position_layout[current_row]:
                    positions.append(self.board.position_layout[current_row][next_column])

        return positions

    def get_directional_diagonal_multiple_squares_adjacent_positions(self, forward: bool, capture: bool) -> List[int]:
        """Get the diagonal directional adjacent positions if the piece can move more than one square (kings)."""
        positions = []
        current_row = self.get_row()
        current_column = self.get_column()

        positions_diagonal_1 = []
        positions_diagonal_2 = []
        for i in range(1, self.board.height):
            next_row = current_row + ((i if self.player == BLACK else -i) * (1 if forward else -1))

            if next_row not in self.board.position_layout:
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

    def get_directional_orthogonal_multiple_squares_adjacent_positions(self, forward: bool, captures: bool) -> List[int]:
        """Get the orthogonal directional adjacent positions if the piece can move more than one square (kings)."""
        if not (self.orthogonal_moves or self.orthogonal_captures and captures):
            return []
        positions = []
        current_row = self.get_row()
        current_column = self.get_column()
        row_in_front = 2 if self.half_of_the_squares_are_playable else 1

        for multiplier in range(1, self.board.height):
            next_row = current_row + multiplier * (row_in_front if self.player == BLACK else -row_in_front) * (1 if forward else -1)
            if next_row in self.board.position_layout:
                positions.append(self.board.position_layout[next_row][current_column])

        for multiplier in range(1, self.board.width):
            next_column = current_column + multiplier * (1 if self.player == BLACK else -1) * (1 if forward else -1)
            if next_column in self.board.position_layout[current_row]:
                positions.append(self.board.position_layout[current_row][next_column])

        return positions

    def get_directional_adjacent_positions(self, forward: bool, capture: bool = False) -> List[int]:
        """Get the adjacent positions, either forwards or backwards."""
        positions = []
        if not self.king:
            if self.diagonal_moves:
                positions += self.get_directional_diagonal_one_square_adjacent_positions(forward)
            if self.orthogonal_captures:
                positions += self.get_directional_orthogonal_one_square_adjacent_positions(forward, capture)
        else:
            if self.kings_can_move_more_than_one_square:
                if self.diagonal_moves:
                    positions += self.get_directional_diagonal_multiple_squares_adjacent_positions(forward, capture)
                if self.orthogonal_captures:
                    positions += self.get_directional_orthogonal_multiple_squares_adjacent_positions(forward, capture)
            else:
                if self.diagonal_moves:
                    positions += self.get_directional_diagonal_one_square_adjacent_positions(forward)
                if self.orthogonal_captures:
                    positions += self.get_directional_orthogonal_one_square_adjacent_positions(forward, capture)
        return positions

    def get_next_column_indexes(self, current_row: int, current_column: int, i: int = 1, unfiltered: bool = False) -> List[int]:
        """
        Get the index of the next column.
        It isn't as simple as finding the next row (where we only add or subtract 1) but the column index only changes
        once every 2 rows.
        e.g. Square 32 and 27 are both in the second row, but 27 and 31 are not.
        :param i: current_row ± i is the row we should search (the columns for current_row + i are the same as current_row - i).
        e.g. if current row=3 and i=2, we will return the 2 possible columns for row 5 (which will be the same for row 1).
        """
        column_indexes = [0, 0]
        start_right = current_row % 2 == int(self.bottom_left_square_is_playable)
        for semi_i in range(1, i + 1):
            if start_right and semi_i % 2 == 1 or not start_right and semi_i % 2 == 0:
                column_indexes[1] += 1
            else:
                column_indexes[0] -= 1

        column_indexes = list(map(lambda value: value + current_column, column_indexes))

        if unfiltered:
            return column_indexes
        else:
            return list(filter((lambda column_index: 0 <= column_index < self.board.width), column_indexes))

    @property
    def other_player(self) -> int:
        return BLACK if self.player == WHITE else WHITE
