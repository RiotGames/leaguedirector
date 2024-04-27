@echo off
cd %~dp0
pip install pipenv==2022.3.24
pipenv install --skip-lock
pipenv run pip install pyinstaller==6.6.0
pipenv run pyinstaller build.spec --noconfirm --workpath=out/build --distpath=out/dist
ISCC.exe install.iss
