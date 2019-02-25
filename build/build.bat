@echo off
cd %~dp0
pip install pipenv
pipenv install --skip-lock
pipenv run pip install pyinstaller==3.4
pipenv run pyinstaller build.spec --noconfirm --workpath=out/build --distpath=out/dist
ISCC.exe install.iss
