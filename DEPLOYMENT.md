# Sistema de Despliegue Automático - Health Prediction MLOps

Este documento describe el sistema de despliegue automático implementado para el modelo de predicción de salud.

## Arquitectura del Sistema

El sistema implementa un pipeline de CI/CD con GitHub Actions que permite el despliegue automático de modelos ONNX en dos ambientes: **dev** y **prod**.

### Componentes Principales

1. **Modelo ONNX**: Almacenado en S3, no incluido en el repositorio
2. **API Flask**: Aplicación que utiliza el modelo ONNX para realizar predicciones
3. **Pipeline CI/CD**: GitHub Actions que ejecuta tests y despliega automáticamente
4. **Almacenamiento S3**: Para modelo, datos de prueba y predicciones
5. **Despliegue en la nube**: AWS ECS/ECR para contenedores Docker

## Estructura del Repositorio

```
healthPrediction-mlops-U2/
├── Api/
│   ├── app.py                 # API Flask con soporte ONNX
│   ├── Dockerfile             # Imagen Docker
│   ├── requirements.txt       # Dependencias Python
│   ├── test_app.py            # Tests unitarios
│   ├── templates/             # Interfaz web
│   └── scripts/               # Scripts de utilidad
│       ├── upload_model_to_s3.py
│       └── create_test_data.py
├── .github/
│   └── workflows/
│       ├── dev-pipeline.yml   # Pipeline para rama develop
│       └── prod-pipeline.yml  # Pipeline para rama prod
└── README.md
```

## Configuración Inicial

> **📘 Guía Completa de AWS**: Para una guía detallada paso a paso sobre cómo configurar AWS, consulta [GUIA_CONFIGURACION_AWS.md](GUIA_CONFIGURACION_AWS.md)

### 1. Configurar AWS

1. Crear un bucket S3 (ej: `health-prediction-mlops`)
2. Crear credenciales IAM con permisos para:
   - S3 (lectura/escritura)
   - ECR (push/pull de imágenes)
   - ECS (despliegue de servicios)

### 2. Subir Modelo ONNX a S3

El modelo ONNX debe estar en formato `.onnx` y subirse a S3:

```bash
# Opción 1: Usar el script proporcionado
cd model
python upload_model_to_s3.py health_model.onnx

# Opción 2: Usar AWS CLI directamente
aws s3 cp model/health_model.onnx s3://health-prediction-mlops/models/health_model.onnx
```

### 3. Crear Datos de Prueba

```bash
cd Api/scripts
python create_test_data.py
```

Esto creará y subirá un archivo CSV con datos de prueba a S3.

### 4. Configurar Secrets en GitHub

En el repositorio de GitHub, ir a Settings > Secrets and variables > Actions y agregar:

- `AWS_ACCESS_KEY_ID`: Clave de acceso de AWS
- `AWS_SECRET_ACCESS_KEY`: Clave secreta de AWS
- `S3_BUCKET`: Nombre del bucket S3 (ej: `health-prediction-mlops`)

### 5. Configurar Variables de Entorno

Para ejecución local, crear un archivo `.env` en `Api/`:

```env
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_REGION=us-east-1
S3_BUCKET=health-prediction-mlops
S3_MODEL_PATH=models/health_model.onnx
S3_PREDICTIONS_DEV=predictions/predicciones_dev.txt
S3_PREDICTIONS_PROD=predictions/predicciones_prod.txt
ENVIRONMENT=dev
S3_TEST_DATA_PATH=test_data/test_data.csv
```

## Pipeline de CI/CD

### Rama Develop (dev/develop)

El pipeline se ejecuta automáticamente cuando se hace push a las ramas `dev` o `develop`.

**Etapas:**

1. **Test**: 
   - Descarga datos de prueba de S3
   - Descarga modelo ONNX de S3
   - Ejecuta tests unitarios que validan:
     - El modelo responde con datos de entrada definidos
     - No hay cambio significativo en métricas (umbral de precisión)

2. **Build/Promote**:
   - Construye imagen Docker
   - Sube imagen a Amazon ECR
   - Despliega en servicio ECS de desarrollo
   - Endpoint: `http://dev-endpoint-url/clasificar`

### Rama Production (prod/main)

El pipeline se ejecuta automáticamente cuando se hace push a las ramas `prod` o `main`.

**Etapas:**

1. **Test**: Mismas pruebas que en develop
2. **Build/Promote**: Despliegue en ambiente de producción
   - Endpoint: `http://prod-endpoint-url/clasificar`

## Funcionalidades de la API

### Endpoints

- `GET /`: Interfaz web para realizar predicciones
- `POST /clasificar`: API para clasificar condición médica
- `GET /logs`: Consultar logs locales de predicciones
- `GET /health`: Health check del servicio

### Uso de la API

```bash
curl -X POST http://localhost:5000/clasificar \
  -H "Content-Type: application/json" \
  -d '{
    "duracion": "aguda",
    "severidad": "intenso",
    "impacto": "incapacidad"
  }'
```

**Respuesta:**
```json
{
  "duracion_dada": "aguda",
  "severidad_dada": "intenso",
  "impacto_dado": "incapacidad",
  "condicion_clasificada": "ENFERMEDAD AGUDA",
  "environment": "dev"
}
```

## Almacenamiento de Predicciones

Cada predicción realizada se guarda automáticamente en S3 en archivos TXT separados:

- **Desarrollo**: `s3://bucket/predictions/predicciones_dev.txt`
- **Producción**: `s3://bucket/predictions/predicciones_prod.txt`

Formato de cada línea:
```
timestamp|duracion|severidad|impacto|resultado
```

## Tests Unitarios

Los tests validan:

1. **Test de Respuesta del Modelo**: Verifica que el modelo responde correctamente con diferentes combinaciones de inputs
2. **Test de Métricas**: Valida que la precisión/consistencia del modelo no caiga por debajo de un umbral definido

Ejecutar tests localmente:

```bash
cd Api
python -m pytest test_app.py -v
```

## Despliegue Local con Docker

```bash
cd Api

# Construir imagen
docker build -t health-prediction:latest .

# Ejecutar contenedor (con variables de entorno)
docker run -p 5000:5000 \
  -e AWS_ACCESS_KEY_ID=tu_key \
  -e AWS_SECRET_ACCESS_KEY=tu_secret \
  -e S3_BUCKET=health-prediction-mlops \
  -e ENVIRONMENT=dev \
  health-prediction:latest
```

## Notas Importantes

1. **Modelo ONNX**: El archivo `.onnx` NO debe estar en el repositorio. Solo se referencia su ubicación en S3.

2. **Datos de Prueba**: Los datos de prueba se descargan desde S3 durante la ejecución de tests, no están en el repositorio.

3. **Variables de Entorno**: El ambiente (`ENVIRONMENT`) determina qué archivo de predicciones se usa (dev o prod).

4. **Seguridad**: Nunca commitear credenciales de AWS. Usar siempre GitHub Secrets o variables de entorno.

## Troubleshooting

### Error: "Model not found in S3"
- Verificar que el modelo esté subido correctamente
- Verificar permisos IAM para acceso a S3
- Verificar que la ruta en `S3_MODEL_PATH` sea correcta

### Error: "Test data not found"
- Ejecutar `create_test_data.py` para crear datos de prueba
- Verificar permisos de lectura en S3

### Error en despliegue ECS
- Verificar que el cluster y servicio ECS existan
- Verificar permisos IAM para ECS
- Verificar que la task definition esté configurada correctamente

## Próximos Pasos

- [ ] Configurar monitoreo con CloudWatch
- [ ] Implementar rollback automático en caso de fallos
- [ ] Agregar más métricas de validación
- [ ] Implementar A/B testing entre modelos

