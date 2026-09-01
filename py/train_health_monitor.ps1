<#
.SYNOPSIS
  OPS-20260828-02 训练日志健康监控脚本
.DESCRIPTION
  - 每 2 分钟循环 1 轮（可用 -Loop $false 只跑 1 轮用于测试）
  - 每轮打印：时间戳 + train_loop.log 文件年龄 + 最近 1 局 r/obs_nz
  - 红警：LastWriteTime 超过 20 分钟没更新
  - 黄警：最近 3 局 r 连续 < -100
  - 可 Ctrl+C 中断（已注册清理）
.PARAMETER IntervalSec
  每轮循环间隔秒数，默认 120。
.PARAMETER Loop
  是否循环运行，默认 $true。
.PARAMETER LogPath
  train_loop.log 路径。
.PARAMETER AlertPath
  告警日志路径。
#>
param(
    [int]$IntervalSec = 120,
    [bool]$Loop = $true,
    [string]$LogPath   = "D:\Bigdata\hero3_fresh\train_loop.log",
    [string]$AlertPath = "D:\Bigdata\hero3_fresh\py\monitor_alerts.log"
)

$ErrorActionPreference = "Continue"

# --- Ctrl+C 处理 ---
$global:MonitorRunning = $true
function Stop-Monitor {
    $global:MonitorRunning = $false
    Write-Host "`n[MONITOR] 收到中断，正在退出..." -ForegroundColor Cyan
}
try {
    [Console]::TreatControlCAsInput = $false
} catch {
    # 非交互 / 无控制台句柄时忽略（例如 Start-Job、CI、nohup 场景）
}
# Ctrl+C 不注册断点：由 PowerShell 内部机制把当前语句抛出异常后走 finally 清理即可

function Write-AlertLine {
    param([string]$Level, [string]$Msg)
    $ts  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$Level] $ts $Msg"
    switch ($Level) {
        "TRAIN RED"    { Write-Host $line -ForegroundColor Red }
        "TRAIN YELLOW" { Write-Host $line -ForegroundColor Yellow }
        default        { Write-Host $line }
    }
    # 追加告警日志
    try {
        Add-Content -Path $AlertPath -Value $line -Encoding UTF8
    } catch {
        Write-Warning "无法写入告警日志 $AlertPath : $_"
    }
}

function Get-LastEpRows {
    param([string]$Path, [int]$LastN = 50)
    if (-not (Test-Path -LiteralPath $Path)) { return @() }
    # 读最后 ~20KB，避免超大日志加载慢
    $fi = Get-Item -LiteralPath $Path
    $bytes = [Math]::Min(128KB, $fi.Length)
    $fs  = [System.IO.FileStream]::new($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    try {
        $fs.Seek($fi.Length - $bytes, [System.IO.SeekOrigin]::Begin) | Out-Null
        $buf = New-Object byte[] $bytes
        $read = $fs.Read($buf, 0, $bytes)
        $txt = [System.Text.Encoding]::UTF8.GetString($buf, 0, $read)
    } finally {
        $fs.Dispose()
    }
    # 拆成行，再挑 ep_steps=... r=...
    $lines = $txt -split "`r?`n"
    $epRowsFound = foreach ($l in $lines) {
        # 形如 "  ep_steps=200 r=32.40 act=[...] obs_nz=375"
        if ($l -match 'ep_steps=(\d+)\s+r=([-+]?\d*\.?\d+).*?obs_nz=(\d+)') {
            [PSCustomObject]@{
                ep_steps = [int]$Matches[1]
                r        = [double]$Matches[2]
                obs_nz   = [int]$Matches[3]
                raw      = $l.Trim()
            }
        }
    }
    # 取最后 LastN 条
    if (-not $epRowsFound -or $epRowsFound.Count -eq 0) { return @() }
    $start = [Math]::Max(0, $epRowsFound.Count - $LastN)
    return @($epRowsFound[$start..($epRowsFound.Count-1)])
}

function Do-OneRound {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    if (-not (Test-Path -LiteralPath $LogPath)) {
        Write-Host "[$ts] log_age=MISSING  last_r=N/A  last_obs_nz=N/A" -ForegroundColor Gray
        Write-AlertLine -Level "TRAIN RED" -Msg "train_loop.log 不存在，训练未启动或路径错误"
        return
    }

    $fi = Get-Item -LiteralPath $LogPath
    $age = (Get-Date) - $fi.LastWriteTime
    $ageStr = if ($age.TotalMinutes -ge 60) {
        "$([int]$age.TotalHours)h$($age.Minutes)m$($age.Seconds)s"
    } elseif ($age.TotalSeconds -ge 60) {
        "$($age.Minutes)m$($age.Seconds)s"
    } else {
        "$($age.Seconds)s"
    }

    # 最近 1 局 r / obs_nz
    $epRows = Get-LastEpRows -Path $LogPath -LastN 50
    if ($epRows.Count -gt 0) {
        $last = $epRows[-1]
        $lineOut = "[$ts] log_age=$ageStr  last_r=$($last.r.ToString('0.00'))  last_obs_nz=$($last.obs_nz)"
    } else {
        $lineOut = "[$ts] log_age=$ageStr  last_r=N/A  last_obs_nz=N/A (暂无 ep_steps 行)"
    }
    Write-Host $lineOut

    # 红警：20 分钟无更新
    if ($age.TotalMinutes -ge 20) {
        Write-AlertLine -Level "TRAIN RED" -Msg ("train_loop.log {0:0.0} 分钟无更新，训练可能死; file_size={1} bytes" -f $age.TotalMinutes, $fi.Length)
    }

    # 黄警：最近 3 局 r 连续 < -100
    if ($epRows.Count -ge 3) {
        $tail3 = $epRows[($epRows.Count-3)..($epRows.Count-1)]
        $bad = $tail3 | Where-Object { $_.r -lt -100 }
        if ($bad.Count -eq 3) {
            $rs = ($tail3.r | ForEach-Object { $_.ToString('0.00') }) -join ','
            Write-AlertLine -Level "TRAIN YELLOW" -Msg "连续 3 局大负 r=[$rs]"
        }
    }
}

# --- 主循环（Ctrl+C 会触发 finally） ---
Write-Host "[MONITOR] start @ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "[MONITOR] log   = $LogPath" -ForegroundColor Cyan
Write-Host "[MONITOR] alert = $AlertPath ; interval=${IntervalSec}s ; loop=$Loop" -ForegroundColor Cyan

try {
    do {
        try {
            Do-OneRound
        } catch {
            Write-Host "[MONITOR EXCEPTION] $_" -ForegroundColor DarkRed
        }
        if (-not $Loop) { break }
        # 可中断 sleep：每 200ms 醒一次检查 $MonitorRunning
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        while ($sw.Elapsed.TotalSeconds -lt $IntervalSec -and $global:MonitorRunning) {
            Start-Sleep -Milliseconds 200
            if ([Console]::KeyAvailable) {
                $ki = [Console]::ReadKey($true)
                if ($ki.Modifiers -band [ConsoleModifiers]::Control -and $ki.Key -eq [ConsoleKey]::C) {
                    Stop-Monitor
                }
            }
        }
    } while ($Loop -and $global:MonitorRunning)
} finally {
    Write-Host "[MONITOR] exited @ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
}
