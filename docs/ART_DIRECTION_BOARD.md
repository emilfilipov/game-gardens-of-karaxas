# Gardens of Karaxas - Art/Tech Reference Board (GOK-MMO-174)

This board locks the visual-direction baseline for the isometric migration.

## Approved Baseline
- Projection: `2:1` isometric (dimetric), not true isometric.
- Camera baseline: slightly zoomed-out MMO view.
- Palette/mood baseline: vibrant + warm color palette with soft global lighting.
- Mood flexibility: localized effect layers can shift specific items/characters/zones toward grim-dark presentation.

## Projection and Camera
- World tile footprint target: `64x32` logical diamonds for authored gameplay space.
- Character authoring target: `128x128` frame space for primary actor sheets.
- Default gameplay zoom: `0.80x`.
- Supported runtime zoom range: `0.70x` to `1.10x`.
- Camera behavior goal: preserve broad world visibility while maintaining readable silhouettes and interaction clarity.

## Color and Lighting Direction
- Primary mood: warm/vibrant base world.
- Global lighting target: soft and readable (no harsh global contrast by default).
- Effect layering model:
  - Global baseline lighting/post profile.
  - Per-zone mood overrides.
  - Per-character/item overlays (for example glints, fog aura, rune glow, grim tinting).

## Palette Tokens (Baseline)
- `karaxas_bg_warm`: `#3A261B`
- `karaxas_surface_amber`: `#7B5132`
- `karaxas_highlight_gold`: `#C79A5A`
- `karaxas_ui_text`: `#F4E6C5`
- `karaxas_grass_warm`: `#6C8A4D`
- `karaxas_stone_warm`: `#8B735C`
- `karaxas_accent_fire`: `#D96A3A`
- `karaxas_shadow_soft`: `#1E1612`

## Readability Constraints
- Interactive entities should remain legible against local background at all times.
- Player/hostile silhouettes must remain distinguishable during overlapping VFX.
- Status-critical visuals (damage zones, interaction prompts, pickups) cannot rely on color alone; shape/icon support required.
- Darkening overrides must not collapse UI/world readability (maintain contrast floor for text and interactables).

## UI-over-World Composition Rules
- Preserve a top safe band for persistent controls/title context.
- Preserve a bottom safe band for version/status/footer context.
- Keep central gameplay area primarily unobstructed by persistent panels.
- Modal/popup overlays must be themed and translucent enough to preserve world context while foregrounding interaction.

## Acceptance Criteria for GOK-MMO-174
- Canonical docs reference this board as the source for visual-direction lock.
- Projection/camera/scale values are explicitly fixed.
- Warm/vibrant baseline and grim-dark override strategy are explicitly documented.
- Readability and UI-over-world constraints are defined for downstream implementation tasks.
