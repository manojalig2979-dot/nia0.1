Set WshShell = CreateObject("WScript.Shell")
Set FileSystem = CreateObject("Scripting.FileSystemObject")
AgentDirectory = FileSystem.GetParentFolderName(WScript.ScriptFullName)
RootDirectory = FileSystem.GetParentFolderName(AgentDirectory)
VenvPython = RootDirectory & "\.venv\Scripts\pythonw.exe"

If FileSystem.FileExists(VenvPython) Then
    PythonCmd = """" & VenvPython & """"
Else
    PythonCmd = "pythonw.exe"
End If

WshShell.CurrentDirectory = AgentDirectory
WshShell.Run PythonCmd & " nia_gui.py", 0, False
