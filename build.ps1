$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name 'Evenicle-2-Save-Editor' `
    --version-file 'version_info.txt' `
    'evenicle2_live_editor.py'

$releaseDirectory = Join-Path $projectRoot 'release'
New-Item -ItemType Directory -Force -Path $releaseDirectory | Out-Null
$executable = Join-Path $projectRoot 'dist\Evenicle-2-Save-Editor.exe'
Copy-Item -LiteralPath $executable -Destination $releaseDirectory -Force
Copy-Item -LiteralPath (Join-Path $projectRoot 'README.md') -Destination $releaseDirectory -Force
Copy-Item -LiteralPath (Join-Path $projectRoot 'CHANGELOG.md') -Destination $releaseDirectory -Force
Copy-Item -LiteralPath (Join-Path $projectRoot 'LICENSE') -Destination $releaseDirectory -Force
Get-FileHash -LiteralPath (Join-Path $releaseDirectory 'Evenicle-2-Save-Editor.exe') -Algorithm SHA256 |
    ForEach-Object { "$($_.Hash.ToLower())  Evenicle-2-Save-Editor.exe" } |
    Set-Content -LiteralPath (Join-Path $releaseDirectory 'SHA256SUMS.txt') -Encoding ascii

Write-Host "Release files created in $releaseDirectory"
