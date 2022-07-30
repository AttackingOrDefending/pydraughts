from draughts import Game, Move


def test_move():
    game = Game(fen='W:W42:B28,38')
    assert Move(game, steps_move=[42, 33, 22]).board_move == [[42, 33], [33, 22]]
    assert Move(game, li_api_move=['4233', '3322']).board_move == [[42, 33], [33, 22]]
    assert Move(game, li_one_move='423322').board_move == [[42, 33], [33, 22]]

    assert Move(steps_move=[42, 33, 22]).board_move == [[42, 33], [33, 22]]
    assert Move(li_api_move=['4233', '3322']).board_move == [[42, 33], [33, 22]]
    assert Move(li_one_move='423322').board_move == [[42, 33], [33, 22]]

    assert Move(hub_position_move='3530').hub_move == '35-30'
    assert Move(hub_move='42x33x22').hub_position_move == '423322'
    assert Move(hub_move='35-30').hub_position_move == '3530'

    assert Move(pdn_position_move='3530').pdn_move == '35-30'

    # From https://github.com/AttackingOrDefending/pydraughts/issues/23
    game = Game(variant='brazilian', fen='Bbbbbebbbbbwbeeeewweeweeewwewwwww')
    move_ordered = Move(board=game, hub_move='8x13x11x17x18')
    move_unordered = Move(board=game, hub_move='8x13x11x18x17')
    assert move_ordered.board_move == move_unordered.board_move
