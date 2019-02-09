import os
import psutil
import platform
from PySide2.QtCore import *

def findWindowsRegistry(paths):
    """
    Find games installs in the windows registry.
    """
    settings = QSettings("HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node", QSettings.NativeFormat);
    settings.beginGroup("Riot Games, Inc")    
    for key in settings.allKeys():
        if key.endswith('/Location'):
            paths.append(settings.value(key))

def findWindowsRunning(paths):
    """
    Find any running games on windows
    """
    for process in psutil.process_iter(attrs=['name', 'exe']):
        name = process.info['name'].lower()
        path = process.info['exe']
        if name == 'leagueclient.exe' and '\\RADS' in path:
            paths.append(path.split('\\RADS')[0])
        elif name in ('launcher.exe', 'singleplayertool.exe') and 'DevRoot' in path:
            paths.append(os.path.join(path.split('\\DevRoot')[0], 'DevRoot'))

def findInstalledGames():
    paths = []

    # Find running games on windows
    if platform.system() == 'Windows':
        findWindowsRegistry(paths)
        findWindowsRunning(paths)

    # Make sure all paths are valid and formatted the same
    paths = [os.path.abspath(path) for path in paths if os.path.isdir(path)]

    # Remove duplicates and sort
    return sorted(list(set(paths)))

def configFilePath(path):
    config = os.path.join(path, "Config", "game.cfg")
    if os.path.exists(config):
        return config
    config = os.path.join(path, "DATA", "CFG", "Game.cfg")
    if os.path.exists(config):
        return config

def isGameEnabled(path):
    path = configFilePath(path)
    if path:
        settings = QSettings(path, QSettings.IniFormat)
        value = settings.value("EnableReplayApi", False)
        return str(value).lower() in ['true', '1']
    return False

def setGameEnabled(path, enabled):
    path = configFilePath(path)
    if path:
        settings = QSettings(path, QSettings.IniFormat)
        settings.setValue("EnableReplayApi", int(enabled))
