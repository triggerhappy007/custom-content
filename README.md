# custom-content

A collection of Tanium sensors, packages, and AI/ML scripts for endpoint management, security monitoring, and anomaly detection.

---

## Projects

### SMB_Config
Configures Samba SMB v3 settings on Linux endpoints.
- **Sensor** (`SMB Configuration`): Reads key settings from `/etc/samba/smb.conf` and reports their current values.
- **Package** (`Set SMB V3 Configuration`): Runs `Package_SMB_Conf.py` to enforce secure SMB settings — encryption, signing, and min/max protocol versions.

Settings managed: `workgroup`, `security`, `client min protocol`, `client max protocol`, `encrypt passwords`, `smb encrypt`, `smb signing`

---

### AI-ML / Fraud Detection (`bank.py`)
A fraud detection demo using Isolation Forest on synthetic financial transaction data.
- Generates legitimate and fraudulent transaction clusters
- Trains an Isolation Forest anomaly detection model
- Simulates an adversarial attack by shifting fraudulent transactions to evade detection
- Visualizes original vs. manipulated data

---

### AI-ML / Student Login Anomaly Detection (`students.py`)
Anomaly detection on student login behaviour using Isolation Forest.
- Features: login time and session duration
- Data is scaled with `StandardScaler` before model fitting
- Flags suspicious logins (e.g. very late-night or unusually long sessions) from a CSV dataset

---

### OneDrive Disk Usage
Reports OneDrive storage breakdown per user across all profiles on a Windows machine.
- **Sensor** (`One Drive Disk Usage`): PowerShell script that scans each user's OneDrive folders and reports locally available, online-only, and always-available file sizes in GB.
- **Scripts**: Standalone PowerShell variants for manual execution (`Get-OneDriveDiskSpace.ps1`, `Get-OneDriveDiskSpaceUsers.ps1`)

---

### OneDrive Files Offline
Forces cloud-only OneDrive files to download locally.
- **Package** (`OneDrive_Files_Offline.ps1`): Iterates files with cloud-only reparse point attributes and runs `attrib.exe` to pin them locally.
- Produces a detailed log at `$env:TEMP\OneDrive_Processed_Log.txt` with success/error tracking and a run summary.

---

### LC - Microsoft Intune Tenant Details
Retrieves Azure AD and Intune join information from Windows endpoints.
- **Sensor** (`LC - Microsoft Intune Tenant Details`): Runs `dsregcmd /status` and extracts key fields.
- **Standalone script** (`Microsoft Intune Tenant.py`): Local test version without Tanium dependencies.

Fields reported: `AzureAdJoined`, `EnterpriseJoined`, `DomainJoined`, `DomainName`, `TenantName`, `TenantId`, `WorkplaceTenantId`, `WorkplaceTenantName`

---

### LC - Deploy - Software Installation Details
Queries the Tanium Deploy SQLite database for recent software installation history.
- **Sensor** (`LC - Deploy - Software Installation Details`): Parameterised by number of days (max 30).
- Returns: software ID, revision, name, operation type, start time, success status, and error details.
- Supports Windows, Linux, and Mac.

---

### LC - User Stats Monitoring
Tracks workstation usage over the last 15 days based on unlock events.
- **Sensor** (`LC - User Stats Monitoring`): Reads a `Locked.csv` log and calculates daily usage in minutes, hours, and percentage of a 7-hour workday.
- **Packages**:
  - `LC - User Monitoring - Enable`: Deploys monitoring scripts and registers a scheduled task.
  - `LC - User Monitoring - Disable`: Removes the scheduled task.
  - `LC - User Monitoring - Now`: Runs the monitoring script immediately.

---

### SDX - CVE List
Surfaces CVE findings from the Tanium Comply module.
- **Sensor** (`SDX - CVE List`): Wraps the built-in `Comply - CVE Findings` sensor and re-publishes results via `tanium.results`.
- Supports Windows, Mac, and Linux.