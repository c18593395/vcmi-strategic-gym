# SendInput keyboard injection - run from a HIDDEN PowerShell process
# Minimizes parent console, focuses VCMI, then sends key via SendInput
param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('N','X','B','ENTER','SPACE','ESC','TAB','F1','F2','LEFT','RIGHT','UP','DOWN','DEL')]
  [string]$Key
)

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class H {
  [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr FindWindowW(string c, string t);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll", SetLastError=true)]
  public static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);
  public const int INPUT_KEYBOARD = 1;
  public const uint KEYEVENTF_KEYUP = 0x0002;
  public const int SW_MINIMIZE = 6;
  public const int SW_RESTORE = 9;
  [StructLayout(LayoutKind.Sequential)] public struct INPUT { public int type; public KEYBDINPUT ki; }
  [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT { public ushort wVk; public ushort wScan; public uint dwFlags; public uint time; public IntPtr dwExtraInfo; }
}
"@

# Minimize our own console window
$console = [H]::GetConsoleWindow()
if($console -ne [IntPtr]::Zero){ [H]::ShowWindow($console, [H]::SW_MINIMIZE) | Out-Null }
Start-Sleep -Milliseconds 300

# Focus VCMI
$hwnd = [H]::FindWindowW('SDL_app', $null)
if($hwnd -eq [IntPtr]::Zero){
    $p = Get-Process VCMI_client -ErrorAction SilentlyContinue | Select-Object -First 1
    if($p){ $hwnd = [IntPtr]$p.MainWindowHandle }
}
Write-Output ("HWND=0x{0:X}" -f $hwnd.ToInt64())
[H]::ShowWindow($hwnd, [H]::SW_RESTORE) | Out-Null
Start-Sleep -Milliseconds 400
[H]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 800

# VK map
$vkMap = @{
  'ENTER'=0x0D; 'SPACE'=0x20; 'ESC'=0x1B; 'TAB'=0x09
  'UP'=0x26; 'DOWN'=0x28; 'LEFT'=0x25; 'RIGHT'=0x27
  'F1'=0x70; 'F2'=0x71; 'DEL'=0x2E
}
if($vkMap.ContainsKey($Key)){ $vk = [ushort]$vkMap[$Key] }
else { $vk = [ushort][byte][char]::ToUpper($Key) }

Write-Output ("Sending VK=0x{0:X} ({1})" -f $vk, $Key)

# Build INPUT array
$size = [System.Runtime.InteropServices.Marshal]::SizeOf([H+INPUT])
$inputs = New-Object H+INPUT[] 2
$inputs[0].type = [H]::INPUT_KEYBOARD
$inputs[0].ki.wVk = $vk
$inputs[1].type = [H]::INPUT_KEYBOARD
$inputs[1].ki.wVk = $vk
$inputs[1].ki.dwFlags = [H]::KEYEVENTF_KEYUP

$sent = [H]::SendInput(2, $inputs, $size)
Write-Output ("SendInput returned $sent")
