# Gardens of Karaxas - Godot Game Client

This module is the unified Godot client shell for Gardens of Karaxas.

## Current Scope
- Hosts auth/account/world/admin UI flows in one Godot runtime surface.
- Defines the launcher/bootstrap contract under `contracts/`.
- Provides runtime world scaffold (`world_canvas.gd`) and update/log tooling entry points.

## Contract
- JSON schema: `contracts/bootstrap.schema.json`
- Version key: `gok_runtime_bootstrap_v1`

## Local Start (when Godot is installed)
- Open this folder in Godot 4.x.
- Run default scene (`res://scenes/bootstrap.tscn`).
