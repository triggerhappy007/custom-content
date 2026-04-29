$PINNED = 0x00080000
$OFFLINE = 0x00001000

$bucketingRaw = "||bucketing||"
$bucketEnabled = $true

if (-not [string]::IsNullOrWhiteSpace($bucketingRaw)) {
    switch -Regex ($bucketingRaw.Trim().ToLower()) {
        ^(0|false|disable|no)$ { $bucketEnabled = $false; break }
        ^(1|true|enable|yes)$ { $bucketEnabled = $true; break }
        default { $bucketEnabled = $true; break }
    }
}

function Get-Bucket {
    param([double]$ValueGb)

    if ($ValueGb -lt 1) { return "0-1 GB" }
    elseif ($ValueGb -lt 2) { return "1-2 GB" }
    elseif ($ValueGb -lt 5) { return "2-5 GB" }
    elseif ($ValueGb -lt 10) { return "5-10 GB" }
    elseif ($ValueGb -lt 20) { return "10-20 GB" }
    elseif ($ValueGb -lt 100) { return "20-100 GB" }
    elseif ($ValueGb -lt 200) { return "100-200 GB" }
    elseif ($ValueGb -lt 500) { return "200-500 GB" }
    else { return "500+ GB" }
}

function Format-Value {
    param(
        [double]$ValueGb,
        [bool]$BucketEnabled
    )

    if (-not $BucketEnabled) {
        return [string]$ValueGb
    }

    return Get-Bucket -ValueGb $ValueGb
}

$results = @()

Get-ChildItem "C:\Users" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $userName = $_.Name
    $profilePath = $_.FullName

    $oneDriveFolders = Get-ChildItem $profilePath -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "OneDrive*" }

    foreach ($folder in $oneDriveFolders) {
        $locallyAvailable = 0
        $onlineOnly = 0
        $alwaysAvailable = 0

        try {
            Get-ChildItem $folder.FullName -Recurse -File -Force -ErrorAction SilentlyContinue | ForEach-Object {
                $size = if ($_.Length) { [int64]$_.Length } else { 0 }
                $attrs = [int64]$_.Attributes

                if (($attrs -band $PINNED) -ne 0) {
                    $alwaysAvailable += $size
                }
                elseif (($attrs -band $OFFLINE) -ne 0) {
                    $onlineOnly += $size
                }
                else {
                    $locallyAvailable += $size
                }
            }

            $localGb = [math]::Round($locallyAvailable / 1GB, 2)
            $onlineGb = [math]::Round($onlineOnly / 1GB, 2)
            $alwaysGb = [math]::Round($alwaysAvailable / 1GB, 2)
            $totalGb = [math]::Round(($locallyAvailable + $onlineOnly + $alwaysAvailable) / 1GB, 2)

            $results += "{0}|{1}|{2}|{3}|{4}|{5}" -f `
                $userName, `
                $folder.FullName, `
                (Format-Value -ValueGb $localGb -BucketEnabled $bucketEnabled), `
                (Format-Value -ValueGb $onlineGb -BucketEnabled $bucketEnabled), `
                (Format-Value -ValueGb $alwaysGb -BucketEnabled $bucketEnabled), `
                (Format-Value -ValueGb $totalGb -BucketEnabled $bucketEnabled)
        }
        catch {
            $results += "{0}|{1}|Error|Error|Error|Error" -f $userName, $folder.FullName
        }
    }
}

if ($results.Count -eq 0) {
    Write-Output "No OneDrive folders found"
}
else {
    $results
}