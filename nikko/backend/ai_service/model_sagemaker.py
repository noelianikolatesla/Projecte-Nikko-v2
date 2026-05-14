import os
import json
import time
from pathlib import Path

import boto3
from dotenv import load_dotenv
from botocore.config import Config

# Guardrails
from guardrails import (
    validar_input,
    respuesta_input_invalido,
    parsear_respuesta_modelo,
    aplicar_guardrails,
)

# --------------------------------------------------
# Cargar el archivo .env desde:
# Projecte-Nikko-v2/nikko/backend/.env
# --------------------------------------------------
env_path = Path(__file__).resolve().parents[1] / ".env"
print(f"📄 Cargando .env desde: {env_path}")

# Cargar variables de entorno y sobrescribir si ya existen
load_dotenv(dotenv_path=env_path, override=True)

# --------------------------------------------------
# Mostrar variables cargadas (solo para depuración)
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
# Función principal
# --------------------------------------------------
def generar_respuesta(mensaje_usuario: str) -> dict:
    """
    Flujo:
    1. Validar input.
    2. Invocar endpoint de SageMaker.
    3. Parsear respuesta del modelo.
    4. Aplicar guardrails.
    5. Devolver respuesta final.
    """

    # ----------------------------------------------
    # 1. Validar entrada
    # ----------------------------------------------
    error_input = validar_input(mensaje_usuario)

    if error_input:
        return respuesta_input_invalido(error_input)

    # ----------------------------------------------
    # 2. Invocar endpoint
    # ----------------------------------------------
    try:
        response = runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            Body=json.dumps({
                "mensaje": mensaje_usuario
            })
        )

    except runtime.exceptions.ModelError:
        print("\n❌ Timeout del endpoint de SageMaker")
        print("El contenedor ha tardado demasiado en responder.\n")

        return {
            "abrir_formulario": None,
            "accion": None,
            "categoria": "error_timeout",
            "nivel": 0,
            "recursos": [],
            "requiere_alerta": False,
            "respuesta_usuario": (
                "El servicio de inteligencia artificial está tardando más de lo "
                "esperado en responder. Inténtalo de nuevo en unos segundos."
            ),
            "telefonos": []
        }

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}\n")

        return {
            "abrir_formulario": None,
            "accion": None,
            "categoria": "error_interno",
            "nivel": 0,
            "recursos": [],
            "requiere_alerta": False,
            "respuesta_usuario": (
                "Se ha producido un error interno al procesar tu mensaje."
            ),
            "telefonos": []
        }

    # ----------------------------------------------
    # 3. Leer respuesta cruda
    # ----------------------------------------------
    salida_cruda = response["Body"].read().decode("utf-8")

    print("\n📥 Respuesta cruda del modelo:")
    print(salida_cruda)

    # ----------------------------------------------
    # 4. Parsear JSON
    # ----------------------------------------------
    respuesta_modelo = parsear_respuesta_modelo(salida_cruda)

    print("\n🧠 Respuesta parseada:")
    print(json.dumps(respuesta_modelo, indent=2, ensure_ascii=False))

    # ----------------------------------------------
    # 5. Aplicar guardrails
    # ----------------------------------------------
    respuesta_final = aplicar_guardrails(
        respuesta_modelo,
        mensaje_usuario=mensaje_usuario
    )

    print("\n🛡️ Respuesta tras guardrails:")
    print(json.dumps(respuesta_final, indent=2, ensure_ascii=False))

    return respuesta_final


# --------------------------------------------------
# Test manual
# --------------------------------------------------
if __name__ == "__main__":
    mensaje = "Me han amenazado con pegarme a la salida"

    print("\n🚀 Enviando petición al endpoint...")
    print(f"📌 Endpoint: {ENDPOINT_NAME}")
    print(f"🌍 Región: {AWS_REGION}")
    print(f"💬 Mensaje: {mensaje}\n")

    inicio = time.time()

    resultado = generar_respuesta(mensaje)

    elapsed = time.time() - inicio

    print(f"\n⏱️ Tiempo total de respuesta: {elapsed:.1f}s")
    print("\n✅ Respuesta final:\n")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))