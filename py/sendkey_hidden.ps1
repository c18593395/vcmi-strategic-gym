# Hidden launcher: hide caller window, focus VCMI, send keys
# Run from: Start-Process powershell.exe -WindowStyle Hidden -File this.ps1
param(
  [Parameter(Mandatory=$true)][string]$Keys   # e.g. "N,ENTER" or "N,X,B"
)

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Kbd {
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr FindWindowW(string c, string t);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  public const uint KEYEVENTF_KEYUP = 2;
  public const uint KEYEVENTF_EXTENDEDKEY = 1;
  public const int SW_SHOWMINIMIZED = 6;
  public const int SW_SHOWNORMAL = 1;
}
"@

# Hide our own window if any
$myhwnd = [Kbd]::FindWindowW('ConsoleWindowClass', $null)
if($myhwnd -ne [IntPtr]::Zero){
    [Kbd]::ShowWindow($myhwnd, [Kbd]::SW_SHOWMINIMIZED) | Out-Null
}

# Find VCMI
$hwnd = [Kbd]::FindWindowW('SDL_app', $null)
if($hwnd -eq [IntPtr]::Zero){
    $p = Get-Process VCMI_client -ErrorAction SilentlyContinue | Select-Object -First 1
    if($p){ $hwnd = [IntPtr]$p.MainWindowHandle }
}
if($hwnd -eq [IntPtr]::Zero){ Write-Output 'NOWINDOW'; exit 1 }

# Restore + focus
[Kbd]::ShowWindow($hwnd, [Kbd]::SW_SHOWNORMAL) | Out-Null
Start-Sleep -Milliseconds 400
[Kbd]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 800

foreach($k in $Keys.ToCharArray()){
    if($k -eq ',') { Start-Sleep -Milliseconds 1200; continue }
    $vk = [byte][char]::ToUpper($k)
    [Kbd]::keybd_event($vk, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 50
    [Kbd]::keybd_event($vk, 0, [Kbd]::KEYEVENTF_KEYUP, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 500
}
Write-Output "KEYS SENT: $Keys"
