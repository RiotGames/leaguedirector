from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from leaguedirector.widgets import *

class Settings(QObject):

    def __init__(self):
        QObject.__init__(self)
        self.data = {}
        self.path = userpath('config.json')
        self.loadFile()

    def value(self, key, default=None):
        return self.data.get(key, default)

    def setValue(self, key, value):
        self.data[key] = value
        self.saveFile()

    def saveFile(self):
        with open(self.path, 'w') as f:
            document = QJsonDocument(self.data)
            json = document.toJson().data().decode('utf8')
            f.write(json)

    def loadFile(self):
        if os.path.isfile(self.path):
            with open(self.path, 'r') as f:
                json = QByteArray(f.read().encode('utf8'))
                document = QJsonDocument.fromJson(json)
