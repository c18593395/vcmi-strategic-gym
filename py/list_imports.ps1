# List DLL imports of a PE file and check resolvability. ASCII only.
param(
    [Parameter(Mandatory=$true)][string]$File,
    [string]$ExtraDir
)

$b = [IO.File]::ReadAllBytes($File)
function U16([int]$o){ [BitConverter]::ToUInt16($script:b,$o) }
function U32([int]$o){ [BitConverter]::ToUInt32($script:b,$o) }

$pe = [int](U32 0x3C)
$magic = U16 ($pe + 0x18)
if($magic -eq 0x20B){ $ddBase = $pe + 0x18 + 0x70 }  # PE32+
elseif($magic -eq 0x10B){ $ddBase = $pe + 0x18 + 0x60 }  # PE32
else { throw ("Unknown PE magic 0x{0:X}" -f $magic) }

$impRVA  = [int](U32 ($ddBase + 8))      # data directory[1] = import table
$nsec    = [int](U16 ($pe + 6))
$optSize = [int](U16 ($pe + 0x14))
$sec0    = $pe + 0x18 + $optSize

function RvaToOff([int]$rva){
    for($i=0; $i -lt $script:nsec; $i++){
        $s = $script:sec0 + 40*$i
        $vs = [int](U32 ($s + 8))
        $va = [int](U32 ($s + 12))
        $raw = [int](U32 ($s + 20))
        if($rva -ge $va -and $rva -lt ($va + [Math]::Max($vs,1) + 1)){ return $raw + ($rva - $va) }
    }
    return 0
}

function ReadCStr([int]$off){
    $sb = New-Object System.Text.StringBuilder
    while($script:b[$off] -ne 0){ [void]$sb.Append([char]$script:b[$off]); $off++ }
    return $sb.ToString()
}

$sysDir = [Environment]::SystemDirectory  # C:\Windows\System32
$binDir = Split-Path -Parent $File
$missing = @()
$off = RvaToOff $impRVA
if($off -eq 0){ throw "No import table found" }

while($true){
    $nameRva = [int](U32 ($off + 12))
    if($nameRva -eq 0){ break }
    $dll = ReadCStr (RvaToOff $nameRva)
    $ok = (Test-Path (Join-Path $binDir $dll)) -or (Test-Path (Join-Path $sysDir $dll))
    if(-not $ok -and $ExtraDir){ $ok = Test-Path (Join-Path $ExtraDir $dll) }
    $tag = if($ok){ "OK     " } else { "MISSING" }
    Write-Output ("{0} {1}" -f $tag, $dll)
    if(-not $ok){ $missing += $dll }
    $off += 20
}
Write-Output ("SUMMARY missing={0}" -f $missing.Count)
