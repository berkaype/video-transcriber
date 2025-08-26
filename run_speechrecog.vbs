Set WshShell = CreateObject("WScript.Shell")
scriptPath = CreateObject("Scripting.FileSystemObject").GetAbsolutePathName("SpeechRecog.py")
WshShell.Run "python """ & scriptPath & """", 0, False
