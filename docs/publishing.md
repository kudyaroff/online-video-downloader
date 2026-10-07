# Publishing a release

The public repository is [video-downloader-windows](https://github.com/kudyaroff/video-downloader-windows).

1. Update the package version and changelog. Review the licenses when changing bundled components.
2. Run the tests and build the Windows ZIP with `scripts/build-windows.ps1`.
3. Extract the ZIP, launch the app and check its SHA-256 checksum.
4. Push the source and wait for the Checks workflow to pass on Windows and Linux.
5. Review [release notes](release-notes.md), then create a matching `vX.Y.Z` tag. The Windows release workflow builds and publishes the ZIP and checksum.
6. Check the release downloads and installation instructions.

Keep credentials, cookies, downloaded media, environments and internal notes out of the repository and release assets. Publish only the intended branch.

An online service needs its own deployment and legal/privacy review.
