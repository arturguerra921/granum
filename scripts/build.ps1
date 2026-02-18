
# 1. Kill any existing process on port 8050 (to prevent "Address already in use")
$port = 8050
Write-Host "Cleaning up port $port..."
$connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($connections) {
    foreach ($conn in $connections) {
        $pid_to_kill = $conn.OwningProcess
        if ($pid_to_kill -gt 0) {
            Write-Host "Killing process $pid_to_kill..."
            Stop-Process -Id $pid_to_kill -Force -ErrorAction SilentlyContinue
        }
    }
}

# 2. Activate Virtual Environment for this script execution
if (Test-Path "granum_env\Scripts\Activate.ps1") {
    # Dot-source the activation script to load the environment variables into the current scope
    . .\granum_env\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found. Please run 'scripts/start_env.ps1' first." -ForegroundColor Red
    exit 1
}

# 3. Install/Update Dependencies (Editable Mode)
# This ensures any changes to setup.py/pyproject.toml or new files are picked up
Write-Host "Installing/Updating package in editable mode..."
pip install -e .

# 4. Run the Application
Write-Host "Starting Granum (granum-run)..."
granum-run
