from draughts.ballots import Ballots


def test_ballots():
    ballots = Ballots('english', moves=2, include_lost_games=True)
    ballots_returned = set()
    for _ in range(49):
        ballots_returned.add(ballots.get_ballot())
    assert len(ballots_returned) == 49
