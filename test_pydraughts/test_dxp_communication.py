from draughts.engines.dxp_communication.dxp_classes import DamExchange
from draughts import Board
import logging

logging.basicConfig()
logger = logging.getLogger("pydraughts")
logger.setLevel(logging.DEBUG)


def test_dam_exchange():
    dam_exchange = DamExchange()

    assert dam_exchange.parse('CMESSAGE') == {'type': 'C', 'text': 'MESSAGE'}  # CHAT
    assert dam_exchange.parse('B001W') == {'type': 'B', 'moveId': '001', 'mColor': 'W'}  # BACKREQ
    assert dam_exchange.parse('K1') == {'type': 'K', 'accCode': '1'}  # BACKACC
    assert dam_exchange.parse('P0') == {'type': '?'}  # Unknown
    assert dam_exchange.parse('E11') == {'type': 'E', 'reason': '1', 'stop': '1'}  # GAMEEND
    assert dam_exchange.parse('ANAME                            1') == {'type': 'A', 'engineName': 'NAME', 'accCode': '1'}  # GAMEACC
    assert dam_exchange.parse('M000135240130') == {'type': 'M', 'time': '0001', 'from': '35', 'to': '24', 'nCaptured': '01', 'captures': ['30']}  # MOVE
    assert dam_exchange.parse(f'R01NAME                            Z010100BW{Board()._game.get_dxp_fen()}') == {'type': 'R', 'name': 'NAME', 'fColor': 'Z', 'gameTime': '010', 'numMoves': '100', 'posInd': 'B', 'mColor': 'W', 'pos': 'zzzzzzzzzzzzzzzzzzzzeeeeeeeeeewwwwwwwwwwwwwwwwwwww'}  # GAMEREQ

    assert dam_exchange.parse(dam_exchange.msg_gamereq(0, 100, 100, Board(), 0)) == {'type': 'R', 'name': 'DXP Client', 'fColor': 'Z', 'gameTime': '100', 'numMoves': '100', 'posInd': 'B', 'mColor': 'W', 'pos': 'zzzzzzzzzzzzzzzzzzzzeeeeeeeeeewwwwwwwwwwwwwwwwwwww'}  # GAMEREQ
    assert dam_exchange.msg_gamereq(0, 100, 100) == 'R01DXP Client                      Z100100A'  # GAMEREQ
    assert dam_exchange.parse(dam_exchange.msg_backreq(1, 1)) == {'type': 'B', 'moveId': '001', 'mColor': 'Z'}  # BACKREQ
    assert dam_exchange.msg_backreq(1, 0) == 'B001W'  # BACKREQ
    assert dam_exchange.parse(dam_exchange.msg_backacc('1')) == {'type': 'K', 'accCode': '1'}  # BACKACC
    assert dam_exchange.msg_backacc('0') == 'K0'  # BACKACC
    assert dam_exchange.msg_chat("chat") == "Cchat"  # CHAT
