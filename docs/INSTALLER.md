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
- Updates are downloaded and applied through Velopack package flow.

## Local install path
Default install root:
`%LOCALAPPDATA%\GardensOfKaraxas`

Logs are stored under `<install_root>\logs` and include launcher/game/update logs.

## CI release
- Workflow: `.github/workflows/release.yml`
- Trigger: pushes to `main`/`master` excluding markdown-only and backend-only changes.
- Publishes Velopack release artifacts and then notifies backend release policy endpoint for forced-update gating (5-minute grace).

## Notes on update tokens
If the update feed is private, users need access tokens to fetch package metadata.
Avoid shipping long-lived tokens in client payloads for production.
