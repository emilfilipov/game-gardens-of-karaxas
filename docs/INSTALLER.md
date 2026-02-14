# Windows Installer/Updater (Velopack)

## One-time setup (Windows 11)
1. Install JDK 17 (Temurin recommended).
2. Install Velopack CLI:
   `dotnet tool install -g vpk --version 0.0.1298`
   If already installed:
   `dotnet tool update -g vpk --version 0.0.1298`

## Build + package
From the repo root:
```
powershell -ExecutionPolicy Bypass -File scripts/pack.ps1 -Version 1.0.0
```

Current status:
- Launcher build is available now via Gradle (`:launcher:build`, `:launcher:fatJar`).
- End-to-end Windows packaging via `scripts/pack.ps1` supports launcher-only mode (`-LauncherOnly`) and produces installer/update artifacts for the launcher while runtime modules are being scaffolded.
- When `desktop/` exists, the same script packages launcher + game runtime together.

This will:
- build fat jars for the launcher and game
- generate Windows app images with `jpackage`
- create a Velopack release under `releases/windows/`
- replace the Velopack `Setup.exe` with a logging wrapper (auto-logs install)
- render `docs/RELEASE_NOTES_TEMPLATE.md` into `patch_notes.md` in the install root (if present)

The `releases/windows/` folder will contain:
- `*Setup*.exe` (installer wrapper)
- `GardensOfKaraxas-1.0.0-full.nupkg`
- `RELEASES`

## Test install locally
Run `releases/windows/*Setup*.exe` on Windows. This installs to:
`%LOCALAPPDATA%\GardensOfKaraxas`

The installer wrapper extracts the embedded Velopack Setup core to:
`%TEMP%\GardensOfKaraxas\GardensOfKaraxas-SetupCore.exe` and runs it with logging enabled.

The wrapper writes logs to `%TEMP%\GOK-setup.log` (override with `GOK_SETUP_LOG_PATH`).

Velopack's Update.exe logs to `Velopack.log` in the install root by default. citeturn0search0
Setup.exe only logs to file when `--log` is provided; the wrapper injects `--log` and `--verbose` to capture debug output. citeturn0search0

## Launcher behavior
The launcher tries to run updates via `Update.exe --update`.
Updates use Velopack package updates (delta packages when available, full package fallback when needed), not re-downloading the installer executable.
Current launcher behavior downloads update packages during update checks, applies them automatically, and restarts with auto-launch of the game.
The game is launched from:
`<install_root>/game/GardensOfKaraxas.exe`

Optional override for development:
```
setx GOK_GAME_EXE "C:\path\to\GardensOfKaraxas.exe"
```

Optional release notes override:
```
setx GOK_PATCH_NOTES_PATH "C:\path\to\patch_notes.md"
```

## GitHub Actions (private repo)
The workflow is at `.github/workflows/release.yml` and runs on every push to `main` or `master`.

Notes:
- Uses `VELOPACK_TOKEN` (or `velopack_token`) repo secret to publish releases.
- Auto-generates version as `1.0.<run_number>` so you don't need to bump manually.
- Release body is rendered from `.github/release-body-template.md`.

## Client update token (private repo)
If the update feed is private, end users need a token. For now, use:
```
setx VELOPACK_GITHUB_TOKEN "<your token>"
```

Optional (build-time): set `VELOPACK_TOKEN` (or `VELOPACK_GITHUB_TOKEN`) in the packaging environment to embed an `update_token.txt` into the payload. The launcher will pass it to `Update.exe`. This is for internal testing only; shipping tokens is insecure.

Security note: shipping PATs is sensitive. A safer option is a public repo or a private file host with short-lived signed URLs.
