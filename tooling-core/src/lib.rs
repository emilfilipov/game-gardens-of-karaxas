//! Shared tooling helpers for code-first authoring and validation surfaces.

use std::collections::BTreeSet;
use std::fmt::Write as _;
use std::fs;
use std::path::Path;

use anyhow::{Context, Result, bail};
use csv::{ReaderBuilder, WriterBuilder};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// Tooling manifest version used by import/export pipelines.
pub const TOOLING_MANIFEST_VERSION: u32 = 1;

/// Validates a stable asset key shape used by internal tooling pipelines.
pub fn is_valid_asset_key(value: &str) -> bool {
    !value.is_empty()
        && value
            .chars()
            .all(|ch| ch.is_ascii_lowercase() || ch.is_ascii_digit() || ch == '_' || ch == '-')
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct SettlementRecord {
    pub id: u64,
    pub name: String,
    pub map_x: i32,
    pub map_y: i32,
    pub kind: SettlementKind,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "snake_case")]
pub enum SettlementKind {
    City,
    Fortress,
    Town,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct RouteRecord {
    pub id: u64,
    pub origin: u64,
    pub destination: u64,
    pub travel_hours: u32,
    pub base_risk: u32,
    pub is_sea_route: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct FactionRecord {
    pub id: u64,
    pub name: String,
    pub starting_influence_bp: u32,
    pub treasury: u32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct MarketSeed {
    pub settlement_id: u64,
    pub food: u32,
    pub horses: u32,
    pub materiel: u32,
    pub price_index_bp: u32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct IntelligenceSeed {
    pub id: u64,
    pub handler_faction: u64,
    pub target_faction: u64,
    pub location: u64,
    pub reliability_bp: u32,
    pub deception_bp: u32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct ProvinceContentPack {
    pub manifest_version: u32,
    pub province_id: String,
    pub display_name: String,
    pub settlements: Vec<SettlementRecord>,
    pub routes: Vec<RouteRecord>,
    pub factions: Vec<FactionRecord>,
    pub markets: Vec<MarketSeed>,
    pub intelligence_seeds: Vec<IntelligenceSeed>,
}

impl ProvinceContentPack {
    pub fn normalized(mut self) -> Self {
        self.normalize_in_place();
        self
    }

    pub fn normalize_in_place(&mut self) {
        self.manifest_version = TOOLING_MANIFEST_VERSION;
        self.province_id = self.province_id.trim().to_lowercase();
        self.display_name = normalize_whitespace(&self.display_name);

        for settlement in &mut self.settlements {
            settlement.name = normalize_whitespace(&settlement.name);
        }
        for faction in &mut self.factions {
            faction.name = normalize_whitespace(&faction.name);
        }

        self.settlements.sort_by_key(|row| row.id);
        self.routes.sort_by_key(|row| row.id);
        self.factions.sort_by_key(|row| row.id);
        self.markets.sort_by_key(|row| row.settlement_id);
        self.intelligence_seeds.sort_by_key(|row| row.id);
    }

    pub fn validate(&self) -> std::result::Result<(), Vec<String>> {
        let mut errors = Vec::new();

        if !is_valid_asset_key(&self.province_id) {
            errors.push(format!(
                "Invalid province_id '{}'; use lowercase letters, digits, '-' and '_' only",
                self.province_id
            ));
        }

        if self.settlements.is_empty() {
            errors.push("At least one settlement is required".to_string());
        }
        if self.routes.is_empty() {
            errors.push("At least one route is required".to_string());
        }

        let mut settlement_ids = BTreeSet::new();
        for settlement in &self.settlements {
            if settlement.name.trim().is_empty() {
                errors.push(format!("Settlement {} has an empty name", settlement.id));
            }
            if !settlement_ids.insert(settlement.id) {
                errors.push(format!("Duplicate settlement id {}", settlement.id));
            }
        }

        let mut route_ids = BTreeSet::new();
        for route in &self.routes {
            if route.travel_hours == 0 {
                errors.push(format!("Route {} has travel_hours=0", route.id));
            }
            if route.origin == route.destination {
                errors.push(format!("Route {} origin equals destination", route.id));
            }
            if !route_ids.insert(route.id) {
                errors.push(format!("Duplicate route id {}", route.id));
            }
            if !settlement_ids.contains(&route.origin) {
                errors.push(format!(
                    "Route {} origin settlement {} does not exist",
                    route.id, route.origin
                ));
            }
            if !settlement_ids.contains(&route.destination) {
                errors.push(format!(
                    "Route {} destination settlement {} does not exist",
                    route.id, route.destination
                ));
            }
        }

        let mut faction_ids = BTreeSet::new();
        for faction in &self.factions {
            if faction.name.trim().is_empty() {
                errors.push(format!("Faction {} has an empty name", faction.id));
            }
            if !faction_ids.insert(faction.id) {
                errors.push(format!("Duplicate faction id {}", faction.id));
            }
        }

        for market in &self.markets {
            if !settlement_ids.contains(&market.settlement_id) {
                errors.push(format!(
                    "Market seed references missing settlement {}",
                    market.settlement_id
                ));
            }
        }

        let mut intel_ids = BTreeSet::new();
        for seed in &self.intelligence_seeds {
            if !intel_ids.insert(seed.id) {
                errors.push(format!("Duplicate intelligence seed id {}", seed.id));
            }
            if !faction_ids.contains(&seed.handler_faction) {
                errors.push(format!(
                    "Intelligence seed {} references missing handler faction {}",
                    seed.id, seed.handler_faction
                ));
            }
            if !faction_ids.contains(&seed.target_faction) {
                errors.push(format!(
                    "Intelligence seed {} references missing target faction {}",
                    seed.id, seed.target_faction
                ));
            }
            if !settlement_ids.contains(&seed.location) {
                errors.push(format!(
                    "Intelligence seed {} references missing settlement {}",
                    seed.id, seed.location
                ));
            }
        }

        if errors.is_empty() { Ok(()) } else { Err(errors) }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContentSignature {
    pub manifest_version: u32,
    pub province_id: String,
    pub content_hash_sha256: String,
    pub settlement_count: usize,
    pub route_count: usize,
    pub faction_count: usize,
    pub market_count: usize,
    pub intelligence_seed_count: usize,
}

pub fn normalize_and_validate(mut pack: ProvinceContentPack) -> Result<ProvinceContentPack> {
    pack.normalize_in_place();
    if let Err(errors) = pack.validate() {
        bail!(format_validation_errors(&errors));
    }
    Ok(pack)
}

pub fn read_pack_json(input_path: &Path) -> Result<ProvinceContentPack> {
    let payload =
        fs::read_to_string(input_path).with_context(|| format!("failed reading JSON pack {}", input_path.display()))?;
    let pack = serde_json::from_str::<ProvinceContentPack>(&payload)
        .with_context(|| format!("failed parsing JSON pack {}", input_path.display()))?;
    normalize_and_validate(pack)
}

pub fn write_pack_json(output_path: &Path, pack: &ProvinceContentPack) -> Result<()> {
    if let Some(parent) = output_path.parent()
        && !parent.as_os_str().is_empty()
    {
        fs::create_dir_all(parent).with_context(|| format!("failed creating output directory {}", parent.display()))?;
    }

    let payload = serde_json::to_string_pretty(pack).context("failed serializing normalized JSON pack")?;
    fs::write(output_path, format!("{payload}\n"))
        .with_context(|| format!("failed writing JSON pack {}", output_path.display()))
}

pub fn content_hash_sha256(pack: &ProvinceContentPack) -> Result<String> {
    let canonical = serde_json::to_vec(pack).context("failed serializing canonical pack payload")?;
    let digest = Sha256::digest(canonical);
    Ok(hex_encode(&digest))
}

pub fn build_signature(pack: &ProvinceContentPack) -> Result<ContentSignature> {
    Ok(ContentSignature {
        manifest_version: TOOLING_MANIFEST_VERSION,
        province_id: pack.province_id.clone(),
        content_hash_sha256: content_hash_sha256(pack)?,
        settlement_count: pack.settlements.len(),
        route_count: pack.routes.len(),
        faction_count: pack.factions.len(),
        market_count: pack.markets.len(),
        intelligence_seed_count: pack.intelligence_seeds.len(),
    })
}

pub fn write_signature_json(output_path: &Path, signature: &ContentSignature) -> Result<()> {
    if let Some(parent) = output_path.parent()
        && !parent.as_os_str().is_empty()
    {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed creating signature directory {}", parent.display()))?;
    }

    let payload = serde_json::to_string_pretty(signature).context("failed serializing signature JSON payload")?;
    fs::write(output_path, format!("{payload}\n"))
        .with_context(|| format!("failed writing signature file {}", output_path.display()))
}

pub fn import_pack_from_csv(input_dir: &Path, province_id: &str, display_name: &str) -> Result<ProvinceContentPack> {
    let settlements: Vec<SettlementRecord> = read_csv(&input_dir.join("settlements.csv"))?;
    let routes: Vec<RouteRecord> = read_csv(&input_dir.join("routes.csv"))?;
    let factions: Vec<FactionRecord> = read_csv(&input_dir.join("factions.csv"))?;
    let markets: Vec<MarketSeed> = read_csv(&input_dir.join("markets.csv"))?;
    let intelligence_seeds: Vec<IntelligenceSeed> = read_csv(&input_dir.join("intelligence_seeds.csv"))?;

    normalize_and_validate(ProvinceContentPack {
        manifest_version: TOOLING_MANIFEST_VERSION,
        province_id: province_id.to_string(),
        display_name: display_name.to_string(),
        settlements,
        routes,
        factions,
        markets,
        intelligence_seeds,
    })
}

pub fn export_pack_to_csv(output_dir: &Path, pack: &ProvinceContentPack) -> Result<()> {
    fs::create_dir_all(output_dir)
        .with_context(|| format!("failed creating CSV output directory {}", output_dir.display()))?;

    write_csv(&output_dir.join("settlements.csv"), &pack.settlements)?;
    write_csv(&output_dir.join("routes.csv"), &pack.routes)?;
    write_csv(&output_dir.join("factions.csv"), &pack.factions)?;
    write_csv(&output_dir.join("markets.csv"), &pack.markets)?;
    write_csv(&output_dir.join("intelligence_seeds.csv"), &pack.intelligence_seeds)?;
    Ok(())
}

fn read_csv<T>(path: &Path) -> Result<Vec<T>>
where
    T: for<'de> Deserialize<'de>,
{
    let mut reader = ReaderBuilder::new()
        .trim(csv::Trim::All)
        .from_path(path)
        .with_context(|| format!("failed opening CSV {}", path.display()))?;

    let mut rows = Vec::new();
    for item in reader.deserialize::<T>() {
        let row = item.with_context(|| format!("failed parsing CSV row in {}", path.display()))?;
        rows.push(row);
    }
    Ok(rows)
}

fn write_csv<T>(path: &Path, rows: &[T]) -> Result<()>
where
    T: Serialize,
{
    let mut writer = WriterBuilder::new()
        .has_headers(true)
        .from_path(path)
        .with_context(|| format!("failed creating CSV {}", path.display()))?;

    for row in rows {
        writer
            .serialize(row)
            .with_context(|| format!("failed writing CSV row to {}", path.display()))?;
    }
    writer
        .flush()
        .with_context(|| format!("failed flushing CSV {}", path.display()))
}

fn format_validation_errors(errors: &[String]) -> String {
    let mut message = String::new();
    for (index, error) in errors.iter().enumerate() {
        let _ = writeln!(&mut message, "{}. {}", index + 1, error);
    }
    message
}

fn normalize_whitespace(value: &str) -> String {
    value.split_whitespace().collect::<Vec<_>>().join(" ")
}

fn hex_encode(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        let _ = write!(&mut output, "{byte:02x}");
    }
    output
}

#[cfg(test)]
mod tests {
    use std::fs;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    use super::{
        FactionRecord, IntelligenceSeed, MarketSeed, ProvinceContentPack, RouteRecord, SettlementKind,
        SettlementRecord, TOOLING_MANIFEST_VERSION, build_signature, content_hash_sha256, export_pack_to_csv,
        import_pack_from_csv, is_valid_asset_key, normalize_and_validate,
    };

    fn sample_pack() -> ProvinceContentPack {
        ProvinceContentPack {
            manifest_version: TOOLING_MANIFEST_VERSION,
            province_id: "acre_region".to_string(),
            display_name: " Acre   Province  ".to_string(),
            settlements: vec![
                SettlementRecord {
                    id: 2,
                    name: "Acre Citadel".to_string(),
                    map_x: 24,
                    map_y: -80,
                    kind: SettlementKind::Fortress,
                },
                SettlementRecord {
                    id: 1,
                    name: " Acre  Port ".to_string(),
                    map_x: -80,
                    map_y: 30,
                    kind: SettlementKind::City,
                },
            ],
            routes: vec![
                RouteRecord {
                    id: 12,
                    origin: 2,
                    destination: 1,
                    travel_hours: 5,
                    base_risk: 900,
                    is_sea_route: false,
                },
                RouteRecord {
                    id: 11,
                    origin: 1,
                    destination: 2,
                    travel_hours: 5,
                    base_risk: 850,
                    is_sea_route: false,
                },
            ],
            factions: vec![FactionRecord {
                id: 7,
                name: "Kingdom of Jerusalem".to_string(),
                starting_influence_bp: 7200,
                treasury: 800,
            }],
            markets: vec![
                MarketSeed {
                    settlement_id: 2,
                    food: 140,
                    horses: 30,
                    materiel: 80,
                    price_index_bp: 10_900,
                },
                MarketSeed {
                    settlement_id: 1,
                    food: 300,
                    horses: 60,
                    materiel: 170,
                    price_index_bp: 10_200,
                },
            ],
            intelligence_seeds: vec![IntelligenceSeed {
                id: 51,
                handler_faction: 7,
                target_faction: 7,
                location: 1,
                reliability_bp: 7600,
                deception_bp: 900,
            }],
        }
    }

    fn temp_dir(name: &str) -> PathBuf {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system clock must be after UNIX_EPOCH")
            .as_nanos();
        let path = std::env::temp_dir().join(format!("tooling-core-{name}-{timestamp}"));
        fs::create_dir_all(&path).expect("temp dir must be created");
        path
    }

    #[test]
    fn accepts_lowercase_keys() {
        assert!(is_valid_asset_key("acres_route_01"));
    }

    #[test]
    fn rejects_uppercase_keys() {
        assert!(!is_valid_asset_key("AcresRoute"));
    }

    #[test]
    fn normalization_is_deterministic() {
        let normalized = normalize_and_validate(sample_pack()).expect("pack should normalize");
        let hash_1 = content_hash_sha256(&normalized).expect("hash should be generated");
        let hash_2 = content_hash_sha256(&normalized).expect("hash should be generated");

        assert_eq!(normalized.display_name, "Acre Province");
        assert_eq!(normalized.settlements[0].id, 1);
        assert_eq!(hash_1, hash_2);
    }

    #[test]
    fn csv_roundtrip_and_signature_are_stable() {
        let normalized = normalize_and_validate(sample_pack()).expect("pack should normalize");
        let out_dir = temp_dir("csv-roundtrip");
        export_pack_to_csv(&out_dir, &normalized).expect("CSV export should succeed");

        let imported = import_pack_from_csv(&out_dir, &normalized.province_id, &normalized.display_name)
            .expect("CSV import should succeed");
        assert_eq!(imported, normalized);

        let sig_1 = build_signature(&normalized).expect("signature should be generated");
        let sig_2 = build_signature(&imported).expect("signature should be generated");
        assert_eq!(sig_1, sig_2);

        fs::remove_dir_all(out_dir).expect("temp dir cleanup should succeed");
    }

    #[test]
    fn converter_output_matches_snapshot() {
        let normalized = normalize_and_validate(sample_pack()).expect("pack should normalize");
        let json = serde_json::to_string_pretty(&normalized).expect("json serialization should succeed");
        let expected = r#"{
  "manifest_version": 1,
  "province_id": "acre_region",
  "display_name": "Acre Province",
  "settlements": [
    {
      "id": 1,
      "name": "Acre Port",
      "map_x": -80,
      "map_y": 30,
      "kind": "city"
    },
    {
      "id": 2,
      "name": "Acre Citadel",
      "map_x": 24,
      "map_y": -80,
      "kind": "fortress"
    }
  ],
  "routes": [
    {
      "id": 11,
      "origin": 1,
      "destination": 2,
      "travel_hours": 5,
      "base_risk": 850,
      "is_sea_route": false
    },
    {
      "id": 12,
      "origin": 2,
      "destination": 1,
      "travel_hours": 5,
      "base_risk": 900,
      "is_sea_route": false
    }
  ],
  "factions": [
    {
      "id": 7,
      "name": "Kingdom of Jerusalem",
      "starting_influence_bp": 7200,
      "treasury": 800
    }
  ],
  "markets": [
    {
      "settlement_id": 1,
      "food": 300,
      "horses": 60,
      "materiel": 170,
      "price_index_bp": 10200
    },
    {
      "settlement_id": 2,
      "food": 140,
      "horses": 30,
      "materiel": 80,
      "price_index_bp": 10900
    }
  ],
  "intelligence_seeds": [
    {
      "id": 51,
      "handler_faction": 7,
      "target_faction": 7,
      "location": 1,
      "reliability_bp": 7600,
      "deception_bp": 900
    }
  ]
}"#;

        assert_eq!(json, expected);
    }
}
