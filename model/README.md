# Generación del Modelo ONNX

Este documento explica cómo generar el modelo ONNX que replica la lógica hardcodeada original.

## ¿Por qué crear un modelo ONNX?

La API original tenía reglas hardcodeadas (if/else) para clasificar condiciones médicas. Para el sistema MLOps, necesitamos un modelo de machine learning real que pueda:
- Ser actualizado sin cambiar código
- Ser versionado y monitoreado
- Ser desplegado automáticamente

El modelo ONNX generado replica exactamente el comportamiento de las reglas originales.

## Requisitos

```bash
pip install scikit-learn skl2onnx joblib pandas numpy
```

O instala todas las dependencias:
```bash
cd Api
pip install -r requirements.txt
```

## Generar el Modelo

1. **Ejecutar el script de generación:**
```bash
cd model
python create_onnx_model.py
```

2. **El script hará lo siguiente:**
   - Genera datos de entrenamiento basados en las reglas originales
   - Entrena un árbol de decisión que replica la lógica
   - Convierte el modelo a formato ONNX
   - Guarda el archivo `health_model.onnx` en la carpeta `model/`

3. **Verificar el modelo:**
   El script mostrará ejemplos de predicciones para validar que funciona correctamente.

## Subir el Modelo a S3

Una vez generado el modelo, súbelo a S3:

```bash
cd model
python upload_model_to_s3.py health_model.onnx
```

O si el modelo está en otra ubicación:
```bash
python upload_model_to_s3.py /ruta/completa/health_model.onnx
```

## Lógica Replicada

El modelo replica exactamente las reglas originales (en orden de prioridad):

1. **ENFERMEDAD CRÓNICA** (primera prioridad): 
   - Si duracion in ('prolongada', 'años', 'meses')
   - Retorna inmediatamente "ENFERMEDAD CRÓNICA"

2. **NO ENFERMO**: 
   - Si duracion in ('ausente', 'breve') 
   - Y severidad in ('nulo', 'mínimo') 
   - Y impacto in ('normal', 'mínimo')

3. **ENFERMEDAD AGUDA**: 
   - Si duracion in ('aguda', 'días', 'semanas')
   - Y (severidad in ('intenso', 'fuerte') O impacto in ('incapacidad', 'limitado'))

4. **ENFERMEDAD LEVE**: 
   - Si duracion in ('aguda', 'días', 'semanas')
   - Y severidad in ('tolerable', 'leve')
   - Y impacto in ('mínimo', 'tolerable')

5. **Por defecto**: NO ENFERMO (para cualquier otra combinación)

## Estructura del Modelo

- **Inputs**: 3 características numéricas
  - `duracion`: 0 (ausente) a 3 (prolongada)
  - `severidad`: 0 (nulo) a 4 (muy intenso)
  - `impacto`: 0 (normal) a 4 (limitado permanentemente)

- **Output**: Clase predicha (índice 0-3)
  - 0: NO ENFERMO
  - 1: ENFERMEDAD LEVE
  - 2: ENFERMEDAD AGUDA
  - 3: ENFERMEDAD CRÓNICA

## Validación

El script incluye validación automática:
- Verifica que el modelo ONNX es válido
- Prueba con casos de ejemplo
- Muestra la precisión en datos de entrenamiento (debe ser 100% ya que replica reglas exactas)

## Notas

- El modelo se entrena con un árbol de decisión que puede aprender las reglas exactas
- El modelo resultante es pequeño y rápido de ejecutar
- Compatible con `onnxruntime` usado en la API

