; Bo cai dat YouTube Downloader (ban onedir) bang Inno Setup 6.
; Giai quyet loi "thieu DLL" khi chay exe trong file zip: nguoi dung hay
; bam doi file exe ngay trong cua so zip, hoac chi keo moi file exe ra ngoai,
; nen thu muc _internal (chua python311.dll) khong nam canh exe nua.
; Bo cai dat nay giai nen CA thu muc app vao %LOCALAPPDATA%\YouTubeDownloader
; (dung cho app tu cap nhat sau nay), tao shortcut Desktop, tao muc go cai
; dat trong Control Panel. Khong can quyen admin.
;
; Build tren Windows:
;   ISCC.exe /DMyAppVersion=2.3.3 YouTubeDownloader.iss
; (Tren GitHub Actions, workflow tu truyen tag vao /DMyAppVersion.)
; Ket qua: Output\YouTubeDownloader-Setup-2.3.3.exe

#ifndef MyAppVersion
#define MyAppVersion "2.3.3"
#endif

[Setup]
AppId=YouTubeDownloader-btanh258
AppName=YouTube Downloader
AppVersion={#MyAppVersion}
AppPublisher=btanh258
DefaultDirName={localappdata}\YouTubeDownloader
DefaultGroupName=YouTube Downloader
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=YouTubeDownloader-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\YouTubeDownloader.exe
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\YouTubeDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\YouTube Downloader"; Filename: "{app}\YouTubeDownloader.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\YouTubeDownloader.exe"; Description: "{cm:LaunchProgram,YouTube Downloader}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
