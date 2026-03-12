# Tower Navigation Admin Checklist

Use this checklist when validating two linked levels end-to-end after a level/content publish.

## Preconditions
- Log in with an admin account.
- Confirm at least two levels exist in `Level Order`.
- Confirm each level has a spawn marker.
- Confirm each level has at least one transition tile (`stairs`, `ladder`, or `elevator`) linking to the other level.

## Authoring Validation
1. Open `Level Editor`.
2. Load `Level A`, place/update transition tile destination to `Level B`, then `Save Local`.
3. Load `Level B`, place/update transition tile destination to `Level A`, then `Save Local`.
4. Click `Publish Changes`.
5. Verify publish succeeds and local draft queue is cleared.

## Ordering Validation
1. Open `Level Order`.
2. Drag/drop `Level A` and `Level B` into intended floor order.
3. Click `Publish Order`.
4. Re-open `Level Order` and confirm ordering persisted.

## Gameplay Validation
1. From `Character List`, select a character and click `Play`.
2. Confirm only gameplay scene is visible (no stacked account/admin cards underneath).
3. Move toward transition in `Level A` and verify adjacent floor preloads (no blocking load screen).
4. Step on transition and verify handoff to `Level B` happens in-scene.
5. Repeat back to `Level A`.
6. Use cog menu -> `Logout Character` and confirm gameplay scene is cleared and account cards are visible without overlap artifacts.

## Metrics Validation (Ops)
1. Query `GET /ops/release/metrics` with ops token.
2. Check `zone_runtime.preload_latency_ms` has samples.
3. Check `zone_runtime.transition_handoff` counters increment after transitions.
4. Check `zone_runtime.zone_scope_updates_total` increments after entering/leaving gameplay.
5. Check `zone_runtime.zone_broadcast` counters increment when multiple clients are in scoped zones.
