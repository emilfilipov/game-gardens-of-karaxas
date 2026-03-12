# Windows Install and Update

## Scope
Windows-first install/update flow for Ambitions of Peace game runtime and standalone designer runtime.

## Distribution Model
- Artifacts are published to GCS by `.github/workflows/release.yml`.
- Two decoupled channels are maintained:
  - game channel (`win-game` default): `AmbitionsOfPeace-client-app-win-x64-<version>.zip`
  - designer channel (`win-designer` default): `AmbitionsOfPeace-designer-client-win-x64-<version>.zip`
- Each artifact publish includes:
  - `.zip` payload
  - `.manifest.json` deterministic file manifest
  - `.sha256` checksum
  - mutable `latest.json` pointer (cache-busted)
- Retention policy: keep latest 3 versions in both feed and archive prefixes per channel.

## CI Trigger Rules
Release workflow triggers on push to `main`/`master` when paths include:
- `client-app/**`
- `designer-client/**`
- `sim-core/**`
- `tooling-core/**`
- `assets/content/**`
- `scripts/**`
- `tools/package_client_app_release.py`
- `tools/package_designer_client_release.py`
- `.github/workflows/release.yml`

Docs-only pushes do not trigger release workflow.

## Local Install Scripts (Windows)
- Shared installer helper: `scripts/install_channel.ps1`
- Game channel installer: `scripts/install_game_client.ps1`
- Designer channel installer: `scripts/install_designer_client.ps1`

Default install roots:
- game: `%LOCALAPPDATA%\\AmbitionsOfPeace\\game-runtime`
- designer: `%LOCALAPPDATA%\\AmbitionsOfPeace\\designer-client`

Example:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_game_client.ps1
powershell -ExecutionPolicy Bypass -File scripts/install_designer_client.ps1
```

Optional overrides:
- pass `-FeedUrl` to target an explicit channel URL.
- pass `-InstallDir` to customize install root.

## Required CI Variables/Secrets
Required for publish:
- `KARAXAS_GCS_RELEASE_BUCKET` (variable)
- `GCP_WORKLOAD_IDENTITY_PROVIDER` (secret)
- `GCP_SERVICE_ACCOUNT` (secret)

Optional:
- `KARAXAS_GCS_GAME_RELEASE_PREFIX` (defaults `win-game`)
- `KARAXAS_GCS_DESIGNER_RELEASE_PREFIX` (defaults `win-designer`)

## Release Validation Baseline
- `python tools/package_client_app_release.py --version <x.y.z> --exe <path/to/client-app.exe> --output-dir releases/game`
- `python tools/package_designer_client_release.py --version <x.y.z> --output-dir releases/designer`
- `PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_security_edges.py backend/tests/test_publish_drain.py`
