# Cost Guardrails (PoC)

## Objective
Keep monthly GCP spend predictable during PoC development while preserving core release and persistence capabilities.

## Monthly Budget Guardrail
- Target monthly total: **$80 USD**
- Warning threshold: **80%** (`$64`)
- Hard stop/escalation threshold: **100%** (`$80`)

## Service Envelope
- Cloud SQL (PostgreSQL): `$42` baseline (fixed-ish instance cost in current profile)
- Cloud Run: `$8` target for low request volume
- GCS: `$4` target with 3-build retention policy
- Artifact Registry: `$2` target
- Redis/Memorystore: `$0` by default
- Other/network/overhead: `$6` target

## Policy Rules
1. Redis remains disabled by default unless `docs/REDIS_ADOPTION_GATE.md` cutover criteria are met.
2. Release retention remains capped at latest 3 builds.
3. Cloud Run minimum instances remain zero unless a documented reliability exception is approved.
4. Any projected monthly cost above warning threshold requires same-week review.

## Monthly Report Process
1. Generate or refresh report markdown:
   - Estimate mode (default):
     - `backend/scripts/generate_monthly_cost_report.py --month YYYY-MM --output docs/cost-reports/YYYY-MM-estimate.md --budget-total 80`
   - Billing export mode:
     - `backend/scripts/generate_monthly_cost_report.py --month YYYY-MM --billing-csv <billing_export.csv> --output docs/cost-reports/YYYY-MM-report.md --budget-total 80`
2. Review totals against thresholds and annotate unusual spikes.
3. Link the report in release/ops notes for traceability.
4. If threshold is breached, execute mitigation plan (artifact cleanup, Cloud Run review, background task schedule reduction).

## Validation Checklist
- Report file exists for current month under `docs/cost-reports/`.
- Redis line item remains `$0.00` unless adoption gate approved.
- GCS cost trend is consistent with 3-build retention policy.
- Guardrail status is explicitly recorded (`OK`, `WARN`, or `OVER`).
