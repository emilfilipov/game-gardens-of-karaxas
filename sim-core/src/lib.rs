//! Shared simulation-domain contracts for Ambitions of Peace.

/// Schema version for shared simulation payloads.
pub const SIM_SCHEMA_VERSION: u32 = 1;

/// Canonical deterministic tick index used by authority services and replay checks.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Tick(pub u64);

impl Tick {
    /// Returns the next deterministic tick value.
    pub fn next(self) -> Self {
        Self(self.0 + 1)
    }
}

#[cfg(test)]
mod tests {
    use super::Tick;

    #[test]
    fn tick_advances_monotonically() {
        let t0 = Tick(41);
        let t1 = t0.next();
        assert_eq!(t1.0, 42);
    }
}
