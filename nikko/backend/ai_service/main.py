from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from pymongo import MongoClient
from datetime import datetime, timezone
from typing import Optional
from passlib.context import CryptContext
from dotenv import load_dotenv
import requests
import os

load_dotenv()

app = FastAPI()

# -------------------------
# CONFIGURACIÓN FLEXIBLE (Docker / local)
# -------------------------
# En Docker:  OLLAMA_HOST=http://ollama:11434
# En local:   OLLAMA_HOST=http://localhost:11434
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "nikko-ia")

# MongoDB Atlas / Mongo local
# Atlas: mongodb+srv://usuario:password@cluster.mongodb.net/
# Local: mongodb://localhost:27017
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "nikko")

# Endpoint real de generación de Ollama
OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"


# -------------------------
# HASH DE CONTRASEÑAS
# -------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("La contraseña no puede estar vacía")

    password = password.strip()

    if len(password.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar los 72 bytes")

    return pwd_context.hash(password)


# -------------------------
# CONEXIÓN A MONGO
# -------------------------
@app.on_event("startup")
def startup_db():
    try:
        app.mongodb_client = MongoClient(MONGODB_URL)
        app.mongodb_client.admin.command("ping")
        app.mongodb = app.mongodb_client[MONGODB_DB]

        print("Conectado correctamente a MongoDB Atlas")
        print(f"Base de datos: {MONGODB_DB}")

    except Exception as e:
        print("Error conectando a MongoDB:", e)
        raise e


@app.on_event("shutdown")
def shutdown_db():
    app.mongodb_client.close()
    print("Conexión a MongoDB cerrada")


# -------------------------
# MODELOS INPUT
# -------------------------
class Ubicacion(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None


class Prompt(BaseModel):
    prompt: str

    # Datos del usuario
    nick: str
    password: str = Field(..., min_length=4, max_length=72)

    # Ubicación recogida por permisos de la web
    ubicacion: Optional[Ubicacion] = None

    # Estos campos pueden venir como null normalmente.
    # Solo se guardarán realmente si el nivel es crítico.
    centro_educativo: Optional[str] = None
    telefono_tutor: Optional[str] = None
    correo_electronico: Optional[str] = None


# -------------------------
# AGENTES 5 NIVELES
# -------------------------
AGENTE_NIVEL_1 = """
Eres un asistente especializado en la prevención del acoso escolar, actuando como el primer nivel de respuesta ante situaciones leves.

OBJETIVO: Ofrecer apoyo inmediato, empático y seguro a víctimas de incidentes aislados.

FILTRO DE DOMINIO (ESTRICTO):
Solo puedes responder sobre: bullying, acoso escolar, ciberacoso y apoyo emocional derivado.

Si el mensaje no tiene relación, responde exclusivamente:
"Solo puedo ayudarte con situaciones relacionadas con el bullying o el acoso. Si estás viviendo algo así, cuéntamelo y trataré de ayudarte."

NORMAS DE COMPORTAMIENTO:
- Tono: empático, cercano y protector.
- Privacidad: trata al usuario con respeto, sabiendo que su identidad está protegida y anonimizada.
- Sin redundancia: no pidas más información ni detalles innecesarios.
- Prohibido: no juzgar, no culpar y no usar frases genéricas.

PROTOCOLO DE RESPUESTA (NIVEL 1: LEVE):
Este nivel se aplica a insultos puntuales, burlas ocasionales o comentarios hirientes aislados.

Estructura de tu respuesta:
1. Validación: confirma que sus sentimientos son válidos.
2. Acción directa: da 2 consejos prácticos.
3. Seguridad: explica que el evento queda registrado para vigilar si se repite.
4. Cierre: anima a mantener la calma y hablar con un adulto de confianza si el malestar persiste.

RESTRICCIÓN DE SEGURIDAD:
- En este nivel, NUNCA menciones teléfonos de emergencia, autoridades ni protocolos de crisis.
"""

AGENTE_NIVEL_2 = """
ROL: Eres un asistente especializado en la gestión de situaciones de acoso recurrente.

OBJETIVO:
Ofrecer estrategias de afrontamiento y preparar al usuario para buscar apoyo formal.

PROTOCOLO DE RESPUESTA (NIVEL 2: RECURRENTE):
Este nivel se aplica a insultos repetidos, humillaciones constantes o burlas continuadas.

Estructura de tu respuesta:
1. Validación firme: reconoce que la repetición no es aceptable y que su malestar está justificado.
2. Estrategia de protección: da 2 o 3 consejos para poner límites o alejarse de dinámicas tóxicas.
3. Acción de sistema: informa de que el sistema ha detectado persistencia y que quedará registrado para revisión por orientación o tutoría.
4. Derivación recomendada: sugiere hablar con un profesor, tutor, orientador o adulto responsable.

RESTRICCIÓN DE SEGURIDAD:
- NO pidas detalles adicionales.
- Mantén un tono firme, protector y claro.
"""

AGENTE_NIVEL_3 = """
ROL: Eres un asistente de respuesta rápida para situaciones de alta gravedad.

TONO:
Protector, serio y resolutivo.

PROTOCOLO DE RESPUESTA (NIVEL 3: ALERTA):
Este nivel se aplica a amenazas, violencia física, acoso continuado o miedo intenso.

Estructura de tu respuesta:
1. Apoyo protector: transmite seguridad inmediata.
2. Notificación de alerta: indica que la situación ha sido marcada como prioritaria para intervención urgente por parte del centro.
3. Recursos externos obligatorios:
   - Teléfono gratuito de ayuda: 900 018 018
   - Enlace oficial:
     https://www.educacionfpydeportes.gob.es/mc/sgctie/acoso-escolar.html
4. Instrucción de seguridad: recomienda buscar físicamente a un adulto de confianza del centro de manera inmediata.

IMPORTANTE:
- No inventes acciones que el sistema no esté ejecutando realmente.
- Habla de "alerta prioritaria" o "intervención urgente recomendada", no de contacto real con autoridades si no existe.
"""

AGENTE_NIVEL_4 = """
ROL: Eres el protocolo de emergencia de Nikko para situaciones de riesgo vital o autolesión.

TU RESPUESTA DEBE SER:
Inmediata, breve, clara y centrada en la preservación de la vida.

PROTOCOLO DE RESPUESTA (NIVEL 4: EMERGENCIA):
Este nivel se aplica a ideas de autolesión, riesgo de suicidio o peligro físico inminente.

Estructura de tu respuesta:
1. Respuesta de choque:
   "Estamos contigo. Tu vida y tu seguridad son lo más importante en este momento."
2. Activación de emergencia:
   Indica que esta situación requiere ayuda urgente e inmediata.
3. Canal directo de ayuda:
   - Llama ahora mismo al 112
   - O al 024 (Línea de atención a la conducta suicida)
   - No te quedes solo si es posible
   - Busca ahora mismo a un adulto de confianza
4. Cierre de contención:
   Mantén un mensaje breve de apoyo y esperanza.

RESTRICCIÓN DE SEGURIDAD:
- No hagas análisis largos.
- No hagas preguntas innecesarias.
- No inventes que ya se ha contactado con emergencias si tu sistema no lo hace de verdad.
"""

AGENTE_NIVEL_5 = """
Eres un sistema de emergencia psicológica.

CONTEXTO:
- Riesgo crítico o vital
- Respuesta urgente y directa
- Sin análisis largo
- Prioridad absoluta: proteger al usuario

INSTRUCCIONES OBLIGATORIAS:
- Indica llamar al 112 inmediatamente
- Indica contactar con un adulto de confianza ahora mismo
- Indica no quedarse solo
- Mantén una respuesta corta, clara y contundente
- No inventes acciones técnicas que el sistema no esté ejecutando realmente
"""


# -------------------------
# LLAMADA A OLLAMA
# -------------------------
def llamar_ollama(prompt: str, temperature: float = 0.3, timeout: int = 30) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature
            },
            timeout=timeout
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    except requests.exceptions.RequestException as e:
        print("Error Ollama:", e)
        raise HTTPException(
            status_code=500,
            detail="Error con el modelo IA"
        )


# -------------------------
# CLASIFICADOR 1–5
# -------------------------
def clasificar_nivel(texto: str) -> str:
    prompt = f"""
Clasifica el siguiente mensaje en nivel de riesgo:

1 = leve
2 = medio
3 = grave
4 = muy grave
5 = crítico

Responde SOLO un número del 1 al 5.
No expliques nada.
No añadas texto extra.

Mensaje:
{texto}
"""

    try:
        resultado = llamar_ollama(prompt, temperature=0, timeout=120)

        if not resultado:
            return "1"

        for char in resultado.strip():
            if char in ["1", "2", "3", "4", "5"]:
                return char

        return "1"

    except Exception as e:
        print("Error en clasificación:", e)
        return "1"


# -------------------------
# SISTEMA EXPERTO (TRIAJE)
# -------------------------
def generar_respuesta(nivel: str, mensaje: str) -> str:
    if nivel == "1":
        agente = AGENTE_NIVEL_1
    elif nivel == "2":
        agente = AGENTE_NIVEL_2
    elif nivel == "3":
        agente = AGENTE_NIVEL_3
    elif nivel == "4":
        agente = AGENTE_NIVEL_4
    else:
        agente = AGENTE_NIVEL_5

    prompt = f"""
{agente}

Mensaje del usuario:
{mensaje}

Instrucciones finales:
- Responde en español.
- Responde de forma natural, clara y útil.
- No repitas literalmente el mensaje del usuario.
- No inventes acciones automáticas del sistema que no existan realmente.
"""

    try:
        respuesta = llamar_ollama(prompt, temperature=0.3, timeout=120)
        return respuesta if respuesta else "Lo siento, hubo un error generando la respuesta."
    except Exception as e:
        print("Error en generación:", e)
        return "Lo siento, mi conexión con el servidor de IA falló."


# -------------------------
# LABEL DEL NIVEL
# -------------------------
def obtener_label_nivel(nivel: int) -> str:
    labels = {
        1: "leve",
        2: "medio",
        3: "grave",
        4: "muy grave",
        5: "critico"
    }

    return labels.get(nivel, "desconocido")


# -------------------------
# GUARDAR EN MONGO
# -------------------------
def guardar_interaccion(request: Request, data: Prompt, respuesta: str, nivel: str) -> str:
    nivel_int = int(nivel)

    # Según lo acordado:
    # centro_educativo, telefono_tutor y correo_electronico
    # solo se guardan cuando el nivel es crítico.
    es_critico = nivel_int == 5

    documento = {
        "prompt": data.prompt,
        "respuesta": respuesta,

        "usuario": {
            "nick": data.nick,
            "password_hash": hash_password(data.password)
        },

        "ubicacion": {
            "latitude": data.ubicacion.latitude if data.ubicacion else None,
            "longitude": data.ubicacion.longitude if data.ubicacion else None,
            "accuracy": data.ubicacion.accuracy if data.ubicacion else None
        },

        "datos_criticos": {
            "centro_educativo": data.centro_educativo if es_critico else None,
            "telefono_tutor": data.telefono_tutor if es_critico else None,
            "correo_electronico": data.correo_electronico if es_critico else None
        },

        "nivel_detectado": nivel_int,
        "nivel_label": obtener_label_nivel(nivel_int),

        "flags": {
            "requiere_revision": nivel_int >= 2,
            "alerta_prioritaria": nivel_int >= 3,
            "emergencia": nivel_int >= 4,
            "critico": nivel_int == 5
        },

        "model": MODEL_NAME,

        "metadata": {
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "endpoint": str(request.url.path),
            "method": request.method
        },

        "estado": {
            "revisado": False,
            "revisado_por": None,
            "fecha_revision": None,
            "notas_orientador": None
        },

        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    resultado = request.app.mongodb.interacciones.insert_one(documento)
    print("Guardado en Mongo con ID:", resultado.inserted_id)
    return str(resultado.inserted_id)


# -------------------------
# ENDPOINTS
# -------------------------
@app.get("/")
def home():
    return {
        "status": "API funcionando 🚀",
        "config": {
            "ollama_host": OLLAMA_HOST,
            "ollama_url": OLLAMA_URL,
            "model": MODEL_NAME,
            "mongodb_url": MONGODB_URL,
            "mongodb_db": MONGODB_DB
        }
    }


@app.post("/chat")
def chat(data: Prompt, request: Request):
    texto = data.prompt.strip()
    print("Texto recibido:", texto)

    if not texto:
        raise HTTPException(status_code=400, detail="Prompt vacío")

    nivel = clasificar_nivel(texto)
    print("Nivel detectado:", nivel)

    respuesta = generar_respuesta(nivel, texto)
    print("Respuesta generada:", respuesta)

    try:
        mongo_id = guardar_interaccion(request, data, respuesta, nivel)
        print("Interacción guardada en Mongo con ID:", mongo_id)

    except Exception as e:
        print("Error guardando en Mongo:", e)
        raise HTTPException(
            status_code=500,
            detail="Error guardando la interacción en MongoDB"
        )

    nivel_int = int(nivel)

    return {
        "respuesta": respuesta,
        "info": {
            "nivel_detectado": nivel_int,
            "nivel_label": obtener_label_nivel(nivel_int),
            "mongo_id": mongo_id
        }
    }


# -------------------------
# ENDPOINT GRAFANA
# -------------------------
@app.get("/grafana/interacciones")
def grafana_interacciones(request: Request):
    datos = list(
        request.app.mongodb.interacciones.find(
            {},
            {
                "_id": 0,
                "created_at": 1,
                "nivel_detectado": 1,
                "nivel_label": 1,
                "flags": 1,
                "usuario.nick": 1,
                "datos_criticos.centro_educativo": 1
            }
        )
    )

    resultado = []

    for item in datos:
        created_at = item.get("created_at")
        nivel_detectado = item.get("nivel_detectado", 1)

        if not created_at:
            continue

        resultado.append({
            "time": int(created_at.timestamp() * 1000),
            "nivel": int(nivel_detectado),
            "nivel_label": item.get("nivel_label"),
            "nick": item.get("usuario", {}).get("nick"),
            "centro_educativo": item.get("datos_criticos", {}).get("centro_educativo"),
            "requiere_revision": item.get("flags", {}).get("requiere_revision", False),
            "alerta_prioritaria": item.get("flags", {}).get("alerta_prioritaria", False),
            "emergencia": item.get("flags", {}).get("emergencia", False),
            "critico": item.get("flags", {}).get("critico", False)
        })

    return resultado