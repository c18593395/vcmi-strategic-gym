# 0911 根因链排查: 按局归因 GUARD_DONE / TOWNSTALL / TOWN_CAPTURE / MINE
$all = Get-Content 'D:\Bigdata\hero3_fresh\train_loop.log'
$start = 0
for ($i = $all.Count - 1; $i -ge 0; $i--) {
    if ($all[$i] -match 'Loaded train state.*step=621725') { $start = $i; break }
}
$w = $all[$start .. ($all.Count - 1)]
$eps = @()
$cur = @{}
foreach ($line in $w) {
    if ($line -match '\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=([-\d.]+) err=(\w+)') {
        $eps += [pscustomobject]@{
            map = ($matches[1] -replace '_adventure_', ''); steps = [int]$matches[2]; secs = [int]$matches[3]; r = [double]$matches[4];
            gd = $cur['gd']; ts = $cur['ts']; cap = $cur['cap']; mn = $cur['mi']; gw = $cur['gw']
        }
        $cur = @{}
    }
    elseif ($line -match '\[GUARD_DONE\]') { if ($null -eq $cur['gd']) { $cur['gd'] = 0 }; $cur['gd']++ }
    elseif ($line -match '\[TOWNSTALL\]') { if ($null -eq $cur['ts']) { $cur['ts'] = 0 }; $cur['ts']++ }
    elseif ($line -match '\[TOWN_CAPTURE\]') { if ($null -eq $cur['cap']) { $cur['cap'] = 0 }; $cur['cap']++ }
    elseif ($line -match '\[MINE\].*fought & won') { if ($null -eq $cur['mi']) { $cur['mi'] = 0 }; $cur['mi']++ }
    elseif ($line -match '\[GUARD\].*fought & won') { if ($null -eq $cur['gw']) { $cur['gw'] = 0 }; $cur['gw']++ }
}
$eps | ForEach-Object {
    Write-Output ('{0,-28} steps={1,3} r={2,7} GD={3} TS={4} CAP={5} MINE={6} GW={7}' -f $_.map, $_.steps, $_.r, [string]$_.gd, [string]$_.ts, [string]$_.cap, [string]$_.mn, [string]$_.gw)
}
# 汇总
$byMap = $eps | Group-Object { $_.map -replace '_\d+$', '' } | ForEach-Object {
    $n = $_.Count
    $gd = @($_.Group | Where-Object { $_.gd }).Count
    $ts = ($_.Group | Measure-Object -Property ts -Sum).Sum
    $cap = ($_.Group | Measure-Object -Property cap -Sum).Sum
    $gw = ($_.Group | Measure-Object -Property gw -Sum).Sum
    [pscustomobject]@{ map = $_.Name; eps = $n; gd_eps = $gd; ts_tot = $ts; cap_tot = $cap; gw_tot = $gw }
}
Write-Output '--- SUMMARY (map-family) ---'
$byMap | ForEach-Object { Write-Output ('{0,-22} eps={1} GD_eps={2} TS_tot={3} CAP={4} GW={5}' -f $_.map, $_.eps, $_.gd_eps, $_.ts_tot, $_.cap_tot, $_.gw_tot) }
