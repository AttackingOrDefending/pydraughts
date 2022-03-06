import os
from typing import Optional, Union, Tuple, Dict, Any
import draughts

from msl.loadlib import Client64


class Engine32(Client64):
    def __init__(self, command: str) -> None:

        command = command.replace('\\', '\\\\')
        with open(os.path.join(os.path.dirname(__file__), 'engine_name.txt'), 'w') as file:
            file.write(command)

        super(Engine32, self).__init__(module32='engine_server', append_sys_path=os.path.dirname(__file__))

    def enginecommand(self, command: str) -> Tuple[bytes, int]:
        """Send an enginecommand to the engine."""
        return self.request32('enginecommand', command)

    def getmove(self, game: draughts.Game, maxtime: Union[int, float, None] = None, time: Union[int, float, None] = None, increment: Union[int, float, None] = None, movetime: Union[int, float, None] = None) -> Tuple[Optional[str], bytes, Dict[str, Any], int]:
        """Send a getmove to the engine."""
        assert maxtime is not None or time is not None or movetime is not None
        return self.request32('getmove', game, maxtime, time, increment, movetime)
