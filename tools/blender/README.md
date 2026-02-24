# Blender Toolchain (Programmatic)

This folder bootstraps and runs Blender in headless mode for reproducible asset generation.

## Install a pinned Blender build

```bash
python3 tools/blender/install_blender.py --version 4.2.3
```

The installer writes `.tools/blender/manifest.env` with `BLENDER_BIN`.
If direct urllib download is blocked by host policy, the installer now falls back to `wget`/`curl` automatically.

## Run a headless Blender script

```bash
python3 tools/blender/run_blender_headless.py --script tools/blender/scripts/generate_sellsword_3d_assets.py
```

## Current generated outputs

- `assets/3d/generated/sellsword_male.glb`
- `assets/3d/generated/sellsword_female.glb`
- `assets/3d/generated/ground_tile_stone.glb`
- `assets/3d/generated/foliage_grass_a.glb`
- `assets/3d/generated/foliage_tree_dead_a.glb`

Sellsword exports now include a baseline armature and baked action set (`idle`, `walk`, `run`, `attack`, `cast`, `hurt`, `death`) for runtime playback.
