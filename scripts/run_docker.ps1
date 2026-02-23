
# 1. Check if Docker is running
Write-Host "Checking if Docker is running..." -ForegroundColor Cyan
try {
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: Docker command not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# 2. Build and Start Containers
Write-Host "Starting Granum and Valhalla services with Docker Compose..." -ForegroundColor Green
Write-Host "Note: If this is the first run, Valhalla will download Brazil map data (3-4GB). This may take 1-2 hours." -ForegroundColor Yellow

docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to start containers." -ForegroundColor Red
    exit 1
}

# 3. Wait for services (simple check)
Write-Host "Containers started. Waiting for services to initialize..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# 4. Open Browser
$url = "http://localhost:8050"
Write-Host "Opening application at $url..." -ForegroundColor Green
Start-Process $url

# 5. Instructions
Write-Host ""
Write-Host "---------------------------------------------------" -ForegroundColor Green
Write-Host "Application is running in the background."
Write-Host "To view logs (especially for Valhalla download progress):"
Write-Host "    docker-compose logs -f" -ForegroundColor Yellow
Write-Host ""
Write-Host "To STOP the application and services, run:"
Write-Host "    docker-compose down" -ForegroundColor Red
Write-Host "---------------------------------------------------" -ForegroundColor Green
