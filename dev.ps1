$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Show-Menu {
    Clear-Host
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "      SAAS PLATFORM V2 - Panel de Control" -ForegroundColor Cyan
    Write-Host "      $ProjectRoot" -ForegroundColor DarkGray
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [1]  Iniciar servicios con Docker (build + up)" -ForegroundColor White
    Write-Host "  [2]  Detener servicios Docker" -ForegroundColor White
    Write-Host "  [3]  Ver logs del backend en vivo" -ForegroundColor White
    Write-Host "  [4]  Reiniciar servicios Docker" -ForegroundColor White
    Write-Host "  [5]  Ver estado del sistema (health check)" -ForegroundColor White
    Write-Host "  [6]  Ejecutar backend local (uvicorn, sin Docker)" -ForegroundColor White
    Write-Host "  [7]  Hacer backup de datos" -ForegroundColor White
    Write-Host "  [8]  Ver estado de git" -ForegroundColor White
    Write-Host "  [9]  Crear commit de cambios" -ForegroundColor White
    Write-Host "  [0]  Salir" -ForegroundColor White
    Write-Host ""
}

function Wait-Key {
    Write-Host ""
    Read-Host "Presiona ENTER para volver al menu"
}

function Invoke-DockerUp {
    Write-Host "Construyendo e iniciando contenedores..." -ForegroundColor Yellow
    docker compose up -d --build
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Servicios iniciados correctamente." -ForegroundColor Green
    } else {
        Write-Host "Ocurrio un error al iniciar los servicios." -ForegroundColor Red
    }
}

function Invoke-DockerDown {
    Write-Host "Deteniendo contenedores..." -ForegroundColor Yellow
    docker compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Servicios detenidos." -ForegroundColor Green
    } else {
        Write-Host "Ocurrio un error al detener los servicios." -ForegroundColor Red
    }
}

function Show-Logs {
    Write-Host "Mostrando logs del backend (presiona Ctrl+C para salir)..." -ForegroundColor Yellow
    docker logs -f saas-backend
}

function Invoke-DockerRestart {
    Write-Host "Reiniciando servicios..." -ForegroundColor Yellow
    docker compose down
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error al detener. Continuando..." -ForegroundColor Red
    }
    docker compose up -d --build
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Servicios reiniciados." -ForegroundColor Green
    } else {
        Write-Host "Ocurrio un error al reiniciar." -ForegroundColor Red
    }
}

function Show-Health {
    Write-Host "Contenedores activos:" -ForegroundColor Yellow
    docker ps --filter "name=saas-backend" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    Write-Host ""
    Write-Host "Consultando health check..." -ForegroundColor Yellow
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
        Write-Host ("Respuesta: {0}" -f ($resp | ConvertTo-Json -Compress)) -ForegroundColor Green
    } catch {
        Write-Host "El backend no responde en http://localhost:8000/health" -ForegroundColor Red
    }
}

function Invoke-LocalDev {
    Write-Host "Ejecutando backend en modo desarrollo..." -ForegroundColor Yellow
    Write-Host "Requiere que las dependencias esten instaladas (pip install -r requirements.txt)" -ForegroundColor DarkGray
    Set-Location (Join-Path $ProjectRoot "backend")
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    Set-Location $ProjectRoot
}

function Invoke-Backup {
    $backupDir = Join-Path $ProjectRoot "backups"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $dest = Join-Path $backupDir ("data-backup-" + $stamp)
    if (Test-Path (Join-Path $ProjectRoot "data")) {
        Copy-Item -Path (Join-Path $ProjectRoot "data") -Destination $dest -Recurse -Force
        Write-Host ("Backup creado en: {0}" -f $dest) -ForegroundColor Green
        Write-Host ("Tamano: {0:N2} MB" -f ((Get-ChildItem $dest -Recurse -File | Measure-Object Length -Sum).Sum / 1MB)) -ForegroundColor DarkGray
    } else {
        Write-Host "No existe la carpeta data en el proyecto." -ForegroundColor Yellow
    }
}

function Show-GitStatus {
    Write-Host "Estado del repositorio:" -ForegroundColor Yellow
    git status
}

function Invoke-GitCommit {
    $msg = Read-Host "Mensaje del commit"
    if ([string]::IsNullOrWhiteSpace($msg)) {
        Write-Host "Commit cancelado: mensaje vacio." -ForegroundColor Red
        return
    }
    git add -A
    git commit -m $msg
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Commit creado." -ForegroundColor Green
    } else {
        Write-Host "No se pudo crear el commit." -ForegroundColor Red
    }
}

while ($true) {
    Show-Menu
    $option = Read-Host "Elige una opcion"
    switch ($option) {
        "1" { Invoke-DockerUp; Wait-Key }
        "2" { Invoke-DockerDown; Wait-Key }
        "3" { Show-Logs }
        "4" { Invoke-DockerRestart; Wait-Key }
        "5" { Show-Health; Wait-Key }
        "6" { Invoke-LocalDev }
        "7" { Invoke-Backup; Wait-Key }
        "8" { Show-GitStatus; Wait-Key }
        "9" { Invoke-GitCommit; Wait-Key }
        "0" { Write-Host "Hasta luego!" -ForegroundColor Cyan; exit }
        default { Write-Host "Opcion invalida. Intenta de nuevo." -ForegroundColor Red; Start-Sleep -Seconds 1 }
    }
}
