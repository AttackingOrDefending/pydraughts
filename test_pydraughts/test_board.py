from draughts import Game
from draughts.core.board import Board


def test_board():
    game = Game()
    game.board = Board()
    assert game.get_li_fen() == 'W:W31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20'
    assert game.board.count_movable_player_pieces() == 5
    game.board, _ = game.board.create_new_board_from_move([35, 30], 1, [])
    assert game.get_li_fen() == 'B:W30,31,32,33,34,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20'

    game = Game(fen='W:W29,31,32,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19,20,23')
    game.get_possible_moves()
    game.board, _ = game.board.create_new_board_from_move([29, 18], 1, [])
    assert game.get_li_fen() == 'B:W18,31,32,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19,20'
