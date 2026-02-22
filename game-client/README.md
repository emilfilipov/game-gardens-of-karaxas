# Gardens of Karaxas - Godot Game Client

This module is the single-player Godot runtime shell for Gardens of Karaxas.

## Current Scope
- Main menu (`New Game`, `Load Game`, `Settings`, `Update`, `Admin`, `Exit`).
- Character creation and local save/load loop.
- In-world runtime surface (`world_canvas.gd`).
- Admin designer suite (level/asset/config/diagnostics tabs).
- Local central configuration loading/validation.

## Entry Scene
- `res://scenes/bootstrap.tscn`
- Script: `res://scripts/single_player_shell.gd`

## Local Start (when Godot is installed)
- Open `game-client/` in Godot 4.x.
- Run default scene (`res://scenes/bootstrap.tscn`).
