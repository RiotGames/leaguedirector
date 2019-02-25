#!/bin/bash
cd "${0%/*}"
pip install pipenv
pipenv install --skip-lock
pipenv run pip install pyinstaller==3.4
pipenv run pyinstaller build.spec --windowed --noconfirm --workpath=out/build --distpath=out/dist
