# Bring VCMI_client window to foreground
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern IntPtr FindWindowW(string cls, string title);
}
"@

$p = Get-Process VCMI_client -ErrorAction SilentlyContinue
if(-not $p){
    Write-Output "VCMI_client not running"
    exit 1
}
Write-Output ("PID={0} HWND={1} Title='{2}' Resp={3}" -f $p.Id, $p.MainWindowHandle, $p.MainWindowTitle, $p.Responding)

$hwnd = $p.MainWindowHandle
if($hwnd -eq 0){
    # Try find SDL window by title
    $hwnd = [Win32]::FindWindowW("SDL_app", $null)
    if($hwnd -eq [IntPtr]::Zero){
        Write-Output "Could not find window handle"
        exit 1
    }
    Write-Output ("Found via FindWindowW: {0}" -f $hwnd)
}

[Win32]::ShowWindow($hwnd, 9) | Out-Null    # SW_RESTORE
Start-Sleep -Milliseconds 300
[Win32]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 300
[Win32]::ShowWindow($hwnd, 1) | Out-Null    # SW_SHOWNORMAL
Start-Sleep -Milliseconds 500
[Win32]::SetForegroundWindow($hwnd) | Out-Null
Write-Output "Focused VCMI window"
