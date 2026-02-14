# Gardens of Karaxas - Technical

## Purpose
This is the single source of truth for technical architecture, stack decisions, module boundaries, and distribution engineering.

## Technology Decision: Kotlin + LibGDX
Decision: use Kotlin + LibGDX.

Why this is a good fit for current goals (Windows first, then Linux/Steam, then Android):
- LibGDX is designed for multi-platform game deployment, including desktop and Android targets.
- Official project bootstrap tooling supports Kotlin and target backends out of the box.
- Kotlin has stable JVM and Android targets, which aligns with desktop + Android portability goals.
- Steam distribution can consume desktop runtime artifacts directly (Windows and Linux depots).

Conclusion:
- Kotlin + LibGDX is a pragmatic and portable choice for the current roadmap.
- Keep architecture modular so future portability remains low-friction.

## Architecture Rules (Must Hold)
1. Core gameplay logic must not depend on launcher/updater code.
2. Game runtime must start and run without updater components.
3. Platform wrappers (desktop/Android/launcher) can orchestrate, but not own gameplay rules.
4. Interfaces between modules must be explicit and stable.

## Target Module Layout
- Current scaffold in repo:
  - `docs/`:
    - Canonical and supporting project documentation.
  - `launcher/`:
    - Windows-only launcher/updater shell.
  - `assets/`:
    - Art/audio/data content independent from launcher code.
  - `tools/`:
    - Setup wrapper and update helper utilities.
  - Root Gradle files:
    - `settings.gradle.kts`, `build.gradle.kts`, `gradlew`, `gradle/`.
- Planned runtime modules (to be added):
  - `sim/`:
    - Pure Kotlin domain logic and simulation rules.
    - No LibGDX types.
  - `game/`:
    - LibGDX-facing gameplay orchestration and state projection.
    - Input mapping and scene/state management.
  - `desktop/`:
    - Standalone desktop runtime entrypoint for Windows/Linux and Steam.

## Portability Strategy
- Shared code will live in `sim/` and most of `game/` once those modules are scaffolded.
- Platform-specific code is isolated to wrappers like `desktop/` and `launcher/`.
- Avoid filesystem, process, and OS calls in core gameplay modules.
- Keep save/data formats platform-neutral and versioned.

## Distribution Strategy
Phase 1 (current priority):
- Windows installer/launcher/updater using Velopack (`scripts/pack.ps1`, `.github/workflows/release.yml`).

Phase 2:
- Steam distribution for Windows and Linux using runtime artifacts from `desktop/`.

Phase 3:
- Android packaging by adding an Android wrapper module around shared logic.

Current status note:
- The current Gradle project is launcher-first (`include("launcher")`).
- CI release flow now supports launcher-only packaging when runtime modules are absent, and switches to full launcher+runtime packaging once `desktop/build.gradle.kts` exists.
- The CI release workflow runs launcher-only checks in scaffold mode and switches to full Velopack packaging once `desktop/build.gradle.kts` exists.
- The launcher currently renders a stylized left-aligned main-menu prototype UI using Swing and image resources in `launcher/src/main/resources/ui/`; launcher tools are surfaced inside the `Update` menu box (update check, patch notes view, and log panels).
- The `Update` menu box now uses `launcher_canvas.png` framing and transparent patch-notes rendering over themed textures.
- Launcher UI layout is responsive: main menu/button stack and menu-box dimensions are recomputed proportionally on window resize.
- Canvas box rendering aligns to the image's opaque bounds (ignoring transparent padding) for visual border alignment.
- Menu-box title strips are removed; update metadata (`Build Version: vX.Y.Z (YYYY-MM-DD)`) is rendered inside the Update box with responsive sizing.
- Update checks currently download updates in-app, trigger apply automatically, and restart the launcher with game auto-launch (`--autoplay`).
- Packaging icon assets are stored under `assets/icons/` and consumed by `scripts/pack.ps1`.
- The setup wrapper executable icon is sourced from `assets/icons/game_icon.ico` (multi-size ICO entries for better shell/browser compatibility).
- Update delivery uses Velopack package updates, not re-downloading installers; delta packages are used when available and full package fallback is automatic.

## Multiplayer-Readiness Guidelines
Future modes include co-op and PvP, so prepare now:
- Define command/state boundaries clearly in `sim/`.
- Keep game-state serialization deterministic and versioned where practical.
- Separate local presentation concerns from network-eligible gameplay state.
- Treat netcode as an adapter layer, not gameplay authority.

## Build, Test, and CI Requirements
- Unit tests for core gameplay rules in `sim/`.
- Integration tests for save/load compatibility.
- Smoke tests for:
  - standalone desktop runtime launch
  - launcher -> runtime handoff
  - Windows packaging artifact validity
- CI should fail on broken module boundaries or packaging regressions.

## Procedural Audio Plan (Deferred)
Status:
- Planned only. No procedural audio generation is implemented yet.

Goal:
- Add free, programmatic runtime audio for both music and sound effects.

Primary option (recommended):
- `libpd` (Pure Data embedded):
  - Free/open source and suitable for real-time procedural/adaptive audio.
  - Good fit for runtime-generated music layers and event-driven SFX.

Secondary options:
- `Csound`:
  - Free/open source and powerful for synthesis/composition scripting.
  - Heavier integration footprint than `libpd`.
- `Magenta RealTime`:
  - Useful for AI-assisted real-time generation/prototyping.
  - Requires strict review of model/weights license terms before production use.

License guardrails:
- Prefer solutions with commercial-friendly licenses for shipped game builds.
- Treat non-commercial model licenses as prototype-only.
- Complete license validation before integrating any AI model weights in release artifacts.

Planned procedural SFX targets:
- Footsteps (surface-variant transient synthesis).
- Quiet fireplace crackle (continuous noise bed + random crackle events).
- Sword clash (metallic transient + short resonant tail).

Integration boundary:
- Keep audio generation inside runtime modules (`game/`/future audio module), not launcher/updater code.
- Preserve portability targets (Windows first, Linux/Steam next, Android later).

## Documentation Rule
This file is the single source of truth for technical information.

Any technical decision change is incomplete until this file is updated in the same change.

## Sources
- LibGDX official site (cross-platform framework overview): https://libgdx.com/
- LibGDX Liftoff docs (project generation, Kotlin support, target backends): https://libgdx.com/wiki/getting-started/project-generation
- Kotlin Multiplatform target support (JVM/Android target status): https://www.jetbrains.com/help/kotlin-multiplatform-dev/supported-platforms.html
- Steamworks documentation hub (desktop distribution context): https://partner.steamgames.com/doc/home
- Steamworks Linux requirements (Linux runtime considerations): https://partner.steamgames.com/doc/store/application/platforms/linux
