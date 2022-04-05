@echo off
cd %~dp0
set /p CODESIGN_TOKEN="CODESIGN_TOKEN: "
pip install pipenv==2022.3.24
pipenv install --skip-lock
pipenv run pip install pyinstaller==4.10
pipenv run pyinstaller build.spec --noconfirm --workpath=out/build --distpath=out/dist
autograph.exe digestsign --signtool signtool.exe --artifact out\dist\LeagueDirector\LeagueDirector.exe --certificate riot_ev --token %CODESIGN_TOKEN% --crossCertificate digicert_ev_x_cert --verify
ISCC.exe install.iss
autograph.exe digestsign --signtool signtool.exe --artifact out\LeagueDirectorSetup.exe --certificate riot_ev --token %CODESIGN_TOKEN% --crossCertificate digicert_ev_x_cert --verify