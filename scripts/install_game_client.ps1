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

function Get-LatestMetadata {
  param([string]$LatestUrl)

  $latestBodyText = $null
  $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
  if ($curl) {
    $curlBody = & $curl.Path -fsSL $LatestUrl
    if ($LASTEXITCODE -eq 0) {
      $latestBodyText = [string]::Join("`n", $curlBody)
    }
  }

  if ([string]::IsNullOrWhiteSpace($latestBodyText)) {
    try {
      $restBody = Invoke-RestMethod -Method Get -Uri $LatestUrl -ErrorAction Stop
    } catch {
      throw "Failed to fetch latest metadata from $LatestUrl. $($_.Exception.Message)"
    }

    if ($null -eq $restBody) {
      throw "latest.json at $LatestUrl is empty."
    }

    if ($restBody -is [string]) {
      $latestBodyText = $restBody
    } else {
      $latestBodyText = $restBody | ConvertTo-Json -Depth 10
    }
  }

  if ([string]::IsNullOrWhiteSpace($latestBodyText)) {
    throw "latest.json at $LatestUrl is empty."
  }

  try {
    return $latestBodyText | ConvertFrom-Json
  } catch {
    throw "latest.json at $LatestUrl is not valid JSON."
  }
}

function Download-Installer {
  param(
    [string]$InstallerUrl,
    [string]$InstallerPath
  )

  $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
  if ($curl) {
    & $curl.Path -fL $InstallerUrl -o $InstallerPath
    if ($LASTEXITCODE -eq 0 -and (Test-Path $InstallerPath)) {
      return
    }
  }

  try {
    Invoke-RestMethod -Method Get -Uri $InstallerUrl -OutFile $InstallerPath -ErrorAction Stop
  } catch {
    throw "Failed to download installer from $InstallerUrl. $($_.Exception.Message)"
  }

  if (-not (Test-Path $InstallerPath)) {
    throw "Installer download did not produce $InstallerPath."
  }
}

$feed = $FeedUrl.TrimEnd("/")
$latestUrl = "$feed/latest.json"
$latest = Get-LatestMetadata -LatestUrl $latestUrl
if (-not $latest.version) {
  throw "latest.json at $latestUrl does not include 'version'."
}

$version = "$($latest.version)"
$installerArtifact = "$($latest.installer_artifact)"
if ([string]::IsNullOrWhiteSpace($installerArtifact)) {
  $installerArtifact = "AmbitionsOfPeace-game-installer-win-x64-$version.exe"
}
$installerUrl = "$feed/$installerArtifact"

$tempRoot = Join-Path $env:TEMP "aop-game-installer"
if (Test-Path $tempRoot) {
  Remove-Item -Path $tempRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$installerPath = Join-Path $tempRoot $installerArtifact

Write-Host "Downloading installer $installerUrl"
Download-Installer -InstallerUrl $installerUrl -InstallerPath $installerPath

$installRoot = Split-Path -Parent $InstallDir
if (-not (Test-Path $installRoot)) {
  New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
}

$args = @("/S", "/D=$InstallDir")
$process = Start-Process -FilePath $installerPath -ArgumentList $args -Wait -PassThru
if ($process.ExitCode -ne 0) {
  throw "Installer exited with code $($process.ExitCode)."
}

$entrypoint = Join-Path $InstallDir "bin\\AmbitionsOfPeaceClient.exe"
if (-not (Test-Path $entrypoint)) {
  throw "Install completed but runtime executable was not found at $entrypoint"
}

Write-Host "Installed game runtime version $version to $InstallDir"
