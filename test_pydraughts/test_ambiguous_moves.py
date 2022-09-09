from draughts import Board, Move


def test_ambiguous_move():
    game = Board(fen='W:WK47:B14,19,29,31,42')
    big_move = [[47, 33], [33, 24], [24, 13], [13, 36]]
    move_move = Move(game, big_move)
    assert move_move.pdn_move == "47x38x24x13x36"  # Not "47x33x24x13x36"
