# Ambitions of Peace

Ambitions of Peace is a persistent online medieval war-and-politics RPG with a Rust-first, code-first stack.
Core simulation contract: all core systems run in real time (travel, logistics, trade, espionage, politics, and battle outcomes).

## Canonical Documentation
- `docs/GAME.md` - canonical product/game scope and gameplay contracts.
- `docs/TECHNICAL.md` - canonical architecture, infra, and runtime contracts.
- `docs/TASKS.md` - granular execution backlog and completion ledger.
- `docs/adr/` - accepted architecture decision records.

## Supporting Documentation
- `docs/INSTALLER.md` - Windows install/update and release-channel behavior.
- `docs/OPERATIONS.md` - release/deploy runbook and incident flow.
- `docs/release-gates/` - dated external PoC go/no-go evidence bundles and rollback proof artifacts.
- `docs/REDIS_ADOPTION_GATE.md` - Redis adoption thresholds and migration/rollback gates.
- `docs/COST_GUARDRAILS.md` - monthly PoC budget policy.
- `docs/DEPRECATION_AUDIT.md` - cleanup inventory and migration removals.

## Repository Layout
- `backend/` - FastAPI control-plane services, Cloud SQL integration, release metadata, auth/session, content APIs.
- `world-service/` - Rust Axum world authority with deterministic tick runner and real-time subsystem simulation.
- `sim-core/` - shared Rust simulation contracts/rules used by world-service and client surfaces.
- `client-app/` - Rust Bevy runtime (`bootstrap-shell`, `sandbox-ui`) with code-first panels/tools.
- `designer-client/` - standalone Python designer client for authenticated content/world promotion operations.
- `tooling-core/` - deterministic content import/export/hash tooling.
- `assets/` - versioned gameplay/content packs and generated signatures.
- `scripts/` - install helpers and release utility scripts.
- `tools/` - build/package helper tools.
- `.github/workflows/` - CI/CD automation.

## Local Validation Baseline
- `python3 -m compileall backend/app`
- `PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_security_edges.py backend/tests/test_publish_drain.py`
- `~/.cargo/bin/cargo fmt --all -- --check`
- `~/.cargo/bin/cargo clippy --workspace --all-targets -- -D warnings`
- `~/.cargo/bin/cargo test --workspace`

## Key Runtime Commands
- One-command local PoC stack bootstrap (backend + world-service + deterministic seed + client handoff): `scripts/run_local_poc_stack.sh`
- One-command bootstrap without launching client: `scripts/run_local_poc_stack.sh --no-client`
- Runtime/log reset flow before re-bootstrap: `scripts/run_local_poc_stack.sh --reset-runtime`
- Bootstrap shell: `~/.cargo/bin/cargo run -p client-app --features bootstrap-shell`
- Bootstrap shell with startup handoff file: `~/.cargo/bin/cargo run -p client-app --features bootstrap-shell -- --handoff-file <path/to/startup_handoff.json>`
- Sandbox UI: `~/.cargo/bin/cargo run -p client-app --features sandbox-ui`
- Deterministic local seed helper only: `python3 backend/scripts/seed_local_poc_account.py --base-url http://127.0.0.1:8000 --output-handoff client-app/runtime/startup_handoff.local.json`
- Placeholder player sprite regeneration: `python3 tools/generate_player_placeholder_png.py`
- Windows installer acceptance smoke (local feed): `powershell -ExecutionPolicy Bypass -File scripts/windows_installer_acceptance_smoke.ps1 -FeedRoot <local-feed-root> -SummaryPath <summary.md>`
- External PoC release gate validator: `python backend/scripts/validate_external_poc_release_gate.py --gate-pointer docs/release-gates/current_gate.json`

## Packaging and Release
- Release workflow: `.github/workflows/release.yml`
- Backend deploy workflow: `.github/workflows/deploy-backend.yml`
- Security scan workflow: `.github/workflows/security-scan.yml`
- Release channels published to GCS:
  - game: `AmbitionsOfPeace-client-app-win-x64-<version>.zip`
  - designer: `AmbitionsOfPeace-designer-client-win-x64-<version>.zip`
- Each channel keeps the latest 3 versions in feed/archive.
