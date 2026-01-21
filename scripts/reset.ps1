Param(
    [switch]$NoConfirm
)

$ErrorActionPreference = "Stop"

Write-Host "=== Message_AutoSend :: RESET DB ==="

# Go to project root (this script is in scripts/)
Set-Location -Path (Split-Path -Parent $PSScriptRoot)

# Ask confirmation (unless -NoConfirm)
if (-not $NoConfirm) {
    $answer = Read-Host "WARNING: all data in DB will be deleted. Type YES to continue"
    if ($answer -ne "YES") {
        Write-Host "Reset cancelled."
        exit 0
    }
}

# If .venv is already activated, just use python
$PYTHON = "python"

function Run-Step {
    param(
        [string]$Title,
        [string]$Args
    )

    Write-Host ">>> $Title"
    & $PYTHON manage.py $Args

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Command failed: python manage.py $Args"
        exit $LASTEXITCODE
    }
}

Run-Step "Applying migrations (initial)" "migrate"
Run-Step "Flush database" "flush --no-input"
Run-Step "Applying migrations (again)" "migrate"
Run-Step "Loading demo data" "seed_demo"
Run-Step "Creating manager users" "seed_managers"

Write-Host "=== RESET DONE ==="