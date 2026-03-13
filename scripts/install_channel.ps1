param(
  [Parameter(Mandatory = $true)]
  [string]$FeedUrl,
  [Parameter(Mandatory = $true)]
  [string]$ArtifactPrefix,
  [Parameter(Mandatory = $true)]
  [string]$InstallDir
)

$ErrorActionPreference = "Stop"

$feed = $FeedUrl.TrimEnd("/")
$latestUrl = "$feed/latest.json"
$latestBody = (Invoke-WebRequest -Method Get -Uri $latestUrl).Content
if (-not $latestBody) {
  throw "latest.json at $latestUrl is empty."
}
try {
  $latest = $latestBody | ConvertFrom-Json
} catch {
  throw "latest.json at $latestUrl is not valid JSON."
}
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
Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath

if (Test-Path $InstallDir) {
  Remove-Item -Path $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

Expand-Archive -Path $zipPath -DestinationPath $InstallDir -Force
Write-Host "Installed version $version to $InstallDir"
