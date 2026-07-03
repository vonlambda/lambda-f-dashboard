# Lambda-F Daily Update Script
# Runs update_lambda.py and logs both stdout and stderr separately so Python
# tracebacks survive even when PowerShell's NativeCommandError wrapping
# would otherwise swallow them. See docs/MASTER.md "Known issues" for the
# 2026-04-14 / 23 / 27 / 29 / 30 short-log incident that motivated this fix.

$ErrorActionPreference = "Continue"

# Setup paths
$scriptDir = "C:\backtesting\lambda-f-engine"
$logDir = Join-Path $scriptDir "logs"
$dateStamp = Get-Date -Format "yyyy-MM-dd"
$logFile = Join-Path $logDir ("lambda_f_" + $dateStamp + ".log")
$stdoutTmp = Join-Path $logDir ("lambda_f_" + $dateStamp + ".stdout.tmp")
$stderrTmp = Join-Path $logDir ("lambda_f_" + $dateStamp + ".stderr.tmp")

# Create logs directory if needed
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Log start
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logFile -Value "==========================================" -Encoding utf8
Add-Content -Path $logFile -Value "Lambda-F Update Started: $timestamp"   -Encoding utf8
Add-Content -Path $logFile -Value "==========================================" -Encoding utf8

# Change to script directory
Set-Location $scriptDir

# Sync the working copy before running. The updater pushes via the GitHub
# API, so an unsynced local copy regenerates the README from stale content
# and silently reverts upstream fixes on its next push (2026-07-03 incident:
# honest-scorecard fix would have been overwritten by the next daily run).
# A failed pull is logged but does not block the run.
$pullStdout = Join-Path $logDir ("git_pull_" + $dateStamp + ".stdout.tmp")
$pullStderr = Join-Path $logDir ("git_pull_" + $dateStamp + ".stderr.tmp")
$pullProc = Start-Process -FilePath "git" `
    -ArgumentList "pull", "--ff-only", "--autostash" `
    -WorkingDirectory $scriptDir `
    -RedirectStandardOutput $pullStdout `
    -RedirectStandardError $pullStderr `
    -NoNewWindow `
    -PassThru `
    -Wait
foreach ($tmp in @($pullStdout, $pullStderr)) {
    if (Test-Path $tmp) {
        Get-Content -Path $tmp -Encoding utf8 | Add-Content -Path $logFile -Encoding utf8
        Remove-Item -Path $tmp -Force
    }
}
if ($pullProc.ExitCode -ne 0) {
    Add-Content -Path $logFile -Value "WARNING: git pull failed (exit $($pullProc.ExitCode)); continuing with existing working copy" -Encoding utf8
}

# Run python via Start-Process so stdout and stderr go to separate files.
# This bypasses PowerShell's NativeCommandError wrapping that previously
# caused stderr-only crashes (import errors, syntax errors, etc.) to disappear.
$proc = Start-Process -FilePath "python" `
    -ArgumentList "update_lambda.py" `
    -WorkingDirectory $scriptDir `
    -RedirectStandardOutput $stdoutTmp `
    -RedirectStandardError $stderrTmp `
    -NoNewWindow `
    -PassThru `
    -Wait

$exitCode = $proc.ExitCode

# Append stdout to the main log
if (Test-Path $stdoutTmp) {
    Get-Content -Path $stdoutTmp -Encoding utf8 | Add-Content -Path $logFile -Encoding utf8
    Remove-Item -Path $stdoutTmp -Force
}

# Append stderr to the main log under a clear header (only if non-empty)
if (Test-Path $stderrTmp) {
    $stderrSize = (Get-Item $stderrTmp).Length
    if ($stderrSize -gt 0) {
        Add-Content -Path $logFile -Value ""                                -Encoding utf8
        Add-Content -Path $logFile -Value "------- STDERR -------"           -Encoding utf8
        Get-Content -Path $stderrTmp -Encoding utf8 | Add-Content -Path $logFile -Encoding utf8
        Add-Content -Path $logFile -Value "----- END STDERR -----"           -Encoding utf8
    }
    Remove-Item -Path $stderrTmp -Force
}

Add-Content -Path $logFile -Value "" -Encoding utf8
if ($exitCode -eq 0) {
    Add-Content -Path $logFile -Value "Update completed successfully (exit 0)" -Encoding utf8
} else {
    Add-Content -Path $logFile -Value "ERROR: python exited with code $exitCode" -Encoding utf8
}

$endTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logFile -Value "Finished: $endTime" -Encoding utf8
Add-Content -Path $logFile -Value ""                    -Encoding utf8

# Surface non-zero exit so the Task Scheduler "Last Result" reflects it.
exit $exitCode
