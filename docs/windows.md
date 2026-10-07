# Windows setup

## Ready-made app

Use Windows 10 or 11, 64-bit. Extract the **whole** release ZIP, including `_internal`, licenses and scripts. Install the tools below, then open `Video Downloader.exe`. Python is included in the build. Do not move the executable away from its folder.

## Tools

| Tool | Purpose |
| --- | --- |
| yt-dlp | Downloads video and audio |
| FFmpeg and ffprobe | Combines streams and extracts audio |
| Deno | Recommended for YouTube JavaScript challenges |
| Microsoft Visual C++ runtime x64 | Required by the bundled Python runtime |

Open PowerShell and run:

```powershell
winget install --exact --id yt-dlp.yt-dlp --source winget
winget install --exact --id Gyan.FFmpeg --source winget
winget install --exact --id DenoLand.Deno --source winget
winget install --exact --id Microsoft.VCRedist.2015+.x64 --source winget
```

Or run `scripts/install-tools.ps1` if your current PowerShell policy allows it. The script shows the packages and uses WinGet's normal installer prompts. It does not change your script policy. Use `-WhatIf` to preview the actions. Read package and source agreements before accepting them.

Click **Check tools** after installation. The app also checks common WinGet and Scoop locations, so a PATH update is usually unnecessary.

## Without WinGet

Use the upstream downloads: [yt-dlp](https://github.com/yt-dlp/yt-dlp/releases), [FFmpeg's Windows download links](https://ffmpeg.org/download.html#build-windows), and [Deno](https://github.com/denoland/deno/releases). Check the source and license of the exact build.

Place `yt-dlp.exe`, `ffmpeg.exe`, `ffprobe.exe` and `deno.exe` in a `tools` folder next to the app executable. For source use, put `tools` in the project folder and launch from that folder. These files are not included in our ZIP.

Install the [Microsoft Visual C++ runtime x64](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist/) from Microsoft if it is missing. Do not copy runtime DLLs from random websites.

## Common errors

- **Missing tool:** install it, then click Check tools.
- **403, sign-in, unavailable video:** update yt-dlp and check that you are allowed to access and save the material. Local browser cookies may help in some cases, but are not guaranteed.
- **Requested format unavailable:** choose another quality or Best source.
- **No permission to save:** choose a writable folder, such as Videos.
- **File will not play:** try a suitable player or a Windows compatible mode. MP4 alone does not guarantee a particular codec.
- **Tkinter missing in source setup:** reinstall Python with Tcl/Tk enabled.
- **Windows warning:** the app is unsigned. Check the source and checksum. Do not disable your antivirus.

Update an installed tool with `winget upgrade --exact --id yt-dlp.yt-dlp --source winget`. Replace the ID to update another tool, then check the versions again.

## Local data

Preferences are stored in `%LOCALAPPDATA%\VideoDownloader\settings.json`. Downloads and failure reports go to your chosen folder. Partial files remain after cancellation so yt-dlp can resume compatible downloads. Delete the preferences file to restore defaults.
