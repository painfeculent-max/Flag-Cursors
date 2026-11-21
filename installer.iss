; Script Inno Setup - Flag Cursors
#define AppName "Flag Cursors"
#define AppVersion "1.1.0"
#define AppExe "FlagCursors.exe"

[Setup]
AppId={{B7E1C2A4-5F3D-4E6B-9A21-7C0D8F4E1A55}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Flag Cursors
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=FlagCursors-Setup
SetupIconFile=app.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remet les curseurs Windows d'origine et retire le lancement au demarrage
Filename: "{app}\{#AppExe}"; Parameters: "--restore --unregister-startup"; Flags: runhidden; RunOnceId: "RestoreCursor"
