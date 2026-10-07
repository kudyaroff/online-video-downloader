# Changelog

## 0.1.1

- Fixed direct video downloads when the source does not report a height.
- Kept quality limits for videos with a known height.
- Added regression checks using yt-dlp's real format selector.

## 0.1.0

First Windows release.

- Video and M4A audio downloads through separately installed yt-dlp.
- Up to four simultaneous downloads, with progress and cancellation.
- Local preferences and tool discovery, including WinGet locations.
- FFmpeg path passed explicitly to yt-dlp.
- Height limits applied to every video fallback.
- Temporary network errors retried once at the app level.
- Read-only activity log that can be cleared.
- Windows build, checksums, runtime notices and setup instructions.
