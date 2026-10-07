[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create the project environment first. See README.md.'
}
Push-Location -LiteralPath $projectRoot
try {
    & $pythonPath (Join-Path $projectRoot 'run.py')
    if ($LASTEXITCODE -ne 0) { throw "The application exited with code $LASTEXITCODE." }
} finally {
    Pop-Location
}
