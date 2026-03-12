//! Shared tooling helpers for code-first authoring and validation surfaces.

/// Tooling manifest version used by import/export pipelines.
pub const TOOLING_MANIFEST_VERSION: u32 = 1;

/// Validates a stable asset key shape used by internal tooling pipelines.
pub fn is_valid_asset_key(value: &str) -> bool {
    !value.is_empty()
        && value
            .chars()
            .all(|ch| ch.is_ascii_lowercase() || ch.is_ascii_digit() || ch == '_' || ch == '-')
}

#[cfg(test)]
mod tests {
    use super::is_valid_asset_key;

    #[test]
    fn accepts_lowercase_keys() {
        assert!(is_valid_asset_key("acres_route_01"));
    }

    #[test]
    fn rejects_uppercase_keys() {
        assert!(!is_valid_asset_key("AcresRoute"));
    }
}
