# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Current Program
- Program name: `AOP-CHARACTER-DEPTH-001`
- Program objective: implement deep character identity at creation time (permanent tradeoffs) and an XP-driven, benefits-only skill book progression system with education/language specialization.
- Canonical references:
  - `docs/GAME.md`
  - `docs/TECHNICAL.md`

## Active Backlog
| Task ID | Status | Complexity | Depends On | Detailed Description |
| --- | --- | --- | --- | --- |
| AOP-PIVOT-051 | ⬜ | 2 | - | Define canonical character-identity contract: `Faction`, `Origin`, `Profession`, `Aspiration` are permanent per-character picks and each pick must always provide one explicit upside plus one explicit downside. |
| AOP-PIVOT-052 | ⬜ | 3 | AOP-PIVOT-051 | Define canonical education/skill-book contract: education is not a creation tradeoff; it is a separate XP-investment progression surface with benefits-only nodes (combat, trade, diplomacy, logistics, espionage, language, etc.). |
| AOP-PIVOT-053 | ⬜ | 4 | AOP-PIVOT-051 | Implement schema + migrations for identity picks, modifier packs, skill-book categories/nodes, XP ledger, and per-language proficiency (`speak/read/write`). |
| AOP-PIVOT-054 | ⬜ | 3 | AOP-PIVOT-053 | Implement backend reference-data APIs for character creation options (factions/origins/professions/aspirations), including exposed upside/downside previews and validation contracts. |
| AOP-PIVOT-055 | ⬜ | 4 | AOP-PIVOT-054 | Extend backend character-creation pipeline to persist permanent identity picks and enforce immutable-after-creation constraints (except future explicit respec mechanics, out of current scope). |
| AOP-PIVOT-056 | ⬜ | 4 | AOP-PIVOT-053 | Implement XP progression subsystem and skill-book spend flow (authoritative spend validation, unlock prerequisites, idempotency, audit trail, rollback-safe transactions). |
| AOP-PIVOT-057 | ⬜ | 4 | AOP-PIVOT-056 | Implement language proficiency mechanics tied to education skill book: communication checks, document readability/intercepted-letter comprehension gates, and interpreter/translator fallback contracts. |
| AOP-PIVOT-058 | ⬜ | 3 | AOP-PIVOT-055 | Implement client character-creator UI upgrade with all four permanent identity layers plus transparent upside/downside presentation and creation-time validation errors. |
| AOP-PIVOT-059 | ⬜ | 4 | AOP-PIVOT-057 | Implement client skill-book UI with XP spend controls, language progression widgets, unlock previews, and authoritative sync/error handling for failed spends. |
| AOP-PIVOT-060 | ⬜ | 4 | AOP-PIVOT-058, AOP-PIVOT-059 | Integrate identity and skill-book effects across gameplay systems (trade/diplomacy/espionage/logistics/combat interactions), add deterministic regression tests, and tune baseline balance matrix. |

## Detailed Task Specs

### AOP-PIVOT-051 - Character Identity Contract
- Objective: lock game-design contract for permanent identity choices.
- Implementation checklist:
  - define `Faction`, `Origin`, `Profession`, `Aspiration` as required creation picks,
  - define permanent/immutable behavior,
  - define mandatory `upside + downside` pair requirement for each selectable option,
  - define modifier budget rules to prevent strictly-better options.
- Acceptance criteria:
  - canonical docs describe the same immutable/tradeoff rules,
  - no creation option exists without both upside and downside.
- Validation:
  - manual doc review across canonical docs,
  - schema/seed lint enforcing upside+downside presence.

### AOP-PIVOT-052 - Education + Skill-Book Contract
- Objective: define education/skills as XP-based benefits-only progression independent of creation tradeoffs.
- Implementation checklist:
  - define major skill-book domains,
  - define XP spend and unlock prerequisite model,
  - define language proficiency dimensions (`speak`, `read`, `write`) and level ranges,
  - define progression-only benefits policy (no direct downside entries inside skill book nodes).
- Acceptance criteria:
  - education is clearly separated from creator tradeoff layers,
  - XP spending contract is deterministic and auditable.
- Validation:
  - doc review + API/schema contract review.

### AOP-PIVOT-053 - Persistence Model for Identity + Skill Book
- Objective: establish durable data model for all new systems.
- Implementation checklist:
  - add identity option definition tables (or static packs + version metadata),
  - add per-character identity selection record,
  - add skill-book node definitions and per-character node progress,
  - add XP event ledger and spend journal,
  - add language proficiency table keyed by character/language/dimension.
- Acceptance criteria:
  - migrations apply/rollback cleanly,
  - model supports deterministic read/write for creator + progression flows.
- Validation:
  - migration tests,
  - backend model tests for FK integrity and uniqueness constraints.

### AOP-PIVOT-054 - Creator Reference Data APIs
- Objective: expose creator options and modifier previews to client.
- Implementation checklist:
  - add endpoint for all creation choices grouped by layer,
  - include structured upside/downside payloads and balance metadata,
  - include validation codes for disallowed/invalid combinations.
- Acceptance criteria:
  - client can fully render creator options from API without hardcoded lists,
  - invalid payloads produce stable error codes.
- Validation:
  - API contract tests,
  - response snapshot tests.

### AOP-PIVOT-055 - Character Creation Pipeline Upgrade
- Objective: persist permanent identity picks at creation time.
- Implementation checklist:
  - extend create-character payload/schema,
  - validate required layers and selected option IDs,
  - persist immutable identity selection,
  - surface clear error messages for bad combinations.
- Acceptance criteria:
  - newly created characters always contain four identity picks,
  - downstream reads include selected identity metadata.
- Validation:
  - backend tests for success/failure cases,
  - regression tests for existing auth/session/character flows.

### AOP-PIVOT-056 - XP Spend + Skill Book Authority
- Objective: implement authoritative XP progression engine.
- Implementation checklist:
  - define XP gain/earn event interface,
  - implement spend endpoint with idempotency keys,
  - enforce node prerequisites and max ranks,
  - persist spend journal + resulting progression snapshot.
- Acceptance criteria:
  - XP cannot go negative,
  - duplicate spend requests are safely idempotent,
  - progression changes are audit-traceable.
- Validation:
  - unit tests for spend/prerequisite logic,
  - integration tests for concurrent spend attempts.

### AOP-PIVOT-057 - Language and Education Mechanics
- Objective: make language knowledge mechanically meaningful.
- Implementation checklist:
  - implement skill-book language nodes,
  - implement conversation comprehension checks,
  - implement document readability checks (letters/reports/intercepts),
  - implement NPC helper contracts (interpreter/translator) with cost/time/accuracy tradeoffs.
- Acceptance criteria:
  - characters lacking language levels cannot fully access relevant content directly,
  - helper path provides alternative with explicit cost/latency/risk.
- Validation:
  - test matrix for language thresholds,
  - gameplay route tests for read/communicate gating behavior.

### AOP-PIVOT-058 - Client Character Creator Expansion
- Objective: ship full creator UX for permanent identity choices.
- Implementation checklist:
  - implement four-layer creator flow,
  - display upside/downside in clear side-by-side UI,
  - block submission until all required layers selected,
  - surface backend validation errors inline.
- Acceptance criteria:
  - player can complete creator without hidden defaults,
  - tradeoff impact is visible before submit.
- Validation:
  - UI/state unit tests,
  - manual creator smoke run.

### AOP-PIVOT-059 - Client Skill Book UI
- Objective: ship in-client XP investment UX.
- Implementation checklist:
  - render categorized skill tree/book,
  - render current XP and per-node cost/requirements,
  - add language proficiency panel (`speak/read/write`) as part of education category,
  - handle optimistic request state + authoritative rollback on rejection.
- Acceptance criteria:
  - XP spends update UI from authoritative responses,
  - failed spends produce clear non-destructive error surfaces.
- Validation:
  - client tests for adapter/state transitions,
  - backend+client integration smoke for spend flow.

### AOP-PIVOT-060 - Gameplay Integration + Balancing
- Objective: integrate modifiers into core loops and prevent dominant builds.
- Implementation checklist:
  - wire creator identity modifiers into diplomacy/trade/espionage/logistics/combat checks,
  - wire education/language effects into communication and intel/document systems,
  - add deterministic regression harness for modifier interactions,
  - publish initial balancing matrix with guardrail thresholds.
- Acceptance criteria:
  - modifiers measurably affect outcomes in intended systems,
  - no obvious strictly-dominant creator archetype in baseline simulation tests.
- Validation:
  - deterministic scenario tests,
  - balance report/checklist artifact in docs.

## Sequencing Guide (Strict Order)
1. Design contracts: `AOP-PIVOT-051`, `AOP-PIVOT-052`.
2. Persistence and API foundation: `AOP-PIVOT-053` to `AOP-PIVOT-055`.
3. XP/education mechanics: `AOP-PIVOT-056`, `AOP-PIVOT-057`.
4. Client experience: `AOP-PIVOT-058`, `AOP-PIVOT-059`.
5. Integration and balance hardening: `AOP-PIVOT-060`.

## Resume Protocol
When work resumes after a pause:
1. Read `docs/GAME.md` and `docs/TECHNICAL.md` first.
2. Continue from the first non-`✅` task in sequencing order.
3. Do not start a higher-order task until dependencies are complete.
4. For each completed task, update this file in the same commit.
