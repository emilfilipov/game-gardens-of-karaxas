# Ambitions of Peace - Legacy Godot Game Client (Transitional)

This module is the legacy Godot client shell retained during migration to the Ambitions of Peace Rust-first runtime direction.

## Current Scope
- Online auth flow (`login/register`) with backend session tokens.
- MFA management UI integrated in settings.
- Account hub with character list/create/select/play.
- In-world top-down 3D runtime surface (`world_canvas_3d.gd`).
- Admin designer suite (level/asset/content version tools) for admin users.
- Runtime gameplay config bootstrap fetched from backend (`/content/runtime-config`, fallback `/content/bootstrap`).

## Entry Scene
- `res://scenes/bootstrap.tscn`
- Script: `res://scripts/client_shell.gd`

## Local Start (when Godot is installed)
- Open `game-client/` in Godot 4.x.
- Run default scene (`res://scenes/bootstrap.tscn`).
