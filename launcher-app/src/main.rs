#![cfg_attr(target_os = "windows", windows_subsystem = "windows")]

use std::env;
use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::mpsc::{self, Receiver, Sender};
use std::thread;
use std::time::Duration;

use anyhow::{Context, Result, anyhow, bail};
use eframe::egui;
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use sha2::Digest;
use zip::ZipArchive;

const DEFAULT_API_BASE_URL: &str = match option_env!("AOP_DEFAULT_API_BASE_URL") {
    Some(url) => url,
    None => "https://karaxas-backend-rss3xj2ixq-ew.a.run.app",
};
const DEFAULT_GAME_FEED_URL: &str = "https://storage.googleapis.com/karaxas-releases-lustrous-bond-298815/win-game";
const APP_TITLE: &str = "Ambitions of Peace";

#[derive(Debug)]
enum WorkerEvent {
    Status(String),
    NewsLoaded {
        latest_version: String,
        notes: String,
        feed_url: Option<String>,
        content_version_key: String,
    },
    DownloadProgress {
        downloaded: u64,
        total: Option<u64>,
    },
    InstallProgress {
        fraction: f32,
        message: String,
    },
    Finished(Result<String, String>),
}

#[derive(Debug, Deserialize)]
struct ReleaseSummaryResponse {
    latest_version: String,
    #[serde(default)]
    update_feed_url: Option<String>,
    #[serde(default)]
    client_content_version_key: String,
    #[serde(default)]
    latest_content_version_key: String,
    #[serde(default)]
    min_supported_content_version_key: String,
    #[serde(default)]
    latest_user_facing_notes: String,
    #[serde(default)]
    latest_build_release_notes: String,
}

#[derive(Debug, Serialize)]
struct LoginRequest {
    email: String,
    password: String,
    otp_code: Option<String>,
    client_version: String,
    client_content_version_key: String,
}

#[derive(Debug, Deserialize)]
struct SessionResponse {
    access_token: String,
    refresh_token: String,
    session_id: String,
    user_id: u64,
    email: String,
    display_name: String,
    version_status: VersionStatus,
}

#[derive(Debug, Deserialize)]
struct VersionStatus {
    latest_version: String,
    #[serde(default)]
    update_feed_url: Option<String>,
    #[serde(default)]
    client_content_version_key: String,
    #[serde(default)]
    latest_content_version_key: String,
}

#[derive(Debug, Deserialize)]
struct LatestFeedPayload {
    version: String,
    #[serde(default)]
    installer_artifact: Option<String>,
    #[serde(default)]
    installer_checksum: Option<String>,
    #[serde(default)]
    deltas: Vec<DeltaFeedEntry>,
}

#[derive(Debug, Deserialize, Clone)]
struct DeltaFeedEntry {
    from_version: String,
    artifact: String,
    #[serde(default)]
    checksum: Option<String>,
}

#[derive(Debug, Deserialize)]
struct DeltaManifest {
    #[serde(default)]
    changed_files: Vec<String>,
    #[serde(default)]
    removed_files: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct ApiErrorEnvelope {
    #[serde(default)]
    detail: Option<ApiErrorDetail>,
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
enum ApiErrorDetail {
    MessageMap {
        message: Option<String>,
        code: Option<String>,
    },
    Plain(String),
}

#[derive(Debug, Serialize)]
struct StartupHandoff {
    schema_version: u32,
    email: String,
    access_token: String,
    refresh_token: String,
    session_id: String,
    user_id: u64,
    display_name: String,
    api_base_url: String,
    client_version: String,
    client_content_version_key: String,
}

struct LauncherApp {
    api_base_url: String,
    feed_url: String,
    install_dir: PathBuf,
    email: String,
    password: String,
    otp_code: String,
    local_version: String,
    latest_version: String,
    client_content_version_key: String,
    news_notes: String,
    status_line: String,
    progress: f32,
    progress_label: String,
    busy: bool,
    pending_minimize: bool,
    tx: Sender<WorkerEvent>,
    rx: Receiver<WorkerEvent>,
}

impl LauncherApp {
    fn new() -> Self {
        let (tx, rx) = mpsc::channel();
        let install_dir = default_install_dir();
        let local_version = read_installed_version(&install_dir).unwrap_or_else(|_| "not installed".to_string());

        let mut app = Self {
            api_base_url: env_or_default("AOP_API_BASE_URL", DEFAULT_API_BASE_URL),
            feed_url: env_or_default("AOP_GAME_FEED_URL", DEFAULT_GAME_FEED_URL),
            install_dir,
            email: String::new(),
            password: String::new(),
            otp_code: String::new(),
            local_version,
            latest_version: "checking...".to_string(),
            client_content_version_key: "unknown".to_string(),
            news_notes: "Loading latest release notes...".to_string(),
            status_line: "Ready".to_string(),
            progress: 0.0,
            progress_label: String::new(),
            busy: false,
            pending_minimize: false,
            tx,
            rx,
        };
        app.refresh_news();
        app
    }

    fn refresh_news(&mut self) {
        if self.busy {
            return;
        }
        let api_base_url = self.api_base_url.clone();
        let client_version = self.local_version.clone();
        let client_content_version_key = self.client_content_version_key.clone();
        let fallback_feed_url = self.feed_url.clone();
        let tx = self.tx.clone();
        self.status_line = "Fetching latest news and patch notes...".to_string();
        thread::spawn(move || {
            let result = fetch_release_summary(&api_base_url, &client_version, &client_content_version_key);
            match result {
                Ok(summary) => {
                    let notes = choose_notes(&summary);
                    let selected_content_key = select_declared_content_key(&summary);
                    let mut latest_version = normalize_version(&summary.latest_version);
                    let feed_candidates =
                        collect_feed_candidates(summary.update_feed_url.as_deref(), None, &fallback_feed_url);
                    let mut selected_feed_url = summary.update_feed_url.clone();
                    for candidate in &feed_candidates {
                        if let Ok(feed_payload) = fetch_latest_feed(candidate)
                            && !feed_payload.version.trim().is_empty()
                        {
                            latest_version = normalize_version(&feed_payload.version);
                            selected_feed_url = Some(candidate.clone());
                            break;
                        }
                    }
                    let _ = tx.send(WorkerEvent::NewsLoaded {
                        latest_version,
                        notes,
                        feed_url: selected_feed_url,
                        content_version_key: selected_content_key,
                    });
                    let _ = tx.send(WorkerEvent::Status("News refreshed".to_string()));
                }
                Err(error) => {
                    if let Ok(feed_payload) = fetch_latest_feed(&fallback_feed_url) {
                        let _ = tx.send(WorkerEvent::NewsLoaded {
                            latest_version: normalize_version(&feed_payload.version),
                            notes: "Release notes are temporarily unavailable.".to_string(),
                            feed_url: Some(fallback_feed_url.clone()),
                            content_version_key: "unknown".to_string(),
                        });
                    }
                    let _ = tx.send(WorkerEvent::Status(format!("News fetch failed: {error}")));
                }
            }
        });
    }

    fn login_update_and_play(&mut self) {
        if self.busy {
            return;
        }
        if self.email.trim().is_empty() || self.password.trim().is_empty() {
            self.status_line = "Email and password are required.".to_string();
            return;
        }

        let tx = self.tx.clone();
        let input = LaunchInput {
            api_base_url: self.api_base_url.clone(),
            configured_feed_url: self.feed_url.clone(),
            install_dir: self.install_dir.clone(),
            email: self.email.trim().to_string(),
            password: self.password.clone(),
            otp_code: trimmed_or_none(&self.otp_code),
            installed_version: self.local_version.clone(),
        };

        self.busy = true;
        self.progress = 0.0;
        self.progress_label = "Starting...".to_string();
        self.status_line = "Authenticating...".to_string();

        thread::spawn(move || {
            let result = run_login_update_launch(input, tx.clone()).map_err(|error| error.to_string());
            let _ = tx.send(WorkerEvent::Finished(result));
        });
    }

    fn handle_worker_events(&mut self) {
        loop {
            match self.rx.try_recv() {
                Ok(event) => match event {
                    WorkerEvent::Status(message) => {
                        self.status_line = message;
                    }
                    WorkerEvent::NewsLoaded {
                        latest_version,
                        notes,
                        feed_url,
                        content_version_key,
                    } => {
                        self.latest_version = latest_version;
                        self.news_notes = notes;
                        self.client_content_version_key = content_version_key;
                        if let Some(url) = feed_url
                            && !url.trim().is_empty()
                        {
                            self.feed_url = url;
                        }
                    }
                    WorkerEvent::DownloadProgress { downloaded, total } => {
                        let fraction = total
                            .map(|value| {
                                if value == 0 {
                                    0.0
                                } else {
                                    downloaded as f32 / value as f32
                                }
                            })
                            .unwrap_or(0.0)
                            .clamp(0.0, 1.0);
                        self.progress = (fraction * 0.75).clamp(0.0, 0.75);
                        self.progress_label = match total {
                            Some(value) if value > 0 => format!(
                                "Downloading update... {:.1}% ({} / {})",
                                fraction * 100.0,
                                human_bytes(downloaded),
                                human_bytes(value)
                            ),
                            _ => format!("Downloading update... {}", human_bytes(downloaded)),
                        };
                    }
                    WorkerEvent::InstallProgress { fraction, message } => {
                        self.progress = (0.75 + (fraction.clamp(0.0, 1.0) * 0.25)).clamp(0.75, 1.0);
                        self.progress_label = message;
                    }
                    WorkerEvent::Finished(result) => {
                        self.busy = false;
                        match result {
                            Ok(message) => {
                                self.progress = 1.0;
                                self.progress_label = "Completed".to_string();
                                self.status_line = message;
                                self.local_version =
                                    read_installed_version(&self.install_dir).unwrap_or_else(|_| "unknown".to_string());
                                self.pending_minimize = true;
                            }
                            Err(error) => {
                                self.progress = 0.0;
                                self.progress_label.clear();
                                self.status_line = format!("Failed: {error}");
                            }
                        }
                    }
                },
                Err(mpsc::TryRecvError::Empty) => break,
                Err(mpsc::TryRecvError::Disconnected) => break,
            }
        }
    }
}

impl eframe::App for LauncherApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.handle_worker_events();
        if self.pending_minimize {
            ctx.send_viewport_cmd(egui::ViewportCommand::Minimized(true));
            self.pending_minimize = false;
        }

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.columns(2, |columns| {
                columns[0].vertical(|ui| {
                    ui.horizontal(|ui| {
                        ui.label(format!("Installed: {}", self.local_version));
                        ui.separator();
                        ui.label(format!("Latest: {}", self.latest_version));
                    });
                    ui.add_space(8.0);
                    ui.group(|ui| {
                        ui.label("Login Required");
                        ui.label("Sign in first. Play checks and installs updates before launch.");
                        ui.add_space(4.0);
                        ui.label("Email");
                        ui.text_edit_singleline(&mut self.email);
                        ui.label("Password");
                        ui.add(egui::TextEdit::singleline(&mut self.password).password(true));
                        ui.label("OTP (optional)");
                        ui.text_edit_singleline(&mut self.otp_code);
                    });
                    ui.add_space(8.0);
                    if self.busy {
                        ui.add_enabled(false, egui::Button::new("Working..."));
                    } else if ui.button("Play").clicked() {
                        self.login_update_and_play();
                    }
                    ui.add_space(4.0);
                    ui.horizontal(|ui| {
                        if ui.button("Refresh News").clicked() {
                            self.refresh_news();
                        }
                        if ui.button("Open Install Folder").clicked() {
                            let _ = open_directory(&self.install_dir);
                        }
                    });

                    ui.add_space(8.0);
                    ui.label(format!("Status: {}", self.status_line));
                    if self.busy || self.progress > 0.0 {
                        ui.add(egui::ProgressBar::new(self.progress.clamp(0.0, 1.0)).show_percentage());
                        if !self.progress_label.is_empty() {
                            ui.label(self.progress_label.clone());
                        }
                    }
                });

                columns[1].vertical(|ui| {
                    ui.label("Latest News / Patch Notes");
                    ui.separator();
                    egui::ScrollArea::vertical().max_height(520.0).show(ui, |ui| {
                        ui.label(&self.news_notes);
                    });
                });
            });
        });
    }
}

#[derive(Debug, Clone)]
struct LaunchInput {
    api_base_url: String,
    configured_feed_url: String,
    install_dir: PathBuf,
    email: String,
    password: String,
    otp_code: Option<String>,
    installed_version: String,
}

fn run_login_update_launch(input: LaunchInput, tx: Sender<WorkerEvent>) -> Result<String> {
    let api_base_url = normalize_url(&input.api_base_url);
    let feed_fallback = normalize_url(&input.configured_feed_url);
    let installed_version = normalize_version(&input.installed_version);

    let _ = tx.send(WorkerEvent::Status("Fetching release summary...".to_string()));
    let summary = fetch_release_summary(&api_base_url, &installed_version, "unknown")?;
    let notes = choose_notes(&summary);
    let _ = tx.send(WorkerEvent::NewsLoaded {
        latest_version: summary.latest_version.clone(),
        notes,
        feed_url: summary.update_feed_url.clone(),
        content_version_key: select_declared_content_key(&summary),
    });

    let declared_version = normalize_version(&summary.latest_version);
    let declared_content_key = select_declared_content_key(&summary);
    let _ = tx.send(WorkerEvent::Status("Logging in...".to_string()));
    let session = login_session(
        &api_base_url,
        &input.email,
        &input.password,
        input.otp_code.as_deref(),
        &declared_version,
        &declared_content_key,
    )?;

    let _ = tx.send(WorkerEvent::Status("Checking for updates...".to_string()));
    let feed_candidates = collect_feed_candidates(
        summary.update_feed_url.as_deref(),
        session.version_status.update_feed_url.as_deref(),
        &feed_fallback,
    );
    let mut resolved_feed_url = String::new();
    let mut last_feed_error: Option<anyhow::Error> = None;
    let mut latest: Option<LatestFeedPayload> = None;
    for candidate in &feed_candidates {
        match fetch_latest_feed(candidate) {
            Ok(payload) => {
                resolved_feed_url = candidate.clone();
                latest = Some(payload);
                break;
            }
            Err(error) => {
                last_feed_error = Some(error);
            }
        }
    }
    let latest = match latest {
        Some(payload) => payload,
        None => {
            if let Some(error) = last_feed_error {
                return Err(error.context("all configured feed URLs failed"));
            }
            bail!("No update feed URL is configured.");
        }
    };
    let current_local =
        normalize_version(&read_installed_version(&input.install_dir).unwrap_or_else(|_| "0.0.0".to_string()));
    let latest_version = if latest.version.trim().is_empty() {
        normalize_version(&session.version_status.latest_version)
    } else {
        normalize_version(&latest.version)
    };

    if current_local != latest_version {
        let temp_root = env::temp_dir().join("aop-launcher-update");
        if temp_root.exists() {
            fs::remove_dir_all(&temp_root).with_context(|| format!("failed clearing {}", temp_root.display()))?;
        }
        fs::create_dir_all(&temp_root).with_context(|| format!("failed creating {}", temp_root.display()))?;

        let maybe_delta = latest
            .deltas
            .iter()
            .find(|delta| normalize_version(&delta.from_version) == current_local)
            .cloned();
        let mut delta_applied = false;

        if let Some(delta) = maybe_delta {
            let _ = tx.send(WorkerEvent::Status(format!(
                "Applying delta update {} -> {}...",
                current_local, latest_version
            )));
            let delta_url = format!("{}/{}", resolved_feed_url.trim_end_matches('/'), delta.artifact);
            let delta_path = temp_root.join(&delta.artifact);
            let delta_apply_result = download_with_progress(&delta_url, &delta_path, &tx).and_then(|_| {
                if let Some(checksum_artifact) = delta.checksum.as_deref() {
                    let expected = fetch_expected_sha256(&resolved_feed_url, checksum_artifact)?;
                    verify_file_sha256(&delta_path, &expected)?;
                }
                apply_delta_with_progress(&delta_path, &input.install_dir, &tx)
            });
            match delta_apply_result {
                Ok(()) => {
                    delta_applied = true;
                    let _ = tx.send(WorkerEvent::Status("Delta update applied".to_string()));
                }
                Err(error) => {
                    let _ = tx.send(WorkerEvent::Status(format!(
                        "Delta update failed ({}). Falling back to full installer...",
                        error
                    )));
                }
            }
        }

        if !delta_applied {
            let installer_name = latest
                .installer_artifact
                .clone()
                .unwrap_or_else(|| format!("AmbitionsOfPeace-game-installer-win-x64-{latest_version}.exe"));
            let installer_url = format!("{}/{}", resolved_feed_url.trim_end_matches('/'), installer_name);
            let installer_path = temp_root.join(installer_name);
            download_with_progress(&installer_url, &installer_path, &tx)?;
            if let Some(checksum_artifact) = latest.installer_checksum.as_deref() {
                let expected = fetch_expected_sha256(&resolved_feed_url, checksum_artifact)?;
                verify_file_sha256(&installer_path, &expected)?;
            }
            run_installer_with_progress(&installer_path, &input.install_dir, &tx)?;
        }
    }

    let handoff_content_key = preferred_content_key(
        &session.version_status.latest_content_version_key,
        &session.version_status.client_content_version_key,
        &declared_content_key,
    );
    let handoff_path = default_handoff_path();
    write_startup_handoff(
        &handoff_path,
        &session,
        &api_base_url,
        &latest_version,
        &handoff_content_key,
    )?;

    launch_game(&input.install_dir, &handoff_path)?;
    Ok(format!("Launched game {}", latest_version))
}

fn fetch_release_summary(
    api_base_url: &str,
    client_version: &str,
    client_content_version_key: &str,
) -> Result<ReleaseSummaryResponse> {
    let url = format!("{}/release/summary", api_base_url.trim_end_matches('/'));
    let client = http_client()?;
    let response = client
        .get(url)
        .header("x-client-version", normalize_version(client_version))
        .header(
            "x-client-content-version",
            preferred_content_key(client_content_version_key, "unknown", "unknown"),
        )
        .send()
        .context("failed to call release summary")?;
    parse_json_response(response, "release summary")
}

fn login_session(
    api_base_url: &str,
    email: &str,
    password: &str,
    otp_code: Option<&str>,
    client_version: &str,
    client_content_version_key: &str,
) -> Result<SessionResponse> {
    let url = format!("{}/auth/login", api_base_url.trim_end_matches('/'));
    let request = LoginRequest {
        email: email.to_string(),
        password: password.to_string(),
        otp_code: otp_code.map(|value| value.to_string()),
        client_version: client_version.to_string(),
        client_content_version_key: client_content_version_key.to_string(),
    };

    let client = http_client()?;
    let response = client.post(url).json(&request).send().context("failed to call login")?;

    parse_json_response(response, "login")
}

fn fetch_latest_feed(feed_url: &str) -> Result<LatestFeedPayload> {
    let latest_url = format!("{}/latest.json", feed_url.trim_end_matches('/'));
    let client = http_client()?;
    let response = client
        .get(latest_url)
        .send()
        .context("failed to fetch feed latest.json")?;
    parse_json_response(response, "feed latest")
}

fn parse_json_response<T: for<'de> Deserialize<'de>>(response: reqwest::blocking::Response, label: &str) -> Result<T> {
    let status = response.status();
    let body = response
        .text()
        .with_context(|| format!("failed reading {label} response body"))?;

    if !status.is_success() {
        let detail = extract_api_error(&body);
        bail!("{label} request failed with status {}: {}", status, detail);
    }

    serde_json::from_str::<T>(&body).with_context(|| format!("invalid {label} JSON response"))
}

fn fetch_expected_sha256(feed_url: &str, checksum_artifact: &str) -> Result<String> {
    let checksum_url = format!("{}/{}", feed_url.trim_end_matches('/'), checksum_artifact.trim());
    let client = http_client()?;
    let response = client
        .get(checksum_url)
        .send()
        .with_context(|| format!("failed to fetch checksum artifact {checksum_artifact}"))?;
    let status = response.status();
    let body = response.text().context("failed reading checksum response")?;
    if !status.is_success() {
        bail!("checksum fetch failed with status {status}");
    }
    let expected = body
        .split_whitespace()
        .next()
        .ok_or_else(|| anyhow!("checksum artifact is empty"))?
        .trim()
        .to_lowercase();
    if expected.len() != 64 {
        bail!("invalid checksum format in {}", checksum_artifact);
    }
    Ok(expected)
}

fn download_with_progress(url: &str, output_path: &Path, tx: &Sender<WorkerEvent>) -> Result<()> {
    let client = http_client()?;
    let mut response = client
        .get(url)
        .send()
        .with_context(|| format!("failed to download {url}"))?;
    if !response.status().is_success() {
        bail!("download failed with status {} for {}", response.status(), url);
    }

    let total = response.content_length();
    let mut file = File::create(output_path).with_context(|| format!("failed creating {}", output_path.display()))?;

    let mut downloaded = 0_u64;
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let read = response.read(&mut buffer).context("failed while downloading")?;
        if read == 0 {
            break;
        }
        file.write_all(&buffer[..read])
            .context("failed writing downloaded bytes")?;
        downloaded += read as u64;
        let _ = tx.send(WorkerEvent::DownloadProgress { downloaded, total });
    }

    Ok(())
}

fn verify_file_sha256(path: &Path, expected_hex: &str) -> Result<()> {
    let mut digest = sha2::Sha256::new();
    let mut file = File::open(path).with_context(|| format!("failed opening {}", path.display()))?;
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let read = file
            .read(&mut buffer)
            .with_context(|| format!("failed reading {}", path.display()))?;
        if read == 0 {
            break;
        }
        digest.update(&buffer[..read]);
    }
    let actual = format!("{:x}", digest.finalize());
    if actual != expected_hex.to_lowercase() {
        bail!(
            "checksum mismatch for {} (expected {}, got {})",
            path.display(),
            expected_hex,
            actual
        );
    }
    Ok(())
}

fn run_installer_with_progress(installer_path: &Path, install_dir: &Path, tx: &Sender<WorkerEvent>) -> Result<()> {
    let _ = tx.send(WorkerEvent::InstallProgress {
        fraction: 0.05,
        message: "Installing update...".to_string(),
    });

    let mut child = Command::new(installer_path)
        .arg("/S")
        .arg(format!("/D={}", install_dir.display()))
        .spawn()
        .with_context(|| format!("failed to launch installer {}", installer_path.display()))?;

    let mut pseudo = 0.08_f32;
    loop {
        match child.try_wait().context("failed waiting for installer")? {
            Some(status) => {
                if !status.success() {
                    bail!("installer failed with exit code {:?}", status.code());
                }
                break;
            }
            None => {
                pseudo = (pseudo + 0.03).min(0.95);
                let _ = tx.send(WorkerEvent::InstallProgress {
                    fraction: pseudo,
                    message: format!("Installing update... {:.0}%", pseudo * 100.0),
                });
                thread::sleep(Duration::from_millis(250));
            }
        }
    }

    let _ = tx.send(WorkerEvent::InstallProgress {
        fraction: 1.0,
        message: "Install completed".to_string(),
    });
    Ok(())
}

fn apply_delta_with_progress(delta_path: &Path, install_dir: &Path, tx: &Sender<WorkerEvent>) -> Result<()> {
    let extract_root = env::temp_dir().join("aop-launcher-delta-stage");
    if extract_root.exists() {
        fs::remove_dir_all(&extract_root).with_context(|| format!("failed clearing {}", extract_root.display()))?;
    }
    fs::create_dir_all(&extract_root).with_context(|| format!("failed creating {}", extract_root.display()))?;
    extract_zip_archive(delta_path, &extract_root)?;

    let manifest_path = extract_root.join("delta_manifest.json");
    let manifest_raw =
        fs::read_to_string(&manifest_path).with_context(|| format!("failed reading {}", manifest_path.display()))?;
    let manifest: DeltaManifest = serde_json::from_str(&manifest_raw).context("invalid delta manifest")?;

    let total_ops = (manifest.changed_files.len() + manifest.removed_files.len()).max(1);
    let mut completed_ops: usize = 0;

    for relative in &manifest.removed_files {
        if relative.trim().is_empty() {
            continue;
        }
        let target = install_dir.join(relative);
        if target.is_dir() {
            let _ = fs::remove_dir_all(&target);
        } else if target.exists() {
            let _ = fs::remove_file(&target);
        }
        completed_ops += 1;
        let _ = tx.send(WorkerEvent::InstallProgress {
            fraction: completed_ops as f32 / total_ops as f32,
            message: format!("Applying delta... ({}/{})", completed_ops, total_ops),
        });
    }

    for relative in &manifest.changed_files {
        if relative.trim().is_empty() || relative == "delta_manifest.json" {
            continue;
        }
        let source = extract_root.join(relative);
        if !source.exists() {
            continue;
        }
        let destination = install_dir.join(relative);
        if let Some(parent) = destination.parent() {
            fs::create_dir_all(parent).with_context(|| format!("failed creating {}", parent.display()))?;
        }
        fs::copy(&source, &destination)
            .with_context(|| format!("failed writing delta target {}", destination.display()))?;

        completed_ops += 1;
        let _ = tx.send(WorkerEvent::InstallProgress {
            fraction: completed_ops as f32 / total_ops as f32,
            message: format!("Applying delta... ({}/{})", completed_ops, total_ops),
        });
    }

    let _ = tx.send(WorkerEvent::InstallProgress {
        fraction: 1.0,
        message: "Delta apply completed".to_string(),
    });
    Ok(())
}

fn extract_zip_archive(zip_path: &Path, destination: &Path) -> Result<()> {
    let zip_file = File::open(zip_path).with_context(|| format!("failed opening {}", zip_path.display()))?;
    let mut archive = ZipArchive::new(zip_file).with_context(|| format!("invalid zip {}", zip_path.display()))?;

    for index in 0..archive.len() {
        let mut entry = archive.by_index(index).context("failed reading zip entry")?;
        let enclosed = entry
            .enclosed_name()
            .ok_or_else(|| anyhow!("zip entry contains unsafe path"))?;
        let output = destination.join(enclosed);

        if entry.is_dir() {
            fs::create_dir_all(&output).with_context(|| format!("failed creating {}", output.display()))?;
            continue;
        }
        if let Some(parent) = output.parent() {
            fs::create_dir_all(parent).with_context(|| format!("failed creating {}", parent.display()))?;
        }
        let mut output_file = File::create(&output).with_context(|| format!("failed creating {}", output.display()))?;
        std::io::copy(&mut entry, &mut output_file)
            .with_context(|| format!("failed extracting {}", output.display()))?;
    }

    Ok(())
}

fn write_startup_handoff(
    path: &Path,
    session: &SessionResponse,
    api_base_url: &str,
    client_version: &str,
    client_content_version_key: &str,
) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).with_context(|| format!("failed creating {}", parent.display()))?;
    }

    let payload = StartupHandoff {
        schema_version: 1,
        email: session.email.clone(),
        access_token: session.access_token.clone(),
        refresh_token: session.refresh_token.clone(),
        session_id: session.session_id.clone(),
        user_id: session.user_id,
        display_name: session.display_name.clone(),
        api_base_url: api_base_url.to_string(),
        client_version: client_version.to_string(),
        client_content_version_key: client_content_version_key.to_string(),
    };

    let raw = serde_json::to_string_pretty(&payload).context("failed serializing handoff")?;
    fs::write(path, format!("{raw}\n")).with_context(|| format!("failed writing {}", path.display()))
}

fn launch_game(install_dir: &Path, handoff_path: &Path) -> Result<()> {
    let game_exe = install_dir.join("bin").join("AmbitionsOfPeaceClient.exe");
    if !game_exe.exists() {
        bail!("game executable not found at {}", game_exe.display());
    }

    Command::new(&game_exe)
        .arg("--handoff-file")
        .arg(handoff_path)
        .arg("--fullscreen")
        .spawn()
        .with_context(|| format!("failed to launch {}", game_exe.display()))?;
    Ok(())
}

fn open_directory(path: &Path) -> Result<()> {
    if !path.exists() {
        fs::create_dir_all(path).with_context(|| format!("failed creating {}", path.display()))?;
    }

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(path)
            .spawn()
            .context("failed opening install directory")?;
        return Ok(());
    }

    #[cfg(not(target_os = "windows"))]
    {
        Command::new("xdg-open")
            .arg(path)
            .spawn()
            .context("failed opening install directory")?;
        Ok(())
    }
}

fn read_installed_version(install_dir: &Path) -> Result<String> {
    let marker = install_dir.join("release_version.txt");
    let raw = fs::read_to_string(&marker).with_context(|| format!("failed reading {}", marker.display()))?;
    Ok(normalize_version(raw.trim()))
}

fn default_install_dir() -> PathBuf {
    if let Some(local_app_data) = env::var_os("LOCALAPPDATA") {
        return PathBuf::from(local_app_data)
            .join("AmbitionsOfPeace")
            .join("game-runtime");
    }
    PathBuf::from("./runtime/game-runtime")
}

fn default_handoff_path() -> PathBuf {
    if let Some(local_app_data) = env::var_os("LOCALAPPDATA") {
        return PathBuf::from(local_app_data)
            .join("AmbitionsOfPeace")
            .join("handoff")
            .join("startup_handoff.json");
    }
    PathBuf::from("./runtime/startup_handoff.json")
}

fn normalize_url(value: &str) -> String {
    value.trim().trim_end_matches('/').to_string()
}

fn normalize_version(value: &str) -> String {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        "0.0.0".to_string()
    } else {
        trimmed.to_string()
    }
}

fn collect_feed_candidates(summary_feed: Option<&str>, session_feed: Option<&str>, fallback_feed: &str) -> Vec<String> {
    let mut feeds = Vec::new();
    for raw in [summary_feed, session_feed, Some(fallback_feed)] {
        let Some(value) = raw else {
            continue;
        };
        let normalized = normalize_url(value);
        if normalized.is_empty() {
            continue;
        }
        if !feeds.iter().any(|existing| existing == &normalized) {
            feeds.push(normalized);
        }
    }
    feeds
}

fn preferred_content_key(primary: &str, secondary: &str, fallback: &str) -> String {
    for candidate in [primary.trim(), secondary.trim(), fallback.trim()] {
        if !candidate.is_empty() && candidate != "unknown" {
            return candidate.to_string();
        }
    }
    "unknown".to_string()
}

fn select_declared_content_key(summary: &ReleaseSummaryResponse) -> String {
    preferred_content_key(
        &summary.latest_content_version_key,
        &summary.min_supported_content_version_key,
        &summary.client_content_version_key,
    )
}

fn env_or_default(key: &str, fallback: &str) -> String {
    env::var(key)
        .ok()
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
        .unwrap_or_else(|| fallback.to_string())
}

fn choose_notes(summary: &ReleaseSummaryResponse) -> String {
    let user_notes = summary.latest_user_facing_notes.trim();
    if !user_notes.is_empty() {
        return user_notes.to_string();
    }
    let build_notes = summary.latest_build_release_notes.trim();
    if !build_notes.is_empty() {
        return build_notes.to_string();
    }
    "No published notes yet.".to_string()
}

fn trimmed_or_none(value: &str) -> Option<String> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed.to_string())
    }
}

fn extract_api_error(raw: &str) -> String {
    if let Ok(parsed) = serde_json::from_str::<ApiErrorEnvelope>(raw)
        && let Some(detail) = parsed.detail
    {
        return match detail {
            ApiErrorDetail::MessageMap { message, code } => {
                let m = message.unwrap_or_else(|| "request rejected".to_string());
                let c = code.unwrap_or_else(|| "unknown".to_string());
                format!("{} [{}]", m, c)
            }
            ApiErrorDetail::Plain(value) => value,
        };
    }

    let trimmed = raw.trim();
    if trimmed.is_empty() {
        "request rejected".to_string()
    } else {
        trimmed.to_string()
    }
}

fn human_bytes(value: u64) -> String {
    const UNITS: [&str; 5] = ["B", "KB", "MB", "GB", "TB"];
    let mut unit_index = 0usize;
    let mut float_value = value as f64;
    while float_value >= 1024.0 && unit_index < UNITS.len() - 1 {
        float_value /= 1024.0;
        unit_index += 1;
    }
    format!("{float_value:.1} {}", UNITS[unit_index])
}

fn http_client() -> Result<Client> {
    Client::builder()
        .timeout(Duration::from_secs(45))
        .build()
        .map_err(|error| anyhow!("failed creating HTTP client: {error}"))
}

fn main() -> Result<()> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title(APP_TITLE)
            .with_inner_size([980.0, 560.0]),
        ..Default::default()
    };

    eframe::run_native(APP_TITLE, options, Box::new(|_cc| Ok(Box::new(LauncherApp::new()))))
        .map_err(|error| anyhow!("launcher failed: {error}"))
}

#[cfg(test)]
mod tests {
    use super::{collect_feed_candidates, extract_api_error, normalize_version, preferred_content_key};

    #[test]
    fn normalize_version_defaults_to_zero() {
        assert_eq!(normalize_version(""), "0.0.0");
        assert_eq!(normalize_version("   \n"), "0.0.0");
    }

    #[test]
    fn extract_api_error_handles_maps_and_plain_values() {
        let mapped = r#"{"detail":{"message":"Denied","code":"invalid_credentials"}}"#;
        assert_eq!(extract_api_error(mapped), "Denied [invalid_credentials]");

        let plain = r#"{"detail":"bad request"}"#;
        assert_eq!(extract_api_error(plain), "bad request");
    }

    #[test]
    fn preferred_content_key_ignores_unknown_values() {
        assert_eq!(
            preferred_content_key("unknown", "cv_bootstrap_v1", "unknown"),
            "cv_bootstrap_v1"
        );
        assert_eq!(preferred_content_key(" ", "unknown", "cv_fallback"), "cv_fallback");
        assert_eq!(preferred_content_key("unknown", "unknown", "unknown"), "unknown");
    }

    #[test]
    fn collect_feed_candidates_dedupes_and_keeps_order() {
        let result = collect_feed_candidates(
            Some("https://storage.googleapis.com/karaxas-releases-lustrous-bond-298815/win"),
            Some("https://storage.googleapis.com/karaxas-releases-lustrous-bond-298815/win-game"),
            "https://storage.googleapis.com/karaxas-releases-lustrous-bond-298815/win-game",
        );
        assert_eq!(result.len(), 2);
        assert_eq!(
            result[0],
            "https://storage.googleapis.com/karaxas-releases-lustrous-bond-298815/win"
        );
        assert_eq!(
            result[1],
            "https://storage.googleapis.com/karaxas-releases-lustrous-bond-298815/win-game"
        );
    }
}
