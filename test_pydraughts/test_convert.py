from draughts.convert import fen_from_variant, fen_to_variant, move_from_variant, move_to_variant, _rotate_move, _algebraic_to_number, _number_to_algebraic, _numeric_to_algebraic_square


def test_convert():
    assert fen_from_variant('B:W19,21,22,23,25,26,27,29-31,32:B1,2,3-5,6,7,9,10,11,12',
                            variant='english') == 'W:W21,22,23,24,26,27,28,29,30,31,32:B1,10,11,12,14,2,3,4,6,7,8'
    assert fen_from_variant('W:Wa3,Kc3,Ke3,g3,b2,d2,f2,h2,a1,c1,e1,g1:Bb8,d8,f8,h8,a7,c7,e7,g7,b6,Kd6,Kf6,h6',
                            variant='russian') == 'W:W21,24,25,26,27,28,29,30,31,32,K22,K23:B1,12,2,3,4,5,6,7,8,9,K10,K11'
    assert fen_from_variant('W:WK12-14:BK28-31', variant='standard') == 'W:WK12,K13,K14:BK28,K29,K30,K31'
    assert fen_to_variant('W:W21,22,23,24,26,27-29,30,31,32:B1,10,11,12,14,2-4,6,7,8',
                          variant='english') == 'B:W19,21,22,23,25,26,27,29,30,31,32:B1,10,11,12,2,3,4,5,6,7,9'
    assert fen_to_variant('B:W17,22,23,24,25,26,27-29,30,31,32:B1,2,3-5,6,7,8,9,10,11,12',
                          variant='russian') == 'B:Wa1,c3,e3,g3,b4,c1,e1,g1,b2,d2,f2,h2:Bb6,d6,f6,h6,a7,c7,e7,g7,b8,d8,f8,h8'
    assert fen_to_variant('W:WK12-14:BK28-31', variant='russian') == 'W:WKa5,Kc5,Kh6:BKa1,Kc1,Ke1,Kh2'

    assert move_from_variant('g3-h4', variant='russian') == '24-20'
    assert move_to_variant('24-20', variant='russian') == 'g3-h4'
    assert _rotate_move('50-45', 3) == '46-41'
    assert _algebraic_to_number('a1a2', variant='turkish') == '1-9'
    assert _number_to_algebraic('1-9', variant='turkish') == 'a1-a2'
    assert _number_to_algebraic('a1-a2', variant='turkish') == 'a1-a2'
    assert _numeric_to_algebraic_square('32', width=4) == 'h8'
    assert _numeric_to_algebraic_square('h8', width=4) == 'h8'
