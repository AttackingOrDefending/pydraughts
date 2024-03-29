import os
from typing import Optional, Union, Tuple, Dict, Any
import draughts

from msl.loadlib import Client64


class Engine32(Client64):
    """64 bit client to communicate with the 32 bit server that is running the old Checkerboard engine."""
    def __init__(self, command: str) -> None:

        command = command.replace('\\', '\\\\')

        super(Engine32, self).__init__(module32='engine_server', append_sys_path=os.path.dirname(__file__), timeout=15.,
                                       dll_name=command)

    def enginecommand(self, command: str) -> Tuple[bytes, int]:
        """Send an enginecommand to the engine."""
        response: Tuple[bytes, int] = self.request32('enginecommand', command)
        return response

    def getmove(self, game: draughts.Board, maxtime: Union[int, float, None] = None, time: Union[int, float, None] = None,
                increment: Union[int, float, None] = None, movetime: Union[int, float, None] = None
                ) -> Tuple[Optional[str], bytes, Dict[str, Any], int]:
        """Send a getmove to the engine."""
        assert maxtime is not None or time is not None or movetime is not None
        response: Tuple[Optional[str], bytes, Dict[str, Any], int] = self.request32('getmove', game, maxtime, time,
                                                                                    increment, movetime)
        return response
