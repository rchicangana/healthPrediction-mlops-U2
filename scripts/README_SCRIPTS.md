# Guía de Ejecución de Scripts

## Script: build_and_push_docker.ps1

Este script construye y sube las imágenes Docker a AWS ECR.

### Requisitos Previos

1. **AWS CLI instalado y configurado:**
   ```powershell
   aws --version
   aws configure
   ```

2. **Docker instalado y funcionando:**
   ```powershell
   docker --version
   ```

3. **Credenciales de AWS configuradas:**
   - Access Key ID
   - Secret Access Key
   - Región

### Configuración Inicial

1. **Edita el script** y ajusta estas variables (líneas 11-12):
   ```powershell
   $AWS_ACCOUNT_ID = "776036137322"  # Tu Account ID de AWS
   $AWS_REGION = "us-east-1"          # Tu región de AWS
   ```

### Ejecución

#### Opción 1: Desde PowerShell (Recomendado)

1. **Abre PowerShell** (no PowerShell ISE)

2. **Navega al directorio del proyecto:**
   ```powershell
   cd "C:\Estudio\Maestria\MLops\Taller 2\healthPrediction-mlops-U2"
   ```

3. **Ejecuta el script:**
   
   **Para construir y subir ambas imágenes (dev y prod):**
   ```powershell
   .\scripts\build_and_push_docker.ps1
   ```
   o
   ```powershell
   .\scripts\build_and_push_docker.ps1 both
   ```
   
   **Solo para desarrollo:**
   ```powershell
   .\scripts\build_and_push_docker.ps1 dev
   ```
   
   **Solo para producción:**
   ```powershell
   .\scripts\build_and_push_docker.ps1 prod
   ```

#### Opción 2: Desde el Explorador de Archivos

1. Navega a la carpeta `scripts`
2. Haz clic derecho en `build_and_push_docker.ps1`
3. Selecciona **"Ejecutar con PowerShell"**

**Nota:** Si obtienes un error de política de ejecución, ejecuta esto primero:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Qué Hace el Script

1. ✅ Verifica que AWS CLI y Docker estén instalados
2. ✅ Verifica que las credenciales de AWS estén configuradas
3. ✅ Se autentica en ECR (Elastic Container Registry)
4. ✅ Construye la imagen Docker desde `Api/Dockerfile`
5. ✅ Etiqueta la imagen con los tags apropiados
6. ✅ Sube la imagen a ECR

### Salida Esperada

```
=== Script de Build y Push a ECR ===

Autenticando en ECR...
✓ Autenticación exitosa

Construyendo imagen Docker...
✓ Imagen construida

Etiquetando imagen como dev-latest...
Subiendo imagen dev-latest a ECR...
✓ Imagen dev-latest subida exitosamente

Etiquetando imagen como prod-latest...
Subiendo imagen prod-latest a ECR...
✓ Imagen prod-latest subida exitosamente

=== Proceso completado exitosamente ===

Imágenes disponibles en ECR:
  - 776036137322.dkr.ecr.us-east-1.amazonaws.com/health-prediction-mlops:dev-latest
  - 776036137322.dkr.ecr.us-east-1.amazonaws.com/health-prediction-mlops:prod-latest
```

### Troubleshooting

#### Error: "Execution policy"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Error: "AWS CLI no está instalado"
Instala AWS CLI desde: https://aws.amazon.com/cli/

#### Error: "Docker no está instalado"
Instala Docker Desktop desde: https://www.docker.com/products/docker-desktop

#### Error: "Las credenciales de AWS no están configuradas"
```powershell
aws configure
# Ingresa:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region name
# - Default output format (json)
```

#### Error: "Cannot connect to Docker daemon"
- Asegúrate de que Docker Desktop esté ejecutándose
- Verifica con: `docker ps`

#### Error: "Access Denied" al subir a ECR
- Verifica que tu usuario IAM tenga permisos para ECR
- Verifica que el Account ID y región sean correctos

