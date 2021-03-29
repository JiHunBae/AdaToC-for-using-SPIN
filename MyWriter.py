__author__ = 'Jihun Bae'

from MyListener import MyListener

class MyWriter:
    _file_name = ''
    _my_listener = MyListener

    def __init__(self, listener, file_name=None):
        if file_name != None:
            self._file_name = file_name
        else:
            self._file_name = 'result.c'

        self._my_listener = listener

    def fileWrite(self):
        file = open(self._file_name, 'w')
        text = self._my_listener.getTextForWriting()
        file.write(text)
        file.close()