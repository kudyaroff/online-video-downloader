[CmdletBinding(SupportsShouldProcess)]
param()
$ErrorActionPreference = 'Stop'

Write-Host 'Install yt-dlp, FFmpeg/ffprobe, Deno and the Microsoft VC runtime through WinGet.'
Write-Host 'These are separate projects with their own licenses. Read the installer prompts.'
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw 'WinGet was not found. See docs/windows.md for manual installation.'
}

foreach ($packageId in @('yt-dlp.yt-dlp', 'Gyan.FFmpeg', 'DenoLand.Deno', 'Microsoft.VCRedist.2015+.x64')) {
    if ($PSCmdlet.ShouldProcess($packageId, 'Install with WinGet')) {
        & winget install --exact --id $packageId --source winget
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "WinGet returned $LASTEXITCODE for $packageId. Check its output. The package may already be installed."
        }
    }
}
Write-Host 'Open the app and click Check tools. For updates, use winget upgrade with the same package ID.'
