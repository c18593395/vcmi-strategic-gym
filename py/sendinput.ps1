# SendInput keyboard injection - updates kernel key state (GetAsyncKeyState sees it)
param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('N','X','B','ENTER','SPACE','ESC','TAB','F1','F2','LEFT','RIGHT','UP','DOWN','DEL')]
  [string]$Key
)

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class SI {
  [DllImport("user32.dll", SetLastError=true)]
  public static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern IntPtr FindWindowW(string c, string t);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);

  public const int INPUT_KEYBOARD = 1;
  public const uint KEYEVENTF_KEYUP = 0x0002;
  public const uint KEYEVENTF_SCANCODE = 0x0008;
  public const int SW_SHOWNORMAL = 1;
  public const int SW_RESTORE = 9;

  [StructLayout(LayoutKind.Sequential)]
  public struct INPUT {
    public int type;
    public KEYBDINPUT ki;
  }
  [StructLayout(LayoutKind.Sequential)]
  public struct KEYBDINPUT {
    public ushort wVk;
    public ushort wScan;
    public uint dwFlags;
    public uint time;
    public IntPtr dwExtraInfo;
  }
}
"@

$vkMap = @{
  'ENTER'=0x0D; 'SPACE'=0x20; 'ESC'=0x1B; 'TAB'=0x09; 'DEL'=0x2E
  'UP'=0x26; 'DOWN'=0x28; 'LEFT'=0x25; 'RIGHT'=0x27
  'F1'=0x70; 'F2'=0x71
}
if($vkMap.ContainsKey($Key)){ $vk = [ushort]$vkMap[$Key] }
else { $vk = [ushort][byte][char]::ToUpper($Key) }

# Ensure VCMI is foreground
$hwnd = [SI]::FindWindowW('SDL_app', $null)
if($hwnd -eq [IntPtr]::Zero){
    $p = Get-Process VCMI_client -ErrorAction SilentlyContinue | Select-Object -First 1
    if($p){ $hwnd = [IntPtr]$p.MainWindowHandle }
}
Write-Output ("HWND=0x{0:X} VK=0x{1:X}" -f $hwnd.ToInt64(), $vk)

if($hwnd -ne [IntPtr]::Zero){
    [SI]::ShowWindow($hwnd, [SI]::SW_RESTORE) | Out-Null
    Start-Sleep -Milliseconds 200
    [SI]::SetForegroundWindow($hwnd) | Out-Null
    Start-Sleep -Milliseconds 500
}

$size = [System.Runtime.InteropServices.Marshal]::SizeOf([SI+INPUT])
Write-Output ("INPUT size=$size")

$inputs = New-Object SI+INPUT[] 2
$inputs[0].type = [SI]::INPUT_KEYBOARD
$inputs[0].ki.wVk = $vk
$inputs[1].type = [SI]::INPUT_KEYBOARD
$inputs[1].ki.wVk = $vk
$inputs[1].ki.dwFlags = [SI]::KEYEVENTF_KEYUP

$sent = [SI]::SendInput(2, $inputs, $size)
Write-Output ("SendInput returned $sent")
if($sent -eq 0){
    $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
    Write-Output ("Win32Error=$err")
}
