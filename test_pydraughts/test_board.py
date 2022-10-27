from draughts import Board
from draughts.core.board import Board as InternalBoard


def test_board():
    game = Board()
    game._game.board = InternalBoard()
    assert game.fen == 'W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,10,11,12,13,14,15,16,17,18,19,2,20,3,4,5,6,7,8,9'
    assert game._game.board.count_movable_player_pieces() == 5
    game._game.board, _ = game._game.board.create_new_board_from_move([35, 30], 1, [])
    assert game._game.get_li_fen() == 'B:W30,31,32,33,34,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20'

    game = Board(fen='W:W29,31,32,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19,20,23')
    game._game.get_possible_moves()
    game._game.board, _ = game._game.board.create_new_board_from_move([29, 18], 1, [])
    assert game._game.get_li_fen() == 'B:W18,31,32,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19,20'
