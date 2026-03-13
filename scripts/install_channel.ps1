param(
  [Parameter(Mandatory = $true)]
  [string]$FeedUrl,
  [Parameter(Mandatory = $true)]
  [string]$ArtifactPrefix,
  [Parameter(Mandatory = $true)]
  [string]$InstallDir
)

$ErrorActionPreference = "Stop"

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

function Download-ArtifactZip {
  param(
    [string]$ZipUrl,
    [string]$ZipPath
  )

  $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
  if ($curl) {
    & $curl.Path -fL $ZipUrl -o $ZipPath
    if ($LASTEXITCODE -eq 0 -and (Test-Path $ZipPath)) {
      return
    }
  }

  try {
    Invoke-RestMethod -Method Get -Uri $ZipUrl -OutFile $ZipPath -ErrorAction Stop
  } catch {
    throw "Failed to download artifact from $ZipUrl. $($_.Exception.Message)"
  }

  if (-not (Test-Path $ZipPath)) {
    throw "Artifact download did not produce $ZipPath."
  }
}

$feed = $FeedUrl.TrimEnd("/")
$latestUrl = "$feed/latest.json"
$latest = Get-LatestMetadata -LatestUrl $latestUrl
if (-not $latest.version) {
  throw "latest.json at $latestUrl does not include 'version'."
}
$version = "$($latest.version)"
$zipName = "$ArtifactPrefix-$version.zip"
$zipUrl = "$feed/$zipName"

$tempRoot = Join-Path $env:TEMP "aop-channel-install"
if (Test-Path $tempRoot) {
  Remove-Item -Path $tempRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$zipPath = Join-Path $tempRoot $zipName

Write-Host "Downloading $zipUrl"
Download-ArtifactZip -ZipUrl $zipUrl -ZipPath $zipPath

if (Test-Path $InstallDir) {
  Remove-Item -Path $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

Expand-Archive -Path $zipPath -DestinationPath $InstallDir -Force
Write-Host "Installed version $version to $InstallDir"
