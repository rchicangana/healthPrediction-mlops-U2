import os
import boto3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import json
from datetime import datetime
import onnxruntime as ort
import numpy as np
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuración de S3
S3_BUCKET = os.getenv('S3_BUCKET', 'health-prediction-mlops')
S3_MODEL_PATH = os.getenv('S3_MODEL_PATH', 'models/health_model.onnx')
S3_PREDICTIONS_DEV = os.getenv('S3_PREDICTIONS_DEV', 'predictions/predicciones_dev.txt')
S3_PREDICTIONS_PROD = os.getenv('S3_PREDICTIONS_PROD', 'predictions/predicciones_prod.txt')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')  # 'dev' o 'prod'
MODEL_PATH = '/tmp/model.onnx'

# Inicializar cliente S3
# Si las credenciales están en variables de entorno explícitas, usarlas
# Si no, boto3 usará las credenciales del entorno (IAM role, AWS CLI config, etc.)
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

if aws_access_key and aws_secret_key:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
else:
    # Usar credenciales del entorno (configuradas por AWS CLI o IAM role)
    s3_client = boto3.client(
        's3',
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )

# Cargar modelo ONNX
onnx_session = None

def download_model_from_s3():
    """Descarga el modelo ONNX desde S3 si no existe localmente."""
    global onnx_session
    try:
        # Si el archivo ya existe localmente, solo cargar el modelo
        if os.path.exists(MODEL_PATH):
            print(f"Modelo encontrado localmente en {MODEL_PATH}")
            if onnx_session is None:
                onnx_session = ort.InferenceSession(MODEL_PATH)
                print("Modelo ONNX cargado exitosamente desde archivo local")
            return
        
        # Si no existe, intentar descargarlo de S3
        print(f"Descargando modelo desde s3://{S3_BUCKET}/{S3_MODEL_PATH}")
        s3_client.download_file(S3_BUCKET, S3_MODEL_PATH, MODEL_PATH)
        print(f"Modelo descargado exitosamente a {MODEL_PATH}")
        
        if onnx_session is None:
            onnx_session = ort.InferenceSession(MODEL_PATH)
            print("Modelo ONNX cargado exitosamente")
    except Exception as e:
        print(f"Error al descargar/cargar modelo: {str(e)}")
        # Si el modelo ya existe localmente pero hubo error en S3, intentar cargar el local
        if os.path.exists(MODEL_PATH) and onnx_session is None:
            try:
                onnx_session = ort.InferenceSession(MODEL_PATH)
                print("Modelo ONNX cargado exitosamente desde archivo local existente")
                return
            except:
                pass
        raise

def save_prediction_to_s3(prediction_text):
    """Guarda una predicción en el archivo TXT correspondiente en S3."""
    try:
        # Determinar el archivo según el ambiente
        predictions_file = S3_PREDICTIONS_DEV if ENVIRONMENT == 'dev' else S3_PREDICTIONS_PROD
        
        # Intentar leer el archivo existente
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=predictions_file)
            existing_content = response['Body'].read().decode('utf-8')
            new_content = existing_content + prediction_text + '\n'
        except s3_client.exceptions.NoSuchKey:
            # Si el archivo no existe, crear uno nuevo
            new_content = prediction_text + '\n'
        
        # Subir el contenido actualizado
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=predictions_file,
            Body=new_content.encode('utf-8')
        )
    except Exception as e:
        print(f"Error al guardar predicción en S3: {str(e)}")
        # No fallar la request si hay error guardando en S3

def preprocess_input(duracion, severidad, impacto):
    """Convierte los inputs categóricos a formato numérico para el modelo ONNX."""
    # Mapeo de valores categóricos a numéricos
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
    
    duracion_val = duracion_map.get(duracion.lower(), 1)
    severidad_val = severidad_map.get(severidad.lower(), 1)
    impacto_val = impacto_map.get(impacto.lower(), 1)
    
    # Retornar como array numpy para ONNX
    return np.array([[duracion_val, severidad_val, impacto_val]], dtype=np.float32)

def predict_with_onnx(input_data):
    """Realiza una predicción usando el modelo ONNX."""
    global onnx_session
    if onnx_session is None:
        download_model_from_s3()
    
    # Obtener nombres de inputs y outputs del modelo
    input_name = onnx_session.get_inputs()[0].name
    output_name = onnx_session.get_outputs()[0].name
    
    # Realizar inferencia
    outputs = onnx_session.run([output_name], {input_name: input_data})
    prediction = outputs[0]
    
    # Mapear la predicción numérica a categoría
    # El modelo retorna índices de clase (0-3)
    class_names = [
        "NO ENFERMO",           # 0
        "ENFERMEDAD LEVE",      # 1
        "ENFERMEDAD AGUDA",     # 2
        "ENFERMEDAD CRÓNICA"    # 3
    ]
    
    predicted_class_idx = int(np.argmax(prediction[0]))
    # Asegurar que el índice esté en el rango válido
    if predicted_class_idx >= len(class_names):
        predicted_class_idx = 0  # Por defecto: NO ENFERMO
    return class_names[predicted_class_idx]

# Inicializar modelo al arrancar
try:
    download_model_from_s3()
except Exception as e:
    print(f"Advertencia: No se pudo cargar el modelo al inicio: {str(e)}")
    print("El modelo se intentará cargar en la primera predicción")

# Logger para logs locales (opcional)
logger = logging.getLogger('clasificaciones')
logger.setLevel(logging.INFO)
LOG_FILE = 'logs_clasificaciones.jsonl'
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        if isinstance(record.msg, dict):
            return json.dumps(record.msg)
        return super().format(record)

file_handler.setFormatter(JsonFormatter())
logger.addHandler(file_handler)

@app.route('/', methods=['GET'])
def index():
    """Sirve el archivo index.html desde la carpeta templates."""
    return render_template('index.html')

@app.route('/clasificar', methods=['POST'])
def clasificar_api():
    """
    Recibe un JSON en el body con 'duracion', 'severidad' e 'impacto'
    y devuelve la condición médica clasificada usando el modelo ONNX.
    """
    # Intentar obtener JSON del body
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "error": "Cuerpo JSON faltante",
            "mensaje": "Envíe un JSON con los campos: duracion, severidad e impacto."
        }), 400

    duracion = data.get('duracion')
    severidad = data.get('severidad')
    impacto = data.get('impacto')

    # Verificar que los 3 datos esenciales estén presentes
    if not duracion or not severidad or not impacto:
        return jsonify({
            "error": "Faltan parámetros",
            "mensaje": "Proporcione los 3 parámetros en el JSON: duracion, severidad e impacto."
        }), 400

    try:
        # Preprocesar inputs
        input_data = preprocess_input(duracion, severidad, impacto)
        
        # Realizar predicción con modelo ONNX
        resultado = predict_with_onnx(input_data)
        
        # Crear texto de predicción para guardar en S3
        timestamp = datetime.utcnow().isoformat()
        prediction_text = f"{timestamp}|{duracion}|{severidad}|{impacto}|{resultado}"
        
        # Guardar predicción en S3
        save_prediction_to_s3(prediction_text)
        
        # Log local (opcional)
        logger.info({
            "timestamp": timestamp,
            "duracion": duracion,
            "severidad": severidad,
            "impacto": impacto,
            "resultado": resultado,
            "environment": ENVIRONMENT
        })

        # Devolver el resultado en formato JSON
        return jsonify({
            "duracion_dada": duracion,
            "severidad_dada": severidad,
            "impacto_dado": impacto,
            "condicion_clasificada": resultado,
            "environment": ENVIRONMENT
        })
    except Exception as e:
        return jsonify({
            "error": "Error en la predicción",
            "mensaje": str(e)
        }), 500

@app.route('/logs', methods=['GET'])
def obtener_logs():
    """
    Devuelve los logs de clasificaciones locales.
    Se puede filtrar por condición mediante query parameter:
    /logs?condicion=ENFERMEDAD TERMINAL
    """
    condicion_filtro = request.args.get('condicion', None)
    logs = []

    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                entry = json.loads(line.strip())
                if condicion_filtro:
                    if entry.get('resultado') == condicion_filtro:
                        logs.append(entry)
                else:
                    logs.append(entry)
    except FileNotFoundError:
        return jsonify({"error": "Archivo de logs no encontrado"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error al leer los logs"}), 500

    return jsonify(logs)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check."""
    model_status = "loaded" if onnx_session is not None else "not_loaded"
    return jsonify({
        "status": "healthy",
        "model_status": model_status,
        "environment": ENVIRONMENT
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
