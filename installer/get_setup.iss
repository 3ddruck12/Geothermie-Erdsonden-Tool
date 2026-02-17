; Inno Setup Script für Geothermie Erdsondentool (GET)
; Ersetzt InstallForge für CI/CD Kompatibilität

[Setup]
AppId={{D37799B5-70A5-4E81-A619-7988B43B712A}
AppName=Geothermie Erdsondentool
AppVersion={#AppVersion}
AppPublisher=3ddruck12
AppPublisherURL=https://github.com/3ddruck12/Geothermie-Erdsonden-Tool
AppSupportURL=https://github.com/3ddruck12/Geothermie-Erdsonden-Tool/issues
AppUpdatesURL=https://github.com/3ddruck12/Geothermie-Erdsonden-Tool/releases
DefaultDirName={autopf}\Geothermie Erdsondentool
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..
OutputBaseFilename=Setup_GET_v{#AppVersion}
SetupIconFile=..\Icons\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
DefaultGroupName=Geothermie Erdsondentool
AllowNoIcons=yes

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\GeothermieErdsondentool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Geothermie Erdsondentool"; Filename: "{app}\GeothermieErdsondentool.exe"; IconFilename: "{app}\Icons\icon.ico"
Name: "{group}\{cm:UninstallProgram,Geothermie Erdsondentool}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Geothermie Erdsondentool"; Filename: "{app}\GeothermieErdsondentool.exe"; Tasks: desktopicon; IconFilename: "{app}\Icons\icon.ico"

[Run]
Filename: "{app}\GeothermieErdsondentool.exe"; Description: "{cm:LaunchProgram,Geothermie Erdsondentool}"; Flags: nowait postinstall skipafs silentcheck
