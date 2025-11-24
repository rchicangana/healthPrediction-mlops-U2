# Guía Paso a Paso: Configuración de AWS para el Proyecto

Esta guía te llevará paso a paso para configurar todos los recursos necesarios en AWS para que el sistema de despliegue automático funcione correctamente.

## 📋 Tabla de Contenidos

1. [Crear Cuenta AWS](#1-crear-cuenta-aws)
2. [Crear Usuario IAM con Permisos](#2-crear-usuario-iam-con-permisos)
3. [Crear Bucket S3](#3-crear-bucket-s3)
4. [Crear Repositorio ECR](#4-crear-repositorio-ecr)
5. [Crear Cluster ECS](#5-crear-cluster-ecs)
6. [Crear Task Definitions](#6-crear-task-definitions)
7. [Crear Servicios ECS](#7-crear-servicios-ecs)
8. [Configurar GitHub Secrets](#8-configurar-github-secrets)
9. [Verificación Final](#9-verificación-final)

---

## 1. Crear Cuenta AWS

### Paso 1.1: Registrarse en AWS

1. Ve a [https://aws.amazon.com/](https://aws.amazon.com/)
2. Haz clic en **"Crear una cuenta de AWS"**
3. Completa el formulario con:
   - Email
   - Contraseña
   - Nombre de cuenta
4. Proporciona información de pago (necesario incluso para el tier gratuito)
5. Verifica tu identidad con un número de teléfono
6. Selecciona un plan de soporte (elige **"Basic"** que es gratuito)

### Paso 1.2: Acceder a la Consola

1. Una vez creada la cuenta, inicia sesión en [https://console.aws.amazon.com/](https://console.aws.amazon.com/)
2. Selecciona la región (recomendado: **us-east-1** - N. Virginia)

---

## 2. Crear Usuario IAM con Permisos

### Paso 2.1: Crear Usuario IAM

1. En la consola de AWS, busca **"IAM"** en la barra de búsqueda
2. En el menú lateral, haz clic en **"Usuarios"**
3. Haz clic en **"Crear usuario"**
4. Nombre de usuario: `health-prediction-mlops-user`
5. Marca **"Proporcionar acceso al portal de usuarios de AWS"** (opcional, solo si quieres acceso web)
6. Haz clic en **"Siguiente"**

### Paso 2.2: Asignar Políticas de Permisos

1. Selecciona **"Adjuntar políticas directamente"**
2. Busca y selecciona las siguientes políticas:
   - `AmazonS3FullAccess` (o crea una política personalizada más restrictiva)
   - `AmazonEC2ContainerRegistryFullAccess`
   - `AmazonECS_FullAccess`
   - `AmazonEC2FullAccess` (necesario para ECS con EC2)

**Nota:** Para producción, es mejor crear políticas personalizadas con permisos mínimos. Para desarrollo/pruebas, estas políticas funcionan.

3. Haz clic en **"Siguiente"**
4. Revisa y haz clic en **"Crear usuario"**

### Paso 2.3: Crear Access Keys (Credenciales)

1. Haz clic en el usuario recién creado (`health-prediction-mlops-user`)
2. Ve a la pestaña **"Credenciales de seguridad"**
3. Haz clic en **"Crear clave de acceso"**
4. Selecciona **"Caso de uso: Aplicación que se ejecuta fuera de AWS"**
5. Agrega una descripción: `GitHub Actions CI/CD`
6. Haz clic en **"Siguiente"**
7. (Opcional) Agrega etiquetas si lo deseas
8. Haz clic en **"Crear clave de acceso"**

### ⚠️ IMPORTANTE: Guardar Credenciales

**¡GUARDA ESTAS CREDENCIALES AHORA!** No podrás verlas de nuevo.

- **Access Key ID**: `AKIA...` (copia este valor)
- **Secret Access Key**: `...` (copia este valor)

**Guárdalas en un lugar seguro.** Las necesitarás para:
- Configurar GitHub Secrets
- Configurar variables de entorno locales

---

## 3. Crear Bucket S3

### Paso 3.1: Crear el Bucket

1. En la consola de AWS, busca **"S3"** en la barra de búsqueda
2. Haz clic en **"Crear bucket"**
3. Configuración:
   - **Nombre del bucket**: `health-prediction-mlops` (debe ser único globalmente)
   - **Región**: `us-east-1` (o la región que prefieras)
   - **Bloquear todo el acceso público**: Desmarcado (o marcado según tu preferencia de seguridad)
4. Haz clic en **"Crear bucket"**

### Paso 3.2: Crear Estructura de Carpetas

1. Haz clic en el bucket creado
2. Haz clic en **"Crear carpeta"** y crea las siguientes:
   - `models/` - Para almacenar el modelo ONNX
   - `test_data/` - Para almacenar datos de prueba
   - `predictions/` - Para almacenar predicciones

### Paso 3.3: Configurar Permisos del Bucket (Opcional)

1. Ve a la pestaña **"Permisos"**
2. En **"Política del bucket"**, puedes agregar una política JSON para permitir acceso desde GitHub Actions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowGitHubActions",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::TU_ACCOUNT_ID:user/health-prediction-mlops-user"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::health-prediction-mlops",
                "arn:aws:s3:::health-prediction-mlops/*"
            ]
        }
    ]
}
```

**Nota:** Reemplaza `TU_ACCOUNT_ID` con tu Account ID (lo encuentras en la parte superior derecha de la consola).

---

## 4. Crear Repositorio ECR

### Paso 4.1: Crear Repositorio

1. En la consola de AWS, busca **"ECR"** (Elastic Container Registry)
2. Haz clic en **"Repositorios"** en el menú lateral
3. Haz clic en **"Crear repositorio"**
4. Configuración:
   - **Visibilidad**: Privado
   - **Nombre del repositorio**: `health-prediction-mlops`
   - **Etiquetas de imagen**: Deja las opciones por defecto
5. Haz clic en **"Crear repositorio"**

### Paso 4.2: Obtener URI del Repositorio

1. Haz clic en el repositorio creado
2. Copia el **URI del repositorio**: `123456789012.dkr.ecr.us-east-1.amazonaws.com/health-prediction-mlops`
3. **Guarda este URI**, lo necesitarás para los pipelines

---

## 5. Crear Cluster ECS

### Paso 5.1: Crear Cluster

1. En la consola de AWS, busca **"ECS"** (Elastic Container Service)
2. Haz clic en **"Clusters"** en el menú lateral
3. Haz clic en **"Crear cluster"**
4. Configuración:
   - **Nombre del cluster**: `health-prediction-cluster`
   - **Infraestructura**: 
     - Selecciona **"AWS Fargate (servidorless)"** (más fácil, pero tiene costo)
     - O **"Amazon EC2 Linux + Networking"** (más económico con tier gratuito)
   
   **Para usar EC2 (más económico):**
   - **EC2 instance type**: `t2.micro` (elegible para tier gratuito)
   - **Number of instances**: 1
   - **VPC**: Selecciona la VPC por defecto o crea una nueva
   - **Subnets**: Selecciona al menos 2 subnets en diferentes zonas de disponibilidad
   - **Security group**: Crea uno nuevo o usa el por defecto
   - **Container instance IAM role**: Selecciona el rol por defecto o crea uno nuevo

5. Haz clic en **"Crear"**

**Nota:** Si eliges EC2, espera a que la instancia se cree (puede tomar unos minutos).

---

## 6. Crear Task Definitions

### Paso 6.1: Crear Task Definition para Desarrollo

1. En ECS, haz clic en **"Task definitions"** en el menú lateral
2. Haz clic en **"Crear nueva definición de tarea"**
3. Configuración:
   - **Familia**: `health-prediction-dev`
   - **Tipo de lanzamiento**: `Fargate` o `EC2` (según tu cluster)
   - **Sistema operativo**: `Linux/X86_64`
   - **CPU**: `256` (0.25 vCPU) para Fargate, o deja por defecto para EC2
   - **Memoria**: `512` (0.5 GB) para Fargate, o deja por defecto para EC2

4. **Contenedor - Configuración básica:**
   - **Nombre del contenedor**: `health-prediction-dev`
   - **URI de imagen**: `123456789012.dkr.ecr.us-east-1.amazonaws.com/health-prediction-mlops:dev-latest`
     (Reemplaza con tu URI de ECR)
   - **Puerto de mapeo**: `5000`

5. **Contenedor - Variables de entorno:**
   Agrega las siguientes variables:
   - `AWS_ACCESS_KEY_ID`: (dejar vacío, se pasará desde el servicio)
   - `AWS_SECRET_ACCESS_KEY`: (dejar vacío, se pasará desde el servicio)
   - `AWS_REGION`: `us-east-1`
   - `S3_BUCKET`: `health-prediction-mlops`
   - `S3_MODEL_PATH`: `models/health_model.onnx`
   - `S3_PREDICTIONS_DEV`: `predictions/predicciones_dev.txt`
   - `S3_PREDICTIONS_PROD`: `predictions/predicciones_prod.txt`
   - `ENVIRONMENT`: `dev`

6. Haz clic en **"Crear"**

### Paso 6.2: Crear Task Definition para Producción

Repite el Paso 6.1 pero con:
- **Familia**: `health-prediction-prod`
- **Nombre del contenedor**: `health-prediction-prod`
- **URI de imagen**: `...health-prediction-mlops:prod-latest`
- **ENVIRONMENT**: `prod`

---

## 7. Subir Imagen Docker a ECR (IMPORTANTE)

**⚠️ ANTES de crear los servicios ECS, debes construir y subir la imagen Docker a ECR.**

### Paso 7.0: Autenticarse en ECR

1. Obtén el comando de autenticación desde la consola de ECR:
   - Ve a ECR > Repositorios > `health-prediction-mlops`
   - Haz clic en **"Ver comandos de push"**
   - Copia el comando que dice `aws ecr get-login-password...`

2. O ejecuta este comando (reemplaza `776036137322` con tu Account ID y `us-east-1` con tu región):

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 776036137322.dkr.ecr.us-east-1.amazonaws.com
```

### Paso 7.1: Construir y Subir Imagen Docker

**Opción A: Usar el script automatizado (Recomendado)**

1. **En Linux/Mac:**
```bash
cd scripts
chmod +x build_and_push_docker.sh
# Edita el script y ajusta AWS_ACCOUNT_ID y AWS_REGION
./build_and_push_docker.sh both
```

2. **En Windows (PowerShell):**
```powershell
cd scripts
# Edita el script y ajusta $AWS_ACCOUNT_ID y $AWS_REGION
.\build_and_push_docker.ps1 both
```

**Opción B: Comandos manuales**

1. **Autenticarse en ECR:**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 776036137322.dkr.ecr.us-east-1.amazonaws.com
```

**Nota:** Reemplaza `776036137322` con tu Account ID y `us-east-1` con tu región.

2. **Construir la imagen localmente:**
```bash
cd Api
docker build -t health-prediction-mlops:latest .
cd ..
```

3. **Etiquetar y subir imagen dev:**
```bash
docker tag health-prediction-mlops:latest 776036137322.dkr.ecr.us-east-1.amazonaws.com/health-prediction-mlops:dev-latest
docker push 776036137322.dkr.ecr.us-east-1.amazonaws.com/health-prediction-mlops:dev-latest
```

4. **Etiquetar y subir imagen prod:**
```bash
docker tag health-prediction-mlops:latest 776036137322.dkr.ecr.us-east-1.amazonaws.com/health-prediction-mlops:prod-latest
docker push 776036137322.dkr.ecr.us-east-1.amazonaws.com/health-prediction-mlops:prod-latest
```

5. **Verificar en ECR:**
   - Ve a ECR > Repositorios > `health-prediction-mlops`
   - Deberías ver las imágenes `dev-latest` y `prod-latest`

### Paso 7.2: Crear Servicio de Desarrollo

**Ahora sí puedes crear el servicio:**

1. Ve al cluster `health-prediction-cluster`
2. Haz clic en la pestaña **"Servicios"**
3. Haz clic en **"Crear"**
4. Configuración:
   - **Familia**: `health-prediction-dev`
   - **Nombre del servicio**: `health-prediction-dev`
   - **Número de tareas**: `1`
   - **Tipo de lanzamiento**: `Fargate` o `EC2` (según tu cluster)
   - **Plataforma**: `Linux/X86_64`
   - **VPC**: Selecciona tu VPC
   - **Subnets**: Selecciona al menos 2 subnets
   - **Security groups**: Selecciona o crea uno que permita tráfico en el puerto 5000
   - **Auto-assign public IP**: `ENABLED` (necesario para Fargate)
   - **Load balancer**: Opcional (puedes agregarlo después)

5. Haz clic en **"Crear"**

### Paso 7.3: Crear Servicio de Producción

Repite el Paso 7.2 pero con:
- **Familia**: `health-prediction-prod`
- **Nombre del servicio**: `health-prediction-prod`

### Paso 7.4: Obtener Endpoints

Una vez creados los servicios:

1. Haz clic en el servicio
2. Ve a la pestaña **"Detalles"**
3. Si configuraste un Load Balancer, copia la **URL del Load Balancer**
4. Si no, necesitarás la **IP pública de la tarea**:
   - Ve a la pestaña **"Tareas"**
   - Haz clic en la tarea
   - Copia la **IP pública**

**Endpoints:**
- Dev: `http://dev-endpoint-url:5000`
- Prod: `http://prod-endpoint-url:5000`

---

## 8. Configurar GitHub Secrets

### Paso 8.1: Acceder a Secrets de GitHub

1. Ve a tu repositorio en GitHub
2. Haz clic en **"Settings"** (Configuración)
3. En el menú lateral, haz clic en **"Secrets and variables"** > **"Actions"**

### Paso 8.2: Agregar Secrets

Haz clic en **"New repository secret"** y agrega los siguientes:

#### Secret 1: AWS_ACCESS_KEY_ID
- **Name**: `AWS_ACCESS_KEY_ID`
- **Secret**: Pega el Access Key ID que guardaste en el Paso 2.3
- Haz clic en **"Add secret"**

#### Secret 2: AWS_SECRET_ACCESS_KEY
- **Name**: `AWS_SECRET_ACCESS_KEY`
- **Secret**: Pega el Secret Access Key que guardaste en el Paso 2.3
- Haz clic en **"Add secret"**

#### Secret 3: S3_BUCKET
- **Name**: `S3_BUCKET`
- **Secret**: `health-prediction-mlops` (o el nombre de tu bucket)
- Haz clic en **"Add secret"**

### Paso 8.3: Verificar Secrets

Deberías ver 3 secrets en la lista:
- ✅ `AWS_ACCESS_KEY_ID`
- ✅ `AWS_SECRET_ACCESS_KEY`
- ✅ `S3_BUCKET`

---

## 9. Verificación Final

### Paso 9.1: Subir Modelo a S3

1. Genera el modelo ONNX (si aún no lo has hecho):
```bash
cd model
python create_onnx_model.py
```

2. Sube el modelo a S3:
```bash
cd model
# Configura las variables de entorno primero
export AWS_ACCESS_KEY_ID=tu_access_key
export AWS_SECRET_ACCESS_KEY=tu_secret_key
export AWS_REGION=us-east-1
export S3_BUCKET=health-prediction-mlops

python upload_model_to_s3.py health_model.onnx
```

### Paso 9.2: Crear Datos de Prueba

```bash
cd Api/scripts
python create_test_data.py
```

### Paso 9.3: Verificar Recursos en AWS

Verifica que todos los recursos estén creados:

- ✅ **S3**: Bucket `health-prediction-mlops` con carpetas `models/`, `test_data/`, `predictions/`
- ✅ **ECR**: Repositorio `health-prediction-mlops`
- ✅ **ECS**: Cluster `health-prediction-cluster`
- ✅ **ECS**: Task definitions `health-prediction-dev` y `health-prediction-prod`
- ✅ **ECS**: Servicios `health-prediction-dev` y `health-prediction-prod`
- ✅ **GitHub**: 3 secrets configurados

### Paso 9.4: Probar el Pipeline

1. Haz un push a la rama `develop`:
```bash
git checkout develop
git add .
git commit -m "Test pipeline"
git push origin develop
```

2. Ve a GitHub > Actions y verifica que el pipeline se ejecute correctamente

---

## 📝 Resumen de Recursos Creados

| Recurso | Nombre | Descripción |
|---------|--------|-------------|
| **IAM User** | `health-prediction-mlops-user` | Usuario con permisos para S3, ECR, ECS |
| **S3 Bucket** | `health-prediction-mlops` | Almacenamiento para modelo, datos y predicciones |
| **ECR Repository** | `health-prediction-mlops` | Repositorio de imágenes Docker |
| **ECS Cluster** | `health-prediction-cluster` | Cluster para ejecutar contenedores |
| **ECS Task Definition** | `health-prediction-dev` | Configuración para ambiente dev |
| **ECS Task Definition** | `health-prediction-prod` | Configuración para ambiente prod |
| **ECS Service** | `health-prediction-dev` | Servicio para ambiente dev |
| **ECS Service** | `health-prediction-prod` | Servicio para ambiente prod |

---

## 🔒 Consideraciones de Seguridad

### Mejores Prácticas:

1. **Políticas IAM Restrictivas**: En producción, crea políticas personalizadas con permisos mínimos necesarios
2. **Rotación de Credenciales**: Rota las access keys periódicamente
3. **Secrets Manager**: Considera usar AWS Secrets Manager en lugar de variables de entorno
4. **VPC Privada**: En producción, usa VPC privadas sin IPs públicas
5. **Load Balancer**: Usa Application Load Balancer con HTTPS

---

## 💰 Estimación de Costos (Free Tier)

Con el tier gratuito de AWS, puedes usar:

- **S3**: 5 GB de almacenamiento gratis por 12 meses
- **EC2**: 750 horas/mes de t2.micro gratis por 12 meses
- **ECR**: 500 MB de almacenamiento gratis por mes
- **ECS**: No tiene costo adicional (solo pagas por EC2/ECR)

**Nota:** Fargate no está incluido en el tier gratuito.

---

## 🆘 Troubleshooting

### Error: "Access Denied"
- Verifica que las credenciales IAM tengan los permisos correctos
- Verifica que el bucket S3 tenga las políticas correctas

### Error: "Repository not found"
- Verifica que el nombre del repositorio ECR sea correcto
- Verifica que la región sea la correcta

### Error: "Task failed to start"
- Verifica que la imagen Docker exista en ECR
- Verifica que las variables de entorno estén configuradas
- Verifica los logs de la tarea en CloudWatch

### Error: "Cannot pull image" o "image not found"
- **Causa más común**: La imagen no existe en ECR
- **Solución**: 
  1. Construye y sube la imagen a ECR primero (ver Paso 7.1)
  2. Verifica que el tag de la imagen coincida exactamente
  3. Verifica que estés en la región correcta
  4. Verifica que el servicio ECS tenga permisos para ECR (IAM role)

### Error: "CannotPullContainerError: pull image manifest has been retried"
- **Causa**: La imagen Docker no existe en ECR con el tag especificado
- **Solución**: 
  1. Ve al Paso 7.1 y construye/sube la imagen primero
  2. Verifica en ECR que la imagen existe: `aws ecr describe-images --repository-name health-prediction-mlops`
  3. Asegúrate de que el tag en la Task Definition coincida con el tag en ECR

---

## 📚 Recursos Adicionales

- [Documentación de AWS S3](https://docs.aws.amazon.com/s3/)
- [Documentación de AWS ECR](https://docs.aws.amazon.com/ecr/)
- [Documentación de AWS ECS](https://docs.aws.amazon.com/ecs/)
- [Documentación de AWS IAM](https://docs.aws.amazon.com/iam/)

---

¿Necesitas ayuda con algún paso específico? ¡Pregunta y te ayudo!

