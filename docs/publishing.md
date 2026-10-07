# Publication checklist

The files are prepared locally. Nothing is published automatically until a repository is created and its code/tag is pushed.

1. Review the MIT copyright holder and confirm you may publish all contributed code.
2. Use the public repository [video-downloader-windows](https://github.com/kudyaroff/video-downloader-windows). Description: `Windows video and audio downloader powered by yt-dlp. Supports YouTube, Instagram and other services.` Topics: `windows`, `python`, `yt-dlp`, `tkinter`, `video-downloader`.
3. Upload only the prepared source branch or the source ZIP. Do not upload the local `.git` folder, internal notes, logs, cookies, videos, virtual environments or build folders. Do not push all local branches: an older local planning branch is not part of the public project.
4. Enable Issues and, if available, private vulnerability reporting in Security settings.
5. Let the Checks workflow run and fix any remote-only failures before making the release.
6. Review the Windows ZIP, runtime licenses, checksum and [release notes](release-notes.md). Use the tag `v0.1.0` for this version. A matching version tag runs the Windows release workflow.
7. After the first release exists, verify its links and adjust the README's first-release wording.

Publishing the desktop source and ZIP does not publish an online service. A site with advertising needs its own deployment and legal/privacy review.
