@echo off
pip install pipenv
pipenv install --skip-lock
pipenv run python -u -m leaguedirector.app
