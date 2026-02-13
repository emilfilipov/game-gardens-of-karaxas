param(
  [string]$Version,
  [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$buildDir = Join-Path $root "build"
$packDir = Join-Path $buildDir "pack"
$payloadDir = Join-Path $packDir "payload"
$releasesDir = Join-Path $root "releases\\windows"
$templatePath = Join-Path $root "RELEASE_NOTES_TEMPLATE.md"
$notesSourcePath = Join-Path $root "patch_notes.md"
$renderedNotes = Join-Path $packDir "patch_notes.md"
$renderedMeta = Join-Path $packDir "patch_notes_meta.txt"
$wrapperProject = Join-Path $root "tools\\setup-wrapper\\SetupWrapper.csproj"
$wrapperOutDir = Join-Path $packDir "setup-wrapper"
$updateHelperProject = Join-Path $root "tools\\update-helper\\UpdateHelper.csproj"
$updateHelperOutDir = Join-Path $packDir "update-helper"

if (-not $Version -or $Version.Trim().Length -eq 0) {
  $versionFile = Join-Path $root "VERSION"
  if (Test-Path $versionFile) {
    $Version = (Get-Content $versionFile -Raw).Trim()
  }
}
if (-not $Version -or $Version.Trim().Length -eq 0) {
  throw "Version is required. Provide -Version or create a VERSION file."
}

if (Test-Path $packDir) {
  Remove-Item -Recurse -Force $packDir
}
if ($env:GOK_CLEAN_RELEASES -eq "1" -and (Test-Path $releasesDir)) {
  Remove-Item -Recurse -Force $releasesDir
}
New-Item -ItemType Directory -Path $releasesDir -Force | Out-Null

Set-Location $root

./gradlew :launcher:fatJar :desktop:fatJar

$launcherJar = Join-Path $root "launcher\\build\\libs\\launcher-all.jar"
$gameJar = Join-Path $root "desktop\\build\\libs\\desktop-all.jar"

if (-not (Test-Path $launcherJar)) { throw "Missing launcher jar at $launcherJar" }
if (-not (Test-Path $gameJar)) { throw "Missing game jar at $gameJar" }

$launcherImageDir = Join-Path $packDir "launcher"
$gameImageDir = Join-Path $packDir "game"
$iconCandidates = @(
  (Join-Path $root "game_icon.ico"),
  (Join-Path $root "game_icon.png")
)
$iconPath = $iconCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

$launcherIcon = if ($iconPath -and (Test-Path $iconPath)) { @("--icon", $iconPath) } else { @() }
$gameIcon = if ($iconPath -and (Test-Path $iconPath)) { @("--icon", $iconPath) } else { @() }

jpackage --type app-image --input (Split-Path $launcherJar) --main-jar (Split-Path $launcherJar -Leaf) --name "GardensOfKaraxasLauncher" --app-version $Version --dest $launcherImageDir @launcherIcon
jpackage --type app-image --input (Split-Path $gameJar) --main-jar (Split-Path $gameJar -Leaf) --name "GardensOfKaraxas" --app-version $Version --dest $gameImageDir @gameIcon

$launcherApp = Join-Path $launcherImageDir "GardensOfKaraxasLauncher"
$gameApp = Join-Path $gameImageDir "GardensOfKaraxas"

if (-not (Test-Path $launcherApp)) { throw "Missing launcher app image at $launcherApp" }
if (-not (Test-Path $gameApp)) { throw "Missing game app image at $gameApp" }

New-Item -ItemType Directory -Path $payloadDir | Out-Null
Copy-Item -Path (Join-Path $launcherApp "*") -Destination $payloadDir -Recurse
New-Item -ItemType Directory -Path (Join-Path $payloadDir "game") | Out-Null
Copy-Item -Path (Join-Path $gameApp "*") -Destination (Join-Path $payloadDir "game") -Recurse

if (Test-Path $updateHelperProject) {
  dotnet publish $updateHelperProject -c Release -r win-x64 -p:PublishSingleFile=true -p:SelfContained=true -p:PublishReadyToRun=true -o $updateHelperOutDir
  $updateHelperExe = Join-Path $updateHelperOutDir "UpdateHelper.exe"
  if (-not (Test-Path $updateHelperExe)) { throw "Missing update helper exe at $updateHelperExe" }
  Copy-Item -Path $updateHelperExe -Destination (Join-Path $payloadDir "UpdateHelper.exe") -Force
}

$date = (Get-Date).ToString("yyyy-MM-dd")
$notesContent = ""
if (Test-Path $notesSourcePath) {
  $notesContent = Get-Content $notesSourcePath -Raw
} elseif (Test-Path $templatePath) {
  $notesTemplate = (Get-Content $templatePath -Raw).Replace("{{version}}", $Version).Replace("{{date}}", $date)
  $changelog = ""
  try {
    $prevTag = git describe --tags --abbrev=0 2>$null
  } catch {
    $prevTag = ""
  }
  if ($prevTag) {
    $log = git log "$prevTag..HEAD" --pretty=format:"- %s"
    if ($log) { $changelog = $log }
  }
  if (-not $changelog) {
    $log = git log -n 20 --pretty=format:"- %s"
    if ($log) { $changelog = $log } else { $changelog = "- Initial release" }
  }
  $notesContent = $notesTemplate.Replace("{{changelog}}", $changelog)
}

$bulletLines = @()
if (-not [string]::IsNullOrWhiteSpace($notesContent)) {
  $normalized = ($notesContent -replace "`r", "").Split("`n")
  foreach ($line in $normalized) {
    $trimmed = $line.Trim()
    if ($trimmed.StartsWith("- ")) {
      $bulletLines += "- " + $trimmed.Substring(2).Trim()
    }
  }
}
if ($bulletLines.Count -eq 0) {
  $bulletLines = @("- Patch notes unavailable.")
}

$notes = [string]::Join("`n", $bulletLines)
$meta = "version=$Version`ndate=$date"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($renderedNotes, $notes, $utf8NoBom)
[System.IO.File]::WriteAllText($renderedMeta, $meta, $utf8NoBom)
Copy-Item -Path $renderedNotes -Destination (Join-Path $payloadDir "patch_notes.md")
Copy-Item -Path $renderedMeta -Destination (Join-Path $payloadDir "patch_notes_meta.txt")

$updateToken = $env:VELOPACK_TOKEN
if (-not $updateToken -or $updateToken.Trim().Length -eq 0) {
  $updateToken = $env:VELOPACK_GITHUB_TOKEN
}
if ($updateToken -and $updateToken.Trim().Length -gt 0) {
  $tokenPath = Join-Path $payloadDir "update_token.txt"
  Set-Content -Path $tokenPath -Value $updateToken.Trim() -Encoding ascii
}

$repoUrl = $env:GOK_UPDATE_REPO
if (-not $repoUrl -or $repoUrl.Trim().Length -eq 0) {
  if ($env:GITHUB_REPOSITORY) {
    $repoUrl = "https://github.com/$env:GITHUB_REPOSITORY"
  }
}
if ($repoUrl -and $repoUrl.Trim().Length -gt 0) {
  $repoPath = Join-Path $payloadDir "update_repo.txt"
  Set-Content -Path $repoPath -Value $repoUrl.Trim() -Encoding ascii
}

$vpkIcon = if ($iconPath -and (Test-Path $iconPath)) { @("--icon", $iconPath) } else { @() }
vpk pack --packId GardensOfKaraxas --packVersion $Version --packDir $payloadDir --mainExe GardensOfKaraxasLauncher.exe --packTitle "Gardens of Karaxas" --outputDir $releasesDir --channel win @vpkIcon

if (-not (Test-Path $wrapperProject)) {
  throw "Missing setup wrapper project at $wrapperProject"
}

$setupExe = Get-ChildItem $releasesDir -Filter "*Setup*.exe" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $setupExe) { throw "Missing setup exe in $releasesDir" }

$setupBaseName = $setupExe.BaseName
$setupCorePath = Join-Path $packDir ($setupBaseName + "Core.exe")
Move-Item -Path $setupExe.FullName -Destination $setupCorePath -Force

dotnet publish $wrapperProject -c Release -r win-x64 -p:PublishSingleFile=true -p:SelfContained=true -p:PublishReadyToRun=true -p:SetupCorePath=$setupCorePath -o $wrapperOutDir
$wrapperExe = Join-Path $wrapperOutDir "SetupWrapper.exe"
if (-not (Test-Path $wrapperExe)) { throw "Missing wrapper exe at $wrapperExe" }
Copy-Item -Path $wrapperExe -Destination (Join-Path $releasesDir ($setupBaseName + ".exe")) -Force

Write-Host "Done. Check the Releases folder in: $releasesDir"
