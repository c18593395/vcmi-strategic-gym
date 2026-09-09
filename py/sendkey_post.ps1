# Send keys via PostMessageW/WM_KEYDOWN to VCMI window
param(
  [Parameter(Mandatory=$true)][string]$Key
)

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Msg {
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern IntPtr FindWindowW(string cls, string title);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern IntPtr PostMessageW(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint uCode, uint uMapType);
  public const uint WM_KEYDOWN = 0x0100;
  public const uint WM_KEYUP   = 0x0101;
  public const uint WM_CHAR    = 0x0102;
}
"@

$hwnd = [Msg]::FindWindowW('SDL_app', $null)
if($hwnd -eq [IntPtr]::Zero){
    $p = Get-Process VCMI_client -ErrorAction SilentlyContinue | Select-Object -First 1
    if($p){ $hwnd = [IntPtr]$p.MainWindowHandle }
}
if($hwnd -eq [IntPtr]::Zero){ Write-Output 'NOWINDOW'; exit 1 }
Write-Output ("HWND=0x{0:X}" -f $hwnd.ToInt64())

foreach($ch in $Key.ToCharArray()){
    if($ch -eq ',') { Start-Sleep -Milliseconds 800; continue }
    $vk = [int16][int][byte][char]::ToUpper($ch)
    $scan = [Msg]::MapVirtualKey([UInt32]$vk, 0)
    $lParamDown = [IntPtr](($scan -shl 16) -bor 1)
    $lParamUp   = [IntPtr](($scan -shl 16) -bor (1 -shl 30) -bor (1 -shl 31))
    $wparam = [IntPtr]$vk
    Write-Output ("VK=0x{0:X} SCAN=0x{1:X}" -f $vk, $scan)
    [Msg]::PostMessageW($hwnd, [Msg]::WM_KEYDOWN, $wparam, $lParamDown) | Out-Null
    Start-Sleep -Milliseconds 200
    if($vk -ge 0x30 -and $vk -le 0x7A){
        [Msg]::PostMessageW($hwnd, [Msg]::WM_CHAR, [IntPtr]$ch, $lParamDown) | Out-Null
        Start-Sleep -Milliseconds 100
    }
    [Msg]::PostMessageW($hwnd, [Msg]::WM_KEYUP, $wparam, $lParamUp) | Out-Null
    Start-Sleep -Milliseconds 400
}
Write-Output "DONE"
