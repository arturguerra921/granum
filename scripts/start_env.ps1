
# 1. Create Virtual Environment
if (-not (Test-Path "granum_env")) {
    Write-Host "Creating Virtual Environment (granum_env)..."
    python -m venv granum_env
} else {
    Write-Host "Virtual Environment found."
}

# 2. Activate in current session (if possible) or instruct
# PowerShell cannot easily activate a venv for the parent shell from a script.
# The standard way is to dot-source it: . ./scripts/start_env.ps1
# But users often just run it.
# We will just print the command to run.

Write-Host "Virtual environment is ready."
Write-Host "To activate it, run:" -ForegroundColor Green
Write-Host "    .\granum_env\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or you can use 'scripts/build.ps1' to automatically run in the environment."
