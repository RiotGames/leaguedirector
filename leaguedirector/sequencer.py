import copy
import threading
import webbrowser
import statistics
from operator import attrgetter, methodcaller
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from leaguedirector.widgets import *

PRECISION = 10000.0
SNAPPING = 4
OVERLAP = 4
ADJACENT = 0.05


class SequenceKeyframe(QGraphicsPixmapItem):

    def __init__(self, api, item, track):
        self.pixmapNormal = QPixmap(respath('kfnormal.png'))
        self.pixmapOverlap = QPixmap(respath('kfoverlap.png'))
        QGraphicsPixmapItem.__init__(self, self.pixmapNormal, track)
        self.api = api
        self.track = track
        self.item = item
        self.duplicate = None
        self.setCursor(Qt.ArrowCursor)
        self.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)
        flags = QGraphicsItem.ItemIgnoresTransformations
        flags |= QGraphicsItem.ItemIsMovable
        flags |= QGraphicsItem.ItemIsSelectable
        flags |= QGraphicsItem.ItemSendsGeometryChanges
        self.setFlags(flags)
        self.setOffset(-10, 3)
        self.update()

    def viewport(self):
        return self.scene().views()[0]

    @property
    def time(self):
        return self.item['time']

    @time.setter
    def time(self, value):
        if self.item['time'] != value:
            self.item['time'] = value
            self.api.sequence.update()
            self.track.updateOverlap()
            self.update()

    @property
    def valueType(self):
        value = self.item['value']
        if isinstance(value, float):
            return 'float'
        elif isinstance(value, bool):
            return 'bool'
        elif isinstance(value, dict):
            if 'x' in value and 'y' in value and 'z' in value:
                return 'vector'
            if 'r' in value and 'g' in value and 'b' in value and 'a' in value:
                return 'color'
        return ''

    @property
    def value(self):
        return self.item['value']

    @value.setter
    def value(self, value):
        if self.item['value'] != value:
            self.item['value'] = value
            self.api.sequence.update()
            self.update()

    @property
    def blend(self):
        return self.item.get('blend')

    @blend.setter
    def blend(self, value):
        if self.item.get('blend') != value:
            self.item['blend'] = value
            self.api.sequence.update()
            self.update()

    def update(self):
        self.setPos(int(self.time * PRECISION), 0)
        self.setToolTip(self.tooltip())

    def tooltip(self):
        value = self.value
        if isinstance(value, dict):
            value = tuple(value.values())
        return 'Time: {}\nBlend: {}\nValue: {}'.format(self.time, self.blend, value)

    def delete(self):
        self.api.sequence.removeKeyframe(self.track.name, self.item)
        self.scene().removeItem(self)

    def setOverlapping(self, overlapping):
        self.setPixmap(self.pixmapOverlap if overlapping else self.pixmapNormal)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.NoModifier:
            if len(self.scene().selectedItems()) < 2:
                self.api.playback.pause(self.time)
                event.accept()
        QGraphicsPixmapItem.mouseDoubleClickEvent(self, event)

    def mouseReleaseEvent(self, event):
        for key in self.scene().selectedItems():
            if isinstance(key, SequenceKeyframe):
                key.duplicate = None
        QGraphicsPixmapItem.mouseReleaseEvent(self, event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            value.setX(self.performSnapping(value.x()))
            value.setX(max(0, value.x()))
            value.setY(0)
            self.performDuplication()
            return value
        elif change == QGraphicsItem.ItemPositionHasChanged:
            if value:
                self.time = value.x() / PRECISION
        return QGraphicsPixmapItem.itemChange(self, change, value)

    def performDuplication(self):
        if self.isSelected() and self.duplicate is None:
            if QApplication.mouseButtons() == Qt.LeftButton:
                if QApplication.keyboardModifiers() == Qt.AltModifier:
                    self.duplicate = self.track.duplicateKeyframe(self)

    def performSnapping(self, time):
        if QApplication.mouseButtons() == Qt.LeftButton:
            if QApplication.keyboardModifiers() == Qt.NoModifier:
                if len(self.scene().selectedItems()) < 2:
                    scene = self.scene()
                    viewport = self.viewport()
                    screenPosition = viewport.mapFromScene(time, 0).x()
                    left = viewport.mapToScene(screenPosition - SNAPPING, 0).x()
                    right = viewport.mapToScene(screenPosition + SNAPPING, 0).x()
                    items = scene.items(left, float(0), right - left, scene.height(), Qt.IntersectsItemBoundingRect, Qt.AscendingOrder)
                    for item in items:
                        if isinstance(item, SequenceKeyframe):
                            if item != self and not item.isSelected() and item.track != self.track:
                                return item.x()
                        elif isinstance(item, SequenceTime):
                            return self.api.playback.time * PRECISION
        return time


class SequenceTrack(QGraphicsRectItem):
    height = 22

    def __init__(self, api, name, index):
        QGraphicsRectItem.__init__(self)
        self.api = api
        self.name = name
        self.index = index
        self.setPos(0, self.height * self.index)
        self.setToolTip(self.api.sequence.getLabel(self.name))
        self.setPen(QPen(QColor(70, 70, 70, 255)))
        self.updateOverlapTimer = QTimer()
        self.updateOverlapTimer.timeout.connect(self.updateOverlapNow)
        self.updateOverlapTimer.setSingleShot(True)
        self.gradient = QLinearGradient(QPointF(0, 0), QPointF(120 * PRECISION, 0))
        self.gradient.setColorAt(0, QColor(30, 30, 30, 255))
        self.gradient.setColorAt(0.49999999999999, QColor(30, 30, 30, 255))
        self.gradient.setColorAt(0.5, QColor(40, 40, 40, 255))
        self.gradient.setColorAt(1, QColor(40, 40, 40, 255))
        self.gradient.setSpread(QGradient.RepeatSpread)
        self.setBrush(QBrush(self.gradient))
        self.reload()
        self.update()

    def viewport(self):
        return self.scene().views()[0]

    def paint(self, *args):
        self.updateOverlap()
        return QGraphicsRectItem.paint(self, *args)

    def reload(self):
        for item in self.childItems():
            if isinstance(item, SequenceKeyframe):
                self.scene().removeItem(item)
        for item in self.api.sequence.getKeyframes(self.name):
            SequenceKeyframe(self.api, item, self)

    def addKeyframe(self):
        item = self.api.sequence.createKeyframe(self.name)
        return SequenceKeyframe(self.api, item, self)

    def duplicateKeyframe(self, keyframe):
        item = copy.deepcopy(keyframe.item)
        self.api.sequence.appendKeyframe(self.name, item)
        return SequenceKeyframe(self.api, item, self)

    def clearKeyframes(self):
        for item in self.childItems():
            if isinstance(item, SequenceKeyframe):
                item.delete()

    def updateOverlapNow(self):
        viewport = self.viewport()
        distance = viewport.mapToScene(OVERLAP, 0).x() - viewport.mapToScene(0, 0).x()
        previous = None
        for child in sorted(self.childItems(), key=methodcaller('x')):
            if isinstance(child, SequenceKeyframe):
                if previous and abs(child.x() - previous.x()) < distance:
                    child.setOverlapping(True)
                    previous.setOverlapping(True)
                else:
                    child.setOverlapping(False)
                previous = child

    def updateOverlap(self):
        self.updateOverlapTimer.start(100)

    def update(self):
        self.setRect(0, 0, int(self.api.playback.length * PRECISION), self.height)


class SequenceHeader(QGraphicsRectItem):
    height = 22

    def __init__(self, api, name, index, callback):
        QGraphicsRectItem.__init__(self)
        self.api = api
        self.name = name
        self.index = index
        self.callback = callback
        self.setPos(0, self.height * self.index)
        self.setRect(0, 0, 160, self.height)
        self.setToolTip(self.label())
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QColor(20, 20, 50, 255))
        self.setFlags(QGraphicsItem.ItemIgnoresTransformations)
        self.text = QGraphicsSimpleTextItem(self.label(), self)
        self.text.setBrush(QApplication.palette().brightText())
        self.text.setPos(145 - self.text.boundingRect().width() - 20, 4)
        self.button = QGraphicsPixmapItem(QPixmap(respath('plus.png')), self)
        self.button.setPos(140, 4)
        self.button.setCursor(Qt.ArrowCursor)
        self.button.mousePressEvent = lambda event: self.callback(self.name)

    def label(self):
        return self.api.sequence.getLabel(self.name)


class SequenceHeaderView(QGraphicsView):
    addKeyframe = Signal(str)

    def __init__(self, api):
        self.api = api
        self.scene = QGraphicsScene()
        QGraphicsView.__init__(self, self.scene)
        self.setFixedWidth(162)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for index, name in enumerate(self.api.sequence.keys()):
            self.scene.addItem(SequenceHeader(self.api, name, index, self.addKeyframe.emit))


class SequenceTime(QGraphicsLineItem):
    pass


class SequenceTrackView(QGraphicsView):
    selectionChanged = Signal()

    def __init__(self, api, headers):
        self.api = api
        self.scene = QGraphicsScene()
        QGraphicsView.__init__(self, self.scene)
        self.tracks = {}
        self.timer = schedule(10, self.animate)
        self.scale(1.0 / PRECISION, 1.0)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        for index, name in enumerate(self.api.sequence.keys()):
            track = SequenceTrack(self.api, name, index)
            self.scene.addItem(track)
            self.tracks[name] = track
        self.time = SequenceTime(0, 1, 0, self.scene.height() - 2)
        self.time.setPen(QPen(QApplication.palette().highlight(), 1))
        self.time.setFlags(QGraphicsItem.ItemIgnoresTransformations)
        self.scene.addItem(self.time)
        self.api.playback.updated.connect(self.update)
        self.api.sequence.updated.connect(self.update)
        self.api.sequence.dataLoaded.connect(self.reload)
        headers.addKeyframe.connect(self.addKeyframe)
        headers.verticalScrollBar().valueChanged.connect(lambda value: self.verticalScrollBar().setValue(value))
        self.verticalScrollBar().valueChanged.connect(lambda value: headers.verticalScrollBar().setValue(value))
        self.scene.selectionChanged.connect(self.selectionChanged.emit)

    def reload(self):
        for track in self.tracks.values():
            track.reload()

    def selectedKeyframes(self):
        return [key for key in self.scene.selectedItems() if isinstance(key, SequenceKeyframe)]

    def allKeyframes(self):
        return [key for key in self.scene.items() if isinstance(key, SequenceKeyframe)]

    def addKeyframe(self, name):
        self.tracks[name].addKeyframe()

    def clearKeyframes(self):
        for track in self.tracks.values():
            track.clearKeyframes()

    def deleteSelectedKeyframes(self):
        for selected in self.selectedKeyframes():
            selected.delete()

    def selectAllKeyframes(self):
        for child in self.allKeyframes():
            child.setSelected(True)

    def selectAdjacentKeyframes(self):
        for selected in self.selectedKeyframes():
            for child in self.allKeyframes():
                if abs(child.time - selected.time) < ADJACENT:
                    child.setSelected(True)

    def selectNextKeyframe(self):
        selectionSorted = sorted(self.selectedKeyframes(), key=attrgetter('time'))
        trackSelection = {key.track : key for key in selectionSorted}
        for track, selected in trackSelection.items():
            for child in sorted(track.childItems(), key=attrgetter('time')):
                if child.time > selected.time:
                    trackSelection[track] = child
                    break
        self.scene.clearSelection()
        for item in trackSelection.values():
            item.setSelected(True)

    def selectPrevKeyframe(self):
        selectionSorted = sorted(self.selectedKeyframes(), key=attrgetter('time'), reverse=True)
        trackSelection = {key.track : key for key in selectionSorted}
        for track, selected in trackSelection.items():
            for child in sorted(track.childItems(), key=attrgetter('time'), reverse=True):
                if child.time < selected.time:
                    trackSelection[track] = child
                    break
        self.scene.clearSelection()
        for item in trackSelection.values():
            item.setSelected(True)

    def seekSelectedKeyframe(self):
        selected = [key.time for key in self.selectedKeyframes()]
        if selected:
            self.api.playback.pause(statistics.mean(selected))

    def update(self):
        for track in self.tracks.values():
            track.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            QGraphicsView.mousePressEvent(self, QMouseEvent(
                QEvent.GraphicsSceneMousePress,
                event.pos(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            ))
        elif event.button() == Qt.LeftButton:
            if event.modifiers() == Qt.ShiftModifier:
                self.setDragMode(QGraphicsView.RubberBandDrag)
                QGraphicsView.mousePressEvent(self, event)
        QGraphicsView.mousePressEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        QGraphicsView.mouseDoubleClickEvent(self, event)
        if not self.scene.selectedItems() and not event.isAccepted():
            self.api.playback.pause(self.mapToScene(event.pos()).x() / PRECISION)

    def mouseReleaseEvent(self, event):
        QGraphicsView.mouseReleaseEvent(self, event)
        self.setDragMode(QGraphicsView.NoDrag)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale(1.1, 1.0)
        else:
            self.scale(0.9, 1.0)

    def animate(self):
        self.time.setPos(self.api.playback.currentTime * PRECISION, 0)


class SequenceCombo(QComboBox):
    def __init__(self, api):
        QComboBox.__init__(self)
        self.api = api
        self.update()
        self.api.sequence.namesLoaded.connect(self.update)
        self.activated.connect(self.onActivated)

    def onActivated(self, index):
        self.api.sequence.load(self.itemText(index))

    def showPopup(self):
        self.api.sequence.reloadNames()
        QComboBox.showPopup(self)

    def update(self):
        self.clear()
        for name in self.api.sequence.names:
            self.addItem(name)
        self.setCurrentIndex(self.api.sequence.index)


class SequenceSelectedView(QWidget):
    def __init__(self, api, tracks):
        QWidget.__init__(self)
        self.api = api
        self.api.playback.updated.connect(self.update)
        self.api.sequence.updated.connect(self.update)
        self.tracks = tracks
        self.tracks.selectionChanged.connect(self.update)
        self.form = QFormLayout(self)
        self.setLayout(self.form)
        self.layout()
        self.update()

    def layout(self):
        self.label = QLabel()
        self.time = FloatInput()
        self.blend = QComboBox()
        self.value = HBoxWidget()
        self.valueLabel = QLabel('Multiple Selected')
        self.valueFloat = FloatInput()
        self.valueBool = BooleanInput()
        self.valueVector = VectorInput()
        self.valueColor = ColorInput()
        self.value.addWidget(self.valueLabel)
        self.value.addWidget(self.valueFloat)
        self.value.addWidget(self.valueBool)
        self.value.addWidget(self.valueVector)
        self.value.addWidget(self.valueColor)
        self.blend.activated.connect(self.updateBlend)
        for option in self.api.sequence.blendOptions:
            self.blend.addItem(option)

        self.blendHelp = QPushButton()
        self.blendHelp.setFixedWidth(20)
        self.blendHelp.setIcon(self.style().standardIcon(QStyle.SP_TitleBarContextHelpButton))
        self.blendHelp.clicked.connect(self.openBlendHelp)

        self.form.addRow('', self.label)
        self.form.addRow('Time', self.time)
        self.form.addRow('Blend', HBoxWidget(self.blend, self.blendHelp))
        self.form.addRow('Value', self.value)
        
        self.time.valueChanged.connect(self.updateTime)
        self.valueFloat.valueChanged.connect(self.updateValue)
        self.valueBool.valueChanged.connect(self.updateValue)
        self.valueVector.valueChanged.connect(self.updateValue)
        self.valueColor.valueChanged.connect(self.updateValue)
        self.blend.activated.connect(self.updateBlend)

    def openBlendHelp(self):
        threading.Thread(target=lambda: webbrowser.open_new('https://easings.net')).start()

    def update(self):
        selected = self.tracks.selectedKeyframes()
        self.setVisible(len(selected))
        self.time.setRange(0, self.api.playback.length)

        blending = list(set([key.blend for key in selected]))
        self.label.setText("{} keyframes selected".format(len(selected)))
        if len(blending) == 1:
            self.blend.setCurrentText(blending[0])
        else:
            self.blend.setCurrentIndex(-1)

        times = list(set([key.time for key in selected]))
        if len(times):
            self.time.update(times[0])

        if len(set([key.valueType for key in selected])) == 1:
            valueType = selected[0].valueType
            if valueType == 'float':
                self.valueFloat.update(selected[0].value)
                self.valueLabel.setVisible(False)
                self.valueFloat.setVisible(True)
                self.valueBool.setVisible(False)
                self.valueVector.setVisible(False)
                self.valueColor.setVisible(False)
            elif valueType == 'bool':
                self.valueBool.update(selected[0].value)
                self.valueLabel.setVisible(False)
                self.valueFloat.setVisible(False)
                self.valueBool.setVisible(True)
                self.valueVector.setVisible(False)
                self.valueColor.setVisible(False)
            elif valueType == 'vector':
                self.valueVector.update(selected[0].value)
                self.valueLabel.setVisible(False)
                self.valueFloat.setVisible(False)
                self.valueBool.setVisible(False)
                self.valueVector.setVisible(True)
                self.valueColor.setVisible(False)
            elif valueType == 'color':
                self.valueColor.update(selected[0].value)
                self.valueLabel.setVisible(False)
                self.valueFloat.setVisible(False)
                self.valueBool.setVisible(False)
                self.valueVector.setVisible(False)
                self.valueColor.setVisible(True)
        else:
            self.valueLabel.setVisible(True)
            self.valueFloat.setVisible(False)
            self.valueBool.setVisible(False)
            self.valueVector.setVisible(False)
            self.valueColor.setVisible(False)

    def updateTime(self):
        for item in self.tracks.selectedKeyframes():
            item.time = self.time.value()

    def updateValue(self, value):
        for item in self.tracks.selectedKeyframes():
            item.value = value

    def updateBlend(self, index):
        for item in self.tracks.selectedKeyframes():
            item.blend = self.blend.itemText(index)
