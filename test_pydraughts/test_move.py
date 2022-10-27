from draughts import Board, Game, Move, StandardMove


def test_move():
    game = Board(fen='W:W42:B28,38')
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

    # From https://github.com/AttackingOrDefending/pydraughts/issues/23 Converted to board
    game = Board(variant='brazilian', fen='B:Wf6,b4,d4,a3,b2,d2,h2,a1,c1,e1,g1:Bb8,d8,f8,h8,c7,e7,g7,b6,d6,h6')
    move_ordered = Move(board=game, hub_move='28x17x13x14x23')
    move_unordered = Move(board=game, hub_move='28x17x14x13x23')
    assert move_ordered.board_move == move_unordered.board_move


def test_standard_move():
    game = Game(fen='W:W42:B28,38')
    assert StandardMove(game, steps_move=[42, 33, 22]).board_move == [[42, 33], [33, 22]]
    assert StandardMove(game, li_api_move=['4233', '3322']).board_move == [[42, 33], [33, 22]]
    assert StandardMove(game, li_one_move='423322').board_move == [[42, 33], [33, 22]]

    assert StandardMove(steps_move=[42, 33, 22]).board_move == [[42, 33], [33, 22]]
    assert StandardMove(li_api_move=['4233', '3322']).board_move == [[42, 33], [33, 22]]
    assert StandardMove(li_one_move='423322').board_move == [[42, 33], [33, 22]]

    assert StandardMove(hub_position_move='3530').hub_move == '35-30'
    assert StandardMove(hub_move='42x33x22').hub_position_move == '423322'
    assert StandardMove(hub_move='35-30').hub_position_move == '3530'

    assert StandardMove(pdn_position_move='3530').pdn_move == '35-30'

    # From https://github.com/AttackingOrDefending/pydraughts/issues/23
    game = Game(variant='brazilian', fen='Bbbbbebbbbbwbeeeewweeweeewwewwwww')
    move_ordered = StandardMove(board=game, hub_move='8x13x11x17x18')
    move_unordered = StandardMove(board=game, hub_move='8x13x11x18x17')
    assert move_ordered.board_move == move_unordered.board_move
    assert Move(Game(), hub_move='31-27').hub_position_move == '3127'
    assert Move(Game(), pdn_move='31-27').pdn_position_move == '3127'
    assert Move(Game(fen='W:WK47:B14,19,29,31,42'), pdn_move='47x38x24x13x36').pdn_position_move == '4738241336'
    assert Move(Game(fen='W:WK47:B14,19,29,31,42'), pdn_position_move='4738200936').pdn_move == '47x38x20x9x36'
