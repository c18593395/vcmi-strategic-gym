# VCMI battle-mode GUI smoke helper v2: screenshot / SendInput keys / PostMessage
# v2: SendInput API (more reliable for SDL) + fallbacks
param(
  [Parameter(Mandatory=$true)][ValidateSet('shot','key','window','focus')][string]$Action,
  [string]$Path = 'D:\Bigdata\hero3_fresh\py\vcmi_shot.png',
  [string]$Key = ''
)

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinAPI {
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern IntPtr FindWindowW(string cls, string title);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern IntPtr PostMessageW(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L; public int T; public int R; public int B; }
  // SendInput
  [DllImport("user32.dll", SetLastError=true)] public static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);
  public const int INPUT_KEYBOARD = 1;
  public const uint KEYEVENTF_KEYUP = 0x0002;
  public const uint KEYEVENTF_UNICODE = 0x0004;
  [StructLayout(LayoutKind.Sequential)]
  public struct INPUT {
    public int type;
    public InputUnion U;
  }
  [StructLayout(LayoutKind.Explicit)]
  public struct InputUnion {
    [FieldOffset(0)] public KEYBDINPUT ki;
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

function Get-VcmiWindow {
  $h = [WinAPI]::FindWindowW('SDL_app', $null)
  if ($h -eq [IntPtr]::Zero) {
    $p = Get-Process VCMI_client -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if ($p) { $h = [IntPtr]$p.MainWindowHandle }
  }
  return $h
}

function Send-Key([IntPtr]$h, [string]$ch) {
  $vk = [byte][char]::ToUpper($ch)
  # Method 1: SendInput
  $down = New-Object WinAPI+INPUT
  $down.type = [WinAPI]::INPUT_KEYBOARD
  $down.U.ki.wVk = $vk
  $up = New-Object WinAPI+INPUT
  $up.type = [WinAPI]::INPUT_KEYBOARD
  $up.U.ki.wVk = $vk
  $up.U.ki.dwFlags = [WinAPI]::KEYEVENTF_KEYUP
  $size = [System.Runtime.InteropServices.Marshal]::SizeOf([WinAPI+INPUT])
  [WinAPI]::SendInput(2, @($down, $up), $size) | Out-Null
}

switch ($Action) {
  'focus' {
    $h = Get-VcmiWindow
    if ($h -eq [IntPtr]::Zero) { Write-Output 'NOWINDOW'; exit 1 }
    [WinAPI]::ShowWindow($h, 9) | Out-Null   # SW_RESTORE
    Start-Sleep -Milliseconds 200
    [WinAPI]::ShowWindow($h, 3) | Out-Null   # SW_MAXIMIZE
    Start-Sleep -Milliseconds 200
    [WinAPI]::SetForegroundWindow($h) | Out-Null
    Start-Sleep -Milliseconds 500
    $fg = [WinAPI]::GetForegroundWindow()
    Write-Output ("FOCUS hWnd=0x{0:X} fg=0x{1:X} match={2}" -f $h.ToInt64(), $fg.ToInt64(), ($fg -eq $h))
  }
  'window' {
    $h = Get-VcmiWindow
    if ($h -eq [IntPtr]::Zero) { Write-Output 'NOWINDOW'; exit 1 }
    $r = New-Object WinAPI+RECT
    [WinAPI]::GetWindowRect($h, [ref]$r) | Out-Null
    $fg = [WinAPI]::GetForegroundWindow()
    Write-Output ("HWND=0x{0:X} FG=0x{1:X} RECT={2},{3},{4},{5}" -f $h.ToInt64(), $fg.ToInt64(), $r.L, $r.T, $r.R, $r.B)
  }
  'key' {
    $h = Get-VcmiWindow
    if ($h -eq [IntPtr]::Zero) { Write-Output 'NOWINDOW'; exit 1 }
    # Ensure window is foreground
    [WinAPI]::SetForegroundWindow($h) | Out-Null
    Start-Sleep -Milliseconds 500
    foreach ($ch in $Key.ToCharArray()) {
      if ($ch -eq ',') { Start-Sleep -Milliseconds 800; continue }
      Send-Key $h ([string]$ch)
      Start-Sleep -Milliseconds 300
    }
    Write-Output "KEYSSENT=$Key"
  }
  'shot' {
    $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($b.X, $b.Y, 0, 0, $bmp.Size)
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    Write-Output "SAVED=$Path"
  }
}
