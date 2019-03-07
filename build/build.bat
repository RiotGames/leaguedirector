@echo off
cd %~dp0
set /p CODESIGN_CERT="CODESIGN_CERT: "
set /p CODESIGN_PASS="CODESIGN_PASS: "
pip install pipenv
pipenv install --skip-lock
pipenv run pip install pyinstaller==3.4
pipenv run pyinstaller build.spec --noconfirm --workpath=out/build --distpath=out/dist
signtool.exe sign /f "%CODESIGN_CERT%" /p "%CODESIGN_PASS%" /t http://timestamp.digicert.com out\dist\LeagueDirector\LeagueDirector.exe
ISCC.exe install.iss
signtool.exe sign /f "%CODESIGN_CERT%" /p "%CODESIGN_PASS%" /t http://timestamp.digicert.com out\LeagueDirectorSetup.exe
