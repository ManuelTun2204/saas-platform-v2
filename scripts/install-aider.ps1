# ============================================
# Script de instalación: Aider + Ollama
# Ejecutar en PowerShell como ADMINISTRADOR
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Instalación: Aider + Ollama para IA   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar si Ollama está instalado
Write-Host "[1/5] Verificando Ollama..." -ForegroundColor Yellow
$ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaPath) {
    Write-Host "  ✅ Ollama ya está instalado" -ForegroundColor Green
} else {
    Write-Host "  📦 Descargando Ollama..." -ForegroundColor Yellow
    $ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
    Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $ollamaInstaller
    Start-Process -FilePath $ollamaInstaller -Wait
    Write-Host "  ✅ Ollama instalado" -ForegroundColor Green
}

# 2. Iniciar servidor Ollama si no está corriendo
Write-Host "[2/5] Verificando servidor Ollama..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3
    Write-Host "  ✅ Ollama ya está corriendo" -ForegroundColor Green
} catch {
    Write-Host "  🔄 Iniciando servidor Ollama..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Minimized
    Start-Sleep -Seconds 5
    Write-Host "  ✅ Servidor Ollama iniciado" -ForegroundColor Green
}

# 3. Descargar modelo (solo si no existe)
Write-Host "[3/5] Verificando modelo llama3.2:3b..." -ForegroundColor Yellow
$modelos = ollama list 2>&1
if ($modelos -match "llama3.2:3b") {
    Write-Host "  ✅ Modelo ya descargado" -ForegroundColor Green
} else {
    Write-Host "  📦 Descargando llama3.2:3b (~2GB, puede tardar)..." -ForegroundColor Yellow
    ollama pull llama3.2:3b
    Write-Host "  ✅ Modelo descargado" -ForegroundColor Green
}

# 4. Instalar Aider
Write-Host "[4/5] Instalando Aider..." -ForegroundColor Yellow
python -m pip install aider-install 2>&1 | Out-Null
python -m aider_install 2>&1 | Out-Null
Write-Host "  ✅ Aider instalado" -ForegroundColor Green

# 5. Configurar variable de entorno
Write-Host "[5/5] Configurando variables de entorno..." -ForegroundColor Yellow
setx OLLAMA_API_BASE "http://127.0.0.1:11434" 2>&1 | Out-Null
Write-Host "  ✅ OLLAMA_API_BASE configurada" -ForegroundColor Green

# Crear acceso directo en escritorio
Write-Host ""
Write-Host "📌 Creando acceso directo en escritorio..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Aider-SaaS.lnk")
$Shortcut.TargetPath = "cmd.exe"
$Shortcut.Arguments = "/k `"set PATH=C:\Users\$env:USERNAME\.local\bin;%PATH% && set OLLAMA_API_BASE=http://127.0.0.1:11434 && echo === Aider + Ollama === && echo Escribe tu instruccion y presiona Enter`""
$Shortcut.WorkingDirectory = "C:\"
$Shortcut.Description = "Aider + Ollama"
$Shortcut.Save()
Write-Host "  ✅ Acceso directo creado en escritorio" -ForegroundColor Green

# Resumen
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ INSTALACIÓN COMPLETADA             " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Modelos instalados:" -ForegroundColor Cyan
ollama list
Write-Host ""
Write-Host "Cómo usar:" -ForegroundColor Cyan
Write-Host "  1. Doble clic en 'Aider-SaaS' del escritorio" -ForegroundColor White
Write-Host "  2. Escribe tu instrucción y presiona Enter" -ForegroundColor White
Write-Host "  3. Aider editará los archivos automáticamente" -ForegroundColor White
Write-Host ""
Write-Host "Ejemplo:" -ForegroundColor Cyan
Write-Host "  'Agrega un botón de WhatsApp en el footer'" -ForegroundColor White
Write-Host ""
