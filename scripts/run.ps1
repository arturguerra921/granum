
# Port used by Granum App
$port = 8050

# Check if process is running on port 8050
Write-Host "Checking for existing process on port $port..."

# Get the process ID using netstat (or Get-NetTCPConnection)
# PowerShell 5+ approach
try {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $pid = $conn.OwningProcess
            if ($pid -gt 0) {
                Write-Host "Killing process $pid on port $port..."
                Stop-Process -Id $pid -Force
            }
        }
    } else {
        Write-Host "No process found on port $port."
    }
} catch {
    Write-Host "Could not automatically kill process. Please check manually."
}

# Run the application
Write-Host "Starting Granum application..."

if (Test-Path "granum_env\Scripts\python.exe") {
    & .\granum_env\Scripts\python.exe -m src.__main__
} else {
    Write-Host "Virtual environment not found. Please run scripts/setup.ps1 first."
}
