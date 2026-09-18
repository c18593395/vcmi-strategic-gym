# homm3 keepalive 守护: 检测 wsl.exe sleep infinity 进程, 丢失则拉起 (计划任务每 5 分钟调用)
$existing = Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" |
    Where-Object { $_.CommandLine -like '*sleep*infinity*' }
if (-not $existing) {
    Start-Process wsl.exe -ArgumentList '-d', 'Ubuntu', 'sleep', 'infinity' -WindowStyle Hidden
}
