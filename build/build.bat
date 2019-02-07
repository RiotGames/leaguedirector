@echo off
cd %~dp0
pipenv run pip install pyinstaller==3.4
pipenv run pyinstaller build.spec --noconfirm --workpath=out/build --distpath=out/dist
ISCC.exe install.iss
