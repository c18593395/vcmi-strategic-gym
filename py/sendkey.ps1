# Send specific key via PostMessageW
param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('N','X','B','ENTER','SPACE','ESC','TAB','F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','LEFT','RIGHT','UP','DOWN')]
  [string]$Key
)

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class M2 {
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern IntPtr FindWindowW(string c, string t);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern IntPtr PostMessageW(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint c, uint t);
  public const uint KD=0x100, KU=0x101;
}
"@

# Map key name to VK code
$vkMap = @{
  'ENTER' = 0x0D; 'SPACE' = 0x20; 'ESC' = 0x1B; 'TAB' = 0x09
  'UP' = 0x26; 'DOWN' = 0x28; 'LEFT' = 0x25; 'RIGHT' = 0x27
  'F1' = 0x70; 'F2' = 0x71; 'F3' = 0x72; 'F4' = 0x73; 'F5' = 0x74
  'F6' = 0x75; 'F7' = 0x76; 'F8' = 0x77; 'F9' = 0x78; 'F10' = 0x79
}
if($vkMap.ContainsKey($Key)){
    $vk = [int]$vkMap[$Key]
} else {
    $vk = [int][byte][char]::ToUpper($Key)
}

$hwnd = [M2]::FindWindowW('SDL_app', $null)
if($hwnd -eq [IntPtr]::Zero){
    $p = Get-Process VCMI_client -ErrorAction SilentlyContinue | Select-Object -First 1
    if($p){ $hwnd = [IntPtr]$p.MainWindowHandle }
}
if($hwnd -eq [IntPtr]::Zero){ Write-Output 'NOWINDOW'; exit 1 }

$scan = [M2]::MapVirtualKey([UInt32]$vk, 0)
$lParamDown = [IntPtr](($scan -shl 16) -bor 1)
$lParamUp   = [IntPtr](($scan -shl 16) -bor (1 -shl 30) -bor (1 -shl 31))
$wparam = [IntPtr]$vk

Write-Output ("HWND=0x{0:X} VK=0x{1:X} SCAN=0x{2:X} Key={3}" -f $hwnd.ToInt64(), $vk, $scan, $Key)
[M2]::PostMessageW($hwnd, [M2]::KD, $wparam, $lParamDown) | Out-Null
Start-Sleep -Milliseconds 300
[M2]::PostMessageW($hwnd, [M2]::KU, $wparam, $lParamUp) | Out-Null
Write-Output "SENT"
