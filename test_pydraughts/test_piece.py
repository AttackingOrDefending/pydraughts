from draughts import Game


def test_piece():
    game = Game(fen='W:WK28:B19,37')
    assert game.legal_moves() == ([[[28, 14]], [[28, 10]], [[28, 5]], [[28, 41]], [[28, 46]]], [[19], [19], [19], [37], [37]])
