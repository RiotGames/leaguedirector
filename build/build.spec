import sys
sys.modules['FixTk'] = None

a = Analysis(['..\\leaguedirector\\app.py'],
    binaries = [],
    datas = [],
    hiddenimports = [],
    hookspath = [],
    runtime_hooks = [],
    excludes = ['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', 'lib2to3'],
    win_no_prefer_redirects = False,
    win_private_assemblies = False,
    cipher = None,
    noarchive = False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(pyz, a.scripts, [],
    exclude_binaries = True,
    name = 'LeagueDirector',
    debug = False,
    bootloader_ignore_signals = False,
    strip = False,
    upx = True,
    console = False,
    icon = '..\\resources\\icon.ico'
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas,
    strip = False,
    upx = True,
    name = 'LeagueDirector'
)
