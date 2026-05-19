; AstraForge v1.2 — Inno Setup Installer Script
; Download Inno Setup: https://jrsoftware.org/isinfo.php
; Compile: open this file in Inno Setup Compiler and press Build

#define AppName      "AstraForge"
#define AppVersion   "1.2"
#define AppPublisher "linuxwifi7"
#define AppExe       "AstraForge.exe"
#define AppCLI       "AstraForgeCLI.exe"

[Setup]
AppId={{6E4A2F3B-A792-4F2E-A935-CE109270A810}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL=https://github.com/linuxwifi7/TP-link-wifi-MT7927-reverse-engineer
AppSupportURL=https://github.com/linuxwifi7/TP-link-wifi-MT7927-reverse-engineer/issues
AppUpdatesURL=https://github.com/linuxwifi7/TP-link-wifi-MT7927-reverse-engineer/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=..\..\dist
OutputBaseFilename=AstraForge_Setup_v1.2
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\{#AppCLI}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}";          Filename: "{app}\{#AppExe}"
Name: "{group}\{#AppName} CLI";      Filename: "{app}\{#AppCLI}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";    Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Dirs]
; Create the writable config directory in %APPDATA% so the app can save settings
Name: "{userappdata}\{#AppName}"; Flags: uninsneveruninstall

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ConfigDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    ConfigDir := ExpandConstant('{userappdata}\{#AppName}');
    if DirExists(ConfigDir) then
    begin
      if MsgBox('Remove saved AstraForge settings from ' + ConfigDir + '?',
                mbConfirmation, MB_YESNO) = IDYES then
        DelTree(ConfigDir, True, True, True);
    end;
  end;
end;
