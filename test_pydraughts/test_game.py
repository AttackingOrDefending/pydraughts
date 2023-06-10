from draughts import Board, Move, WHITE


def test_game():
    assert Board('breakthrough', 'B:WK4,31,35,36,38,40,43,44,45,46,47,48,49,50:B1,2,3,6,7,8,9,11,13,16').is_over()
    assert Board('breakthrough', 'B:WK4,31,35,36,38,40,43,44,45,46,47,48,49,50:B1,2,3,6,7,8,9,11,13,16').winner() == WHITE

    game = Board(variant='from position', fen='B:W27,28,32,34,35,37,39,40,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,12,13,15,16,19,23,24')
    moves = game.legal_moves()
    captures = list(map(lambda move: move.captures, moves))
    moves = list(map(lambda move: move.board_move, moves))
    correct_moves = [[[15, 20]], [[10, 14]], [[9, 14]], [[24, 30]], [[24, 29]], [[23, 29]], [[13, 18]], [[12, 18]], [[12, 17]], [[7, 11]], [[6, 11]], [[16, 21]]]
    correct_moves.sort()
    correct_captures = [[]] * 12
    assert moves == correct_moves and captures == correct_captures

    assert not game._game.board.is_valid_row_and_column(11, 0)
    assert not game._game.board.is_valid_row_and_column(5, 8)
    assert game._game.board.is_valid_row_and_column(5, 4)
    try:
        game._game.push([1, 46])
        assert False
    except ValueError:
        assert True

    game = Board(fen='W')
    assert game.legal_moves() == []
    game = Board()
    game._game.push_str_move('3530')
    game = Board(fen='W:W1-40:B41-50')
    game._game = game._game.copy()
    assert game.fen == 'W:W1,10,11,12,13,14,15,16,17,18,19,2,20,21,22,23,24,25,26,27,28,29,3,30,31,32,33,34,35,36,37,38,39,4,40,5,6,7,8,9:B41,42,43,44,45,46,47,48,49,50'
    assert game._game.board.pieces[0].get_diagonal_one_square_behind_enemy(game._game.board.pieces[10]) == []

    game = Board(fen='W:WK12-14:BK28-31')
    assert game.fen == 'W:WK12,K13,K14:BK28,K29,K30,K31'

    # Test all legal move conditions for italian

    # All rules except for 2 are tested by both fens, so the specific rule each fen tests is mentioned in a comment.
    # This fen tests the rule "The capture sequence that captures the most kings has to be played."
    game = Board('italian', 'W:W31,32,K25:B12,20,21,28,5,K13,K14,K7')
    assert list(map(lambda move: move.board_move, game.legal_moves())) == [[[25, 18], [18, 11], [11, 4]]]
    # This fen tests the rule "The capture sequence where the king occurs first has to be played."
    game = Board('italian', 'W:W31,32,K25:B12,13,20,21,28,7,K14,K5')
    assert list(map(lambda move: move.board_move, game.legal_moves())) == [[[25, 18], [18, 11], [11, 4]]]

    game = Board(fen='W:W6:B1')
    assert game._game.legal_moves() == ([], [])

    # Test pop()
    game = Board()
    game.push(Move(steps_move=[35, 30]))
    game.pop()
    game.push(Move(steps_move=[35, 30]))
    game.push(Move(steps_move=[19, 24]))
    game.pop()
    game.push(Move(steps_move=[19, 24]))
    game.push(Move(steps_move=[30, 19]))
    game.pop()
    game.pop()
    game.pop()
    game.push(Move(steps_move=[35, 30]))
    game.push(Move(steps_move=[19, 24]))
    game.push(Move(steps_move=[30, 19]))

    game = Board(fen='W:WK44:B9,18,33')
    game.push(Move(steps_move=[44, 22]))
    game.push(Move(steps_move=[22, 13]))
    game.pop()
    assert game._game._not_added_move == []
    assert game._game.get_fen() == 'WeeeeeeeebeeeeeeeebeeeeeeeeeeeeeebeeeeeeeeeeWeeeeee'

    game = Board(fen='W:WK43:BK9')
    game.push(Move(steps_move=[43, 49]))
    game.pop()
    assert game._game.reversible_moves == []

    game = Board(fen='W:WK39:B23,33')
    _, captures = game._game.push([[39, 28], [28, 19]])
    assert captures == [33, 23]

    game = Board()
    game.null()
    assert game._game.get_fen() == 'Bbbbbbbbbbbbbbbbbbbbbeeeeeeeeeewwwwwwwwwwwwwwwwwwww'
    assert game.move_stack[0].pdn_move == '0-0'

    game = Board('frisian', 'W:WK4,36,41,42,43,44,46,47,48,49,50:B1,2,6,12,14,17,18,23')
    assert (list(map(lambda move: move.board_move, game.legal_moves())) ==
            [[[4, 24], [24, 22], [22, 11], [11, 13], [13, 22]], [[4, 24], [24, 22], [22, 11], [11, 13], [13, 27]],
             [[4, 24], [24, 22], [22, 11], [11, 13], [13, 31]], [[4, 24], [24, 22], [22, 13], [13, 11], [11, 22]],
             [[4, 24], [24, 22], [22, 13], [13, 11], [11, 28]], [[4, 24], [24, 22], [22, 13], [13, 11], [11, 33]],
             [[4, 24], [24, 22], [22, 13], [13, 11], [11, 39]]])

    assert Board(fen='W:WKa1,K8,9:BK7,Kb2,23').fen == 'W:W9,K1,K8:B23,K6,K7'

    game = Board()
    game._game.move([31, 27], include_pdn=True)
    game._game.null()
    assert game._game.is_over() is False
    assert game._game.li_fen_to_hub_fen('W:WK1-3:BK4-6') == 'WWWWBBBeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'

    # From https://github.com/AttackingOrDefending/pydraughts/issues/28
    game = Board('russian', 'W:Wh6:Bg7,c5,d2')
    assert len(game.legal_moves()) == 1
    assert game.legal_moves()[0].board_move == [[24, 31], [31, 13], [13, 3]]


def fifty_square_draw_board(game, repeat_time=12, half_time=True):
    for _ in range(repeat_time):
        game.push(Move(steps_move=[28, 33]))
        game.push(Move(steps_move=[1, 7]))
        game.push(Move(steps_move=[33, 28]))
        game.push(Move(steps_move=[7, 1]))
    if half_time:
        game.push(Move(steps_move=[28, 33]))
        game.push(Move(steps_move=[1, 7]))
    return game


def thirtytwo_square_draw_board(game, repeat_time=7, half_time=True):
    for _ in range(repeat_time):
        game._game.push([[32, 27]])
        game._game.push([[1, 6]])
        game._game.push([[27, 32]])
        game._game.push([[6, 1]])
    if half_time:
        game._game.push([[32, 27]])
        game._game.push([[1, 6]])
    return game


def test_drawing_conditions():
    # 25 consecutive non-capture king moves.
    game = Board(fen='W:WK28:BK1')
    game = fifty_square_draw_board(game)
    assert game.winner() == 0
    game = Board(fen='B:WK1:BK28')
    game = fifty_square_draw_board(game)
    assert game.winner() == 0

    # 1 king vs 3 pieces (with at least 1 king) and 16 moves made.
    game = Board(fen='W:WK28:BK1,2,3')
    game = fifty_square_draw_board(game, 8, False)
    assert game.winner() == 0
    game = Board(fen='B:WK1,K2,K3:BK28')
    game = fifty_square_draw_board(game, 8, False)
    assert game.winner() == 0

    # 1 king vs 2 or fewer pieces (with at least 1 king) and 5 moves made.
    game = Board(fen='W:WK28:BK1,2')
    game = fifty_square_draw_board(game, 2)
    assert game.winner() == 0
    game = Board(fen='B:WK1,K2:BK28')
    game = fifty_square_draw_board(game, 2)
    assert game.winner() == 0

    # 2 kings vs 1 king and 7 moves made.
    game = Board('frisian', 'W:WK28:BK1,K2')
    game = fifty_square_draw_board(game, 3)
    assert game.winner() == 0
    game = Board('frisian', 'B:WK1,K2:BK28')
    game = fifty_square_draw_board(game, 3)
    assert game.winner() == 0

    # 3 or more kings vs 1 king and 15 moves made.
    game = Board('russian', 'W:WKg1:BKb8,Kd8,Kf8')
    game = thirtytwo_square_draw_board(game)
    assert game.winner() == 0
    game = Board('russian', 'B:WKb8,Kd8,Kf8:BKg1')
    game = thirtytwo_square_draw_board(game)
    assert game.winner() == 0

    # 15 consecutive non-capture king moves.
    game = Board('russian', 'W:WKg1:BKb8')
    game = thirtytwo_square_draw_board(game)
    assert game.winner() == 0

    # Same number of kings, same number of pieces, 4 or 5 pieces per side and 30 moves made.
    game = Board('russian', 'W:Wa1,c1,e1,Kg1:BKb8,d8,f8,h8')
    game._game.moves_since_last_capture = 60
    assert game.winner() == 0

    # Same number of kings, same number of pieces, 6 or 7 pieces per side and 60 moves made.
    game = Board('russian', 'W:Wb2,d2,a1,c1,e1,Kg1:BKb8,d8,f8,h8,e7,g7')
    game._game.moves_since_last_capture = 120
    assert game.winner() == 0

    # 3 pieces (with at least 1 king) vs 1 king on the long diagonal.
    game = Board('russian', 'W:WKa7,b4,f4:BKa1')
    for _ in range(2):
        game._game.push([[5, 9]])
        game._game.push([[29, 4]])
        game._game.push([[9, 5]])
        game._game.push([[4, 29]])
    game._game.push([[5, 9]])
    game._game.push([[29, 4]])
    assert game.winner() == 0
    game = Board('russian', 'B:WKa1:BKa7,b4,f4')
    for _ in range(2):
        game._game.push([[5, 9]])
        game._game.push([[29, 4]])
        game._game.push([[9, 5]])
        game._game.push([[4, 29]])
    game._game.push([[5, 9]])
    game._game.push([[29, 4]])
    assert game.winner() == 0

    # 2 pieces (with at least 1 king) vs 1 king and 5 moves made.
    game = Board('russian', 'W:WKg1:BKb8,h8')
    game = thirtytwo_square_draw_board(game, 2)
    assert game.winner() == 0
    game = Board('russian', 'B:WKb8,a1:BKg1')
    game = thirtytwo_square_draw_board(game, 2)
    assert game.winner() == 0

    game = Board('english', 'B:WK32:BK1')
    game = thirtytwo_square_draw_board(game, 20, False)
    assert game.winner() == 0

    game = Board('turkish', 'W:WKh5:Bb7')
    game._game.push([[32, 31]])
    game._game.push([[10, 9]])
    game._game.push([[31, 32]])
    game._game.push([[9, 10]])
    assert game.winner() == 0
