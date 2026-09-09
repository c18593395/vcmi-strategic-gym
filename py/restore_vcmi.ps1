# Restore hidden/minimized VCMI SDL window
Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public class F {
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr FindWindowW(string c, string t);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, System.Text.StringBuilder sb, int nMax);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
}
"@

$hwnd = [F]::FindWindowW('SDL_app', $null)
Write-Output ("FindWindowW SDL_app = 0x{0:X}" -f $hwnd.ToInt64())
if($hwnd -eq [IntPtr]::Zero){
    $p = Get-Process VCMI_client -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if($p){ $hwnd = [IntPtr]$p.MainWindowHandle; Write-Output ("From process PID=$($p.Id) HWND=0x{0:X}" -f $hwnd.ToInt64()) }
}
if($hwnd -eq [IntPtr]::Zero){ Write-Output 'NO VCMI WINDOW'; exit 1 }

$vis = [F]::IsWindowVisible($hwnd)
Write-Output ("IsWindowVisible=$vis")
$txt = New-Object System.Text.StringBuilder 256
[F]::GetWindowTextW($hwnd, $txt, 256) | Out-Null
Write-Output ("Title: " + $txt.ToString())

[F]::ShowWindow($hwnd, 9) | Out-Null   # SW_RESTORE
Start-Sleep -Milliseconds 300
[F]::ShowWindow($hwnd, 1) | Out-Null   # SW_SHOWNORMAL
Start-Sleep -Milliseconds 300
[F]::SetForegroundWindow($hwnd) | Out-Null
Write-Output "RESTORED & FOCUSED"
