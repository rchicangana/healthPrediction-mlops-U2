"""
Script para subir el modelo ONNX a S3.
Este script debe ejecutarse manualmente para subir el modelo inicial.
"""
import boto3
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def upload_model_to_s3(model_path, bucket_name, s3_key):
    """Sube un modelo ONNX a S3."""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    try:
        print(f"Subiendo {model_path} a s3://{bucket_name}/{s3_key}")
        s3_client.upload_file(model_path, bucket_name, s3_key)
        print(f"✓ Modelo subido exitosamente a s3://{bucket_name}/{s3_key}")
    except Exception as e:
        print(f"✗ Error al subir modelo: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python upload_model_to_s3.py <ruta_al_modelo.onnx>")
        sys.exit(1)
    
    model_path = sys.argv[1]
    bucket_name = os.getenv('S3_BUCKET', 'health-prediction-mlops')
    s3_key = os.getenv('S3_MODEL_PATH', 'models/health_model.onnx')
    
    if not os.path.exists(model_path):
        print(f"✗ Error: El archivo {model_path} no existe")
        sys.exit(1)
    
    upload_model_to_s3(model_path, bucket_name, s3_key)

