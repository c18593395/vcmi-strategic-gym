# 新栈窗口 [GUARD_DONE] 计数
$all = Get-Content 'D:\Bigdata\hero3_fresh\train_loop.log'
$start = 0
for ($i = $all.Count - 1; $i -ge 0; $i--) {
    if ($all[$i] -match 'Loaded train state.*step=621725') { $start = $i; break }
}
$w = $all[$start .. ($all.Count - 1)]
$gd = @($w | Select-String -Pattern '\[GUARD_DONE\]')
Write-Output ('GUARD_DONE_in_window=' + $gd.Count)
$gd | Select-Object -Last 5 | ForEach-Object { Write-Output ('  ' + $_.Line.Trim()) }
