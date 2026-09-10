Set WshShell = CreateObject("WScript.Shell")
Set FileSystem = CreateObject("Scripting.FileSystemObject")
AgentDirectory = FileSystem.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = AgentDirectory
WshShell.Run "pythonw.exe nia_gui.py", 0, False

