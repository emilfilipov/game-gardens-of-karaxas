# Plompers Arena Inc. - Art/Tech Reference Board

This board locks the visual baseline for the 3D top-down arena pivot.

## Approved Baseline
- Camera baseline: top-down / Path of Exile-like high-angle gameplay view.
- Palette baseline: black/white/gray by default.
- Color rule: world gains color only through player interaction.
- Mood baseline: high contrast, readable silhouettes, minimal visual noise.

## Camera and Composition
- Core gameplay camera is high-angle top-down with consistent tactical readability.
- Arena floor readability takes priority over cinematic camera behavior.
- UI and world must coexist without obstructing player movement awareness.

## Interaction Colorization Direction
- Untouched assets remain monochrome.
- Interaction events reveal local color (grass turns green on traversal, collision spots colorize).
- Revealed color must remain localized and readable at gameplay zoom.
- Colorization is feedback and territory expression, not random decoration.

## Readability Constraints
- Player avatars must remain legible against monochrome backgrounds.
- Collision/impact feedback must be visible without relying only on hue.
- Critical combat state should still be interpretable in grayscale.

## UI-over-World Composition Rules
- Keep central arena view mostly unobstructed.
- Keep persistent menu/status surfaces compact and themed.
- Ensure graph viewer and account panels remain readable in black/white style.

## Acceptance Criteria
- Canonical docs reference black/white + interaction-colorization baseline.
- Top-down 3D camera rules are explicit.
- Readability constraints are defined for implementation and QA.
