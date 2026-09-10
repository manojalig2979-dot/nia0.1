$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$AgentDirectory = $PSScriptRoot
$LaunchScript = Join-Path $AgentDirectory 'Launch_Nia.vbs'
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\NIA.lnk")
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$LaunchScript`""
$Shortcut.WorkingDirectory = $AgentDirectory
$Shortcut.Description = "NIA - Your AI Companion"
$Shortcut.Save()
Write-Host "Desktop shortcut created successfully at: $DesktopPath\NIA.lnk"

