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

Write-Host "Construindo e iniciando containers..."
docker-compose up -d --build

Write-Host "Aguardando serviços iniciarem..."
Start-Sleep -Seconds 5

Write-Host "Aplicação disponível em http://localhost:8050"
Write-Host "Valhalla disponível em http://localhost:8002"
Write-Host "Nota: Na primeira execução, o Valhalla irá baixar e processar o mapa do Brasil. Isso pode levar alguns minutos."

Start-Process "http://localhost:8050"
