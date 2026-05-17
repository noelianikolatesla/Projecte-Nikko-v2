"""
config.py - Configuracion centralizada del backend Nikko.

Lee el archivo .env de la carpeta padre (backend/.env)
y expone las variables como constantes.

Para cambiar entre LOCAL y RUNPOD, edita backend/.env
NUNCA modifiques este archivo.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# CARGAR .env
# ============================================================
# El .env esta en la carpeta PADRE de ai_service/
# Estructura:
#   backend/
#     .env              <- aqui
#     ai_service/
#       config.py       <- este archivo

ENV_PATH = Path(__file__).parent.parent / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
    print(f"[CONFIG] Cargado: {ENV_PATH}")
else:
    # Si no existe en la carpeta padre, intenta en la misma carpeta
    # (por compatibilidad si alguien lo pone aqui)
    load_dotenv()
    print(f"[CONFIG] .env no encontrado en {ENV_PATH}, usando entorno")


# ============================================================
# OLLAMA / MODELO NIKKO
# ============================================================

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_FALLBACK_HOST = os.getenv("OLLAMA_FALLBACK_HOST", "").rstrip("/")
NIKKO_MODEL_NAME = os.getenv("NIKKO_MODEL_NAME", "bullying-nikko")
OLLAMA_GENERATE_URL = f"{OLLAMA_HOST}/api/generate"
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))


# ============================================================
# MONGODB
# ============================================================
# Soportamos los dos nombres por compatibilidad:
#   - MONGODB_URL / MONGODB_DB (nuevo, recomendado)
#   - MONGO_URL   / MONGO_DB   (antiguo)
#
# Si estan los dos, gana el nuevo (MONGODB_*).

MONGODB_URL = (
    os.getenv("MONGODB_URL")
    or os.getenv("MONGO_URL")
    or "mongodb://localhost:27017"
)

MONGODB_DB = (
    os.getenv("MONGODB_DB")
    or os.getenv("MONGO_DB")
    or "nikko"
)

MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "interacciones")


# ============================================================
# AWS (opcional)
# ============================================================

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN", "")

BEDROCK_AGENT_ID = os.getenv("BEDROCK_AGENT_ID", "")
BEDROCK_ALIAS_ID = os.getenv("BEDROCK_ALIAS_ID", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
SAGEMAKER_ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT_NAME", "")


# ============================================================
# SERVIDOR API
# ============================================================

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))


# ============================================================
# DETECCION DE ENTORNO
# ============================================================

def detectar_entorno():
    """Devuelve 'local', 'docker' o 'runpod' segun la URL."""
    if "runpod.net" in OLLAMA_HOST:
        return "runpod"
    if "localhost" in OLLAMA_HOST or "127.0.0.1" in OLLAMA_HOST:
        return "local"
    if "ollama" in OLLAMA_HOST and "http://ollama" in OLLAMA_HOST:
        return "docker"
    return "custom"


ENTORNO = detectar_entorno()


# ============================================================
# IMPRESION DE CONFIGURACION AL ARRANCAR
# ============================================================

def imprimir_config():
    """Imprime la configuracion actual (oculta secretos)."""

    def ocultar(valor):
        """Oculta valores sensibles mostrando solo unos pocos caracteres."""
        if not valor:
            return "(vacio)"
        if len(valor) > 8:
            return valor[:6] + "..." + valor[-2:]
        return "***"

    print("=" * 60)
    print("CONFIGURACION BACKEND NIKKO")
    print("=" * 60)
    print(f"  Entorno:        {ENTORNO}")
    print(f"  Ollama URL:     {OLLAMA_HOST}")
    print(f"  Modelo:         {NIKKO_MODEL_NAME}")
    print(f"  Timeout:        {OLLAMA_TIMEOUT}s")
    mongo_safe = (
        MONGODB_URL.split('@')[-1] if '@' in MONGODB_URL else MONGODB_URL
    )
    print(f"  MongoDB:        {mongo_safe}")
    print(f"  Base de datos:  {MONGODB_DB}")
    print(f"  Coleccion:      {MONGODB_COLLECTION}")
    print(f"  API:            http://{API_HOST}:{API_PORT}")
    print(f"  AWS region:     {AWS_REGION}")
    print(f"  AWS keys:       {ocultar(AWS_ACCESS_KEY_ID)}")
    print("=" * 60)
