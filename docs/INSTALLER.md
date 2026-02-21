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

This produces installer/update artifacts under `releases/windows/`.

## Launcher runtime behavior
- Launcher hosts account/auth/lobby screens.
- Launcher keeps updater tools available from the Update screen/card.
- Updates are downloaded and applied through Velopack package flow from configured feed URL (`update_repo.txt` or backend release summary feed).
- Runtime host defaults can be shipped via `runtime_host.properties` in payload:
  - `runtime_host=launcher_legacy|godot`
  - `godot_executable=<path-or-command>`
  - `godot_project_path=<project-dir>`
- Runtime host values from process environment (`GOK_RUNTIME_HOST`, `GOK_GODOT_EXECUTABLE`, `GOK_GODOT_PROJECT_PATH`) override packaged defaults.
- Release CI now bundles a Windows Godot executable into payload when runtime host is `godot` (`game-client/runtime/windows/godot4.exe`) and sets `godot_executable` to this relative path by default.
- Optional release variables for bundled runtime source integrity:
  - `KARAXAS_GODOT_WINDOWS_DOWNLOAD_URL` (override default official Godot zip URL)
  - `KARAXAS_GODOT_WINDOWS_SHA256` (recommended; verifies downloaded runtime archive hash during CI)

## Local install path
Default install root:
`%LOCALAPPDATA%\GardensOfKaraxas`

Logs are stored under `<install_root>\logs` and include launcher/game/update logs.

## CI release
- Workflow: `.github/workflows/release.yml`
- Trigger: pushes to `main`/`master` excluding markdown-only and backend-only changes.
- Publishes Velopack feed artifacts to GCS (feed path + version archive) and notifies backend release policy endpoint for forced-update gating (5-minute grace).
- Release packaging prefetches existing GCS `.nupkg` artifacts so clients can still use delta updates when they skip several versions.

## Notes on update credentials
Updater flow is designed for public-read GCS feed access and does not require embedding repository tokens in the game client.
