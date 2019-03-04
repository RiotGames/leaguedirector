import os
import json
from leaguedirector.widgets import userpath

class Settings(object):

    def __init__(self):
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
            json.dump(self.data, f, sort_keys=True, indent=4)

    def loadFile(self):
        if os.path.isfile(self.path):
            with open(self.path, 'r') as f:
                self.data = json.load(f)
