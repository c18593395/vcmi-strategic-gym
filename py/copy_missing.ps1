# Scan all PE files in a bin dir, collect actually-missing DLLs (not in bin or System32),
# then copy each from source dir if present there.
param(
    [Parameter(Mandatory=$true)][string]$BinDir,
    [Parameter(Mandatory=$true)][string]$SourceDir
)

$sys = [Environment]::SystemDirectory
$downlevel = Join-Path $sys 'downlevel'
$missing = @{}

$files = Get-ChildItem $BinDir -Include *.exe,*.dll -File

foreach($f in $files){
    $b = [IO.File]::ReadAllBytes($f.FullName)
    function U16([int]$o){ [BitConverter]::ToUInt16($script:b,$o) }
    function U32([int]$o){ [BitConverter]::ToUInt32($script:b,$o) }

    $pe = [int](U32 0x3C)
    $magic = U16 ($pe + 0x18)
    if($magic -eq 0x20B){ $ddBase = $pe + 0x18 + 0x70 }
    elseif($magic -eq 0x10B){ $ddBase = $pe + 0x18 + 0x60 }
    else { continue }

    $impRVA  = [int](U32 ($ddBase + 8))
    $nsec    = [int](U16 ($pe + 6))
    $optSize = [int](U16 ($pe + 0x14))
    $sec0    = $pe + 0x18 + $optSize

    function RvaToOff([int]$rva){
        for($i=0; $i -lt $script:nsec; $i++){
            $s = $script:sec0 + 40*$i
            $vs = [int](U32 ($s + 8))
            $va = [int](U32 ($s + 12))
            $raw = [int](U32 ($s + 20))
            if($rva -ge $va -and $rva -lt ($va + [Math]::Max($vs,1)+1)){
                return $raw + ($rva - $va)
            }
        }
        return 0
    }
    function ReadCStr([int]$off){
        $sb = New-Object Text.StringBuilder
        while($script:b[$off] -ne 0){ [void]$sb.Append([char]$script:b[$off]); $off++ }
        return $sb.ToString()
    }

    $off = RvaToOff $impRVA
    if($off -eq 0){ continue }

    while($true){
        $nameRva = [int](U32 ($off + 12))
        if($nameRva -eq 0){ break }
        $dll = ReadCStr (RvaToOff $nameRva)
        if(-not (Test-Path (Join-Path $BinDir $dll)) -and -not (Test-Path (Join-Path $sys $dll)) -and -not (Test-Path (Join-Path $downlevel $dll))){
            if(-not $missing.ContainsKey($dll)){ $missing[$dll] = 1 }
        }
        $off += 20
    }
}

Write-Output ("MISSING count={0}" -f $missing.Count)

$copied = 0
$notFound = @()
foreach($dll in ($missing.Keys | Sort-Object)){
    $src = Join-Path $SourceDir $dll
    $dst = Join-Path $BinDir $dll
    if(Test-Path $src){
        Copy-Item $src $dst -Force
        $copied++
        Write-Output ("  COPIED {0}" -f $dll)
    } else {
        Write-Output ("  NOT FOUND {0}" -f $dll)
        $notFound += $dll
    }
}
Write-Output ("COPIED={0}  NOT_FOUND={1}" -f $copied, $notFound.Count)
if($notFound.Count -gt 0){ Write-Output "--- STILL MISSING ---"; $notFound }
