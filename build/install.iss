[Setup]
AppName=League Director
AppVersion=0.1.1
AppVerName=League Director
DisableDirPage=no
DefaultDirName={pf}\League Director
DefaultGroupName=League Director
UninstallDisplayIcon={app}\LeagueDirector.exe
Compression=lzma2
SolidCompression=yes
OutputDir=out
OutputBaseFilename=LeagueDirectorSetup
SetupIconFile=..\resources\icon.ico
LicenseFile=..\LICENSE

[Files]
Source: "out\dist\LeagueDirector\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\League Director"; Filename: "{app}\LeagueDirector.exe"

[Run]
Filename: "{app}\LeagueDirector.exe"; Description: "Launch League Directory"; Flags: postinstall nowait skipifsilent
