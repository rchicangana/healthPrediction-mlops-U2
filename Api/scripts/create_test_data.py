"""
Script para crear datos de prueba y subirlos a S3.
"""
import pandas as pd
import boto3
import os
import sys
from io import StringIO
from dotenv import load_dotenv

load_dotenv()

def create_test_data():
    """Crea un DataFrame con datos de prueba."""
    test_data = {
        'duracion': ['aguda', 'prolongada', 'ausente', 'aguda', 'prolongada'],
        'severidad': ['intenso', 'grave', 'mínimo', 'leve', 'muy intenso'],
        'impacto': ['incapacidad', 'incapacidad total', 'normal', 'mínimo', 'limitado permanentemente'],
        'expected_result': ['ENFERMEDAD AGUDA', 'ENFERMEDAD CRÓNICA', 'NO ENFERMO', 'ENFERMEDAD LEVE', 'ENFERMEDAD CRÓNICA']
    }
    return pd.DataFrame(test_data)

def upload_test_data_to_s3(df, bucket_name, s3_key):
    """Sube los datos de prueba a S3 como CSV."""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    try:
        # Convertir DataFrame a CSV en memoria
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        
        # Subir a S3
        print(f"Subiendo datos de prueba a s3://{bucket_name}/{s3_key}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=csv_buffer.getvalue()
        )
        print(f"✓ Datos de prueba subidos exitosamente a s3://{bucket_name}/{s3_key}")
    except Exception as e:
        print(f"✗ Error al subir datos de prueba: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    df = create_test_data()
    bucket_name = os.getenv('S3_BUCKET', 'health-prediction-mlops')
    s3_key = os.getenv('S3_TEST_DATA_PATH', 'test_data/test_data.csv')
    
    upload_test_data_to_s3(df, bucket_name, s3_key)

