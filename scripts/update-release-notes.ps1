param(
  [string]$Version = "Unreleased"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$templatePath = Join-Path $root "docs\\RELEASE_NOTES_TEMPLATE.md"
$outPath = Join-Path $root "docs\\patch_notes.md"
$date = (Get-Date).ToString("yyyy-MM-dd")

if (Test-Path $templatePath) {
  $notes = Get-Content $templatePath -Raw
} else {
  $notes = "# Gardens of Karaxas v{{version}}`n`nRelease Date: {{date}}`n`n## Changes`n{{changelog}}"
}

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

$notes = $notes.Replace("{{version}}", $Version).Replace("{{date}}", $date).Replace("{{changelog}}", $changelog)
if (-not $notes.Contains($changelog)) {
  $notes = "$notes`n`n## Changelog`n$changelog"
}

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($outPath, $notes, $utf8NoBom)
Write-Host "Wrote $outPath"
