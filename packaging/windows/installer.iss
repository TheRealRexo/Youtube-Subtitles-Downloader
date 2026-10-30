; Optional Inno Setup installer for the Windows portable build.
; Build the portable app first with: python scripts\build.py
; Then open this file in Inno Setup Compiler and compile it.

#define MyAppName "Youtube Subtitles Downloader"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TheRealRexo"
#define MyAppExeName "Youtube Subtitles Downloader.exe"

[Setup]
AppId={{8D9B2C7E-6A7F-4A3B-9C61-2E7F3A1D4B52}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=YoutubeSubtitlesDownloader-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "..\..\dist\Youtube Subtitles Downloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
