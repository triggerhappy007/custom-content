# Get logged-in users (interactive sessions only)
$LoggedOnUsers = Get-CimInstance Win32_LoggedOnUser |
    ForEach-Object {
        ($_ | Select-Object -ExpandProperty Antecedent) -match 'Domain="(.+)",Name="(.+)"' | Out-Null
        [PSCustomObject]@{
            Domain = $Matches[1]
            User   = $Matches[2]
        }
    } | Sort-Object User -Unique

$Results = @()

foreach ($User in $LoggedOnUsers) {

    try {
        # Get SID
        $Account = New-Object System.Security.Principal.NTAccount($User.Domain, $User.User)
        $SID = $Account.Translate([System.Security.Principal.SecurityIdentifier]).Value

        # Registry path for user OneDrive config
        $RegPath = "Registry::HKEY_USERS\$SID\Software\Microsoft\OneDrive"

        # Try to get OneDrive folder
        $OneDrivePath = (Get-ItemProperty -Path $RegPath -ErrorAction Stop).UserFolder

        if (-not (Test-Path $OneDrivePath)) {
            throw "Path not found"
        }

        # Calculate folder size
        $SizeBytes = (Get-ChildItem -Path $OneDrivePath -Recurse -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum).Sum

        $SizeGB = [math]::Round($SizeBytes / 1GB, 2)

        $Results += [PSCustomObject]@{
            User          = "$($User.Domain)\$($User.User)"
            OneDrivePath  = $OneDrivePath
            SizeGB        = $SizeGB
        }
    }
    catch {
        $Results += [PSCustomObject]@{
            User          = "$($User.Domain)\$($User.User)"
            OneDrivePath  = "Not found / Not configured"
            SizeGB        = 0
        }
    }
}

# Output results
$Results | Format-Table -AutoSize