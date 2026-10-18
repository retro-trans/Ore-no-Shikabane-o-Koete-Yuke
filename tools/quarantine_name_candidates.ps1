param([switch]$Execute)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$taskOutput = [IO.Path]::GetFullPath((Join-Path $taskRoot 'work/output')) + [IO.Path]::DirectorySeparatorChar
$taskRejected = [IO.Path]::GetFullPath((Join-Path $taskRoot 'work/source/rejected-name-candidates'))
$moves = @()
foreach ($version in @('0.2.13','0.2.14')) {
    foreach ($suffix in @('','.iso','.manifest.json')) {
        $source = [IO.Path]::GetFullPath((Join-Path $taskOutput ('english-native-' + $version + $suffix)))
        $target = [IO.Path]::GetFullPath((Join-Path $taskRejected ('english-native-' + $version + $suffix)))
        if (-not $source.StartsWith($taskOutput, [StringComparison]::OrdinalIgnoreCase)) { throw 'Source escapes output folder' }
        if (-not $target.StartsWith(($taskRejected + [IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) { throw 'Target escapes rejected-candidate folder' }
        if ((Test-Path -LiteralPath $source) -and (Test-Path -LiteralPath $target)) { throw 'Preserve existing target' }
        if (Test-Path -LiteralPath $source) { $moves += [pscustomobject]@{ source=$source; target=$target } }
    }
}
$moves | ConvertTo-Json
if ($Execute) {
    New-Item -ItemType Directory -Path $taskRejected -Force | Out-Null
    foreach ($move in $moves) { Move-Item -LiteralPath $move.source -Destination $move.target }
}
