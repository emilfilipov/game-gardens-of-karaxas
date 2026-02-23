# Steam Dual Distribution Plan

## Goal
Run two supported distribution channels in parallel:
- `standalone` (Velopack + GCS feed, current default)
- `steam` (Steam depot/channel delivery)

## Channel Contract
- Every client build publishes:
  - `build_version` (binary/package version)
  - `content_version` (runtime gameplay config/content signature)
  - `channel` (`standalone` or `steam`)
- Backend release policy evaluates minimum-supported build/content **per channel**.
- Forced update + grace/drain behavior is channel-aware.

## Channel Routing
- Standalone:
  - login/update checks use `update_feed_url` from release policy.
  - updater executes via UpdateHelper/Velopack.
- Steam:
  - login/update checks still enforce backend min-supported versions.
  - update execution is delegated to Steam client/depot flow.

## Backend Changes Required
- Extend release policy model with channel partitions:
  - latest/min build per channel
  - latest/min content per channel
- Keep shared gameplay/content contract validation identical across channels.
- Session drain notifications include channel reason text.

## Client Changes Required
- Add immutable runtime channel identifier in bootstrap headers.
- Update UX messaging:
  - `standalone`: "Update via launcher"
  - `steam`: "Update via Steam client"

## CI/CD Mapping
- `release.yml` publishes standalone artifacts to GCS feed.
- Steam publish pipeline (separate workflow) packages the same game payload into Steam depots.
- Both pipelines call backend ops release endpoints with channel-targeted policy fields.

## Security/Support Notes
- Channel separation reduces accidental cross-channel lockouts.
- Preserve crash/log telemetry format across channels to keep ops workflow identical.
