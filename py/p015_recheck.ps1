# P-015 N=16 long-stability 12h recheck - pure observation (no git, no code changes).
# Flow: ssh remote probe -> log -> kanban comment handoff.
$ErrorActionPreference = "Continue"
$ssh = "C:\Windows\System32\OpenSSH\ssh.exe"
$key = "C:\Users\Administrator\.ssh\id_rsa"
$hermes = "C:\Users\Administrator\AppData\Local\hermes\bin\hermes.exe"
$logDir = "C:\Users\Administrator\AppData\Local\hermes\profiles\hero3\cache\scratch"
$log = Join-Path $logDir "p015_recheck.log"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

$env:HERMES_KANBAN_BOARD = "hero3-collab"
$env:HERMES_DISABLE_LAZY_INSTALLS = "1"

Add-Content $log "===== P-015 recheck $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ====="

# remote probe (script already on server, no local pipe/quote issues)
$out = & $ssh -i $key -o IdentitiesOnly=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@172.16.2.40 "/root/p015_probe.sh" 2>&1
$out | ForEach-Object { Add-Content $log $_ }

# one-line kanban handoff (auto, no agent)
$nr   = ($out | Select-String 'NRestarts=' | ForEach-Object { $_.Line }) -join " "
$runs = ($out | Select-String 'runners=' | ForEach-Object { $_.Line }) -join " "
$step = ($out | Select-String 'step\d+' | Select-Object -First 1 | ForEach-Object { $_.Line })
$unit = ($out | Select-String 'unit=' | ForEach-Object { $_.Line }) -join " "

$msg = "hero3 auto-recheck $(Get-Date -Format 'HH:mm'): $unit | $nr | $runs | last step: $step | full log: $log (baseline 05:35 step1710891 ep=339 NRestarts=0; 12h mark=14:25, PASS if NRestarts still 0 + runners ~16 + step advanced)."

Add-Content $log "-- comment --"
& $hermes kanban comment t_816a46bf $msg 2>&1 | ForEach-Object { Add-Content $log $_ }
Add-Content $log "DONE"
Write-Output "P015 recheck complete. Comment: $msg"
