param(
  [Parameter(Mandatory = $true)]
  [string]$Version,
  [Parameter(Mandatory = $true)]
  [string]$RuntimeZip,
  [string]$LauncherExe = "",
  [string]$OutputDir = "releases/game"
)

$ErrorActionPreference = "Stop"

function Resolve-OrCreateDirectory {
  param([string]$PathValue)

  if (-not (Test-Path $PathValue)) {
    New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
  }
  return (Resolve-Path $PathValue).Path
}

if ([string]::IsNullOrWhiteSpace($Version)) {
  throw "Version cannot be empty."
}

$runtimeZipPath = (Resolve-Path $RuntimeZip).Path
if (-not (Test-Path $runtimeZipPath)) {
  throw "Runtime zip does not exist: $RuntimeZip"
}

$launcherExePath = ""
if (-not [string]::IsNullOrWhiteSpace($LauncherExe)) {
  $launcherExePath = (Resolve-Path $LauncherExe).Path
  if (-not (Test-Path $launcherExePath)) {
    throw "Launcher executable does not exist: $LauncherExe"
  }
}

$outDir = Resolve-OrCreateDirectory -PathValue $OutputDir
$installerFileName = "AmbitionsOfPeace-game-installer-win-x64-$Version.exe"
$installerPath = Join-Path $outDir $installerFileName
$checksumPath = Join-Path $outDir "AmbitionsOfPeace-game-installer-win-x64-$Version.sha256"

$makensis = Get-Command makensis.exe -ErrorAction SilentlyContinue
if (-not $makensis) {
  $defaultNsis = "C:\\Program Files (x86)\\NSIS\\makensis.exe"
  if (Test-Path $defaultNsis) {
    $makensis = @{ Path = $defaultNsis }
  } else {
    throw "makensis.exe is required. Install NSIS before running this script."
  }
}

$tempRoot = Join-Path $env:TEMP ("aop-installer-build-" + [guid]::NewGuid().ToString("N"))
$payloadDir = Join-Path $tempRoot "payload"
$nsiPath = Join-Path $tempRoot "installer.nsi"

try {
  New-Item -ItemType Directory -Path $payloadDir -Force | Out-Null
  Expand-Archive -Path $runtimeZipPath -DestinationPath $payloadDir -Force

  $entrypoint = Join-Path $payloadDir "bin\\AmbitionsOfPeaceClient.exe"
  if (-not (Test-Path $entrypoint)) {
    throw "Runtime zip missing expected executable: $entrypoint"
  }

  $shortcutTarget = "`$INSTDIR\bin\AmbitionsOfPeaceClient.exe"
  if (-not [string]::IsNullOrWhiteSpace($launcherExePath)) {
    Copy-Item -Path $launcherExePath -Destination (Join-Path $payloadDir "AmbitionsOfPeaceLauncher.exe") -Force
    $shortcutTarget = "`$INSTDIR\AmbitionsOfPeaceLauncher.exe"
  }

  $payloadNsisPath = $payloadDir -replace "\\", "/"
  $installerNsisPath = $installerPath -replace "\\", "/"

  $nsi = @"
!include "MUI2.nsh"

Unicode True
Name "Ambitions of Peace"
OutFile "$installerNsisPath"
InstallDir "`$LOCALAPPDATA\AmbitionsOfPeace\game-runtime"
InstallDirRegKey HKCU "Software\AmbitionsOfPeace" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma

!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "`$INSTDIR"
  File /r "$payloadNsisPath\*"
  WriteRegStr HKCU "Software\AmbitionsOfPeace" "InstallDir" "`$INSTDIR"
  CreateDirectory "`$SMPROGRAMS\Ambitions of Peace"
  CreateShortCut "`$SMPROGRAMS\Ambitions of Peace\Ambitions of Peace.lnk" "$shortcutTarget"
  CreateShortCut "`$DESKTOP\Ambitions of Peace.lnk" "$shortcutTarget"
  WriteUninstaller "`$INSTDIR\Uninstall Ambitions of Peace.exe"
SectionEnd

Section "Uninstall"
  Delete "`$SMPROGRAMS\Ambitions of Peace\Ambitions of Peace.lnk"
  RMDir "`$SMPROGRAMS\Ambitions of Peace"
  Delete "`$DESKTOP\Ambitions of Peace.lnk"
  Delete "`$INSTDIR\Uninstall Ambitions of Peace.exe"
  Delete "`$INSTDIR\AmbitionsOfPeaceLauncher.exe"
  RMDir /r "`$INSTDIR\bin"
  RMDir /r "`$INSTDIR\client-app"
  RMDir /r "`$INSTDIR\assets"
  Delete "`$INSTDIR\release_version.txt"
  RMDir "`$INSTDIR"
  DeleteRegKey HKCU "Software\AmbitionsOfPeace"
SectionEnd
"@

  Set-Content -Path $nsiPath -Value $nsi -Encoding utf8
  & $makensis.Path $nsiPath | Out-Host

  if (-not (Test-Path $installerPath)) {
    throw "Installer compilation failed: missing output $installerPath"
  }

  $hash = Get-FileHash -Path $installerPath -Algorithm SHA256
  Set-Content -Path $checksumPath -Value ($hash.Hash.ToLower() + "  " + $installerFileName) -Encoding ascii
  Write-Host "Built installer: $installerPath"
}
finally {
  if (Test-Path $tempRoot) {
    Remove-Item -Path $tempRoot -Recurse -Force
  }
}
