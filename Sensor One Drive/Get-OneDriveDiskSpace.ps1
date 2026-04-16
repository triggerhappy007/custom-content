# Get-OneDriveDiskSpace.ps1
# Calculates the local disk space usage of OneDrive for Business
# Output: OneDrive Commercial Path|Always Available Files|Always Available Size|Cloud Only Files|Cloud Only Size

$OneDrivePath = $ENV:OneDriveCommercial

# --- Validate the path ---
if (-not $OneDrivePath) {
    Write-Error "The environment variable EnvOneDriveCommercial is not set or empty."
    exit 1
}

if (-not (Test-Path -Path $OneDrivePath)) {
    Write-Error "OneDrive path not found: $OneDrivePath"
    exit 1
}

# --- Format helper ---
function Format-Size {
    param([long]$Bytes)
    if ($Bytes -ge 1TB) { return [string]::Format("{0:N2} TB", ($Bytes / 1TB)) }
    elseif ($Bytes -ge 1GB) { return [string]::Format("{0:N2} GB", ($Bytes / 1GB)) }
    elseif ($Bytes -ge 1MB) { return [string]::Format("{0:N2} MB", ($Bytes / 1MB)) }
    elseif ($Bytes -ge 1KB) { return [string]::Format("{0:N2} KB", ($Bytes / 1KB)) }
    else { return "$Bytes Bytes" }
}

# --- OneDrive file state helper ---
# FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x400000 -> cloud-only (online-only)
# FILE_ATTRIBUTE_RECALL_ON_OPEN        = 0x40000  -> cloud-only (not downloaded)
# Files WITHOUT these flags are locally available (Always available / pinned)
$cloudOnlyMask = [uint32]0x400000 -bor [uint32]0x40000

function Get-OneDriveFileState {
    param($File)
    $attrs = [uint32]$File.Attributes
    if (($attrs -band $cloudOnlyMask) -ne 0) {
        return "CloudOnly"
    }
    return "AlwaysAvailable"
}

# --- Scan all files ---
$allItems = Get-ChildItem -Path $OneDrivePath -Recurse -Force -ErrorAction SilentlyContinue
$allFiles = $allItems | Where-Object { -not $_.PSIsContainer }

# --- Classify files ---
$alwaysAvailableFiles = [System.Collections.Generic.List[object]]::new()
$cloudOnlyFiles       = [System.Collections.Generic.List[object]]::new()

foreach ($file in $allFiles) {
    if ((Get-OneDriveFileState -File $file) -eq "AlwaysAvailable") {
        $alwaysAvailableFiles.Add($file)
    } else {
        $cloudOnlyFiles.Add($file)
    }
}

$alwaysAvailCount    = $alwaysAvailableFiles.Count
$alwaysAvailableSize = ($alwaysAvailableFiles | Measure-Object -Property Length -Sum).Sum
$alwaysAvailLabel    = Format-Size $alwaysAvailableSize

$cloudOnlyCount      = $cloudOnlyFiles.Count
$cloudOnlySize       = ($cloudOnlyFiles | Measure-Object -Property Length -Sum).Sum
$cloudOnlyLabel      = Format-Size $cloudOnlySize

# --- Output single pipe-delimited line ---
Write-Host "$OneDrivePath|$alwaysAvailCount|$alwaysAvailLabel|$cloudOnlyCount|$cloudOnlyLabel"
