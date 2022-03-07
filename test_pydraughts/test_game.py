from draughts import Game, WHITE


def test_game():
    assert Game('breakthrough', 'B:WK4,31,35,36,38,40,43,44,45,46,47,48,49,50:B1,2,3,6,7,8,9,11,13,16').is_over()
    assert Game('breakthrough', 'B:WK4,31,35,36,38,40,43,44,45,46,47,48,49,50:B1,2,3,6,7,8,9,11,13,16').get_winner() == WHITE

    game = Game(fen='B:W27,28,32,34,35,37,39,40,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,12,13,15,16,19,23,24')
    moves, captures = game.legal_moves()
    correct_moves = [[[15, 20]], [[10, 14]], [[9, 14]], [[24, 30]], [[24, 29]], [[23, 29]], [[13, 18]], [[12, 18]], [[12, 17]], [[7, 11]], [[6, 11]], [[16, 21]]]
    correct_moves.sort()
    correct_captures = [[None]] * 12
    assert moves == correct_moves and captures == correct_captures


test_game()
