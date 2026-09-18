Set oShell = CreateObject("WScript.Shell")
oShell.Run "wsl.exe -d Ubuntu sleep infinity", 0, False
