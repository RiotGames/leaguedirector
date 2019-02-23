#!/bin/bash
python -m venv env
env/bin/python -m pip install --upgrade pip
env/bin/python -m pip install -r requirements.txt
env/bin/python -u -m leaguedirector.app
