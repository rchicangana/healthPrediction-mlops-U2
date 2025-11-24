# Script helper para ejecutar build_and_push_docker.ps1
# Ejecuta este archivo desde cualquier ubicación

# Cambiar al directorio del proyecto
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "Directorio actual: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Verificar que el script existe
if (Test-Path ".\scripts\build_and_push_docker.ps1") {
    Write-Host "Ejecutando script..." -ForegroundColor Green
    Write-Host ""
    & ".\scripts\build_and_push_docker.ps1" $args
} else {
    Write-Host "Error: No se encontró el script build_and_push_docker.ps1" -ForegroundColor Red
    Write-Host "Asegúrate de estar en el directorio correcto del proyecto." -ForegroundColor Yellow
}

