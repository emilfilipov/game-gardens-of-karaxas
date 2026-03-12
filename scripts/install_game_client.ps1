param(
  [string]$FeedUrl = "",
  [string]$InstallDir = "$env:LOCALAPPDATA\\AmbitionsOfPeace\\game-runtime"
)

$ErrorActionPreference = "Stop"

if (-not $FeedUrl -or $FeedUrl.Trim().Length -eq 0) {
  $bucket = $env:KARAXAS_GCS_RELEASE_BUCKET
  $prefix = $env:KARAXAS_GCS_GAME_RELEASE_PREFIX
  if (-not $prefix -or $prefix.Trim().Length -eq 0) {
    $prefix = "win-game"
  }
  if ($bucket -and $bucket.Trim().Length -gt 0) {
    $FeedUrl = "https://storage.googleapis.com/$bucket/$prefix"
  } else {
    throw "FeedUrl not provided and KARAXAS_GCS_RELEASE_BUCKET is not set."
  }
}

powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/install_channel.ps1" `
  -FeedUrl $FeedUrl `
  -ArtifactPrefix "AmbitionsOfPeace-client-app-win-x64" `
  -InstallDir $InstallDir
