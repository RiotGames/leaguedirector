import os
import time
import json
import copy
import logging
import functools
from leaguedirector.widgets import userpath
from PySide2.QtCore import *
from PySide2.QtNetwork import *


class Resource(QObject):
    """
    Base class for a remote api resources.
    """
    updated     = Signal()
    host        = 'https://127.0.0.1:2999'
    url         = ''
    fields      = {}
    connected   = False
    readonly    = False
    writeonly   = False
    network     = None

    def __init__(self):
        object.__setattr__(self, 'timestamp', time.time())
        for name, default in self.fields.items():
            object.__setattr__(self, name, default)
        QObject.__init__(self)

    def __setattr__(self, name, value):
        if name in self.fields:
            if self.readonly:
                raise AttributeError("Resource is readonly")
            if getattr(self, name) != value:
                object.__setattr__(self, name, value)
                self.update({name: value})
        else:
            object.__setattr__(self, name, value)

    def sslErrors(self, response, errors):
        allowed = [QSslError.CertificateUntrusted, QSslError.HostNameMismatch]
        response.ignoreSslErrors([e for e in errors if e.error() in allowed])

    def manager(self):
        if Resource.network is None:
            # QT does not ship SSL binaries so we have to bundle them in our res directory
            os.environ['PATH'] = os.path.abspath('resources') + os.pathsep + os.environ['PATH']

            # Then setup our certificate for the lol game client
            QSslSocket.addDefaultCaCertificates(os.path.abspath('resources/riotgames.pem'))
            Resource.network = QNetworkAccessManager(QCoreApplication.instance())
            Resource.network.sslErrors.connect(self.sslErrors)
        return Resource.network

    def set(self, name, value):
        self.__setattr__(name, value)

    def get(self, name):
        return getattr(self, name)

    def shutdown(self):
        pass

    def data(self):
        return {name: getattr(self, name) for name in self.fields}

    def keys(self):
        return self.fields.keys()

    def update(self, data=None):
        request = QNetworkRequest(QUrl(self.host + self.url))
        if data is not None:
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            response = self.manager().post(request, QByteArray(json.dumps(data).encode()))
        else:
            response = self.manager().get(request)
        response.finished.connect(functools.partial(self.finished, response))

    def finished(self, response):
        error = response.error()
        if error == QNetworkReply.NoError:
            Resource.connected = True
            self.apply(json.loads(response.readAll().data().decode()))
            self.timestamp = time.time()
        elif error in (QNetworkReply.ConnectionRefusedError, QNetworkReply.TimeoutError):
            Resource.connected = False
        else:
            logging.error("Request Failed: {} {}".format(self.url, response.errorString()))
        self.updated.emit()

    def apply(self, data):
        if not self.writeonly:
            for key, value in data.items():
                if key in self.fields:
                    object.__setattr__(self, key, value)


class Game(Resource):
    url = '/replay/game'
    fields = {'processID': 0}
    readonly = True


class Recording(Resource):
    url = '/replay/recording'
    fields = {
        'recording': False,
        'path': '',
        'codec': '',
        'startTime': 0,
        'endTime': 0,
        'currentTime': 0,
        'width': 0,
        'height': 0,
        'framesPerSecond': 0,
        'enforceFrameRate': False,
        'replaySpeed': 0,
    }


class Render(Resource):
    url = '/replay/render'
    fields = {
        'cameraMode' : '',
        'cameraPosition' : {'x': 0, 'y': 0, 'z': 0},
        'cameraRotation' : {'x': 0, 'y': 0, 'z': 0},
        'cameraAttached' : False,
        'cameraMoveSpeed' : 0,
        'cameraLookSpeed' : 0,
        'fieldOfView' : 0,
        'nearClip' : 0,
        'farClip' : 0,
        'fogOfWar' : True,
        'outlineSelect' : True,
        'outlineHover' : True,
        'floatingText' : True,
        'navGridOffset' : 0,
        'interfaceAll' : True,
        'interfaceReplay' : True,
        'interfaceScore' : True,
        'interfaceScoreboard' : True,
        'interfaceFrames' : True,
        'interfaceMinimap' : True,
        'interfaceTimeline' : True,
        'interfaceChat' : True,
        'interfaceTarget' : True,
        'interfaceQuests' : True,
        'interfaceAnnounce' : True,
        'healthBarChampions' : True,
        'healthBarStructures' : True,
        'healthBarWards' : True,
        'healthBarPets' : True,
        'healthBarMinions' : True,
        'environment' : True,
        'characters' : True,
        'particles' : True,
        'skyboxPath' : '',
        'skyboxRotation' : 0,
        'skyboxRadius' : 0,
        'skyboxOffset' : 0,
        'sunDirection' : {'x': 0, 'y': 0, 'z': 0},
        'depthFogEnabled' : False,
        'depthFogStart' : 0,
        'depthFogEnd' : 0,
        'depthFogIntensity' : 1,
        'depthFogColor' : {'r': 0, 'g': 0, 'b': 0, 'a': 0},
        'heightFogEnabled' : False,
        'heightFogStart' : 0,
        'heightFogEnd' : 0,
        'heightFogIntensity' : 1,
        'heightFogColor' : {'r': 0, 'g': 0, 'b': 0, 'a': 0},
        'depthOfFieldEnabled' : False,
        'depthOfFieldDebug' : False,
        'depthOfFieldCircle' : 0,
        'depthOfFieldWidth' : 0,
        'depthOfFieldNear' : 0,
        'depthOfFieldMid' : 0,
        'depthOfFieldFar' : 0,
    }

    def __init__(self):
        Resource.__init__(self)
        self.cameraLockX = None
        self.cameraLockY = None
        self.cameraLockZ = None
        self.cameraLockLast = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateCameraLock)
        self.timer.start(600)

    def updateCameraLock(self, *args):
        # Wait until the camera stops moving before snapping it
        if self.cameraLockLast != self.cameraPosition:
            self.cameraLockLast = self.cameraPosition
        else:
            copy = dict(self.cameraPosition)
            if self.cameraLockX is not None:
                copy['x'] = self.cameraLockX
            if self.cameraLockY is not None:
                copy['y'] = self.cameraLockY
            if self.cameraLockZ is not None:
                copy['z'] = self.cameraLockZ
            self.cameraPosition = copy

    def toggleCameraLockX(self):
        self.cameraLockX = self.cameraPosition['x'] if self.cameraLockX is None else None

    def toggleCameraLockY(self):
        self.cameraLockY = self.cameraPosition['y'] if self.cameraLockY is None else None

    def toggleCameraLockZ(self):
        self.cameraLockZ = self.cameraPosition['z'] if self.cameraLockZ is None else None

    def moveCamera(self, x=0, y=0, z=0):
        copy = dict(self.cameraPosition)
        copy['x'] += x
        copy['y'] += y
        copy['z'] += z
        self.cameraPosition = copy

    def rotateCamera(self, x=0, y=0, z=0):
        copy = dict(self.cameraRotation)
        copy['x'] += x
        copy['y'] += y
        copy['z'] += z
        self.cameraRotation = copy


class Particles(Resource):
    url = '/replay/particles'
    fields = {}
    particles = {}

    def apply(self, data):
        self.particles = data

    def items(self):
        return self.particles.items()

    def hasParticle(self, particle):
        return particle in self.particles

    def setParticle(self, particle, enabled):
        if particle in self.particles:
            self.update({particle:enabled})

    def getParticle(self, particle):
        return self.particles.get(particle, True)


class Playback(Resource):
    url = '/replay/playback'
    fields = {
        'paused':   False,
        'seeking':  False,
        'time':     0.0,
        'speed':    0.0,
        'length':   1.0,
    }

    @property
    def currentTime(self):
        if self.paused:
            return self.time
        else:
            return min(self.time + (time.time() - self.timestamp) * self.speed, self.length)

    @property
    def currentTimeFormatted(self):
        minutes, seconds = divmod(self.currentTime, 60)
        return '{0:02}:{1:05.2f}'.format(int(minutes), seconds)

    def togglePlay(self):
        self.paused = not self.paused

    def setSpeed(self, speed):
        self.speed = speed

    def adjustTime(self, delta):
        self.time = self.currentTime + delta

    def play(self, time=None):
        if not self.seeking:
            data = {'paused': False}
            if time is not None:
                data['time'] = time
            self.update(data)

    def pause(self, time=None):
        if not self.seeking:
            data = {'paused': True}
            if time is not None:
                data['time'] = time
            self.update(data)


class Sequence(Resource):
    dataLoaded = Signal()
    namesLoaded = Signal()
    url = '/replay/sequence'
    writeonly = True
    history = []
    history_index = 0
    fields = {
        'playbackSpeed': [],
        'cameraPosition': [],
        'cameraRotation': [],
        'fieldOfView': [],
        'nearClip': [],
        'farClip': [],
        'navGridOffset': [],
        'skyboxRotation': [],
        'skyboxRadius': [],
        'skyboxOffset': [],
        'sunDirection': [],
        'depthFogEnabled': [],
        'depthFogStart': [],
        'depthFogEnd': [],
        'depthFogIntensity': [],
        'depthFogColor': [],
        'heightFogEnabled': [],
        'heightFogStart': [],
        'heightFogEnd': [],
        'heightFogIntensity': [],
        'heightFogColor': [],
        'depthOfFieldEnabled': [],
        'depthOfFieldCircle': [],
        'depthOfFieldWidth': [],
        'depthOfFieldNear': [],
        'depthOfFieldMid': [],
        'depthOfFieldFar': [],
    }
    blendOptions = [
        'linear',
        'snap',
        'smoothStep',
        'smootherStep',
        'quadraticEaseIn',
        'quadraticEaseOut',
        'quadraticEaseInOut',
        'cubicEaseIn',
        'cubicEaseOut',
        'cubicEaseInOut',
        'quarticEaseIn',
        'quarticEaseOut',
        'quarticEaseInOut',
        'quinticEaseIn',
        'quinticEaseOut',
        'quinticEaseInOut',
        'sineEaseIn',
        'sineEaseOut',
        'sineEaseInOut',
        'circularEaseIn',
        'circularEaseOut',
        'circularEaseInOut',
        'exponentialEaseIn',
        'exponentialEaseOut',
        'exponentialEaseInOut',
        'elasticEaseIn',
        'elasticEaseOut',
        'elasticEaseInOut',
        'backEaseIn',
        'backEaseOut',
        'backEaseInOut',
        'bounceEaseIn',
        'bounceEaseOut',
        'bounceEaseInOut',
    ]

    def __init__(self, render, playback):
        Resource.__init__(self)
        self.render = render
        self.playback = playback
        self.name = ''
        self.names = []
        self.directory = None
        self.sequencing = False
        self.saveRemoteTimer = QTimer()
        self.saveRemoteTimer.timeout.connect(self.saveRemoteNow)
        self.saveRemoteTimer.setSingleShot(True)
        self.saveHistoryTimer = QTimer()
        self.saveHistoryTimer.timeout.connect(self.saveHistoryNow)
        self.saveHistoryTimer.setSingleShot(True)
        self.saveFileTimer = QTimer()
        self.saveFileTimer.timeout.connect(self.saveFileNow)
        self.saveFileTimer.setSingleShot(True)

    def update(self, *args):
        self.saveRemote()
        self.saveFile()
        self.saveHistory()

    def data(self):
        return {key:getattr(self, key) for key in self.fields}

    @property
    def startTime(self):
        keyframes = self.cameraPosition + self.cameraRotation
        if len(keyframes):
            return min(keyframe['time'] for keyframe in keyframes)            

    @property
    def endTime(self):
        keyframes = self.cameraPosition + self.cameraRotation
        if len(keyframes):
            return max(keyframe['time'] for keyframe in keyframes)            

    def path(self):
        return os.path.join(self.directory, self.name + '.json')

    def load(self, name):
        self.saveFileNow()
        self.loadFile(name)

    def create(self, name):
        self.saveFileNow()
        self.clearData()
        self.resetHistory()
        self.saveFileNow(name)
        self.reloadNames()

    def save(self, name=None):
        self.saveFile(name)

    def copy(self, name):
        oldName = self.name
        self.saveFileNow(name)
        self.saveFileNow(oldName)
        self.reloadNames()

    def undo(self):
        self.loadHistory(self.history_index - 1)

    def redo(self):
        self.loadHistory(self.history_index + 1)

    def setDirectory(self, path):
        if os.path.exists(path) and os.path.isdir(path):
            self.directory = path
            self.clearData()
            self.loadFile('default')
            self.saveFileNow()
            self.reloadNames()

    def saveRemoteNow(self):
        self.sortData()
        if self.sequencing:
            Resource.update(self, self.data())
        else:
            Resource.update(self, {})

    def saveRemote(self):
        self.saveRemoteTimer.start(0)

    def saveHistoryNow(self):
        self.history = self.history[0:self.history_index + 1]
        self.history_index = len(self.history)
        self.history.append(copy.deepcopy(self.data()))

    def saveHistory(self):
        self.saveHistoryTimer.start(500)

    def loadHistory(self, index):
        if len(self.history):
            self.history_index = max(min(index, len(self.history) - 1), 0)
            self.loadData(copy.deepcopy(self.history[self.history_index]))
            self.saveRemote()
            self.saveFileNow()

    def resetHistory(self):
        self.history = []
        self.history_index = 0

    def loadFile(self, name):
        self.name = name
        if os.path.exists(self.path()):
            with open(self.path(), 'r') as f:
                self.resetHistory()
                self.loadData(json.load(f))
                self.saveRemote()
                self.saveHistory()

    def saveFileNow(self, name=None):
        self.name = name or self.name
        if self.name:
            path = self.path()
            exists = os.path.exists(path)
            with open(path, 'w') as f:
                json.dump(self.data(), f, sort_keys=True, indent=4)
                if not exists:
                    self.reloadNames()

    def saveFile(self, name=None):
        self.name = name or self.name
        self.saveFileTimer.start(1000)

    def clearData(self):
        for track in self.fields:
            getattr(self, track, []).clear()
        self.dataLoaded.emit()

    def loadData(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if value is not None:
                    object.__setattr__(self, key, value)
            self.dataLoaded.emit()

    def sortData(self):
        for track in self.fields:
            if getattr(self, track):
                getattr(self, track).sort(key = lambda item: item['time'])

    def reloadNames(self):
        self.names = sorted([f.replace('.json', '') for f in os.listdir(self.directory) if f.endswith('.json')], key=str.lower)
        self.namesLoaded.emit()

    @property
    def index(self):
        try:
            return self.names.index(self.name)
        except ValueError:
            return 0

    def setSequencing(self, value):
        self.sequencing = value
        self.update()

    def getKeyframes(self, name):
        return getattr(self, name)

    def createKeyframe(self, name):
        keyframe = {
            'time': self.playback.time,
            'value': self.getValue(name),
            'blend': 'linear',
        }
        self.appendKeyframe(name, keyframe)
        return keyframe

    def appendKeyframe(self, name, keyframe):
        getattr(self, name).append(keyframe)
        self.update()

    def removeKeyframe(self, name, item):
        getattr(self, name).remove(item)
        self.update()

    def getLabel(self, name):
        if name == 'cameraPosition':
            return 'Camera Position'
        if name == 'cameraRotation':
            return 'Camera Rotation'
        if name == 'playbackSpeed':
            return 'Playback Speed'
        if name == 'fieldOfView':
            return 'Field Of View'
        if name == 'nearClip':
            return 'Near Clip'
        if name == 'farClip':
            return 'Far Clip'
        if name == 'navGridOffset':
            return 'Nav Grid Offset'
        if name == 'skyboxRotation':
            return 'Skybox Rotation'
        if name == 'skyboxRadius':
            return 'Skybox Radius'
        if name == 'skyboxOffset':
            return 'Skybox Offset'
        if name == 'sunDirection':
            return 'Sun Direction'
        if name == 'depthFogEnabled':
            return 'Depth Fog Enable'
        if name == 'depthFogStart':
            return 'Depth Fog Start'
        if name == 'depthFogEnd':
            return 'Depth Fog End'
        if name == 'depthFogIntensity':
            return 'Depth Fog Intensity'
        if name == 'depthFogColor':
            return 'Depth Fog Color'
        if name == 'heightFogEnabled':
            return 'Height Fog Enabled'
        if name == 'heightFogStart':
            return 'Height Fog Start'
        if name == 'heightFogEnd':
            return 'Height Fog End'
        if name == 'heightFogIntensity':
            return 'Height Fog Intensity'
        if name == 'heightFogColor':
            return 'Height Fog Color'
        if name == 'depthOfFieldEnabled':
            return 'DOF Enabled'
        if name == 'depthOfFieldCircle':
            return 'DOF Circle'
        if name == 'depthOfFieldWidth':
            return 'DOF Width'
        if name == 'depthOfFieldNear':
            return 'DOF Near'
        if name == 'depthOfFieldMid':
            return 'DOF Mid'
        if name == 'depthOfFieldFar':
            return 'DOF Far'
        return name

    def getValue(self, name):
        if name == 'cameraPosition':
            return self.render.cameraPosition
        if name == 'cameraRotation':
            return self.render.cameraRotation
        if name == 'playbackSpeed':
            return self.playback.speed
        if name == 'fieldOfView':
            return self.render.fieldOfView
        if name == 'nearClip':
            return self.render.nearClip
        if name == 'farClip':
            return self.render.farClip
        if name == 'navGridOffset':
            return self.render.navGridOffset
        if name == 'skyboxRotation':
            return self.render.skyboxRotation
        if name == 'skyboxRadius':
            return self.render.skyboxRadius
        if name == 'skyboxOffset':
            return self.render.skyboxOffset
        if name == 'sunDirection':
            return self.render.sunDirection
        if name == 'depthFogEnabled':
            return self.render.depthFogEnabled
        if name == 'depthFogStart':
            return self.render.depthFogStart
        if name == 'depthFogEnd':
            return self.render.depthFogEnd
        if name == 'depthFogIntensity':
            return self.render.depthFogIntensity
        if name == 'depthFogColor':
            return self.render.depthFogColor
        if name == 'heightFogEnabled':
            return self.render.heightFogEnabled
        if name == 'heightFogStart':
            return self.render.heightFogStart
        if name == 'heightFogEnd':
            return self.render.heightFogEnd
        if name == 'heightFogIntensity':
            return self.render.heightFogIntensity
        if name == 'heightFogColor':
            return self.render.heightFogColor
        if name == 'depthOfFieldEnabled':
            return self.render.depthOfFieldEnabled
        if name == 'depthOfFieldCircle':
            return self.render.depthOfFieldCircle
        if name == 'depthOfFieldWidth':
            return self.render.depthOfFieldWidth
        if name == 'depthOfFieldNear':
            return self.render.depthOfFieldNear
        if name == 'depthOfFieldMid':
            return self.render.depthOfFieldMid
        if name == 'depthOfFieldFar':
            return self.render.depthOfFieldFar
