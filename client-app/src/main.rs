use sim_core::{SIM_SCHEMA_VERSION, Tick};

fn main() {
    let first_tick = Tick(1);
    println!(
        "Ambitions of Peace client-app scaffold (schema={}, tick={})",
        SIM_SCHEMA_VERSION, first_tick.0
    );
}
