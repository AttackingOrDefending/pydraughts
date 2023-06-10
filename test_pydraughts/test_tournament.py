from draughts.tournament import RoundRobin
import pytest
import sys
import logging
platform = sys.platform
file_extension = '.exe' if platform == 'win32' else ''

logging.basicConfig()
logger = logging.getLogger("pydraughts")
logger.setLevel(logging.DEBUG)

@pytest.mark.timeout(300, method="thread")
def test_tournament():
    if platform != 'win32':
        assert True
        return
    players = [(["scan.exe", "dxp"], "dxp", {'engine-opened': False}), ("kr_hub.exe", "hub", {})]
    tournament = RoundRobin(players, 20, .2)
    scores = tournament.play()
    tournament.print_standings()
