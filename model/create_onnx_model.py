"""
Script para crear un modelo ONNX que replica la lógica hardcodeada original.
Este modelo se entrena con datos generados basados en las reglas originales.
"""
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import onnx
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import joblib

def create_training_data():
    """
    Crea datos de entrenamiento basados en las reglas originales de clasificación.
    """
    # Mapeo de valores categóricos a numéricos (igual que en app.py)
    duracion_map = {
        'ausente': 0, 'breve': 1, 'aguda': 2, 'días': 2, 'semanas': 2,
        'meses': 3, 'años': 3, 'prolongada': 3
    }
    severidad_map = {
        'nulo': 0, 'mínimo': 1, 'tolerable': 2, 'leve': 2,
        'intenso': 3, 'fuerte': 3, 'grave': 4, 'muy intenso': 4
    }
    impacto_map = {
        'normal': 0, 'mínimo': 1, 'tolerable': 2,
        'incapacidad': 3, 'limitado': 3,
        'incapacidad total': 4, 'limitado permanentemente': 4
    }
    
    # Clases de salida (según la lógica original)
    classes = [
        "NO ENFERMO",
        "ENFERMEDAD LEVE",
        "ENFERMEDAD AGUDA",
        "ENFERMEDAD CRÓNICA"
    ]
    
    # Generar datos de entrenamiento basados en las reglas originales
    # Replicando exactamente la función clasificar_condicion original
    # Orden de prioridad según el código original:
    training_data = []
    
    # Regla 1: ENFERMEDAD CRÓNICA (primera prioridad en el código original)
    # if duracion in ('prolongada', 'años', 'meses'):
    #     return "ENFERMEDAD CRÓNICA"
    for d in ['prolongada', 'años', 'meses']:
        for s in ['nulo', 'mínimo', 'tolerable', 'leve', 'intenso', 'fuerte', 'grave', 'muy intenso']:
            for i in ['normal', 'mínimo', 'tolerable', 'incapacidad', 'limitado', 'incapacidad total', 'limitado permanentemente']:
                training_data.append({
                    'duracion': duracion_map[d],
                    'severidad': severidad_map[s],
                    'impacto': impacto_map[i],
                    'clase': 'ENFERMEDAD CRÓNICA'
                })
    
    # Regla 2: NO ENFERMO
    # elif duracion in ('ausente', 'breve') and severidad in ('nulo', 'mínimo') and impacto in ('normal', 'mínimo'):
    #     return "NO ENFERMO"
    for d in ['ausente', 'breve']:
        for s in ['nulo', 'mínimo']:
            for i in ['normal', 'mínimo']:
                training_data.append({
                    'duracion': duracion_map[d],
                    'severidad': severidad_map[s],
                    'impacto': impacto_map[i],
                    'clase': 'NO ENFERMO'
                })
    
    # Regla 3: ENFERMEDAD AGUDA
    # elif duracion in ('aguda', 'días', 'semanas') and (severidad in ('intenso', 'fuerte') or impacto in ('incapacidad', 'limitado')):
    #     return "ENFERMEDAD AGUDA"
    for d in ['aguda', 'días', 'semanas']:
        # Casos con severidad intensa/fuerte (cualquier impacto)
        for s in ['intenso', 'fuerte']:
            for i in ['normal', 'mínimo', 'tolerable', 'incapacidad', 'limitado', 'incapacidad total', 'limitado permanentemente']:
                training_data.append({
                    'duracion': duracion_map[d],
                    'severidad': severidad_map[s],
                    'impacto': impacto_map[i],
                    'clase': 'ENFERMEDAD AGUDA'
                })
        # Casos con impacto incapacidad/limitado (cualquier severidad, excepto los ya cubiertos)
        for s in ['nulo', 'mínimo', 'tolerable', 'leve', 'grave', 'muy intenso']:
            for i in ['incapacidad', 'limitado']:
                training_data.append({
                    'duracion': duracion_map[d],
                    'severidad': severidad_map[s],
                    'impacto': impacto_map[i],
                    'clase': 'ENFERMEDAD AGUDA'
                })
    
    # Regla 4: ENFERMEDAD LEVE
    # elif duracion in ('aguda', 'días', 'semanas') and severidad in ('tolerable', 'leve') and impacto in ('mínimo', 'tolerable'):
    #     return "ENFERMEDAD LEVE"
    for d in ['aguda', 'días', 'semanas']:
        for s in ['tolerable', 'leve']:
            for i in ['mínimo', 'tolerable']:
                # Solo si no es AGUDA (ya cubierto arriba)
                # Verificar que no esté ya en AGUDA
                is_aguda = (s in ['intenso', 'fuerte']) or (i in ['incapacidad', 'limitado'])
                if not is_aguda:
                    training_data.append({
                        'duracion': duracion_map[d],
                        'severidad': severidad_map[s],
                        'impacto': impacto_map[i],
                        'clase': 'ENFERMEDAD LEVE'
                    })
    
    # Agregar casos por defecto (NO ENFERMO para combinaciones no cubiertas)
    for d in range(4):
        for s in range(5):
            for i in range(5):
                # Solo agregar si no existe ya
                exists = any(
                    row['duracion'] == d and row['severidad'] == s and row['impacto'] == i
                    for row in training_data
                )
                if not exists:
                    training_data.append({
                        'duracion': d,
                        'severidad': s,
                        'impacto': i,
                        'clase': 'NO ENFERMO'
                    })
    
    # Convertir a DataFrame
    df = pd.DataFrame(training_data)
    
    # Separar features y target
    X = df[['duracion', 'severidad', 'impacto']].values.astype(np.float32)
    y = df['clase'].values
    
    return X, y, classes

def train_and_export_onnx():
    """
    Entrena un modelo y lo exporta a formato ONNX.
    """
    print("Generando datos de entrenamiento...")
    X, y, classes = create_training_data()
    
    print(f"Datos generados: {len(X)} ejemplos")
    print(f"Clases: {classes}")
    print(f"Distribución de clases:\n{pd.Series(y).value_counts()}")
    
    # Entrenar un árbol de decisión
    # Usamos max_depth para evitar overfitting y mantener reglas simples
    print("\nEntrenando modelo (Decision Tree)...")
    model = DecisionTreeClassifier(
        max_depth=10,
        min_samples_split=5,
        random_state=42
    )
    model.fit(X, y)
    
    # Evaluar el modelo
    accuracy = model.score(X, y)
    print(f"\nPrecisión en datos de entrenamiento: {accuracy:.4f}")
    
    # Guardar modelo sklearn (opcional, para referencia)
    joblib.dump(model, 'health_model_sklearn.pkl')
    print("Modelo sklearn guardado en: health_model_sklearn.pkl")
    
    # Convertir a ONNX
    print("\nConvirtiendo a formato ONNX...")
    
    # Definir el tipo de entrada (3 features de tipo float)
    initial_type = [('float_input', FloatTensorType([None, 3]))]
    
    # Convertir el modelo
    onnx_model = convert_sklearn(
        model,
        initial_types=initial_type,
        target_opset=13  # Versión de opset ONNX
    )
    
    # Guardar modelo ONNX
    onnx_filename = 'health_model.onnx'
    with open(onnx_filename, 'wb') as f:
        f.write(onnx_model.SerializeToString())
    
    print(f"✓ Modelo ONNX guardado en: {onnx_filename}")
    
    # Verificar el modelo
    print("\nVerificando modelo ONNX...")
    onnx_model_check = onnx.load(onnx_filename)
    onnx.checker.check_model(onnx_model_check)
    print("✓ Modelo ONNX válido")
    
    # Probar el modelo con algunos ejemplos
    print("\nProbando el modelo con ejemplos:")
    test_cases = [
        ([2, 3, 3], "ENFERMEDAD AGUDA"),  # aguda, intenso, incapacidad
        ([3, 4, 4], "ENFERMEDAD CRÓNICA"),  # prolongada, grave, incapacidad total (según lógica original)
        ([0, 0, 0], "NO ENFERMO"),  # ausente, nulo, normal
        ([2, 2, 1], "ENFERMEDAD LEVE"),  # aguda, leve, mínimo
        ([3, 2, 1], "ENFERMEDAD CRÓNICA"),  # prolongada, tolerable, mínimo
        ([1, 0, 0], "NO ENFERMO"),  # breve, nulo, normal
        ([2, 1, 3], "ENFERMEDAD AGUDA"),  # aguda, mínimo, incapacidad
    ]
    
    for features, expected in test_cases:
        prediction = model.predict([features])[0]
        proba = model.predict_proba([features])[0]
        max_proba = np.max(proba)
        print(f"  Input: {features} → Predicción: {prediction} (prob: {max_proba:.3f}) [Esperado: {expected}]")
    
    print(f"\n✓ Modelo creado exitosamente!")
    print(f"\nPróximos pasos:")
    print(f"  1. Subir el modelo a S3 usando: python upload_model_to_s3.py {onnx_filename}")
    print(f"  2. El modelo está listo para usar en la API")
    
    return onnx_filename

if __name__ == '__main__':
    try:
        train_and_export_onnx()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

