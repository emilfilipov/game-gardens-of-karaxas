# Windows Installer/Updater (Velopack)

## One-time setup (Windows)
1. Install JDK 17 (Temurin recommended).
2. Install Velopack CLI:
   `dotnet tool install -g vpk --version 0.0.1298`

## Build and package launcher
From repo root:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/pack.ps1 -Version 1.0.0
```

Artifacts are written to `releases/windows/`.

## Runtime behavior
- Installed executable launches Godot single-player shell.
- Update control is available from main menu (`Update`).
- Updater uses packaged `UpdateHelper.exe`.
- Feed URL source order:
  1. `game_config.update.feed_url`
  2. `GOK_UPDATE_REPO` environment variable
  3. `update_repo.txt` in packaged payload (release-time value)

## Local install path
Default install root:
`%LOCALAPPDATA%\GardensOfKaraxas`

Logs:
- launcher logs: `<install_root>\logs\launcher.log`
- game logs: `<install_root>\logs\game.log`
- updater logs: `<install_root>\logs\velopack.log`

## CI release
- Workflow: `.github/workflows/release.yml`
- Trigger: pushes to `main`/`master` (markdown-only changes ignored)
- Release uploads Velopack artifacts to GCS feed path and versioned archive path.
- Mutable feed artifacts receive `Cache-Control: no-cache, max-age=0`.
- Historical `.nupkg` artifacts are prefetched from feed before packing to preserve delta continuity.

## Runtime host defaults in payload
`runtime_host.properties` is emitted at package time:
- `runtime_host`
- `godot_executable`
- `godot_project_path`

Environment overrides (launcher process):
- `GOK_RUNTIME_HOST`
- `GOK_GODOT_EXECUTABLE`
- `GOK_GODOT_PROJECT_PATH`

## Release variables/secrets used by workflow
Required:
- `KARAXAS_GCS_RELEASE_BUCKET` (variable)
- `GCP_WORKLOAD_IDENTITY_PROVIDER` (secret)
- `GCP_SERVICE_ACCOUNT` (secret)

Optional:
- `KARAXAS_GCS_RELEASE_PREFIX`
- `KARAXAS_RUNTIME_HOST`
- `KARAXAS_GODOT_EXECUTABLE`
- `KARAXAS_GODOT_PROJECT_PATH`
- `KARAXAS_GODOT_WINDOWS_DOWNLOAD_URL`
- `KARAXAS_GODOT_WINDOWS_SHA256`
