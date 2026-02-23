Assets live here and should be organized as the project grows.

Suggested structure:
- `characters/` - player appearance sprites (idle + walk/run sheets).
- `tiles/` - world/level-builder tile sprites (ground, obstacles, ambient overlays).
- `sprites/` - gameplay and environment sprites
- `fonts/` - bitmap or TTF fonts
- `shaders/` - GLSL shaders
- `ui/` - UI skins, nine-patches, and textures
- `audio/` - music, ambience, and SFX
- `data/` - gameplay/config data files

Keep large source files and export pipelines documented alongside final runtime assets.

## Sellsword V1 Pack
- Runtime pack root: `assets/characters/sellsword_v1/`
- Metadata: `assets/characters/sellsword_v1/catalog.json`
- Generated sheets: `assets/characters/sellsword_v1/sheets/`
- Layered-ready sources: `assets/characters/sellsword_v1/layers/`

Generation command:
- `python3 tools/generate_sellsword_sprite_pack.py`
