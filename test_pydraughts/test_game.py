from draughts import Game, WHITE


def test_game():
    assert Game('breakthrough', 'B:WK4,31,35,36,38,40,43,44,45,46,47,48,49,50:B1,2,3,6,7,8,9,11,13,16').is_over()
    assert Game('breakthrough', 'B:WK4,31,35,36,38,40,43,44,45,46,47,48,49,50:B1,2,3,6,7,8,9,11,13,16').get_winner() == WHITE

    game = Game(variant='from position', fen='B:W27,28,32,34,35,37,39,40,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,12,13,15,16,19,23,24')
    moves, captures = game.legal_moves()
    correct_moves = [[[15, 20]], [[10, 14]], [[9, 14]], [[24, 30]], [[24, 29]], [[23, 29]], [[13, 18]], [[12, 18]], [[12, 17]], [[7, 11]], [[6, 11]], [[16, 21]]]
    correct_moves.sort()
    correct_captures = [[None]] * 12
    assert moves == correct_moves and captures == correct_captures

    assert not game.board.is_valid_row_and_column(11, 0)
    assert not game.board.is_valid_row_and_column(5, 8)
    assert game.board.is_valid_row_and_column(5, 4)
    try:
        game.push([1, 46])
        assert False
    except ValueError:
        assert True

    game = Game(fen='W')
    assert game.legal_moves() == ([], [])
    game = Game()
    game.push_str_move('3530')
    game = Game(fen='W:W1-40:B41-50')
    assert game.get_fen() == f'W{"w" * 40}{"b" * 10}'
    assert game.board.pieces[0].get_diagonal_one_square_behind_enemy(game.board.pieces[10]) == []

    game = Game(fen='W:WK12-14:BK28-31')
    assert game.get_li_fen() == 'W:WK12,K13,K14:BK28,K29,K30,K31'

    # Test all legal move conditions for italian

    # All rules except for 2 are tested by both fens, so the specific rule each fen tests is mentioned in a comment.
    # This fen tests the rule "The capture sequence that captures the most kings has to be played."
    game = Game('italian', 'W:WK25,32,31:BK7,5,12,K14,K13,20,21,28')
    assert game.legal_moves() == ([[[25, 18], [18, 11], [11, 4]]], [[21, 14, 7]])
    # This fen tests the rule "The capture sequence where the king occurs first has to be played."
    game = Game('italian', 'W:WK25,32,31:B7,K5,12,K14,13,20,21,28')
    assert game.legal_moves() == ([[[25, 18], [18, 11], [11, 4]]], [[21, 14, 7]])

    game = Game(fen='W:W6:B1')
    assert game.legal_moves() == ([], [])

    # Test pop()
    game = Game()
    game.pop()
    game.push([35, 30])
    game.pop()
    game.push([35, 30])
    game.push([19, 24])
    game.pop()
    game.push([19, 24])
    game.push([30, 19])
    game.pop()
    game.pop()
    game.pop()
    game.push([35, 30])
    game.push([19, 24])
    game.push([30, 19])

    game = Game(fen='W:WK44:B9,18,33')
    game.push([44, 22])
    game.push([22, 13])
    game.pop()
    assert game._not_added_move == []
    assert game.get_fen() == 'WeeeeeeeebeeeeeeeebeeeeeeeeeeeeeebeeeeeeeeeeWeeeeee'
    
    game = Game(fen='W:WK43:BK9')
    game.push([43, 49])
    game.pop()
    assert game.reversible_moves == []

    game = Game(fen='W:WK39:B23,33')
    _, captures = game.push([[39, 28], [28, 19]], return_captured=True)
    assert captures == [33, 23]

    game = Game()
    game.null()
    assert game.get_fen() == 'Bbbbbbbbbbbbbbbbbbbbbeeeeeeeeeewwwwwwwwwwwwwwwwwwww'
    assert game.move_stack[0].pdn_move == '0-0'

    game = Game('frisian', 'W:WK4,36,41,42,43,44,46,47,48,49,50:B1,2,6,12,14,17,18,23')
    assert game.legal_moves() == ([[[4, 24], [24, 22], [22, 11], [11, 13], [13, 22]], [[4, 24], [24, 22], [22, 11], [11, 13], [13, 27]], [[4, 24], [24, 22], [22, 11], [11, 13], [13, 31]], [[4, 24], [24, 22], [22, 13], [13, 11], [11, 22]], [[4, 24], [24, 22], [22, 13], [13, 11], [11, 28]], [[4, 24], [24, 22], [22, 13], [13, 11], [11, 33]], [[4, 24], [24, 22], [22, 13], [13, 11], [11, 39]]], [[14, 23, 17, 12, 18], [14, 23, 17, 12, 18], [14, 23, 17, 12, 18], [14, 23, 18, 12, 17], [14, 23, 18, 12, 17], [14, 23, 18, 12, 17], [14, 23, 18, 12, 17]])

    assert Game(fen='W:WKa1,K8,9:BK7,Kb2,23').get_li_fen() == 'W:WK1,K8,9:BK6,K7,23'


def fifty_square_draw_board(game, repeat_time=12, half_time=True):
    for _ in range(repeat_time):
        game.push([28, 33])
        game.push([1, 7])
        game.push([33, 28])
        game.push([7, 1])
    if half_time:
        game.push([28, 33])
        game.push([1, 7])
    return game


def thirtytwo_square_draw_board(game, repeat_time=7, half_time=True):
    for _ in range(repeat_time):
        game.push([32, 27])
        game.push([1, 6])
        game.push([27, 32])
        game.push([6, 1])
    if half_time:
        game.push([32, 27])
        game.push([1, 6])
    return game


def test_drawing_conditions():
    # 25 consecutive non-capture king moves.
    game = Game(fen='W:WK28:BK1')
    game = fifty_square_draw_board(game)
    assert game.is_draw()
    game = Game(fen='B:WK1:BK28')
    game = fifty_square_draw_board(game)
    assert game.is_draw()

    # 1 king vs 3 pieces (with at least 1 king) and 16 moves made.
    game = Game(fen='W:WK28:BK1,2,3')
    game = fifty_square_draw_board(game, 8, False)
    assert game.is_draw()
    game = Game(fen='B:WK1,K2,K3:BK28')
    game = fifty_square_draw_board(game, 8, False)
    assert game.is_draw()

    # 1 king vs 2 or fewer pieces (with at least 1 king) and 5 moves made.
    game = Game(fen='W:WK28:BK1,2')
    game = fifty_square_draw_board(game, 2)
    assert game.is_draw()
    game = Game(fen='B:WK1,K2:BK28')
    game = fifty_square_draw_board(game, 2)
    assert game.is_draw()

    # 2 kings vs 1 king and 7 moves made.
    game = Game('frisian', 'W:WK28:BK1,K2')
    game = fifty_square_draw_board(game, 3)
    assert game.is_draw()
    game = Game('frisian', 'B:WK1,K2:BK28')
    game = fifty_square_draw_board(game, 3)
    assert game.is_draw()

    # 3 or more kings vs 1 king and 15 moves made.
    game = Game('russian', 'W:WK32:BK1,K2,K3')
    game = thirtytwo_square_draw_board(game)
    assert game.is_draw()
    game = Game('russian', 'B:WK1,K2,K3:BK32')
    game = thirtytwo_square_draw_board(game)
    assert game.is_draw()

    # 15 consecutive non-capture king moves.
    game = Game('russian', 'W:WK32:BK1')
    game = thirtytwo_square_draw_board(game)
    assert game.is_draw()

    # Same number of kings, same number of pieces, 4 or 5 pieces per side and 30 moves made.
    game = Game('russian', 'W:W29-31,K32:BK1,2-4')
    game.moves_since_last_capture = 60
    assert game.is_draw()

    # Same number of kings, same number of pieces, 6 or 7 pieces per side and 60 moves made.
    game = Game('russian', 'W:W25-26,29-31,K32:BK1,2-4,7-8')
    game.moves_since_last_capture = 120
    assert game.is_draw()

    # 3 pieces (with at least 1 king) vs 1 king on the long diagonal.
    game = Game('russian', 'W:WK5,17,19:BK29')
    for _ in range(2):
        game.push([5, 9])
        game.push([29, 4])
        game.push([9, 5])
        game.push([4, 29])
    game.push([5, 9])
    game.push([29, 4])
    assert game.is_draw()
    game = Game('russian', 'B:WK29:BK5,17,19')
    for _ in range(2):
        game.push([5, 9])
        game.push([29, 4])
        game.push([9, 5])
        game.push([4, 29])
    game.push([5, 9])
    game.push([29, 4])
    assert game.is_draw()

    # 2 pieces (with at least 1 king) vs 1 king and 5 moves made.
    game = Game('russian', 'W:WK32:BK1,4')
    game = thirtytwo_square_draw_board(game, 2)
    assert game.is_draw()
    game = Game('russian', 'B:WK1,29:BK32')
    game = thirtytwo_square_draw_board(game, 2)
    assert game.is_draw()

    game = Game('english', 'W:WK32:BK1')
    game = thirtytwo_square_draw_board(game, 20, False)
    assert game.is_draw()

    game = Game('turkish', 'W:WK32:B10')
    game.push([32, 31])
    game.push([10, 9])
    game.push([31, 32])
    game.push([9, 10])
    assert game.is_draw()
