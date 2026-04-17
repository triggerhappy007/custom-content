$count = 0
$errorCount = 0
$outputFile = "$env:TEMP\OneDrive_Processed_Log.txt"

# Remove existing log file
if (Test-Path $outputFile) {
    Remove-Item $outputFile -Force
}

# Arrays to store errors
$errorsList = @()

# Start log
"===== Run started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') =====" |
    Set-Content -Path $outputFile -Encoding utf8

Get-ChildItem $ENV:OneDriveCommercial -Force -File -Recurse -ErrorAction SilentlyContinue |
Where-Object { $_.Attributes -match 'ReparsePoint' -or $_.Attributes -eq '525344' } |
ForEach-Object {
    try {
        $p = Start-Process attrib.exe -ArgumentList "`"$($_.FullName)`" +U -P /s" -NoNewWindow -Wait -PassThru

        if ($p.ExitCode -eq 0) {
            $count++
            "SUCCESS | $(Get-Date -Format 'HH:mm:ss') | $($_.FullName)" |
                Add-Content -Path $outputFile -Encoding utf8
        }
        else {
            $errorCount++
            $msg = "ERROR   | $(Get-Date -Format 'HH:mm:ss') | $($_.FullName) | ExitCode: $($p.ExitCode)"
            $errorsList += $msg
            $msg | Add-Content -Path $outputFile -Encoding utf8
        }
    }
    catch {
        $errorCount++
        $msg = "ERROR   | $(Get-Date -Format 'HH:mm:ss') | $($_.FullName) | $($_.Exception.Message)"
        $errorsList += $msg
        $msg | Add-Content -Path $outputFile -Encoding utf8
    }
}

# Summary
@"
===== SUMMARY =====
Total processed : $count
Errors          : $errorCount
Completed       : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@ | Add-Content -Path $outputFile -Encoding utf8

# Dedicated error section (clean and easy to read)
if ($errorsList.Count -gt 0) {
    "`n===== ERROR DETAILS =====" | Add-Content -Path $outputFile -Encoding utf8
    $errorsList | Add-Content -Path $outputFile -Encoding utf8
}

Write-Host "Log written to: $outputFile"