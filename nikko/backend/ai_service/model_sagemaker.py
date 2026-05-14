import os
import json
import time
from pathlib import Path

import boto3
from dotenv import load_dotenv
from botocore.config import Config

# --------------------------------------------------
# Cargar el archivo .env desde:
# Projecte-Nikko-v2/nikko/.env
# --------------------------------------------------
env_path = Path(__file__).resolve().parents[1] / ".env"
print(f"📄 Cargando .env desde: {env_path}")

# Cargar variables y sobrescribir las existentes
load_dotenv(dotenv_path=env_path, override=True)

# --------------------------------------------------
# Mostrar variables cargadas
# --------------------------------------------------
print("ACCESS KEY:", os.getenv("AWS_ACCESS_KEY_ID"))
print("REGION:", os.getenv("AWS_REGION"))
print("ENDPOINT:", os.getenv("SAGEMAKER_ENDPOINT_NAME"))
print("SESSION TOKEN cargado:", os.getenv("AWS_SESSION_TOKEN") is not None)

# --------------------------------------------------
# Configuración
# --------------------------------------------------
ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

if not ENDPOINT_NAME:
    raise ValueError(
        f"No se ha encontrado la variable SAGEMAKER_ENDPOINT_NAME en {env_path}"
    )

# --------------------------------------------------
# Cliente SageMaker Runtime
# --------------------------------------------------
config = Config(
    read_timeout=300,
    connect_timeout=60,
    retries={"max_attempts": 0}
)

runtime = boto3.client(
    "sagemaker-runtime",
    region_name=AWS_REGION,
    config=config
)

# --------------------------------------------------
# Petición de prueba
# --------------------------------------------------
print("\n🚀 Enviando petición al endpoint...")
print(f"📌 Endpoint: {ENDPOINT_NAME}")
print(f"🌍 Región: {AWS_REGION}\n")

inicio = time.time()

response = runtime.invoke_endpoint(
    EndpointName=ENDPOINT_NAME,
    ContentType="application/json",
    Body=json.dumps({
        "mensaje": "hola"
    })
)

elapsed = time.time() - inicio
resultado = json.loads(response["Body"].read())

# --------------------------------------------------
# Resultado
# --------------------------------------------------
print(f"⏱️ Tiempo de respuesta: {elapsed:.1f}s")
print("\n✅ Respuesta del endpoint:\n")
print(json.dumps(resultado, indent=2, ensure_ascii=False))