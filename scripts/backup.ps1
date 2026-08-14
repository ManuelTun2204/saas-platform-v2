param(
    [int]$Keep = 10
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$DataDir = Join-Path $ProjectRoot 'data'
$BackupDir = Join-Path $ProjectRoot 'backups'

if (-not (Test-Path -LiteralPath $DataDir)) {
    Write-Host "No existe la carpeta data en $ProjectRoot"
    exit 1
}

New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dest = Join-Path $BackupDir ("data-backup-" + $stamp)

Copy-Item -Path $DataDir -Destination $dest -Recurse -Force

$sizeMB = (Get-ChildItem -Path $dest -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
Write-Host "Backup creado en: $dest ($([math]::Round($sizeMB, 2)) MB)"

# Rotacion: mantener solo los ultimos $Keep
$all = Get-ChildItem -Path $BackupDir -Directory -Filter 'data-backup-*' | Sort-Object Name -Descending
$toRemove = $all | Select-Object -Skip $Keep
foreach ($old in $toRemove) {
    Remove-Item -Path $old.FullName -Recurse -Force
    Write-Host "Backup antiguo eliminado: $($old.Name)"
}
