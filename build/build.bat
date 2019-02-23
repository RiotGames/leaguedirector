@echo off
cd %~dp0
python -m venv ../env
..\env\Scripts\python.exe -m pip install --upgrade pip
..\env\Scripts\python.exe -m pip install -r ../requirements.txt
..\env\Scripts\python.exe -m pip install pyinstaller==3.4
..\env\Scripts\pyinstaller.exe build.spec --noconfirm --workpath=out/build --distpath=out/dist
ISCC.exe install.iss
