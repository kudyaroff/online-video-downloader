[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
if ([Environment]::OSVersion.Platform -ne 'Win32NT') { throw 'Build this release on Windows.' }
if (-not [Environment]::Is64BitProcess) { throw 'Use 64-bit PowerShell and Python.' }
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Install the build environment. See docs/development.md.' }

function Invoke-CheckedPython {
    param([string[]]$Arguments)
    & $pythonPath @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Python command failed: $($Arguments -join ' ')" }
}

Push-Location -LiteralPath $projectRoot
try {
    Invoke-CheckedPython @('-m', 'pytest', '-q')
    Invoke-CheckedPython @('-m', 'ruff', 'check', 'src', 'tests', 'run.py', 'packaging/collect_notices.py')
    Invoke-CheckedPython @('-m', 'PyInstaller', '--noconfirm', '--clean', 'packaging/windows.spec')
    $bundlePath = Join-Path $projectRoot 'dist/Video Downloader'
    foreach ($name in @('LICENSE', 'THIRD_PARTY_NOTICES.md', 'README.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'SECURITY.md')) {
        Copy-Item -LiteralPath (Join-Path $projectRoot $name) -Destination $bundlePath
    }
    $docsPath = Join-Path $bundlePath 'docs'
    $scriptsPath = Join-Path $bundlePath 'scripts'
    New-Item -ItemType Directory -Force -Path $docsPath, $scriptsPath | Out-Null
    Copy-Item -LiteralPath (Join-Path $projectRoot 'docs/windows.md') -Destination $docsPath
    Copy-Item -LiteralPath (Join-Path $projectRoot 'docs/legal.md') -Destination $docsPath
    Copy-Item -LiteralPath (Join-Path $projectRoot 'docs/development.md') -Destination $docsPath
    $assetsPath = Join-Path $docsPath 'assets'
    New-Item -ItemType Directory -Force -Path $assetsPath | Out-Null
    Copy-Item -LiteralPath (Join-Path $projectRoot 'docs/assets/desktop.png') -Destination $assetsPath
    Copy-Item -LiteralPath (Join-Path $projectRoot 'scripts/install-tools.ps1') -Destination $scriptsPath
    Invoke-CheckedPython @('packaging/collect_notices.py', $bundlePath)
    $archivePath = Join-Path $projectRoot 'dist/Video-Downloader-Windows-x64.zip'
    Compress-Archive -Path (Join-Path $bundlePath '*') -DestinationPath $archivePath -Force
    $hashValue = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $hashValue + '  Video-Downloader-Windows-x64.zip' | Set-Content -LiteralPath ($archivePath + '.sha256') -Encoding ascii
    Write-Host "Ready: $archivePath"
} finally {
    Pop-Location
}
