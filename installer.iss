[Setup]
AppId={{D7ACD694-2A16-47DD-8CF5-A49BF6B72BB1}
AppName=微信好友助手
AppVersion=1.0.0
DefaultDirName={localappdata}\Programs\WeChatFriendAssistant
DefaultGroupName=微信好友助手
PrivilegesRequired=lowest
OutputDir=installer-output
OutputBaseFilename=WeChatFriendAssistant-Setup-1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\WeChatFriendAssistant.exe
CloseApplications=yes

[Languages]
Name: "default"; MessagesFile: "compiler:Default.isl"

[Messages]
SetupWindowTitle=安装 - %1
WelcomeLabel1=欢迎安装 [name]
WelcomeLabel2=将为你安装 [name/ver]。程序已包含 Python 运行环境。
ButtonNext=下一步(&N) >
ButtonBack=< 上一步(&B)
ButtonInstall=安装(&I)
ButtonCancel=取消
ButtonFinish=完成(&F)
SelectDirLabel3=请选择安装位置。
FinishedHeadingLabel=安装完成
FinishedLabelNoIcons=[name] 已安装完成。

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: checkedonce

[Files]
Source: "dist\WeChatFriendAssistant\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\微信好友助手"; Filename: "{app}\WeChatFriendAssistant.exe"
Name: "{autodesktop}\微信好友助手"; Filename: "{app}\WeChatFriendAssistant.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\WeChatFriendAssistant.exe"; Description: "启动微信好友助手"; Flags: nowait postinstall skipifsilent
