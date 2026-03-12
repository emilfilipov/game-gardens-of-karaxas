# ADR-0001: Rust-First Runtime and Services

- Status: accepted
- Date: 2026-03-12
- Deciders: project owner + implementation agent
- Related tasks: `AOP-PIVOT-003`, `AOP-PIVOT-004`, `AOP-PIVOT-005`, `AOP-PIVOT-006`

## Context
The repository currently mixes Kotlin, Godot, and Python components from prior prototype directions. The active product direction requires high simulation performance, deterministic behavior, and long-term maintainability for an online persistent world.

## Decision
Adopt Rust as the primary implementation language for new runtime modules, gameplay simulation crates, and world-authority services.

## Consequences
- Positive:
  - Single-language core architecture across simulation, services, and tooling paths.
  - Strong safety/performance profile for authoritative simulation workloads.
  - Improved reuse through shared domain crates.
- Tradeoffs:
  - Migration cost from existing prototype modules.
  - Team/tooling learning overhead where Rust is new.

## Notes
This decision does not require immediate removal of existing FastAPI/Kotlin/Godot modules; those remain transitional until replacement milestones are met.
