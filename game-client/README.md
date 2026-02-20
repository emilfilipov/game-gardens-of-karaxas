# Gardens of Karaxas - Godot Game Client

This module is the runtime/editor host scaffold introduced by `GOK-MMO-176`.

## Current Scope (Phase 0)
- Holds the Godot project scaffold.
- Defines the launcher-to-game bootstrap contract under `contracts/`.
- Provides a minimal bootstrap scene/script to validate startup wiring.

## Contract
- JSON schema: `contracts/bootstrap.schema.json`
- Version key: `gok_runtime_bootstrap_v1`

## Local Start (when Godot is installed)
- Open this folder in Godot 4.x.
- Run default scene (`res://scenes/bootstrap.tscn`).
- Optional bootstrap handoff:
  - pass launcher-style argument `--bootstrap=<absolute-path-to-json>`.
