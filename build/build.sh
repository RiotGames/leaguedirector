#!/bin/bash
cd "${0%/*}"
pipenv run pip install pyinstaller==3.4
pipenv run pyinstaller build.spec --windowed --noconfirm --workpath=out/build --distpath=out/dist
