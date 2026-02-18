
# 1. Kill the process on port 8050
$port = 8050
Write-Host "Stopping Granum on port $port..."
$connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($connections) {
    foreach ($conn in $connections) {
        $pid_to_kill = $conn.OwningProcess
        if ($pid_to_kill -gt 0) {
            Write-Host "Killing process $pid_to_kill..."
            Stop-Process -Id $pid_to_kill -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "No process found running on port $port."
}

# 2. Deactivate (if in venv)
# PowerShell 'deactivate' function is only available if venv was activated in the shell.
if (Get-Command deactivate -ErrorAction SilentlyContinue) {
    deactivate
    Write-Host "Environment deactivated."
} else {
    Write-Host "Environment was not active in this shell."
}
