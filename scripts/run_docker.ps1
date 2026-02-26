param (
    [switch]$Build
)

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

# --- Python Setup (Download Logic) ---
Write-Host "Iniciando setup do Valhalla e dados..."
try {
    # Assuming python is in PATH
    python scripts/setup_valhalla.py
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Erro no setup do Valhalla. Verifique se o Python e Docker estão instalados e rodando."
        exit 1
    }
} catch {
    Write-Error "Falha ao executar script de setup: $_"
    exit 1
}
# --- End Setup Logic ---

Write-Host "Iniciando containers..."
if ($Build) {
    Write-Host "Reconstruindo imagens..."
    docker-compose up -d --build
} else {
    Write-Host "Usando imagens existentes (use -Build para forçar reconstrução)..."
    docker-compose up -d
}

Write-Host "Aguardando serviços iniciarem..."
Start-Sleep -Seconds 5

Write-Host "Aplicação disponível em http://localhost:8050"
Write-Host "Valhalla disponível em http://localhost:8002"
Write-Host "Nota: Se o Valhalla já processou o mapa, a inicialização será rápida. Caso contrário, aguarde alguns minutos."
Write-Host "Nota: Alterações no código da aplicação serão aplicadas automaticamente (hot-reload)."

Start-Process "http://localhost:8050"
