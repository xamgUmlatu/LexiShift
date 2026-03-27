#ifndef AppName
  #define AppName "LexiShift"
#endif
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
#ifndef AppExePath
  #define AppExePath "LexiShift\LexiShift.exe"
#endif
#ifndef DistDir
  #define DistDir "."
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif
#define AppPublisher 'LexiShift'
#define AppId '{{8A1F77B1-9A8C-4D45-8C6A-5B64E18C6B9A}}'

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
UsePreviousAppDir=no
DefaultGroupName={#AppName}
OutputDir={#OutputDir}
OutputBaseFilename={#AppName}-Setup
SetupIconFile=..\\resources\\ttbn.ico
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Files]
Source: "{#DistDir}\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "installers\\*"

[Icons]
Name: "{group}\\{#AppName}"; Filename: "{app}\\{#AppExePath}"

[Run]
Filename: "{app}\\{#AppExePath}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
