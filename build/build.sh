#!/bin/bash
cd "${0%/*}"
python -m venv ../env
../env/bin/python -m pip install --upgrade pip
../env/bin/python -m pip install -r ../requirements.txt
../env/bin/python -m pip install pyinstaller==3.4
../env/bin/pyinstaller build.spec --windowed --noconfirm --workpath=out/build --distpath=out/dist
