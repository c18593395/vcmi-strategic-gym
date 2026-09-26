$PS1 = 'C:\Users\Administrator\AppData\Local\hermes\profiles\hero3\scripts\p015_recheck.ps1'
$cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$PS1`""
schtasks /create /tn "p015_recheck_1425" /tr $cmd /sc once /st 14:25 /f
schtasks /query /tn "p015_recheck_1425" /fo list
