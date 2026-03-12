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
- Installed game executable launches Godot online client shell.
- Installer payload also includes a separate designer executable.
- Release feed now also includes standalone Windows Rust runtime artifacts (`client-app`) with deterministic manifest/checksum metadata for migration validation.
- Velopack install/update hooks create desktop shortcuts for:
  - `Ambitions of Peace` (game launcher entry)
  - `Ambitions of Peace Designer` (designer entry)
- Update control is available from main menu (`Update`).
- Updater uses packaged `UpdateHelper.exe`.
- Feed URL source order:
  1. `game_config.update.feed_url`
  2. `GOK_UPDATE_REPO` environment variable
  3. `update_repo.txt` in packaged payload (release-time value)

## Local install path
Default install root target:
`%LOCALAPPDATA%\AmbitionsOfPeace`

Compatibility note:
- Legacy installs may still exist under `%LOCALAPPDATA%\PlompersArenaInc` and `%LOCALAPPDATA%\ChildrenOfIkphelion` until naming/path migration is finalized.

Logs:
- launcher logs: `<install_root>\\logs\\launcher.log`
- game logs: `<install_root>\\logs\\game.log`
- updater logs: `<install_root>\\logs\\velopack.log`
- updater status: `<install_root>\\logs\\update_status.json`

## CI release
- Workflow: `.github/workflows/release.yml`
- Trigger: pushes to `main`/`master` only when runtime/package paths change (`launcher/**`, `game-client/**`, `client-app/**`, `sim-core/**`, `designer-client/**`, `assets/**`, `scripts/**`, `tools/package_client_app_release.py`, Cargo/Gradle wrapper/build files). Concept docs/images/tooling-only changes do not auto-trigger releases.
- Release uploads Velopack artifacts to GCS feed path and versioned archive path.
- Release also uploads versioned Windows Rust runtime artifacts to the same feed/archive path:
  - `AmbitionsOfPeace-client-app-win-x64-<version>.zip`
  - `AmbitionsOfPeace-client-app-win-x64-<version>.manifest.json`
  - `AmbitionsOfPeace-client-app-win-x64-<version>.sha256`
- Mutable feed artifacts receive `Cache-Control: no-cache, max-age=0`.
- Historical `.nupkg` artifacts are prefetched from feed before packing to preserve delta continuity.
- Post-upload retention keeps the 3 newest feed/archive build versions and prunes older ones (Velopack packages and versioned Rust runtime artifacts).

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
