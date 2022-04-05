@echo off
pip install pipenv==2022.3.24
pipenv install --skip-lock
pipenv run python -u -m leaguedirector.app
