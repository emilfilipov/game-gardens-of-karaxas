# ADR-0002: Bevy with Code-First UI and Tooling

- Status: accepted
- Date: 2026-03-12
- Deciders: project owner + implementation agent
- Related tasks: `AOP-PIVOT-003`, `AOP-PIVOT-020`, `AOP-PIVOT-022`, `AOP-PIVOT-023`

## Context
The product requires that gameplay systems, UI, and authoring tools are created and maintained programmatically, without dependence on a game engine's visual editor for core workflow.

## Decision
Use Bevy as the runtime framework and `bevy_egui` for code-defined in-game UI and internal authoring surfaces.

## Consequences
- Positive:
  - Full code ownership of UI/tooling and easier diff/review in source control.
  - Consistent architecture with Rust-first decision.
  - Fast iteration on gameplay/editor logic without scene-editor coupling.
- Tradeoffs:
  - More custom UI/layout engineering effort than editor-driven approaches.
  - Fewer out-of-the-box high-level tool interfaces compared with traditional engines.

## Notes
Legacy Godot client remains transitional until Bevy client reaches feature parity needed by migration milestones.
