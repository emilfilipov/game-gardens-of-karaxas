# Acre Province PoC Pack

This directory is the first playable province content pack (`AOP-PIVOT-025`).

## Contents
- `settlements.csv` - one city (`Acre Port`) and one fortress (`Montmusard Fortress`)
- `routes.csv` - connected land and sea routes between both settlements
- `factions.csv` - two starting factions with initial influence/treasury distribution
- `markets.csv` - baseline market inventory and price pressure seeds
- `intelligence_seeds.csv` - baseline informant seeds for both factions
- `acre_poc_v1.json` - normalized deterministic pack generated from CSV
- `acre_poc_v1.sig.json` - deterministic SHA256 signature metadata for the pack

## Regeneration
Run from repository root:

```bash
cargo run -p tooling-core -- import-csv \
  --input-dir assets/content/provinces/acre \
  --province-id acre_poc_v1 \
  --display-name "Acre Province PoC" \
  --output assets/content/provinces/acre/acre_poc_v1.json \
  --signature-output assets/content/provinces/acre/acre_poc_v1.sig.json
```

