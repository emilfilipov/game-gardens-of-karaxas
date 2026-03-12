use sim_core::{SIM_SCHEMA_VERSION, Tick};

fn main() {
    let boot_tick = Tick(0);
    println!(
        "Ambitions of Peace world-service scaffold (schema={}, tick={})",
        SIM_SCHEMA_VERSION, boot_tick.0
    );
}
