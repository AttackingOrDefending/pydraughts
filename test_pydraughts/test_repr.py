from draughts import Board


def test_repr():
    game = Board(fen="B:W27,34,35,36,37,39,40,41,42,43,44,45,46,47,48,49,50:B1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20")
    assert str(game) == """   | b |   | b |   | b |   | b |   | b 
---------------------------------------
 b |   | b |   | b |   | b |   | b |   
---------------------------------------
   | b |   | b |   | b |   | b |   | b 
---------------------------------------
 b |   |   |   | b |   | b |   | b |   
---------------------------------------
   |   |   |   |   |   |   |   |   |   
---------------------------------------
   |   | w |   |   |   |   |   |   |   
---------------------------------------
   |   |   |   |   |   |   | w |   | w 
---------------------------------------
 w |   | w |   |   |   | w |   | w |   
---------------------------------------
   | w |   | w |   | w |   | w |   | w 
---------------------------------------
 w |   | w |   | w |   | w |   | w |   """
    game = Board(variant="italian", fen="W:W29,32:BK15")
    assert str(game) == """   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   | B |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   | w |   |   |   |   |   | w """
    game = Board(variant="english", fen="W:W29,32:BK14")
    assert str(game) == """   | w |   |   |   |   |   | w 
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   | B |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   """
    game = Board(variant="russian", fen="W:Wb2,Kc3:Bd4,e5,b8,f8")
    assert str(game) == """   | b |   |   |   | b |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   | b |   |   |   
-------------------------------
   |   |   | b |   |   |   |   
-------------------------------
   |   | W |   |   |   |   |   
-------------------------------
   | w |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   """
    game = Board(variant="turkish", fen="W:Wa3,Kb3:Ba7,c7")
    assert str(game) == """   |   |   |   |   |   |   |   
-------------------------------
 b |   | b |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
 w | W |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   
-------------------------------
   |   |   |   |   |   |   |   """
