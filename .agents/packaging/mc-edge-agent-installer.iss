; Mission Control Edge Agent - Windows EXE Installer
; Build with: ISCC.exe mc-edge-agent-installer.iss
; Download InnoSetup from: https://jrsoftware.org/isdl.php

; Define application constants
#define AppName "Mission Control Edge Agent"
#define AppVersion "3.0.0-rc1-edge"
#define AppPublisher "Mission Control"
#define AppURL "https://missioncontrol.optichosting.co.za"
#define DefaultInstallDir "{pf}\MC Edge Agent"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={#DefaultInstallDir}
DisableDirPage=no
DisableProgramGroupPage=yes
OutputDir=.\output
OutputBaseFilename=mc-edge-agent-setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=.\assets\icon.ico
UninstallDisplayIcon={app}\tools\nssm.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Core agent package
Source: ".\agent-bundle-live.zip"; DestDir: "{tmp}"; Flags: deleteafterinstall

; Configuration
Source: ".\config\config.yaml"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: ".\README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme

; Install Python 3.12 if not present
; Note: User must download python-3.12.x-amd64.exe separately or include it in Source

[Run]
; Install Python if needed
Filename: "{tmp}\python-3.12.x-amd64.exe"; Parameters: "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0"; Flags: waituntilterminated; Check: not PythonInstalled

; Install agent package
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{tmp}\install-agent.ps1"" -ServerUrl ""{code:GetServerUrl}"" -AgentName ""{code:GetAgentName}"""; Flags: waituntilterminated runhidden postinstall

; Start the service
Filename: "powershell.exe"; Parameters: "-Command ""Start-Service -Name 'MissionControlEdgeAgent' -ErrorAction SilentlyContinue; Start-Sleep -Seconds 3; Get-Service -Name 'MissionControlEdgeAgent'"""; Flags: waituntilterminated runhidden postinstall skipifdoesntexist

[Code]
var
  ServerUrlPage: TInputQueryWizardPage;
  AgentNamePage: TInputQueryWizardPage;

function PythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := not Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  if Result then
  begin
    Result := not Exec('py', '-3 --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

function GetServerUrl(Param: String): String;
begin
  Result := ServerUrlPage.Values[0];
end;

function GetAgentName(Param: String): String;
begin
  Result := AgentNamePage.Values[0];
end;

procedure InitializeWizard;
begin
  ServerUrlPage := CreateInputQueryPage(wpWelcome,
    'Mission Control Server URL',
    'Enter the URL of your Mission Control server',
    'This is the address where the agent will send its data.');
  ServerUrlPage.Add('Server URL:', False);
  ServerUrlPage.Values[0] := 'https://missioncontrol.optichosting.co.za';

  AgentNamePage := CreateInputQueryPage(ServerUrlPage.ID,
    'Agent Name',
    'Enter a name for this agent',
    'This name will appear in the Mission Control dashboard.');
  AgentNamePage.Add('Agent Name:', False);
  AgentNamePage.Values[0] := ExpandConstant('{computername}');
end;

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\tools\nssm.exe"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\tools\nssm.exe"; Tasks: desktopicon
