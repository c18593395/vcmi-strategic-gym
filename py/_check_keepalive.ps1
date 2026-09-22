$n = @(Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" | Where-Object { $_.CommandLine -like '*sleep*infinity*' }).Count
Write-Output "keepalive_count=$n"
if ($n -lt 1) {
    Start-Process wsl.exe -ArgumentList '-d','Ubuntu','sleep','infinity' -WindowStyle Hidden
    Start-Sleep -Seconds 3
    $n2 = @(Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" | Where-Object { $_.CommandLine -like '*sleep*infinity*' }).Count
    Write-Output "restarted, keepalive_count=$n2"
}
