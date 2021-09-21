import os

from msl.loadlib import Client64


class Engine32(Client64):
    def __init__(self, command):

        command = command.replace('\\', '\\\\')
        with open(os.path.join(os.path.dirname(__file__), 'engine_name.txt'), 'w') as file:
            file.write(command)

        super(Engine32, self).__init__(module32='engine_server', append_sys_path=os.path.dirname(__file__))

    def enginecommand(self, command):
        return self.request32('enginecommand', command)

    def getmove(self, game, maxtime=None, time=None, increment=None, movetime=None):
        assert maxtime is not None or time is not None or movetime is not None
        return self.request32('getmove', game, maxtime, time, increment, movetime)
