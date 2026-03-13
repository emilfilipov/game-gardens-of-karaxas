param(
  [Parameter(Mandatory = $true)]
  [string]$FeedRoot,
  [string]$GameChannel = "win-game",
  [string]$DesignerChannel = "win-designer",
  [string]$GameFromVersion = "",
  [string]$GameToVersion = "",
  [string]$DesignerFromVersion = "",
  [string]$DesignerToVersion = "",
  [string]$GameInstallDir = "$env:TEMP\\AmbitionsOfPeace\\smoke-game-runtime",
  [string]$DesignerInstallDir = "$env:TEMP\\AmbitionsOfPeace\\smoke-designer-runtime",
  [string]$SummaryPath = "$env:TEMP\\AmbitionsOfPeace\\windows-installer-smoke-summary.md",
  [int]$Port = 18080
)

$ErrorActionPreference = "Stop"

function Require-Path {
  param([string]$Path, [string]$Label)
  if (-not (Test-Path $Path)) {
    throw "Missing ${Label}: ${Path}"
  }
}

function Find-Versions {
  param([string]$ChannelDir, [string]$ArtifactPrefix)

  $items = @()
  $pattern = "^" + [regex]::Escape($ArtifactPrefix) + "-(?<version>\\d+\\.\\d+\\.\\d+)\\.zip$"
  foreach ($zip in Get-ChildItem -Path $ChannelDir -Filter "$ArtifactPrefix-*.zip" -ErrorAction SilentlyContinue) {
    $match = [regex]::Match($zip.Name, $pattern)
    if (-not $match.Success) {
      continue
    }
    $versionText = $match.Groups["version"].Value
    try {
      $versionObj = [version]$versionText
    } catch {
      continue
    }
    $items += [PSCustomObject]@{ VersionText = $versionText; Version = $versionObj }
  }

  $ordered = $items | Sort-Object Version
  if (-not $ordered -or $ordered.Count -lt 2) {
    throw "Need at least two versions in $ChannelDir for $ArtifactPrefix install/update smoke."
  }
  return $ordered
}

function Write-Latest {
  param(
    [string]$ChannelDir,
    [string]$Version,
    [string]$Channel,
    [string]$ArtifactPrefix
  )

  $payload = @{ version = $Version; channel = $Channel; artifact_prefix = $ArtifactPrefix } | ConvertTo-Json
  Set-Content -Path (Join-Path $ChannelDir "latest.json") -Value $payload -Encoding utf8
}

function Read-InstalledVersion {
  param([string]$InstallDir)
  $marker = Join-Path $InstallDir "release_version.txt"
  Require-Path -Path $marker -Label "release version marker"
  return (Get-Content -Path $marker -Raw).Trim()
}

$feedRootPath = Resolve-Path $FeedRoot
$gameChannelDir = Join-Path $feedRootPath $GameChannel
$designerChannelDir = Join-Path $feedRootPath $DesignerChannel
Require-Path -Path $gameChannelDir -Label "game feed directory"
Require-Path -Path $designerChannelDir -Label "designer feed directory"

$gamePrefix = "AmbitionsOfPeace-client-app-win-x64"
$designerPrefix = "AmbitionsOfPeace-designer-client-win-x64"

if ($GameFromVersion -and $GameToVersion -and $DesignerFromVersion -and $DesignerToVersion) {
  $gameOld = $GameFromVersion
  $gameNew = $GameToVersion
  $designerOld = $DesignerFromVersion
  $designerNew = $DesignerToVersion
} else {
  $gameVersions = Find-Versions -ChannelDir $gameChannelDir -ArtifactPrefix $gamePrefix
  $designerVersions = Find-Versions -ChannelDir $designerChannelDir -ArtifactPrefix $designerPrefix
  $gameOld = $gameVersions[0].VersionText
  $gameNew = $gameVersions[-1].VersionText
  $designerOld = $designerVersions[0].VersionText
  $designerNew = $designerVersions[-1].VersionText
}

Require-Path -Path (Join-Path $gameChannelDir "$gamePrefix-$gameOld.zip") -Label "game from-version zip"
Require-Path -Path (Join-Path $gameChannelDir "$gamePrefix-$gameNew.zip") -Label "game to-version zip"
Require-Path -Path (Join-Path $designerChannelDir "$designerPrefix-$designerOld.zip") -Label "designer from-version zip"
Require-Path -Path (Join-Path $designerChannelDir "$designerPrefix-$designerNew.zip") -Label "designer to-version zip"

$summaryDir = Split-Path -Parent $SummaryPath
if (-not (Test-Path $summaryDir)) {
  New-Item -ItemType Directory -Path $summaryDir -Force | Out-Null
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  throw "python is required for local HTTP feed hosting"
}

$server = $null
$summary = New-Object System.Collections.Generic.List[string]
try {
  if (Test-Path $GameInstallDir) {
    Remove-Item -Path $GameInstallDir -Recurse -Force
  }
  if (Test-Path $DesignerInstallDir) {
    Remove-Item -Path $DesignerInstallDir -Recurse -Force
  }

  $server = Start-Process -FilePath $pythonCmd.Path -ArgumentList "-m", "http.server", "$Port", "--bind", "127.0.0.1", "--directory", "$feedRootPath" -PassThru
  Start-Sleep -Seconds 2

  $baseUrl = "http://127.0.0.1:$Port"
  $gameFeedUrl = "$baseUrl/$GameChannel"
  $designerFeedUrl = "$baseUrl/$DesignerChannel"

  Write-Latest -ChannelDir $gameChannelDir -Version $gameOld -Channel "game" -ArtifactPrefix $gamePrefix
  Write-Latest -ChannelDir $designerChannelDir -Version $designerOld -Channel "designer" -ArtifactPrefix $designerPrefix

  & powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/install_game_client.ps1" -FeedUrl $gameFeedUrl -InstallDir $GameInstallDir
  & powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/install_designer_client.ps1" -FeedUrl $designerFeedUrl -InstallDir $DesignerInstallDir

  Require-Path -Path (Join-Path $GameInstallDir "bin\\AmbitionsOfPeaceClient.exe") -Label "game runtime executable"
  Require-Path -Path (Join-Path $DesignerInstallDir "start_designer_client.bat") -Label "designer launcher"

  $installedGameOld = Read-InstalledVersion -InstallDir $GameInstallDir
  $installedDesignerOld = Read-InstalledVersion -InstallDir $DesignerInstallDir
  if ($installedGameOld -ne $gameOld) {
    throw "Game install expected version $gameOld but found $installedGameOld"
  }
  if ($installedDesignerOld -ne $designerOld) {
    throw "Designer install expected version $designerOld but found $installedDesignerOld"
  }

  Write-Latest -ChannelDir $gameChannelDir -Version $gameNew -Channel "game" -ArtifactPrefix $gamePrefix
  Write-Latest -ChannelDir $designerChannelDir -Version $designerNew -Channel "designer" -ArtifactPrefix $designerPrefix

  & powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/install_game_client.ps1" -FeedUrl $gameFeedUrl -InstallDir $GameInstallDir
  & powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/install_designer_client.ps1" -FeedUrl $designerFeedUrl -InstallDir $DesignerInstallDir

  $installedGameNew = Read-InstalledVersion -InstallDir $GameInstallDir
  $installedDesignerNew = Read-InstalledVersion -InstallDir $DesignerInstallDir
  if ($installedGameNew -ne $gameNew) {
    throw "Game update expected version $gameNew but found $installedGameNew"
  }
  if ($installedDesignerNew -ne $designerNew) {
    throw "Designer update expected version $designerNew but found $installedDesignerNew"
  }

  $summary.Add("# Windows Installer Acceptance Smoke")
  $summary.Add("")
  $summary.Add("- Feed root: $feedRootPath")
  $summary.Add("- Game install/update: $gameOld -> $gameNew")
  $summary.Add("- Designer install/update: $designerOld -> $designerNew")
  $summary.Add("- Game install dir: $GameInstallDir")
  $summary.Add("- Designer install dir: $DesignerInstallDir")
  $summary.Add("- Result: PASS")

  Set-Content -Path $SummaryPath -Value ($summary -join "`n") -Encoding utf8
  Write-Host "Windows installer acceptance smoke passed. Summary: $SummaryPath"
}
finally {
  if ($server -and -not $server.HasExited) {
    Stop-Process -Id $server.Id -Force
  }
}
