# Monthly Cost Report - 2026-03

- Project: `ambitions-of-peace`
- Source: `estimate_defaults`
- Generated at: `2026-03-12T20:20:05.161862+00:00`
- Budget guardrail: `$80.00`

| Component | Cost (USD) | Status |
| --- | ---: | --- |
| Cloud Run | $8.00 | OK |
| Cloud SQL | $42.00 | OK |
| GCS | $4.00 | OK |
| Artifact Registry | $2.00 | OK |
| Redis/Memorystore | $0.00 | OK |
| Other | $6.00 | OK |

- Total estimated/observed monthly cost: `$62.00`
- Guardrail status: `OK`

## Notes
- Redis is expected to remain `$0.00` unless `docs/REDIS_ADOPTION_GATE.md` conditions are met.
- Keep release retention at latest 3 builds to control GCS growth.
