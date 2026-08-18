# Instalación en otra computadora

## Requisitos
- Windows 10/11
- Python 3.10+ instalado
- Docker Desktop instalado

## Paso 1: Copiar el script
Copia la carpeta `scripts/` a la otra computadora.

## Paso 2: Ejecutar como administrador
1. Click derecho en `install-aider.ps1`
2. "Ejecutar con PowerShell" (como administrador)
3. Esperar a que termine (~5-10 minutos)

## Paso 3: Usar
1. Doble clic en `Aider-SaaS` del escritorio
2. Escribir instrucción y presionar Enter
3. Aider edita los archivos automáticamente

## Modelos incluidos
- `llama3.2:3b` (~2GB) — Rápido, bueno para ediciones simples

## Para agregar más modelos
```powershell
ollama pull qwen3:4b
ollama pull deepseek-r1:latest
```

## Variables de entorno configuradas
- `OLLAMA_API_BASE=http://127.0.0.1:11434`
