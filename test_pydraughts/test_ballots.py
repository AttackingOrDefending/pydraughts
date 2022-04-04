from draughts.ballots import Ballots


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
