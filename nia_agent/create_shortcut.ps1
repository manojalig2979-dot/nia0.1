$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$StartupPath = [Environment]::GetFolderPath('Startup')
$AgentDirectory = $PSScriptRoot
$LaunchScript = Join-Path $AgentDirectory 'Launch_Nia.vbs'
$IconPath = Join-Path $AgentDirectory 'nia_icon.ico'

# 1. Desktop Shortcut
$DesktopShortcut = $WshShell.CreateShortcut("$DesktopPath\NIA.lnk")
$DesktopShortcut.TargetPath = "wscript.exe"
$DesktopShortcut.Arguments = "`"$LaunchScript`""
$DesktopShortcut.WorkingDirectory = $AgentDirectory
$DesktopShortcut.Description = "NIA - Your AI Companion"
$DesktopShortcut.IconLocation = "$IconPath,0"
$DesktopShortcut.Save()
Write-Host "Desktop shortcut created successfully at: $DesktopPath\NIA.lnk"

# 2. Windows Startup Shortcut (auto-starts when computer starts/logs in)
$StartupShortcut = $WshShell.CreateShortcut("$StartupPath\NIA.lnk")
$StartupShortcut.TargetPath = "wscript.exe"
$StartupShortcut.Arguments = "`"$LaunchScript`""
$StartupShortcut.WorkingDirectory = $AgentDirectory
$StartupShortcut.Description = "NIA - Your AI Companion (Startup)"
$StartupShortcut.IconLocation = "$IconPath,0"
$StartupShortcut.Save()
Write-Host "Startup shortcut created successfully at: $StartupPath\NIA.lnk"
