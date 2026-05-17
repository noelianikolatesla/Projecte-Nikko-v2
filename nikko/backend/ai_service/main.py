"""
main.py - API FastAPI del backend Nikko.

Este es el UNICO punto de entrada para el equipo de frontend.

Flujo del endpoint /chat:
  1. Frontend envia {"prompt": "..."}
  2. validar_input()      -> rechaza si es fuera de alcance, jailbreak, etc.
  3. llamar_modelo()      -> llama a Nikko via Ollama (local o RunPod)
  4. parsear_respuesta()  -> extrae JSON del texto crudo
  5. aplicar_guardrails() -> corrige nivel, categoria, recursos, etc.
  6. guardar en Mongo
  7. devolver al frontend

Para arrancar:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient

# Modulos propios
from .config import (
    MONGODB_URL,
    MONGODB_DB,
    MONGODB_COLLECTION,
    NIKKO_MODEL_NAME,
    ENTORNO,
    imprimir_config,
)
from .consumir_nikko import (
    llamar_modelo,
    ping,
    modelo_disponible,
    ModeloTimeoutError,
    ModeloConexionError,
    _resolver_ollama_host,
)
from .guardrails import (
    validar_input,
    parsear_respuesta_modelo,
    aplicar_guardrails,
    respuesta_input_invalido,
    MENSAJE_ERROR_TECNICO,
)


# ============================================================
# APLICACION FASTAPI
# ============================================================

app = FastAPI(
    title="Nikko - Asistente de prevencion de bullying",
    description="API que conecta el frontend con el modelo Nikko fine-tuneado",
    version="2.0.0",
)

# CORS para que el frontend (otro dominio) pueda llamar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODELOS DE DATOS
# ============================================================

class Prompt(BaseModel):
    """Lo que envia el frontend a /chat"""
    prompt: str


# ============================================================
# EVENTOS DE STARTUP / SHUTDOWN
# ============================================================

@app.on_event("startup")
def startup():
    """Se ejecuta al arrancar el servidor."""
    imprimir_config()

    # Conectar a MongoDB
    app.mongodb_client = MongoClient(MONGODB_URL)
    app.mongodb = app.mongodb_client[MONGODB_DB]
    app.mongo_collection = app.mongodb[MONGODB_COLLECTION]
    print(f"[OK] MongoDB: {MONGODB_DB}.{MONGODB_COLLECTION}")

    # Comprobar conexion con Ollama (no bloqueante)
    # Comprobar conexion con Ollama (no bloqueante)
    host_real = _resolver_ollama_host()

    if ping():
        print(f"[OK] Ollama responde en {host_real}")
        if modelo_disponible():
            print(f"[OK] Modelo {NIKKO_MODEL_NAME} cargado")
        else:
            print(f"[!] Modelo {NIKKO_MODEL_NAME} NO esta cargado")
            print(f"    Ejecuta: ollama create {NIKKO_MODEL_NAME} -f Modelfile")
    else:
        print(f"[!] Ollama NO responde en {host_real}")

@app.on_event("shutdown")
def shutdown():
    app.mongodb_client.close()
    print("[OK] MongoDB cerrado")


# ============================================================
# UTILIDADES INTERNAS
# ============================================================

def _guardar_en_mongo(request: Request, prompt: str, respuesta: dict, duracion_ms: int) -> str:
    """
    Guarda la interaccion completa en MongoDB.
    Guarda el JSON entero de Nikko + metadatos.
    """
    documento = {
        "prompt": prompt,
        "nivel": respuesta.get("nivel"),
        "categoria": respuesta.get("categoria"),
        "accion": respuesta.get("accion"),
        "recursos": respuesta.get("recursos", []),
        "telefonos": respuesta.get("telefonos", []),
        "requiere_alerta": respuesta.get("requiere_alerta", False),
        "abrir_formulario": respuesta.get("abrir_formulario"),
        "respuesta_usuario": respuesta.get("respuesta_usuario"),
        "model": NIKKO_MODEL_NAME,
        "source": ENTORNO,
        "duracion_ms": duracion_ms,
        "created_at": datetime.now(timezone.utc),
    }
    resultado = request.app.mongo_collection.insert_one(documento)
    return str(resultado.inserted_id)


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
def home():
    """Informacion general de la API."""
    return {
        "status": "Nikko API funcionando",
        "version": "2.0.0",
        "entorno": ENTORNO,
        "modelo": NIKKO_MODEL_NAME,
        "endpoints": [
            "GET  /",
            "POST /chat",
            "GET  /health",
            "GET  /grafana/interacciones",
            "GET  /grafana/stats",
        ],
    }


@app.get("/health")
def health():
    """Healthcheck para Docker, Kubernetes o Grafana."""
    ollama_ok = ping()
    modelo_ok = modelo_disponible() if ollama_ok else False
    estado = "ok" if (ollama_ok and modelo_ok) else "degraded"

    return {
        "status": estado,
        "ollama": ollama_ok,
        "modelo_cargado": modelo_ok,
        "entorno": ENTORNO,
        "modelo": NIKKO_MODEL_NAME,
    }


@app.post("/chat")
def chat(data: Prompt, request: Request):
    """
    Endpoint principal: recibe mensaje del usuario y devuelve
    la respuesta de Nikko con guardrails aplicados.

    Frontend envia:
        POST /chat
        Content-Type: application/json
        {"prompt": "Me han amenazado con pegarme"}

    Frontend recibe (los 8 campos de Nikko + metadatos):
        {
            "nivel": 3,
            "categoria": "amenaza_de_violencia",
            "accion": "proteccion_inmediata_y_derivacion",
            "recursos": ["jefatura", "conserjeria", "familia"],
            "telefonos": ["900018018"],
            "requiere_alerta": true,
            "abrir_formulario": "aviso",
            "respuesta_usuario": "Lo que me cuentas es muy grave...",
            "mongo_id": "...",
            "duracion_ms": 2340
        }
    """
    prompt = (data.prompt or "").strip()
    inicio = time.time()

    # ---- 1. Validar entrada con TU guardrails -----------------------
    rechazo = validar_input(prompt)
    if rechazo is not None:
        # validar_input devuelve un mensaje string si rechaza
        print(f"[VALIDACION] Mensaje rechazado: {rechazo[:80]}")
        respuesta = respuesta_input_invalido(rechazo)

        try:
            mongo_id = _guardar_en_mongo(request, prompt, respuesta, 0)
            respuesta["mongo_id"] = mongo_id
        except Exception as e:
            print(f"[!] Error guardando en Mongo: {e}")
            respuesta["mongo_id"] = None

        respuesta["duracion_ms"] = 0
        return respuesta

    # ---- 2. Llamar al modelo Nikko --------------------------
    try:
        texto_crudo = llamar_modelo(prompt)
    except ModeloTimeoutError as e:
        print(f"[TIMEOUT] {e}")
        duracion_ms = int((time.time() - inicio) * 1000)
        return {
            "nivel": -1,
            "categoria": "error_sistema",
            "accion": "reintentar",
            "recursos": [],
            "telefonos": [],
            "requiere_alerta": False,
            "abrir_formulario": None,
            "respuesta_usuario": MENSAJE_ERROR_TECNICO,
            "duracion_ms": duracion_ms,
        }
    except ModeloConexionError as e:
        print(f"[CONEXION] {e}")
        raise HTTPException(
            status_code=503,
            detail="El modelo Nikko no esta disponible en este momento",
        )

    # ---- 3. Parsear respuesta del modelo --------------------
    data_modelo = parsear_respuesta_modelo(texto_crudo)

    # ---- 4. Aplicar guardrails (con mensaje del usuario) ----
    respuesta = aplicar_guardrails(data_modelo, mensaje_usuario=prompt)

    duracion_ms = int((time.time() - inicio) * 1000)

    # ---- 5. Guardar en MongoDB ------------------------------
    try:
        mongo_id = _guardar_en_mongo(request, prompt, respuesta, duracion_ms)
        respuesta["mongo_id"] = mongo_id
    except Exception as e:
        print(f"[!] Error guardando en Mongo: {e}")
        respuesta["mongo_id"] = None

    respuesta["duracion_ms"] = duracion_ms

    print(f"[OK] /chat - nivel={respuesta.get('nivel')} duracion={duracion_ms}ms")

    return respuesta


# ============================================================
# ENDPOINTS PARA GRAFANA
# ============================================================

@app.get("/grafana/interacciones")
def grafana_interacciones(request: Request):
    """
    Endpoint para Grafana: devuelve todas las interacciones
    en formato compatible con paneles temporales.
    """
    datos = list(request.app.mongo_collection.find())

    resultado = []
    for item in datos:
        resultado.append({
            "time": int(item["created_at"].timestamp() * 1000),
            "nivel": int(item.get("nivel", 0)) if item.get("nivel") is not None else 0,
            "categoria": item.get("categoria", ""),
            "duracion_ms": item.get("duracion_ms", 0),
        })

    return resultado


@app.get("/grafana/stats")
def grafana_stats(request: Request):
    """
    Estadisticas agregadas para dashboard:
      - Total de interacciones
      - Distribucion por nivel
      - Distribucion por categoria
      - Latencia promedio
    """
    total = request.app.mongo_collection.count_documents({})

    pipeline_nivel = [
        {"$group": {"_id": "$nivel", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    por_nivel = list(request.app.mongo_collection.aggregate(pipeline_nivel))

    pipeline_cat = [
        {"$group": {"_id": "$categoria", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    por_categoria = list(request.app.mongo_collection.aggregate(pipeline_cat))

    pipeline_lat = [
        {"$group": {"_id": None, "avg_ms": {"$avg": "$duracion_ms"}}},
    ]
    lat = list(request.app.mongo_collection.aggregate(pipeline_lat))
    latencia_promedio = lat[0]["avg_ms"] if lat else 0

    return {
        "total_interacciones": total,
        "por_nivel": [{"nivel": x["_id"], "count": x["count"]} for x in por_nivel],
        "por_categoria": [{"categoria": x["_id"], "count": x["count"]} for x in por_categoria],
        "latencia_promedio_ms": round(latencia_promedio or 0, 2),
    }
