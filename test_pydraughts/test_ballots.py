from draughts.ballots import Ballots
from draughts import Board, Move


def test_ballots():
    ballots = Ballots('english', moves=2, include_lost_games=True)
    ballots_returned = set()
    for _ in range(60):
        ballots_returned.add(ballots.get_ballot())
    assert len(ballots_returned) == 49

    ballots = Ballots('english', moves=3)
    ballots = Ballots('english', moves=4)
    ballots = Ballots('english', moves=5)
    ballots = Ballots('english', eleven_pieces=True)
    ballots = Ballots('italian', eleven_pieces=True)
    ballots = Ballots('russian')
    ballots = Ballots('brazilian')
    ballots = Ballots('russian', basic_positions=True)

    ballots = Ballots('english', moves=2, include_lost_games=True)
    for key, fen in ballots.positions.items():
        moves = key.split()[1:]
        board1 = Board('english', fen)
        board2 = Board('english')
        for move in moves:
            board2.push(Move(board2, pdn_move=move))
        assert board1._game.get_fen() == board2._game.get_fen()
