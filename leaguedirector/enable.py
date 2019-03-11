import os
import psutil
import platform
import logging
import subprocess
from PySide2.QtCore import *

def findWindowsInstalled(paths):
    """
    Find games installs in the windows registry.
    """
    settings = QSettings('HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node', QSettings.NativeFormat);
    settings.beginGroup('Riot Games, Inc')
    for key in settings.allKeys():
        if key.endswith('/Location'):
            paths.append(settings.value(key))
    settings.endGroup()

def findWindowsRunning(paths):
    """
    Find any running games on windows
    """
    for process in psutil.process_iter(attrs=['name', 'exe']):
        name = process.info['name'].lower()
        path = process.info['exe']
        if name == 'leagueclient.exe' and '\\RADS' in path:
            paths.append(path.split('\\RADS')[0])
        if name == 'leagueclient.exe' and '\\LeagueClient\\' in path:
            paths.append(os.path.join(path.split('\\LeagueClient')[0]))
        elif name in ('launcher.exe', 'singleplayertool.exe') and 'DevRoot' in path:
            paths.append(os.path.join(path.split('\\DevRoot')[0], 'DevRoot'))

def findWindowsCached(paths):
    """
    Search through the windows MUI cache which is another place windows
    will keep track of league of legends clients that have been started
    on this machine.
    """
    settings = QSettings('HKEY_CURRENT_USER\\Software\\Classes\\Local Settings\\Software\\Microsoft\\Windows\\Shell\\MuiCache', QSettings.NativeFormat);
    for key in settings.allKeys():
        index = key.lower().find('league of legends.exe')
        if index > 0:
            paths.append(key[0:index])

def findMacInstalled(paths):
    """
    Ask the mac system profiler to list all installed apps.
    """
    query = 'kMDItemCFBundleIdentifier==com.riotgames.leagueoflegends'
    for line in subprocess.check_output(['mdfind', query]).splitlines():
        paths.append(line.decode())

def findMacRunning(paths):
    """
    List all the running league client processes.
    """
    for process in psutil.process_iter(attrs=['name']):
        if process.info['name'].lower() == 'leagueclient':
            path = process.exe().split('/Contents/LoL/RADS/')
            if len(path) == 2:
                paths.append(path[0])

def findInstalledGames():
    paths = []

    # Find running games on windows
    if platform.system() == 'Windows':
        findWindowsInstalled(paths)
        findWindowsRunning(paths)
        findWindowsCached(paths)
    elif platform.system() == 'Darwin':
        findMacInstalled(paths)
        findMacRunning(paths)

    # Make sure all paths are valid and formatted the same
    paths = [configFilePath(os.path.abspath(path)) for path in paths]

    # Remove nones + duplicates and sort
    return sorted(list(set([os.path.normcase(path) for path in paths if path is not None])))

def configFilePath(path):
    path = os.path.abspath(path)
    if platform.system() == 'Darwin':
        path = os.path.join(path, 'Contents', 'LoL')
    config = os.path.join(path, 'Config', 'game.cfg')
    if os.path.isfile(config):
        return config
    config = os.path.join(path, 'Game', 'Config', 'game.cfg')
    if os.path.isfile(config):
        return config
    config = os.path.join(path, 'DATA', 'CFG', 'game.cfg')
    if os.path.isfile(config):
        return config

def isGameEnabled(path):
    if os.path.isfile(path):
        settings = QSettings(path, QSettings.IniFormat)
        value = settings.value('EnableReplayApi', False)
        return str(value).lower() in ['true', '1']
    return False

def setGameEnabled(path, enabled):
    if os.path.isfile(path):
        logging.info('Setting EnableReplayApi %s=%d', path, enabled)
        settings = QSettings(path, QSettings.IniFormat)
        settings.setValue('EnableReplayApi', int(enabled))
