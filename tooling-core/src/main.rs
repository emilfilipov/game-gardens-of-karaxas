use std::path::PathBuf;

use anyhow::Result;
use clap::{Parser, Subcommand};
use tooling_core::{
    build_signature, export_pack_to_csv, import_pack_from_csv, read_pack_json, write_pack_json, write_signature_json,
};

#[derive(Debug, Parser)]
#[command(name = "tooling-core")]
#[command(about = "Ambitions of Peace content tooling CLI")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Normalize and validate a JSON content pack file.
    NormalizeJson {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        output: PathBuf,
        #[arg(long)]
        signature_output: Option<PathBuf>,
    },
    /// Import province content from CSV files and emit normalized JSON.
    ImportCsv {
        #[arg(long)]
        input_dir: PathBuf,
        #[arg(long)]
        province_id: String,
        #[arg(long)]
        display_name: String,
        #[arg(long)]
        output: PathBuf,
        #[arg(long)]
        signature_output: Option<PathBuf>,
    },
    /// Export a normalized JSON content pack to deterministic CSV files.
    ExportCsv {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        output_dir: PathBuf,
        #[arg(long)]
        signature_output: Option<PathBuf>,
    },
    /// Print deterministic SHA256 hash for a normalized JSON pack.
    Hash {
        #[arg(long)]
        input: PathBuf,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Command::NormalizeJson {
            input,
            output,
            signature_output,
        } => {
            let pack = read_pack_json(&input)?;
            write_pack_json(&output, &pack)?;
            if let Some(path) = signature_output {
                write_signature_json(&path, &build_signature(&pack)?)?;
            }
        }
        Command::ImportCsv {
            input_dir,
            province_id,
            display_name,
            output,
            signature_output,
        } => {
            let pack = import_pack_from_csv(&input_dir, &province_id, &display_name)?;
            write_pack_json(&output, &pack)?;
            if let Some(path) = signature_output {
                write_signature_json(&path, &build_signature(&pack)?)?;
            }
        }
        Command::ExportCsv {
            input,
            output_dir,
            signature_output,
        } => {
            let pack = read_pack_json(&input)?;
            export_pack_to_csv(&output_dir, &pack)?;
            if let Some(path) = signature_output {
                write_signature_json(&path, &build_signature(&pack)?)?;
            }
        }
        Command::Hash { input } => {
            let pack = read_pack_json(&input)?;
            let signature = build_signature(&pack)?;
            println!("{}", signature.content_hash_sha256);
        }
    }

    Ok(())
}
