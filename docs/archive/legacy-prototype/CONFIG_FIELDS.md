# Config Fields

Generated from `game-client/assets/config/schema/game_config.schema.json`.

| Root Key | Required | Type | Description |
| --- | --- | --- | --- |
| `assets` | Yes | `object` | Asset catalog and collision metadata |
| `character_creation` | Yes | `object` | Character creator point budget, options, stat/skill catalogs |
| `gameplay` | Yes | `object` | Runtime gameplay tuning domains |
| `meta` | Yes | `object` | Build-independent local config metadata |
| `ui` | No | `object` | UI text/tooltip catalogs |
| `update` | Yes | `object` | Updater feed configuration |
| `world` | Yes | `object` | World/default-level bootstrap settings |

## Notes
- Runtime-level validation is enforced in `single_player_shell.gd`.
- Keep this file in sync by running:
  - `python3 tools/generate_config_docs.py`
