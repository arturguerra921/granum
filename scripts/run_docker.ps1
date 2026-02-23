Write-Host "Iniciando verificação de portas..."
$port = 8050
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($process) {
    Write-Host "Processo encontrado na porta $port (PID: $process). Encerrando..."
    Stop-Process -Id $process -Force
    Write-Host "Processo encerrado."
} else {
    Write-Host "Nenhum processo encontrado na porta $port."
}

Write-Host "Verificando se o Docker está rodando..."
if (!(docker info)) {
    Write-Error "Docker não está rodando. Por favor, inicie o Docker Desktop."
    exit 1
}

# --- Download Map Data Logic ---
$dataDir = "valhalla_data"
$mapFile = "$dataDir\brazil-latest.osm.pbf"
$mapUrl = "https://download.geofabrik.de/south-america/brazil-latest.osm.pbf"

if (!(Test-Path -Path $dataDir)) {
    New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
    Write-Host "Diretório '$dataDir' criado."
}

if (!(Test-Path -Path $mapFile)) {
    Write-Host "Arquivo de mapa não encontrado. Baixando de $mapUrl..."
    Write-Host "Isso pode levar alguns minutos (arquivo grande)..."
    try {
        Invoke-WebRequest -Uri $mapUrl -OutFile $mapFile
        Write-Host "Download concluído com sucesso."
    } catch {
        Write-Error "Falha no download do mapa: $_"
        exit 1
    }
} else {
    Write-Host "Arquivo de mapa encontrado em '$mapFile'. Pulando download."
}
# --- End Download Logic ---


Write-Host "Construindo e iniciando containers..."
docker-compose up -d --build

Write-Host "Aguardando serviços iniciarem..."
Start-Sleep -Seconds 5

Write-Host "Aplicação disponível em http://localhost:8050"
Write-Host "Valhalla disponível em http://localhost:8002"
Write-Host "Nota: O Valhalla irá processar o arquivo de mapa local agora. Isso pode levar alguns minutos na primeira execução para construir o grafo."

Start-Process "http://localhost:8050"
