"""
modelo_client.py - Cliente para hablar con el modelo Nikko via Ollama.

Funciona igual contra:
  - Ollama local (http://localhost:11434)
  - Ollama en Docker (http://ollama:11434)
  - Ollama en RunPod (https://XXX-11434.proxy.runpod.net)

La URL se configura en .env, este modulo NO sabe donde esta el modelo.

Devuelve TEXTO CRUDO. El parseo de JSON lo hace guardrails.parsear_respuesta_modelo()
"""

import requests
import json

from config import (
    OLLAMA_HOST,
    OLLAMA_FALLBACK_HOST,
    NIKKO_MODEL_NAME,
    OLLAMA_TIMEOUT,
)


# ============================================================
# EXCEPCIONES PROPIAS
# ============================================================

class ModeloTimeoutError(Exception):
    """El modelo no respondio a tiempo."""
    pass


class ModeloConexionError(Exception):
    """No se pudo conectar con el servidor Ollama."""
    pass

def _host_responde(host: str) -> bool:
    if not host:
        return False
    try:
        r = requests.get(f"{host}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _resolver_ollama_host() -> str:
    if _host_responde(OLLAMA_HOST):
        return OLLAMA_HOST

    if _host_responde(OLLAMA_FALLBACK_HOST):
        print(f"[INFO] Ollama local no disponible. Usando fallback: {OLLAMA_FALLBACK_HOST}")
        return OLLAMA_FALLBACK_HOST

    return OLLAMA_HOST


OLLAMA_HOST = _resolver_ollama_host()
OLLAMA_GENERATE_URL = f"{OLLAMA_HOST}/api/generate"

# ============================================================
# FUNCION PRINCIPAL
# ============================================================

def llamar_modelo(prompt: str) -> str:
    """
    Envia un prompt al modelo Nikko via Ollama.

    Args:
        prompt: texto del usuario (ya validado por guardrails antes).

    Returns:
        Texto CRUDO de la respuesta del modelo (puede contener JSON,
        texto antes/despues, lo que sea). El parseo es de guardrails.

    Lanza:
        ModeloTimeoutError, ModeloConexionError si hay problemas.
    """
    
    host_activo = _resolver_ollama_host()
    url = f"{host_activo}/api/generate"

    print(f"[INFO] Usando Ollama en: {url}")
    try:
        response = requests.post(
            url,
            json={
                "model": NIKKO_MODEL_NAME,
                "prompt": prompt.strip(),
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 400,
                },
            },
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()

    except requests.exceptions.Timeout:
        raise ModeloTimeoutError(
            f"El modelo no respondio en {OLLAMA_TIMEOUT}s"
        )

    except requests.exceptions.ConnectionError:
        raise ModeloConexionError(
            f"No se pudo conectar con Ollama en {OLLAMA_GENERATE_URL}"
        )

    except requests.exceptions.RequestException as e:
        raise ModeloConexionError(f"Error de red: {e}")

    # Devolver texto crudo
    try:
        data = response.json()
        return data.get("response", "")
    except json.JSONDecodeError:
        raise ModeloConexionError("Ollama no devolvio JSON valido")


# ============================================================
# HEALTHCHECKS
# ============================================================

def ping() -> bool:
    """
    Comprueba si Ollama responde. Devuelve True si esta vivo.
    """
    try:
        response = requests.get(
            OLLAMA_GENERATE_URL.replace("/generate", "/tags"),
            timeout=5,
        )
        return response.status_code == 200
    except Exception:
        return False


def modelo_disponible() -> bool:
    """
    Comprueba si el modelo NIKKO_MODEL_NAME esta cargado en Ollama.
    """
    try:
        response = requests.get(
            OLLAMA_GENERATE_URL.replace("/generate", "/tags"),
            timeout=5,
        )
        data = response.json()
        modelos = [m["name"] for m in data.get("models", [])]
        for m in modelos:
            if NIKKO_MODEL_NAME in m:
                return True
        return False
    except Exception:
        return False
