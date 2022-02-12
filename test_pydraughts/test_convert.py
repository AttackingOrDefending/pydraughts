from draughts.convert import fen_from_variant, fen_to_variant, move_from_variant, move_to_variant


def test_convert():
    assert fen_from_variant('B:W19,21,22,23,25,26,27,29,30,31,32:B1,2,3,4,5,6,7,9,10,11,12', variant='english') == 'W:W21,22,23,24,26,27,28,29,30,31,32:B1,2,3,4,6,7,8,10,11,12,14'
    assert fen_to_variant('W:W21,22,23,24,26,27,28,29,30,31,32:B1,10,11,12,14,2,3,4,6,7,8', variant='english') == 'B:W19,21,22,23,25,26,27,29,30,31,32:B1,2,3,4,5,6,7,9,10,11,12'
    assert fen_to_variant('B:W17,22,23,24,25,26,27,28,29,30,31,32:B1,2,3,4,5,6,7,8,9,10,11,12', variant='russian') == 'B:Wa1,c1,e1,g1,b2,d2,f2,h2,c3,e3,g3,b4:Bb6,d6,f6,h6,a7,c7,e7,g7,b8,d8,f8,h8'

    assert move_from_variant('g3-h4', variant='russian') == '24-20'
    assert move_to_variant('24-20', variant='russian') == 'g3-h4'