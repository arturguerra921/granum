
# Create Virtual Environment if it doesn't exist
if (-not (Test-Path "granum_env")) {
    Write-Host "Creating Virtual Environment..."
    python -m venv granum_env
} else {
    Write-Host "Virtual Environment already exists."
}

# Install dependencies
Write-Host "Installing dependencies..."
.\granum_env\Scripts\python -m pip install --upgrade pip
.\granum_env\Scripts\pip install -e .

Write-Host "Setup complete. You can now run the app with 'scripts/run.ps1'."
