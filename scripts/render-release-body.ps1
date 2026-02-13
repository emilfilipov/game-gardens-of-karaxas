param(
  [string]$Version
)

$ErrorActionPreference = "Stop"

if (-not $Version -or $Version.Trim().Length -eq 0) {
  throw "Version is required."
}

$tag = "v$Version"
$date = (Get-Date).ToString("yyyy-MM-dd")
$templatePath = Join-Path $PSScriptRoot "..\\.github\\release-body-template.md"

if (Test-Path $templatePath) {
  $body = Get-Content $templatePath -Raw
} else {
  $body = "# Gardens of Karaxas $tag`n`n{{changelog}}"
}

$changelog = ""
try {
  $prevTag = git describe --tags --abbrev=0 2>$null
} catch {
  $prevTag = ""
}

if ($prevTag) {
  $log = git log "$prevTag..HEAD" --pretty=format:"- %s (%h)"
  if ($log) { $changelog = $log }
}

if (-not $changelog) { $changelog = "- Initial release" }

$body = $body.Replace("{{version}}", $Version).Replace("{{date}}", $date).Replace("{{tag}}", $tag)
if ($body.Contains("{{changelog}}")) {
  $body = $body.Replace("{{changelog}}", $changelog)
} else {
  $body = "$body`n`n## Changelog`n$changelog"
}

Set-Content -Path "release_body.md" -Value $body -Encoding utf8
