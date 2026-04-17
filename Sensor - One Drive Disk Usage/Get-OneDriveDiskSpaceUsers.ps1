$PINNED = 0x00080000
$OFFLINE = 0x00001000

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

            $results += "{0}|{1}|{2}|{3}|{4}" -f `
                $userName, `
                $folder.FullName, `
                ([math]::Round($locallyAvailable / 1GB, 2)), `
                ([math]::Round($onlineOnly / 1GB, 2)), `
                ([math]::Round($alwaysAvailable / 1GB, 2))
        }
        catch {
            $results += "{0}|{1}|Error|Error|Error" -f $userName, $folder.FullName
        }
    }
}

if ($results.Count -eq 0) {
    Write-Output "No OneDrive folders found"
}
else {
    $results
}