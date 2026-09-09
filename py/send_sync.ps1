# Send Enter via SendMessage (synchronous) to VCMI SDL window
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class SM {
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern IntPtr FindWindowW(string c, string t);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern IntPtr SendMessageW(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern IntPtr PostMessageW(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint c, uint t);
  public const uint WM_KEYDOWN = 0x0100;
  public const uint WM_KEYUP   = 0x0101;
  public const uint WM_CHAR    = 0x0102;
  public const uint WM_SYSCOMMAND = 0x0112;
  public const uint WM_COMMAND = 0x0111;
}
"@

$hwnd = [SM]::FindWindowW('SDL_app', $null)
if($hwnd -eq [IntPtr]::Zero){
    $p = Get-Process VCMI_client -ErrorAction SilentlyContinue | Select-Object -First 1
    if($p){ $hwnd = [IntPtr]$p.MainWindowHandle }
}
Write-Output ("HWND=0x{0:X}" -f $hwnd.ToInt64())

# 1) Try SendMessage Enter
$vk = 0x0D
$scan = [SM]::MapVirtualKey($vk, 0)
$ld = [IntPtr](($scan -shl 16) -bor 1)
$lu = [IntPtr](($scan -shl 16) -bor 0xC0000001)
$r1 = [SM]::SendMessageW($hwnd, [SM]::WM_KEYDOWN, [IntPtr]$vk, $ld)
Write-Output ("SendMessage WM_KEYDOWN ret=0x{0:X}" -f $r1.ToInt64())
$r2 = [SM]::SendMessageW($hwnd, [SM]::WM_CHAR, [IntPtr]$vk, $ld)
Write-Output ("SendMessage WM_CHAR ret=0x{0:X}" -f $r2.ToInt64())
$r3 = [SM]::SendMessageW($hwnd, [SM]::WM_KEYUP, [IntPtr]$vk, $lu)
Write-Output ("SendMessage WM_KEYUP ret=0x{0:X}" -f $r3.ToInt64())

Write-Output '---'
# 2) Try SendMessage 'N'
$vk2 = 0x4E
$scan2 = [SM]::MapVirtualKey($vk2, 0)
$ld2 = [IntPtr](($scan2 -shl 16) -bor 1)
$lu2 = [IntPtr](($scan2 -shl 16) -bor 0xC0000001)
$r4 = [SM]::SendMessageW($hwnd, [SM]::WM_KEYDOWN, [IntPtr]$vk2, $ld2)
Write-Output ("SendMessage N ret=0x{0:X}" -f $r4.ToInt64())
$r5 = [SM]::SendMessageW($hwnd, [SM]::WM_CHAR, [IntPtr][int][char]'n', $ld2)
Write-Output ("SendMessage WM_CHAR 'n' ret=0x{0:X}" -f $r5.ToInt64())
$r6 = [SM]::SendMessageW($hwnd, [SM]::WM_KEYUP, [IntPtr]$vk2, $lu2)
Write-Output ("SendMessage N UP ret=0x{0:X}" -f $r6.ToInt64())
