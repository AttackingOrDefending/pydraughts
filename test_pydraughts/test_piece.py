from draughts import Board


def test_piece():
    game = Board(fen='W:WK28:B19,37')
    assert (list(map(lambda move: move.board_move, game.legal_moves())) ==
            [[[28, 14]], [[28, 10]], [[28, 5]], [[28, 41]], [[28, 46]]])
