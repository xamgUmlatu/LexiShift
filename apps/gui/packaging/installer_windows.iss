#define AppName GetStringParam('AppName', 'LexiShift')
#define AppVersion GetStringParam('AppVersion', '0.1.0')
#define AppExeName GetStringParam('AppExeName', 'LexiShift.exe')
#define DistDir GetStringParam('DistDir', '.')
#define OutputDir GetStringParam('OutputDir', '.')
#define AppPublisher 'LexiShift'
#define AppId '{{8A1F77B1-9A8C-4D45-8C6A-5B64E18C6B9A}}'

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={pf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir={#OutputDir}
OutputBaseFilename={#AppName}-Setup
SetupIconFile=..\\resources\\ttbn.ico
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Files]
Source: "{#DistDir}\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\{#AppName}"; Filename: "{app}\\{#AppExeName}"

[Run]
Filename: "{app}\\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
