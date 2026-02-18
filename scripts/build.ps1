
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
            # Fallback for stubborn processes
            if (Get-Process -Id $pid_to_kill -ErrorAction SilentlyContinue) {
                Write-Host "  Using taskkill fallback for $pid_to_kill..."
                taskkill /F /PID $pid_to_kill
            }
        }
    }
}

# 2. Activate Virtual Environment for this script execution (for install)
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

# 4. Run the Application in a NEW WINDOW
# This prevents the VS Code terminal from freezing/blocking and causing ETIMEDOUT errors.
Write-Host "Starting Granum in a separate window..."
Write-Host "NOTE: To stop the server, close the new window or run 'scripts/end_env.ps1'." -ForegroundColor Cyan

# We start a new PowerShell process that activates the venv and runs the server.
# -NoExit keeps the window open so you can see logs/errors.
# The command block:
#   1. Activate venv
#   2. Change to project root (Get-Location of current script context)
#   3. Run granum-run
$projectRoot = Get-Location
$argList = "-NoExit", "-Command", "& { Set-Location '$projectRoot'; . .\granum_env\Scripts\Activate.ps1; Write-Host 'Granum Server Running...'; granum-run }"

Start-Process powershell -ArgumentList $argList
