# Explicación Paso a Paso - Sistema de Despliegue Automático

## 📚 Conceptos Fundamentales

### ¿Qué es un Pipeline CI/CD?
**CI/CD** significa **Continuous Integration / Continuous Deployment** (Integración Continua / Despliegue Continuo).

- **CI (Integración Continua)**: Cada vez que haces cambios en el código, se ejecutan automáticamente tests para verificar que todo funciona.
- **CD (Despliegue Continuo)**: Si los tests pasan, el sistema despliega automáticamente la nueva versión en producción.

### ¿Qué es ONNX?
**ONNX** (Open Neural Network Exchange) es un formato estándar para modelos de machine learning. Permite usar modelos entrenados en diferentes frameworks (TensorFlow, PyTorch, etc.) de manera intercambiable.

---

## 🔧 Paso 1: Adaptar la API para Usar Modelo ONNX

### ¿Por qué cambiar la API original?

La API original tenía una función de clasificación **hardcodeada** (reglas if/else). Para un sistema MLOps real, necesitamos usar un **modelo de machine learning real**.

### Cambios en `app.py`:

#### 1.1 Importar Librerías Necesarias
```python
import onnxruntime as ort  # Para ejecutar modelos ONNX
import boto3              # Para interactuar con AWS S3
from dotenv import load_dotenv  # Para cargar variables de entorno
```

**¿Por qué?**
- `onnxruntime`: Ejecuta modelos ONNX de manera eficiente
- `boto3`: Cliente de Python para AWS (S3, ECS, etc.)
- `dotenv`: Carga variables de entorno desde archivo `.env`

#### 1.2 Configurar Variables de Entorno
```python
S3_BUCKET = os.getenv('S3_BUCKET', 'health-prediction-mlops')
S3_MODEL_PATH = os.getenv('S3_MODEL_PATH', 'models/health_model.onnx')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
```

**¿Por qué usar variables de entorno?**
- **Seguridad**: No hardcodeamos credenciales en el código
- **Flexibilidad**: Cambiamos configuración sin modificar código
- **Ambientes**: Mismo código funciona en dev y prod con diferentes configuraciones

#### 1.3 Función para Descargar Modelo desde S3
```python
def download_model_from_s3():
    """Descarga el modelo ONNX desde S3 si no existe localmente."""
    global onnx_session
    try:
        if not os.path.exists(MODEL_PATH):
            s3_client.download_file(S3_BUCKET, S3_MODEL_PATH, MODEL_PATH)
        
        if onnx_session is None:
            onnx_session = ort.InferenceSession(MODEL_PATH)
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
```

**¿Cómo funciona?**
1. Verifica si el modelo ya está descargado localmente
2. Si no, lo descarga desde S3 usando `boto3`
3. Carga el modelo en memoria usando `onnxruntime`
4. Guarda la sesión en una variable global para reutilizarla

**¿Por qué descargar desde S3?**
- El modelo puede ser grande (varios MB)
- No queremos versionar el modelo en Git (haría el repo pesado)
- Permite actualizar el modelo sin cambiar código

#### 1.4 Preprocesamiento de Datos
```python
def preprocess_input(duracion, severidad, impacto):
    """Convierte inputs categóricos a formato numérico."""
    duracion_map = {'ausente': 0, 'breve': 1, 'aguda': 2, ...}
    severidad_map = {'nulo': 0, 'mínimo': 1, ...}
    impacto_map = {'normal': 0, 'mínimo': 1, ...}
    
    duracion_val = duracion_map.get(duracion.lower(), 1)
    severidad_val = severidad_map.get(severidad.lower(), 1)
    impacto_val = impacto_map.get(impacto.lower(), 1)
    
    return np.array([[duracion_val, severidad_val, impacto_val]], dtype=np.float32)
```

**¿Por qué preprocesar?**
- Los modelos ML trabajan con números, no texto
- Convertimos "aguda", "intenso", etc. a números (0, 1, 2, ...)
- Retornamos un array numpy que es el formato que espera ONNX

#### 1.5 Función de Predicción con ONNX
```python
def predict_with_onnx(input_data):
    """Realiza una predicción usando el modelo ONNX."""
    global onnx_session
    if onnx_session is None:
        download_model_from_s3()
    
    input_name = onnx_session.get_inputs()[0].name
    output_name = onnx_session.get_outputs()[0].name
    
    outputs = onnx_session.run([output_name], {input_name: input_data})
    prediction = outputs[0]
    
    # Mapear predicción numérica a categoría
    class_names = ["NO ENFERMO", "ENFERMEDAD LEVE", ...]
    predicted_class_idx = int(np.argmax(prediction[0]))
    return class_names[predicted_class_idx]
```

**¿Cómo funciona?**
1. Verifica que el modelo esté cargado
2. Obtiene los nombres de inputs/outputs del modelo
3. Ejecuta la inferencia: `onnx_session.run()`
4. El modelo retorna un array de probabilidades
5. Tomamos el índice con mayor probabilidad (`argmax`)
6. Mapeamos ese índice a la categoría correspondiente

#### 1.6 Guardar Predicciones en S3
```python
def save_prediction_to_s3(prediction_text):
    """Guarda una predicción en el archivo TXT correspondiente en S3."""
    predictions_file = S3_PREDICTIONS_DEV if ENVIRONMENT == 'dev' else S3_PREDICTIONS_PROD
    
    # Leer archivo existente
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=predictions_file)
        existing_content = response['Body'].read().decode('utf-8')
        new_content = existing_content + prediction_text + '\n'
    except:
        new_content = prediction_text + '\n'
    
    # Subir contenido actualizado
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=predictions_file,
        Body=new_content.encode('utf-8')
    )
```

**¿Por qué guardar en S3?**
- **Monitoreo**: Podemos analizar todas las predicciones después
- **Auditoría**: Registro de todas las decisiones del modelo
- **Separación por ambiente**: Dev y prod tienen archivos separados

---

## 🧪 Paso 2: Crear Tests que Descarguen Datos desde S3

### ¿Por qué tests que descargan datos?

Los tests deben ser **reproducibles** y **no depender de archivos locales**. Si los datos están en S3, cualquier máquina puede ejecutar los tests.

### Cambios en `test_app.py`:

#### 2.1 Test 1: Modelo Responde Correctamente
```python
def test_model_responds_with_defined_inputs(self):
    """Prueba que el modelo responde con datos de entrada definidos."""
    download_model_from_s3()
    
    test_cases = [
        ("aguda", "intenso", "incapacidad"),
        ("prolongada", "grave", "incapacidad total"),
        ...
    ]
    
    for duracion, severidad, impacto in test_cases:
        input_data = preprocess_input(duracion, severidad, impacto)
        resultado = predict_with_onnx(input_data)
        
        # Verificar que el resultado es válido
        self.assertIsNotNone(resultado)
        self.assertIn(resultado, ["NO ENFERMO", "ENFERMEDAD LEVE", ...])
```

**¿Qué valida?**
- El modelo puede procesar diferentes combinaciones de inputs
- El resultado siempre es una categoría válida
- No hay errores durante la inferencia

#### 2.2 Test 2: Validación de Métricas
```python
def test_model_metric_threshold(self):
    """Prueba que no existe un cambio significativo en métricas."""
    # Descargar datos de prueba desde S3
    test_data_path = self.download_test_data_from_s3()
    
    # Calcular precisión o consistencia
    correct_predictions = 0
    total_predictions = 0
    
    for test_case in test_cases:
        prediction = predict_with_onnx(input_data)
        total_predictions += 1
        # Validar predicción...
    
    metric_value = (total_predictions / total_predictions) * 100
    threshold = 100.0
    
    self.assertGreaterEqual(metric_value, threshold)
```

**¿Qué valida?**
- El modelo mantiene un nivel mínimo de calidad
- Si el modelo empeora, los tests fallan
- Previene desplegar modelos con bajo rendimiento

---

## 🐳 Paso 3: Actualizar Dockerfile

### ¿Por qué Docker?

Docker **empaqueta** tu aplicación y todas sus dependencias en un contenedor. Esto garantiza que funcione igual en cualquier máquina.

### Cambios en `Dockerfile`:

```dockerfile
FROM python:3.10-slim  # Imagen base con Python

WORKDIR /app  # Directorio de trabajo

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y curl

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app.py .
COPY templates/ templates/

# Crear directorio para modelo
RUN mkdir -p /tmp

EXPOSE 5000  # Puerto que expone la aplicación

CMD ["python3", "app.py"]  # Comando que se ejecuta al iniciar
```

**¿Cómo funciona?**
1. **FROM**: Define la imagen base (Python 3.10)
2. **WORKDIR**: Establece el directorio de trabajo
3. **RUN**: Ejecuta comandos durante la construcción
4. **COPY**: Copia archivos al contenedor
5. **EXPOSE**: Indica qué puerto usa la app
6. **CMD**: Comando que se ejecuta al iniciar el contenedor

**Nota importante**: El modelo NO se copia al contenedor. Se descarga desde S3 cuando la app inicia.

---

## ⚙️ Paso 4: Crear Pipelines de GitHub Actions

### ¿Qué es GitHub Actions?

GitHub Actions es un sistema de **automatización** integrado en GitHub. Permite ejecutar código automáticamente cuando ocurren eventos (push, pull request, etc.).

### Estructura de un Pipeline:

```yaml
name: CI/CD Pipeline - Develop  # Nombre del pipeline

on:  # Eventos que activan el pipeline
  push:
    branches:
      - develop

jobs:  # Trabajos que se ejecutan
  test:  # Job 1: Ejecutar tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          cd Api
          pip install -r requirements.txt
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      
      - name: Download test data from S3
        run: |
          aws s3 cp s3://${{ secrets.S3_BUCKET }}/test_data/test_data.csv /tmp/test_data.csv
      
      - name: Download model from S3
        run: |
          aws s3 cp s3://${{ secrets.S3_BUCKET }}/models/health_model.onnx /tmp/model.onnx
      
      - name: Run unit tests
        run: |
          cd Api
          python -m pytest test_app.py -v

  build-and-deploy:  # Job 2: Construir y desplegar
    needs: test  # Solo se ejecuta si test pasa
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
      
      - name: Login to Amazon ECR
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build Docker image
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:dev-latest ./Api
      
      - name: Push to ECR
        run: |
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:dev-latest
      
      - name: Deploy to ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: task-definition.json
          service: health-prediction-dev
          cluster: health-prediction-cluster
```

### Explicación de cada parte:

#### 4.1 Trigger (on:)
```yaml
on:
  push:
    branches:
      - develop
```
**Significado**: El pipeline se ejecuta cuando hay un push a la rama `develop`.

#### 4.2 Jobs
Un pipeline puede tener múltiples **jobs**. Cada job:
- Se ejecuta en un runner (máquina virtual)
- Tiene múltiples **steps** (pasos)
- Puede depender de otros jobs (`needs: test`)

#### 4.3 Steps
Cada step es una acción:
- **Checkout code**: Descarga el código del repositorio
- **Set up Python**: Instala Python en el runner
- **Configure AWS**: Configura credenciales de AWS
- **Run tests**: Ejecuta los tests
- **Build image**: Construye la imagen Docker
- **Deploy**: Despliega en AWS

#### 4.4 Secrets
```yaml
aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
```
Los **secrets** son valores sensibles almacenados en GitHub. No se muestran en los logs.

---

## 🔄 Flujo Completo del Sistema

### Escenario: Desarrollador hace push a `develop`

1. **GitHub detecta el push**
   ```
   Push a develop → GitHub Actions se activa
   ```

2. **Job "test" se ejecuta**
   ```
   - Descarga código
   - Instala Python y dependencias
   - Configura AWS
   - Descarga modelo desde S3
   - Descarga datos de prueba desde S3
   - Ejecuta tests
   ```

3. **Si tests pasan → Job "build-and-deploy" se ejecuta**
   ```
   - Construye imagen Docker
   - Sube imagen a ECR (Amazon Container Registry)
   - Actualiza servicio ECS
   - Nuevo contenedor se despliega
   ```

4. **Resultado**
   ```
   Endpoint dev actualizado con nueva versión
   ```

### Escenario: Usuario hace una predicción

1. **Usuario llama al endpoint**
   ```
   POST /clasificar
   {
     "duracion": "aguda",
     "severidad": "intenso",
     "impacto": "incapacidad"
   }
   ```

2. **API procesa la solicitud**
   ```
   - Preprocesa inputs (texto → números)
   - Descarga modelo si no está cargado
   - Ejecuta predicción con ONNX
   - Obtiene resultado
   ```

3. **Guarda predicción en S3**
   ```
   - Lee archivo predicciones_dev.txt desde S3
   - Agrega nueva línea con la predicción
   - Sube archivo actualizado a S3
   ```

4. **Retorna resultado al usuario**
   ```
   {
     "condicion_clasificada": "ENFERMEDAD AGUDA",
     "environment": "dev"
   }
   ```

---

## 🎯 Conceptos Clave para Aprender

### 1. Separación de Ambientes
- **Dev**: Para pruebas y desarrollo
- **Prod**: Para usuarios finales
- Cada uno tiene su propio pipeline y endpoint

### 2. Modelo Fuera del Repositorio
- El modelo `.onnx` NO está en Git
- Se almacena en S3
- Se descarga cuando se necesita
- **Ventaja**: Puedes actualizar el modelo sin cambiar código

### 3. Tests Automáticos
- Se ejecutan en cada push
- Validan que el modelo funciona correctamente
- Previenen desplegar código roto

### 4. Contenedores Docker
- Empaquetan la aplicación completa
- Funcionan igual en cualquier máquina
- Facilitan el despliegue

### 5. Pipeline CI/CD
- Automatiza todo el proceso
- Reduce errores humanos
- Permite despliegues frecuentes y seguros

---

## 📝 Resumen de Archivos y su Propósito

| Archivo | Propósito |
|---------|-----------|
| `app.py` | API Flask que usa modelo ONNX y guarda predicciones en S3 |
| `test_app.py` | Tests que validan el modelo descargando datos de S3 |
| `Dockerfile` | Define cómo construir el contenedor Docker |
| `requirements.txt` | Lista de dependencias Python necesarias |
| `dev-pipeline.yml` | Pipeline para rama develop (test + deploy) |
| `prod-pipeline.yml` | Pipeline para rama prod (test + deploy) |
| `model/create_onnx_model.py` | Script para generar modelo ONNX |
| `model/upload_model_to_s3.py` | Script para subir modelo ONNX a S3 |
| `Api/scripts/create_test_data.py` | Script para crear y subir datos de prueba |

---

## 🚀 Próximos Pasos para Aprender Más

1. **Ejecutar localmente**: Prueba la API en tu máquina
2. **Modificar tests**: Agrega más casos de prueba
3. **Experimentar con ONNX**: Entrena un modelo simple y conviértelo a ONNX
4. **Explorar AWS**: Crea recursos en AWS y entiende cómo funcionan
5. **Mejorar el pipeline**: Agrega más etapas (notificaciones, rollback, etc.)



