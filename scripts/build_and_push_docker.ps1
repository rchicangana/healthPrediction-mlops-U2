# Script PowerShell para construir y subir imagenes Docker a ECR
# Uso: .\build_and_push_docker.ps1 [dev|prod|both]

param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "prod", "both")]
    [string]$Mode = "both"
)

# Configuracion (ajusta estos valores)
$AWS_ACCOUNT_ID = "776036137322"  # Reemplaza con tu Account ID
$AWS_REGION = "us-east-1"          # Reemplaza con tu region
$ECR_REPOSITORY = "health-prediction-mlops"
$IMAGE_NAME = "health-prediction-mlops"

Write-Host "=== Script de Build y Push a ECR ===" -ForegroundColor Green
Write-Host ""

# Detectar si usar Docker o Podman
$CONTAINER_TOOL = $null
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $CONTAINER_TOOL = "docker"
    Write-Host "Detectado: Docker" -ForegroundColor Cyan
} elseif (Get-Command podman -ErrorAction SilentlyContinue) {
    $CONTAINER_TOOL = "podman"
    Write-Host "Detectado: Podman" -ForegroundColor Cyan
} else {
    Write-Host "Error: Ni Docker ni Podman estan instalados." -ForegroundColor Red
    Write-Host "Instala Docker desde https://www.docker.com/" -ForegroundColor Yellow
    Write-Host "O Podman desde https://podman.io/" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Funcion para conectarse a ECR
function Connect-ECR {
    Write-Host "Autenticando en ECR..." -ForegroundColor Yellow
    $loginCmd = "aws ecr get-login-password --region $AWS_REGION | $CONTAINER_TOOL login --username AWS --password-stdin `"${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com`""
    Invoke-Expression $loginCmd | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Autenticacion exitosa" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[ERROR] Error en autenticacion" -ForegroundColor Red
        exit 1
    }
}

# Funcion para construir imagen
function New-Image {
    Write-Host "Construyendo imagen con $CONTAINER_TOOL..." -ForegroundColor Yellow
    Set-Location Api
    & $CONTAINER_TOOL build -t "${IMAGE_NAME}:latest" .
    Set-Location ..
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Imagen construida" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[ERROR] Error construyendo imagen" -ForegroundColor Red
        exit 1
    }
}

# Funcion para etiquetar y subir imagen
function Publish-Image {
    param([string]$Tag)
    
    $ECR_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${Tag}"
    
    Write-Host "Etiquetando imagen como ${Tag}..." -ForegroundColor Yellow
    & $CONTAINER_TOOL tag "${IMAGE_NAME}:latest" $ECR_URI
    
    Write-Host "Subiendo imagen ${Tag} a ECR..." -ForegroundColor Yellow
    & $CONTAINER_TOOL push $ECR_URI
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Imagen ${Tag} subida exitosamente" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "[ERROR] Error subiendo imagen" -ForegroundColor Red
        exit 1
    }
}

# Verificar que AWS CLI esta instalado
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "Error: AWS CLI no esta instalado. Instalalo desde https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# Verificar que las credenciales de AWS estan configuradas
try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Host "Error: Las credenciales de AWS no estan configuradas." -ForegroundColor Red
    Write-Host "Configuralas con: aws configure" -ForegroundColor Yellow
    exit 1
}

# Procesar modo
switch ($Mode) {
    "dev" {
        Connect-ECR
        New-Image
        Publish-Image "dev-latest"
    }
    "prod" {
        Connect-ECR
        New-Image
        Publish-Image "prod-latest"
    }
    "both" {
        Connect-ECR
        New-Image
        Publish-Image "dev-latest"
        Publish-Image "prod-latest"
    }
}

Write-Host "=== Proceso completado exitosamente ===" -ForegroundColor Green
Write-Host ""
Write-Host "Imagenes disponibles en ECR:" -ForegroundColor Cyan
$baseUri = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"
$devUri = $baseUri + ":dev-latest"
$prodUri = $baseUri + ":prod-latest"
Write-Host "  - $devUri"
Write-Host "  - $prodUri"
