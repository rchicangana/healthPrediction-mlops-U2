#!/bin/bash
# Script para construir y subir imágenes Docker a ECR
# Uso: ./build_and_push_docker.sh [dev|prod|both]

set -e

# Configuración (ajusta estos valores)
AWS_ACCOUNT_ID="776036137322"  # Reemplaza con tu Account ID
AWS_REGION="us-east-1"          # Reemplaza con tu región
ECR_REPOSITORY="health-prediction-mlops"
IMAGE_NAME="health-prediction-mlops"

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Script de Build y Push a ECR ===${NC}\n"

# Función para autenticarse en ECR
authenticate_ecr() {
    echo -e "${YELLOW}Autenticando en ECR...${NC}"
    aws ecr get-login-password --region ${AWS_REGION} | \
        docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    echo -e "${GREEN}✓ Autenticación exitosa${NC}\n"
}

# Función para construir imagen
build_image() {
    echo -e "${YELLOW}Construyendo imagen Docker...${NC}"
    cd Api
    docker build -t ${IMAGE_NAME}:latest .
    cd ..
    echo -e "${GREEN}✓ Imagen construida${NC}\n"
}

# Función para etiquetar y subir imagen
push_image() {
    local TAG=$1
    local ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${TAG}"
    
    echo -e "${YELLOW}Etiquetando imagen como ${TAG}...${NC}"
    docker tag ${IMAGE_NAME}:latest ${ECR_URI}
    
    echo -e "${YELLOW}Subiendo imagen ${TAG} a ECR...${NC}"
    docker push ${ECR_URI}
    
    echo -e "${GREEN}✓ Imagen ${TAG} subida exitosamente${NC}\n"
}

# Verificar que AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI no está instalado. Instálalo desde https://aws.amazon.com/cli/"
    exit 1
fi

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado. Instálalo desde https://www.docker.com/"
    exit 1
fi

# Verificar que las credenciales de AWS están configuradas
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: Las credenciales de AWS no están configuradas."
    echo "Configúralas con: aws configure"
    exit 1
fi

# Procesar argumentos
MODE=${1:-both}

case $MODE in
    dev)
        authenticate_ecr
        build_image
        push_image "dev-latest"
        ;;
    prod)
        authenticate_ecr
        build_image
        push_image "prod-latest"
        ;;
    both)
        authenticate_ecr
        build_image
        push_image "dev-latest"
        push_image "prod-latest"
        ;;
    *)
        echo "Uso: $0 [dev|prod|both]"
        echo "  dev  - Construye y sube solo la imagen dev"
        echo "  prod - Construye y sube solo la imagen prod"
        echo "  both - Construye y sube ambas imágenes (por defecto)"
        exit 1
        ;;
esac

echo -e "${GREEN}=== Proceso completado exitosamente ===${NC}"
echo -e "\nImágenes disponibles en ECR:"
echo "  - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:dev-latest"
echo "  - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:prod-latest"

