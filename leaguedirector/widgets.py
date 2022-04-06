import os
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


def schedule(interval, callback):
    timer = QTimer()
    timer.timeout.connect(callback)
    timer.start(interval)
    return timer


def respath(*args):
    directory = os.path.abspath(os.path.join(os.curdir, 'resources'))
    return os.path.join(directory, *args)


def userpath(*args):
    base = os.path.expanduser('~/Documents/LeagueDirector')
    path = os.path.abspath(os.path.join(base, *args))
    if '.' in os.path.basename(path):
        directory = os.path.dirname(path)
    else:
        directory = path
    if not os.path.exists(directory):
        os.makedirs(directory)
    return path


def default(value1, value2):
    return value1 if value1 is not None else value2


class Separator(QFrame):
    def __init__(self):
        QFrame.__init__(self)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class HBoxWidget(QWidget):
    def __init__(self, *widgets):
        QWidget.__init__(self)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        for widget in widgets:
            self.addWidget(widget)

    def addWidget(self, widget):
        self.layout.addWidget(widget)


class VBoxWidget(QWidget):
    def __init__(self, *widgets):
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        for widget in widgets:
            self.addWidget(widget)

    def addWidget(self, widget):
        self.layout.addWidget(widget)


class FloatSlider(QWidget):
    valueChanged = Signal(float)

    def __init__(self, label, precision=5):
        QWidget.__init__(self)

        self.updating = False
        self.precision = 10 ** precision
        self.label = QLabel(label)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setTracking(True)
        self.input = QDoubleSpinBox()

        self.slider.valueChanged.connect(self.sliderValueChanged)
        self.input.valueChanged.connect(self.inputValueChanged)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.input)
        self.setLayout(self.layout)

    def sliderValueChanged(self):
        value = float(self.slider.value()) / self.precision
        self.input.blockSignals(True)
        self.input.setValue(value)
        self.input.blockSignals(False)
        self.valueChanged.emit(value)

    def inputValueChanged(self):
        value = self.input.value()
        self.slider.blockSignals(True)
        self.slider.setValue(value * self.precision)
        self.slider.blockSignals(False)
        self.valueChanged.emit(value)

    def setRange(self, min_value, max_value):
        self.slider.setRange(min_value * self.precision, max_value * self.precision)
        self.input.setRange(min_value, max_value)

    def setSingleStep(self, step):
        self.input.setSingleStep(step)

    def setValue(self, value):
        self.slider.setValue(value)
        self.input.setValue(value)

    def value(self):
        return self.input.value()

    def update(self, value):
        if not self.slider.isSliderDown() and not self.input.hasFocus():
            self.blockSignals(True)
            self.setValue(value)
            self.blockSignals(False)


class FloatInput(QWidget):
    valueChanged = Signal(float)

    def __init__(self, min_value=None, max_value=None):
        QWidget.__init__(self)
        self.range = None
        self.step = None
        self.spin = QDoubleSpinBox()
        self.spin.valueChanged.connect(self.handleValueChanged)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.spin)
        self.setLayout(self.layout)
        self.setRange(default(min_value, float('-inf')), default(max_value, float('inf')))

    def handleValueChanged(self, value):
        self.applyRelativeRange()
        self.applyRelativeStep()
        self.valueChanged.emit(value)

    def update(self, value):
        if not self.spin.hasFocus():
            self.blockSignals(True)
            self.spin.setValue(value)
            self.applyRelativeRange()
            self.applyRelativeStep()
            self.blockSignals(False)

    def applyRelativeRange(self):
        if self.range is not None:
            delta = self.spin.value() * self.range
            self.spin.setRange(self.spin.value() - delta, self.spin.value() + delta)

    def applyRelativeStep(self):
        if self.step is not None:
            self.spin.setSingleStep(max(abs(self.spin.value()) * self.step, 1))

    def setRange(self, min_value, max_value):
        self.spin.setRange(min_value, max_value)
        self.range = None

    def setRelativeRange(self, value):
        self.range = value
        self.applyRelativeRange()

    def setSingleStep(self, step):
        self.spin.setSingleStep(step)
        self.step = None

    def setRelativeStep(self, value):
        self.step = value
        self.applyRelativeStep()

    def setSpecialValueText(self, text):
        self.spin.setSpecialValueText(text)

    def setValue(self, value):
        self.spin.setValue(value)

    def value(self):
        return self.spin.value()


class BooleanInput(QWidget):
    valueChanged = Signal(bool)

    def __init__(self, text=''):
        QWidget.__init__(self)
        self.checkbox = QCheckBox(text)
        self.checkbox.stateChanged.connect(self.handleValueChanged)
        self.label = QLabel('')
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def handleValueChanged(self, state):
        self.valueChanged.emit(bool(state == Qt.Checked))

    def update(self, value):
        self.blockSignals(True)
        self.checkbox.setCheckState(Qt.Checked if value else Qt.Unchecked)
        self.blockSignals(False)

    def setValue(self, value):
        self.checkbox.setCheckState(Qt.Checked if value else Qt.Unchecked)

    def value(self):
        return bool(self.checkbox.checkState() == Qt.Checked)

    def toggle(self):
        self.setValue(not self.value())

    def setText(self, text):
        self.label.setText(text)

    def setCheckboxText(self, text):
        self.checkbox.setText(text)


class VectorInput(QWidget):
    valueChanged = Signal(dict)

    def __init__(self, min_value=None, max_value=None):
        QWidget.__init__(self)
        self.step = None
        self.range = None
        self.x = QDoubleSpinBox()
        self.y = QDoubleSpinBox()
        self.z = QDoubleSpinBox()
        self.x.valueChanged.connect(self.handleValueChanged)
        self.y.valueChanged.connect(self.handleValueChanged)
        self.z.valueChanged.connect(self.handleValueChanged)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.x)
        self.layout.addWidget(self.y)
        self.layout.addWidget(self.z)
        self.setLayout(self.layout)
        min_value = min_value or [float('-inf'), float('-inf'), float('-inf')]
        max_value = max_value or [float('inf'), float('inf'), float('inf')]
        self.setRange(min_value, max_value)

    def handleValueChanged(self, value):
        self.applyRelativeRange()
        self.applyRelativeStep()
        self.valueChanged.emit(self.value())

    def update(self, value):
        if not self.x.hasFocus() and not self.y.hasFocus() and not self.z.hasFocus():
            self.blockSignals(True)
            self.x.setValue(value['x'])
            self.y.setValue(value['y'])
            self.z.setValue(value['z'])
            self.applyRelativeRange()
            self.applyRelativeStep()
            self.blockSignals(False)

    def applyRelativeRange(self):
        if self.range is not None:
            delta = self.x.value() * self.range
            self.x.setRange(self.x.value() - delta, self.x.value() + delta)
            delta = self.y.value() * self.range
            self.y.setRange(self.y.value() - delta, self.y.value() + delta)
            delta = self.z.value() * self.range
            self.z.setRange(self.z.value() - delta, self.z.value() + delta)

    def applyRelativeStep(self):
        if self.step is not None:
            self.x.setSingleStep(max(abs(self.x.value()) * self.step, 1))
            self.y.setSingleStep(max(abs(self.y.value()) * self.step, 1))
            self.z.setSingleStep(max(abs(self.z.value()) * self.step, 1))

    def setRange(self, min_value, max_value):
        self.x.setRange(min_value[0], max_value[0])
        self.y.setRange(min_value[1], max_value[1])
        self.z.setRange(min_value[2], max_value[2])
        self.range = None

    def setSingleStep(self, step):
        self.x.setSingleStep(step)
        self.y.setSingleStep(step)
        self.z.setSingleStep(step)

    def setRelativeRange(self, value):
        self.range = value
        self.applyRelativeRange()

    def setRelativeStep(self, value):
        self.step = value
        self.applyRelativeStep()

    def setValue(self, value):
        self.x.setValue(value['x'])
        self.y.setValue(value['y'])
        self.z.setValue(value['z'])
        self.applyRelativeRange()
        self.applyRelativeStep()

    def value(self):
        return {
            'x' : self.x.value(),
            'y' : self.y.value(),
            'z' : self.z.value()
        }


class ColorInput(QWidget):
    valueChanged = Signal(dict)

    def __init__(self):
        QWidget.__init__(self)
        self.r = QSpinBox()
        self.g = QSpinBox()
        self.b = QSpinBox()
        self.a = QSpinBox()
        self.dialog = QColorDialog()
        self.dialog.setModal(True)
        self.dialog.setOption(QColorDialog.ShowAlphaChannel)
        self.dialog.setOption(QColorDialog.NoButtons)
        self.dialog.setOption(QColorDialog.DontUseNativeDialog)
        self.palette = QPalette()
        self.button = QPushButton()
        self.button.setFlat(True)
        self.button.setAutoFillBackground(True)
        self.button.setFixedSize(QSize(18, 18))
        self.r.setRange(0, 255)
        self.g.setRange(0, 255)
        self.b.setRange(0, 255)
        self.a.setRange(0, 255)
        self.r.valueChanged.connect(self.handleValueChanged)
        self.g.valueChanged.connect(self.handleValueChanged)
        self.b.valueChanged.connect(self.handleValueChanged)
        self.a.valueChanged.connect(self.handleValueChanged)
        self.dialog.currentColorChanged.connect(self.handleColorPicked)
        self.button.clicked.connect(self.dialog.show)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.r)
        self.layout.addWidget(self.g)
        self.layout.addWidget(self.b)
        self.layout.addWidget(self.a)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def handleValueChanged(self, value):
        self.palette.setColor(QPalette.Button, self.color())
        self.button.setPalette(self.palette)
        self.valueChanged.emit(self.value())

    def handleColorPicked(self):
        self.blockSignals(True)
        color = self.dialog.currentColor()
        self.r.setValue(color.red())
        self.g.setValue(color.green())
        self.b.setValue(color.blue())
        self.a.setValue(color.alpha())
        self.blockSignals(False)
        self.valueChanged.emit(self.value())

    def update(self, value):
        if not self.r.hasFocus() and not self.g.hasFocus() and not self.b.hasFocus() and not self.a.hasFocus():
            self.blockSignals(True)
            self.r.setValue(value['r'] * 255)
            self.g.setValue(value['g'] * 255)
            self.b.setValue(value['b'] * 255)
            self.a.setValue(value['a'] * 255)
            self.blockSignals(False)

    def setValue(self, value):
        self.r.setValue(value['r'] * 255)
        self.g.setValue(value['g'] * 255)
        self.b.setValue(value['b'] * 255)
        self.a.setValue(value['a'] * 255)

    def value(self):
        return {
            'r' : float(self.r.value()) / 255,
            'g' : float(self.g.value()) / 255,
            'b' : float(self.b.value()) / 255,
            'a' : float(self.a.value()) / 255
        }

    def color(self):
        return QColor(self.r.value(), self.g.value(), self.b.value(), self.a.value())
