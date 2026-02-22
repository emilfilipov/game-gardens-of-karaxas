# Gardens of Karaxas - Game

## High Concept
Gardens of Karaxas is a single-player isometric ARPG/RPG.

The game ships as a Windows-first Godot client with a launcher/updater pipeline.
There is no account login, no persistent online world, and no live social layer in the current direction.
The only online dependency is update delivery.

## Core Pillars
- Isometric exploration and combat progression in a large tower world.
- Deep character creation with stat and skill allocation.
- Fast local iteration through in-client admin/designer tools.
- Data-driven tuning from one local central configuration file.
- Reliable local save/load loop.
- Branded, themed UI across all menus (no placeholder/system-default surfaces).

## Main Menu Contract
Main menu must expose exactly:
- `New Game`
- `Load Game`
- `Settings`
- `Update`
- `Admin`
- `Exit`

Behavior:
1. `New Game` -> Character Creation flow.
2. `Load Game` -> Save-slot list with metadata preview.
3. `Settings` -> Local settings (video/audio/input/gameplay/accessibility), auto-apply.
4. `Update` -> Starts updater flow.
5. `Admin` -> Opens designer suite tabs.
6. `Exit` -> Quits game.

## In-Game Menu Contract
In-game menu is intentionally smaller than main menu:
- `Save Game`
- `Settings`
- `Main Menu`
- `Exit`

## Character Flow (Current)
- Character creation runs before world entry for new saves.
- Character creation includes:
  - Name
  - Sex
  - Race
  - Background
  - Affiliation
  - Stat allocation
  - Starter skill selection
- Point budget is config-driven (default: 10).
- New saves start at level 1 / 0 XP.
- Character preview uses shared podium component and supports direction control.

## Gameplay Runtime (Current)
- World runtime now supports a playable combat loop:
  - basic attack
  - `Ember`
  - `Cleave`
  - `Quick Strike`
  - `Bandage`
- Ability cooldowns/resources and enemy combat stats are config-driven.
- Enemy prototype AI is active with chase/attack/death and loot drops.
- Inventory/equipment loop is active:
  - pickup/use/equip/drop
  - stack handling
  - equipment bonuses affecting combat stats
- Quest/dialog loop v1 is active:
  - NPC interaction
  - quest accept/progress (kill goals)
  - quest state persisted in saves

## Save/Load Model (Current)
- Save model is file-based (no backend dependency):
  - save index file
  - per-slot save payload files
- Save payload stores character state, world state, inventory/quests/dialog placeholders, and timestamps.
- Manual save is available in-world.
- Autosave interval is a local setting.
- Save writes are atomic and backup-protected:
  - temp-write + rename semantics
  - timestamped backup snapshots
  - auto-recovery from latest backup if primary save/config file is corrupted
  - load menu exposes backup-restore action

## Admin Workspace (Current)
Admin opens a tabbed local tool suite:
- `Level Editor`
- `Asset Editor`
- `Config Editor`
- `Diagnostics`

Notes:
- Level ordering/tower-floor ordering UI is removed for the single-player open-world direction.
- Admin tools operate on local files and central config.
- Level Editor is tool-first (brush/layer/mode/canvas overlays) with optional advanced JSON fallback.
- Asset Editor is form-first (search + structured asset/collision fields) with validation guardrails.

## Data-Driven Rule (Single Source)
All game-configurable values must be sourced from central local config, including:
- character creation catalogs/options,
- movement/combat tunables,
- stat and skill text/metadata,
- quest/dialog text scaffolds,
- asset metadata,
- tooltip/descriptive UI text.

Current root config file:
- `game-client/assets/config/game_config.json` (default template shipped with build)
- runtime editable copy: `user://config/game_config.json`
- schema: `game-client/assets/config/schema/game_config.schema.json`
- generated reference: `docs/CONFIG_FIELDS.md`

## Settings Scope (Current)
- Settings auto-apply and persist locally.
- Current active settings include:
  - video mode and UI scaling
  - audio mute/volume
  - gameplay difficulty and autosave interval
  - accessibility toggles (high contrast, reduced motion)
  - input keybindings plus gamepad enable/deadzone

## Update Policy
- Velopack/GCS updater remains the release/update authority.
- Client update checks are user-triggered from menu (not forced auto-update).
- If no update exists, user remains in game and sees `Game is up to date.`
- Latest local release notes are shown in main menu and in-world side panel.

## Visual Direction
- Isometric (`2:1`) direction remains locked.
- Warm, stylized, burgundy-forward UI and world palette is the current baseline.
- Future grim mood shifts should be effect-driven (zone/item/time-of-day), not by replacing the core readability baseline.

## Out Of Scope (Current)
- Account registration/login
- Chat/friends/guild systems
- MMO backend session/social flows
- MFA/security account UX

## Documentation Rule
`docs/GAME.md` is the canonical product source of truth.
Any gameplay/product change is incomplete until reflected here in the same change.
