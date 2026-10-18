param([switch]$Execute, [string]$GamePath, [ValidateSet('directx11','opengl','vulkan','software')][string]$Graphics = 'opengl', [switch]$IsolateInput, [string]$LogPath)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$emulatorRoot = Join-Path $taskRoot 'work/source/emulator'
$installedRoot = 'C:\Program Files\PPSSPP'
$emulator = Join-Path $emulatorRoot 'PPSSPPWindows64.exe'
if (-not $GamePath) { $GamePath = (Get-ChildItem -LiteralPath $taskRoot -Filter '*.iso' | Select-Object -First 1).FullName }
$game = (Resolve-Path -LiteralPath $GamePath).Path
$baseConfig = Join-Path $emulatorRoot 'profile.ini'
$config = if ($IsolateInput) { Join-Path $emulatorRoot 'input-isolated.ini' } else { $baseConfig }
$arguments = @('--windowed', ('--graphics=' + $Graphics), ('--config="' + $config + '"'), ('"' + $game + '"'))
if ($LogPath) { $arguments += @('--loglevel=2', ('--log="' + $LogPath + '"')) }
[pscustomobject]@{ mode = $(if ($Execute) { 'execute' } else { 'dry run' }); emulator = $emulator; game = $game; config = $config; debugger = 'ws://127.0.0.1:19417/debugger'; resolution = 4; action = 'Copy installed emulator/assets to an isolated project profile, then launch hidden.' } | ConvertTo-Json
if (-not $Execute) { return }
New-Item -ItemType Directory -Path (Join-Path $emulatorRoot 'memstick') -Force | Out-Null
if (-not (Test-Path -LiteralPath $emulator)) {
    Copy-Item -LiteralPath (Join-Path $installedRoot 'PPSSPPWindows64.exe') -Destination $emulator
    Copy-Item -LiteralPath (Join-Path $installedRoot 'assets') -Destination $emulatorRoot -Recurse
}
if (-not (Test-Path -LiteralPath $baseConfig)) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'ppsspp_profile.ini') -Destination $baseConfig }
if ($IsolateInput) {
    $qaConfig = [IO.File]::ReadAllText($baseConfig)
    foreach ($key in @('AllowXInput','AllowDInput','AllowHIDInput')) {
        if ($qaConfig -notmatch ('(?m)^' + $key + ' = (True|False)')) { throw "Missing input setting: $key" }
        $qaConfig = [regex]::Replace($qaConfig, ('(?m)^' + $key + ' = (True|False)'), ($key + ' = False'))
    }
    [IO.File]::WriteAllText($config, $qaConfig, (New-Object Text.UTF8Encoding($false)))
}
$existing = Get-Process -Name PPSSPPWindows64 -ErrorAction SilentlyContinue | Where-Object Path -EQ $emulator
if ($existing) { $existing | Select-Object Id,Path | ConvertTo-Json; return }
$proc = Start-Process -FilePath $emulator -ArgumentList $arguments -WorkingDirectory $emulatorRoot -WindowStyle Hidden -PassThru
$proc | Select-Object Id,Path | ConvertTo-Json
