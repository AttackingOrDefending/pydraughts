from draughts import Board, Move


def test_ambiguous_move():
    game = Board(fen='W:WK47:B14,19,29,31,42')
    big_move = [[47, 33], [33, 24], [24, 13], [13, 36]]
    move_move = Move(game, big_move)
    assert move_move.pdn_move == "47x38x24x13x36"  # Not "47x33x24x13x36"

    board = Board("russian", fen="W:WKd2:Bf6,c5,e5,e3:H0:F1")
    legal_moves = list(map(lambda m: m.pdn_move, board.legal_moves()))
    assert legal_moves == ['6x15x22x13', '6x15x22x9', '6x20x27x13', '6x20x27x9']

    board = Board("russian", fen="W:We3,g3,h4,a5,b2,h2,a3,Kf8:Bc5,e5,g5,g7,h8")
    legal_moves = list(map(lambda m: m.pdn_move, board.legal_moves()))
    assert legal_moves == ['31x13', '31x24x15x22x13', '16x21']

    board = Board("russian", fen="W:WKd2:Bc5,e5,c3,e3:H0:F1")
    legal_moves = list(map(lambda m: m.pdn_move, board.legal_moves()))
    assert legal_moves == ['6x13x22x15x6', '6x2', '6x15x22x13x6', '6x3']

    board = Board(fen="W:WK38:B18,19,32,33:H0:F1")
    legal_moves = list(map(lambda m: m.pdn_move, board.legal_moves()))
    assert legal_moves == ['38x27x13x24x38', '38x42', '38x47', '38x24x13x27x38', '38x43', '38x49']
