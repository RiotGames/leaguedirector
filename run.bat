@echo off
python -m venv env
env\Scripts\python.exe -m pip install --upgrade pip
env\Scripts\python.exe -m pip install -r requirements.txt
env\Scripts\python.exe -u -m leaguedirector.app
