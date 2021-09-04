import os

from msl.loadlib import Client64


class Engine32(Client64):
    def __init__(self, command):

        command = command.replace('\\', '\\\\')
        filename = os.path.join(os.path.dirname(__file__), 'engine_server.py')
        with open(filename) as file:
            content = file.read().split('\n')
        for index, line in enumerate(content):
            if line.startswith("DLL_name"):
                content[index] = f'DLL_name = "{command}"'
                break
        content = '\n'.join(content)
        with open(filename, 'w') as file:
            file.write(content)

        super(Engine32, self).__init__(module32='engine_server', append_sys_path=os.path.dirname(__file__))

    def enginecommand(self, command):
        return self.request32('enginecommand', command)

    def getmove(self, game, maxtime=None, increment=None, movetime=None, depth=None):
        assert maxtime is not None or movetime is not None or depth is not None
        return self.request32('getmove', game, maxtime, increment, movetime, depth)
