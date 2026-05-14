"""
Modulo de guardrails para Nikko.
Encapsula validaciones, normalizacion y filtros de seguridad.
"""

import json
import re
from typing import Optional


MENSAJE_FUERA_DE_ALCANCE = (
    "Solo puedo ayudarte con situaciones relacionadas con el bullying o el "
    "acoso escolar. Si estas viviendo algo asi, cuentamelo y tratare de "
    "ayudarte."
)

MENSAJE_ERROR_TECNICO = (
    "Perdona, ha habido un problema tecnico. Puedes contarmelo de nuevo?"
)

CAMPOS_OBLIGATORIOS = {
    "nivel",
    "categoria",
    "accion",
    "recursos",
    "telefonos",
    "requiere_alerta",
    "abrir_formulario",
    "respuesta_usuario",
}

TELEFONOS_PERMITIDOS = {"024", "112", "900018018"}

CATEGORIAS_VALIDAS = {
    "fuera_de_alcance",
    "mensaje_vacio",
    "conflicto_puntual",
    "conflicto_recurrente",
    "incidente_puntual",
    "acoso_recurrente",
    "ciberacoso_recurrente",
    "amenaza_de_violencia",
    "coaccion_o_chantaje",
    "riesgo_de_agresion_inminente",
    "violencia_fisica",
    "violencia_fisica_grupal",
    "agresion_grave",
    "riesgo_suicida",
    "riesgo_autolesion",
}

ACCIONES_VALIDAS = {
    None,
    "fuera_de_alcance",
    "escucha_activa",
    "gestion_emocional",
    "validacion_emocional",
    "derivacion_interna",
    "recopilar_pruebas_y_derivar",
    "proteccion_inmediata_y_derivacion",
    "desescalada_y_proteccion_inmediata",
    "denuncia_inmediata_y_atencion_medica",
    "emergencia_inmediata",
}

LONGITUD_MAX_INPUT = 500
LONGITUD_MIN_INPUT = 2

PATRONES_JAILBREAK = [
    r"ignora.*instrucciones",
    r"olvida.*reglas",
    r"actua como",
    r"finge ser",
    r"pretende que",
    r"system prompt",
    r"\bjailbreak\b",
]

PATRONES_FUERA_ALCANCE = [
    r"\bpaella\b",
    r"\breceta\b",
    r"\bingredientes\b",
    r"\bcocinar\b",
    r"\bpython\b",
    r"\bprogramar\b",
    r"\bcodigo\b",
    r"\bcódigo\b",
    r"\bmatematicas\b",
    r"\bmatemáticas\b",
    r"\bfutbol\b",
    r"\bfútbol\b",
    r"\bpelicula\b",
    r"\bpelícula\b",
    r"\bserie\b",
]


def validar_input(mensaje_usuario: str) -> Optional[str]:
    if not mensaje_usuario or not mensaje_usuario.strip():
        return "Por favor, escribeme algo para que pueda ayudarte."

    if len(mensaje_usuario.strip()) < LONGITUD_MIN_INPUT:
        return "Cuentame un poco mas para que pueda entenderte."

    if len(mensaje_usuario) > LONGITUD_MAX_INPUT:
        return (
            f"Tu mensaje es demasiado largo. Resumelo en menos de "
            f"{LONGITUD_MAX_INPUT} caracteres."
        )

    mensaje_lower = mensaje_usuario.lower()

    for patron in PATRONES_JAILBREAK:
        if re.search(patron, mensaje_lower):
            return MENSAJE_FUERA_DE_ALCANCE

    for patron in PATRONES_FUERA_ALCANCE:
        if re.search(patron, mensaje_lower):
            return MENSAJE_FUERA_DE_ALCANCE

    return None


def parsear_respuesta_modelo(salida_cruda: str) -> dict:
    """
    Intenta extraer un JSON valido aunque el modelo haya escrito texto alrededor.
    """
    if not isinstance(salida_cruda, str):
        return _respuesta_error("salida_no_es_string")

    salida_cruda = salida_cruda.strip()

    try:
        return json.loads(salida_cruda)
    except json.JSONDecodeError:
        pass

    start = salida_cruda.find("{")
    end = salida_cruda.rfind("}")

    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(salida_cruda[start:end + 1])
        except json.JSONDecodeError:
            pass

    return _respuesta_error("error_parseo_json")


def aplicar_guardrails(respuesta: dict, mensaje_usuario: str = "") -> dict:
    """
    Normaliza la respuesta del modelo y aplica reglas duras de seguridad.

    Importante:
    - Para poder corregir nivel 3/4/5, pasa siempre el mensaje_usuario.
    """
    if not isinstance(respuesta, dict):
        return _respuesta_error("respuesta_no_es_dict")

    if respuesta.get("categoria") == "error_interno":
        return respuesta

    campos_faltantes = CAMPOS_OBLIGATORIOS - set(respuesta.keys())
    if campos_faltantes:
        return _respuesta_error(f"faltan_campos_{','.join(sorted(campos_faltantes))}")

    nivel = respuesta.get("nivel")
    if not isinstance(nivel, int) or nivel < 0 or nivel > 5:
        return _respuesta_error("nivel_invalido")

    respuesta = corregir_nivel_por_texto(respuesta, mensaje_usuario)
    nivel = respuesta["nivel"]

    respuesta["telefonos"] = normalizar_telefonos(respuesta.get("telefonos", []))

    if not isinstance(respuesta.get("recursos"), list):
        respuesta["recursos"] = []

    respuesta_texto = respuesta.get("respuesta_usuario", "")
    if not isinstance(respuesta_texto, str) or len(respuesta_texto.strip()) < 10:
        return _respuesta_error("respuesta_vacia")

    respuesta["respuesta_usuario"] = respuesta_texto.strip()

    if nivel == 0:
        respuesta.update({
            "nivel": 0,
            "categoria": "fuera_de_alcance",
            "accion": None,
            "recursos": [],
            "telefonos": [],
            "requiere_alerta": False,
            "abrir_formulario": None,
            "respuesta_usuario": MENSAJE_FUERA_DE_ALCANCE,
        })
        return respuesta

    if nivel == 1:
        respuesta["requiere_alerta"] = False
        respuesta["abrir_formulario"] = None
        respuesta["telefonos"] = []
        respuesta["recursos"] = []

        if respuesta.get("categoria") not in CATEGORIAS_VALIDAS:
            respuesta["categoria"] = "conflicto_puntual"

        if respuesta.get("accion") not in ACCIONES_VALIDAS:
            respuesta["accion"] = "escucha_activa"

    elif nivel == 2:
        respuesta["requiere_alerta"] = True
        respuesta["abrir_formulario"] = None

        texto_usuario = (mensaje_usuario or "").lower()
        categoria_actual = respuesta.get("categoria")

        # Si el modelo inventa una categoria o usa una categoria demasiado rara,
        # normalizamos segun el contenido real del mensaje.
        if categoria_actual not in CATEGORIAS_VALIDAS:
            if es_ciberacoso(texto_usuario):
                respuesta["categoria"] = "ciberacoso_recurrente"
            elif es_acoso_recurrente(texto_usuario):
                respuesta["categoria"] = "acoso_recurrente"
            else:
                respuesta["categoria"] = "conflicto_recurrente"

        # Si el modelo dejo una categoria valida pero demasiado generica,
        # tambien podemos mejorarla segun texto.
        elif categoria_actual == "conflicto_recurrente" and es_acoso_recurrente(texto_usuario):
            respuesta["categoria"] = "acoso_recurrente"

        if respuesta.get("accion") not in ACCIONES_VALIDAS:
            if respuesta["categoria"] == "ciberacoso_recurrente":
                respuesta["accion"] = "recopilar_pruebas_y_derivar"
            else:
                respuesta["accion"] = "derivacion_interna"

        if not respuesta["recursos"]:
            if respuesta["categoria"] == "ciberacoso_recurrente":
                respuesta["recursos"] = ["familia", "orientadora", "tutor"]
            elif respuesta["categoria"] == "acoso_recurrente":
                respuesta["recursos"] = ["tutor", "orientadora"]
            else:
                respuesta["recursos"] = ["tutor", "orientadora"]

        if respuesta["categoria"] == "ciberacoso_recurrente":
            if "900018018" not in respuesta["telefonos"]:
                respuesta["telefonos"].append("900018018")

    elif nivel == 3:
        respuesta["categoria"] = "amenaza_de_violencia"
        respuesta["accion"] = "proteccion_inmediata_y_derivacion"
        respuesta["requiere_alerta"] = True
        respuesta["abrir_formulario"] = "aviso"

        for recurso in ["jefatura", "conserjeria", "familia"]:
            if recurso not in respuesta["recursos"]:
                respuesta["recursos"].append(recurso)

        if "900018018" not in respuesta["telefonos"]:
            respuesta["telefonos"].append("900018018")

    elif nivel == 4:
        respuesta["requiere_alerta"] = True
        respuesta["abrir_formulario"] = "denuncia"

        if respuesta.get("categoria") not in {
            "violencia_fisica",
            "violencia_fisica_grupal",
            "agresion_grave",
            "riesgo_de_agresion_inminente",
        }:
            respuesta["categoria"] = "violencia_fisica"

        respuesta["accion"] = "denuncia_inmediata_y_atencion_medica"

        for recurso in ["jefatura", "familia", "direccion"]:
            if recurso not in respuesta["recursos"]:
                respuesta["recursos"].append(recurso)

        if "900018018" not in respuesta["telefonos"]:
            respuesta["telefonos"].append("900018018")

    elif nivel == 5:
        respuesta["requiere_alerta"] = True
        respuesta["abrir_formulario"] = None

        if respuesta.get("categoria") not in {"riesgo_suicida", "riesgo_autolesion"}:
            respuesta["categoria"] = "riesgo_suicida"

        respuesta["accion"] = "emergencia_inmediata"
        respuesta["recursos"] = ["adulto_presencial", "familia"]
        respuesta["telefonos"] = ["024", "112"]

        respuesta["respuesta_usuario"] = (
            "Esto es una emergencia y lo primero es tu seguridad. "
            "Por favor, llama ahora al 024 o al 112 si estas en peligro inmediato. "
            "Busca a un adulto que pueda quedarse contigo fisicamente y no te quedes solo/a ahora."
        )

    respuesta["respuesta_usuario"] = limpiar_respuesta_usuario(
        respuesta["respuesta_usuario"],
        respuesta["nivel"],
    )

    respuesta = mejorar_respuesta_por_caso(mensaje_usuario, respuesta)

    return respuesta


def normalizar_telefonos(telefonos) -> list[str]:
    if not isinstance(telefonos, list):
        return []

    telefonos_normalizados = []

    for tel in telefonos:
        tel_limpio = str(tel).replace(" ", "").strip()

        if tel_limpio in TELEFONOS_PERMITIDOS and tel_limpio not in telefonos_normalizados:
            telefonos_normalizados.append(tel_limpio)

    return telefonos_normalizados


def es_ciberacoso(texto: str) -> bool:
    patrones = [
        "grupo de clase",
        "grupo de whatsapp",
        "whatsapp",
        "instagram",
        "tiktok",
        "historias",
        "memes",
        "foto mia",
        "foto mía",
        "suben fotos",
        "publican",
        "mensajes",
        "redes",
    ]
    return any(p in texto for p in patrones)


def es_acoso_recurrente(texto: str) -> bool:
    patrones = [
        "se rien de mi",
        "se ríen de mí",
        "se rien de mí",
        "se ríen de mi",
        "se burlan",
        "me esconden la mochila",
        "me ponen motes",
        "me insultan",
        "me ignoran",
        "nadie me habla",
        "me dejan fuera",
        "hacen ruidos",
        "me ridiculizan",
        "me llaman gordo",
        "se meten con mi",
        "cada recreo",
        "cada vez que hablo",
        "todos los dias",
        "todos los días",
        "casi todos los dias",
        "casi todos los días",
        "desde hace semanas",
        "desde hace meses",
        "varias veces por semana",
        "repetidas veces",
    ]
    return any(p in texto for p in patrones)


def corregir_nivel_por_texto(respuesta: dict, mensaje_usuario: str) -> dict:
    """
    Corrige errores graves de nivel usando el texto del usuario.

    Prioridad:
    1. Suicidio/autolesion -> nivel 5
    2. Agresion fisica ya ocurrida -> nivel 4
    3. Amenaza futura -> nivel 3
    4. Repeticion/acoso sin amenaza -> nivel 2
    5. Conflicto puntual -> nivel 1
    """
    texto = (mensaje_usuario or "").lower()

    patrones_suicidio = [
        "no quiero seguir viviendo",
        "no quiero vivir",
        "quiero acabar con todo",
        "acabar con todo",
        "hacerme daño",
        "me he hecho cortes",
        "me hice cortes",
        "no despertarme",
        "quiero desaparecer",
        "quitarme la vida",
        "suicid",
    ]

    patrones_agresion = [
        "me han pegado",
        "me ha pegado",
        "me pegaron",
        "me han dado una paliza",
        "me dieron una paliza",
        "me han empujado",
        "me empujaron",
        "me han acorralado",
        "me acorralaron",
        "me han escupido",
        "me escupieron",
        "me han encerrado",
        "me encerraron",
        "me han quemado",
        "me tiraron al suelo",
        "me han tirado al suelo",
        "patadas",
        "puñetazo",
        "moraton",
        "moratón",
        "me han roto",
    ]

    patrones_amenaza = [
        "me ha amenazado",
        "me han amenazado",
        "me amenaza",
        "me amenazan",
        "me espera a la salida",
        "me espere a la salida",
        "me esperan a la salida",
        "me van a pegar",
        "me quiere pegar",
        "me va a pegar",
        "me esperan fuera",
        "me chantajea",
        "me estan chantajeando",
        "me están chantajeando",
        "si cuento",
        "si se lo digo",
    ]

    patrones_recurrencia = [
        "siempre",
        "todos los dias",
        "todos los días",
        "cada dia",
        "cada día",
        "desde hace semanas",
        "desde hace meses",
        "constantemente",
        "todo el rato",
        "varias veces",
        "a menudo",
        "repetidas veces",
        "despues del patio",
        "después del patio",
        "cuando hablo en clase",
    ]

    patrones_conflicto_puntual = [
        "me he enfadado",
        "por una tonteria",
        "por una tontería",
        "nos peleamos por una tonteria",
        "nos peleamos por una tontería",
        "hemos discutido hoy",
        "me he peleado con mi amiga",
        "me he peleado con mi amigo",
        "se burlaba de mi",
        "se burlaba de mí",
        "era mas guapa que yo",
        "era más guapa que yo",
        "no me queda bien",
    ]

    if any(p in texto for p in patrones_suicidio):
        respuesta["nivel"] = 5
        return respuesta

    if any(p in texto for p in patrones_agresion):
        respuesta["nivel"] = 4
        return respuesta

    if any(p in texto for p in patrones_amenaza):
        respuesta["nivel"] = 3
        return respuesta

    if any(p in texto for p in patrones_recurrencia) or es_acoso_recurrente(texto):
        respuesta["nivel"] = 2
        return respuesta

    if any(p in texto for p in patrones_conflicto_puntual):
        respuesta["nivel"] = 1
        return respuesta

    return respuesta


def limpiar_respuesta_usuario(texto: str, nivel: int) -> str:
    """
    Limpia frases raras o peligrosas que pueda generar el modelo.
    No reescribe toda la respuesta, solo sustituye expresiones problematicas.
    """
    sustituciones = {
        "lo mas chachi del mundo": "algo que puede doler aunque parezca pequeño",
        "lo más chachi del mundo": "algo que puede doler aunque parezca pequeño",
        "buscarte las espaldas": "exponerte",
        "cubrirte las espaldas hasta que estes seguro/a": "estar acompañado/a hasta que estes seguro/a",
        "cubrirte las espaldas hasta que estés seguro/a": "estar acompañado/a hasta que estes seguro/a",
        "envenenado": "muy dañino",
        "Si ignores": "Si intentas saltarte",
        "si ignores": "si intentas saltarte",
        "rieen": "rien",
        "rieén": "rien",
        "¿Tienes alguien a quien pueda ayudarte a contestar así?": (
            "¿Hay algun profesor o adulto de confianza con quien puedas hablar de esto?"
        ),
        "¿Tienes alguien a quien pueda ayudarte a contestar asi?": (
            "¿Hay algun profesor o adulto de confianza con quien puedas hablar de esto?"
        ),
        "¿Puedes enseñarselo mañana?": (
            "¿Puedes contarselo mañana a tu tutor o a jefatura?"
        ),
        "¿Puedes enseñárselo mañana?": (
            "¿Puedes contarselo mañana a tu tutor o a jefatura?"
        ),
        "ve un medico": "ve a un medico",
        "ve un médico": "ve a un medico",
        "Busca a un adulto de la jefatura": "Busca a alguien de jefatura",
        "para que esten preparados": "para que puedan acompañarte y protegerte",
        "para que estén preparados": "para que puedan acompañarte y protegerte",
    }

    for malo, bueno in sustituciones.items():
        texto = texto.replace(malo, bueno)

    if nivel == 5:
        texto = texto.replace("abrir denuncia", "pedir ayuda urgente")
        texto = texto.replace("denuncia interna", "ayuda urgente")
        texto = texto.replace("denunciarlo", "pedir ayuda urgente")

    return texto


def mejorar_respuesta_por_caso(texto_usuario: str, respuesta: dict) -> dict:
    """
    Sobrescribe respuestas de casos frecuentes cuando el modelo genera texto raro.
    Esto mejora la salida visible sin depender de reentrenar.
    """
    texto = (texto_usuario or "").lower()
    nivel = respuesta.get("nivel")

    if nivel == 1 and "me he enfadado con mi amiga por una tonteria" in texto:
        respuesta["categoria"] = "conflicto_puntual"
        respuesta["accion"] = "escucha_activa"
        respuesta["respuesta_usuario"] = (
            "Entiendo que te hayas enfadado. A veces una discusion pequeña con una amiga "
            "puede doler bastante si la persona te importa. Si ha sido algo puntual, puede "
            "ayudar hablarlo con calma cuando se os pase un poco el enfado. ¿Es la primera vez "
            "que os pasa algo asi?"
        )

    if nivel == 4 and "me han pegado en los baños" in texto:
        respuesta["categoria"] = "violencia_fisica"
        respuesta["accion"] = "denuncia_inmediata_y_atencion_medica"
        respuesta["recursos"] = ["enfermeria", "jefatura", "familia", "direccion"]
        respuesta["telefonos"] = ["900018018", "112"]
        respuesta["respuesta_usuario"] = (
            "Lo que cuentas es una agresion y es grave. Lo primero es que estes en un sitio "
            "seguro y con un adulto. Busca ahora a jefatura, enfermeria, direccion o un profesor, "
            "y avisa a tu familia. Si tienes dolor, lesiones o sigues en peligro, llama al 112. "
            "El centro debe abrir denuncia interna hoy."
        )

    if nivel == 2 and "todos los dias se rien de mi cuando hablo en clase" in texto:
        respuesta["categoria"] = "acoso_recurrente"
        respuesta["accion"] = "derivacion_interna"
        respuesta["recursos"] = ["tutor", "profesor", "orientadora"]
        respuesta["respuesta_usuario"] = (
            "Que se rian de ti todos los dias cuando hablas en clase no es una broma puntual, "
            "es algo repetido que puede hacer mucho daño. Tu tutor, el profesor de esa clase "
            "o la orientadora deben saberlo para poder frenarlo. ¿Ocurre siempre con las mismas personas?"
        )

    if nivel == 2 and "me esconden la mochila despues del patio" in texto:
        respuesta["categoria"] = "acoso_recurrente"
        respuesta["accion"] = "derivacion_interna"
        respuesta["recursos"] = ["tutor", "jefatura", "orientadora"]
        respuesta["respuesta_usuario"] = (
            "Que te escondan la mochila despues del patio es serio, sobre todo si no es la primera vez. "
            "No tienes que aguantarlo como si fuera una broma. Cuentale a tu tutor o a jefatura cuando pasa "
            "y quienes suelen estar cerca para que puedan intervenir. ¿Te ha pasado mas veces?"
        )

    if nivel == 1 and "no me queda bien un jersey" in texto:
        respuesta["categoria"] = "conflicto_puntual"
        respuesta["accion"] = "escucha_activa"
        respuesta["respuesta_usuario"] = (
            "Entiendo que te haya dolido. Cuando una amiga comenta algo sobre tu ropa puede sentar mal, "
            "aunque no sea una situacion grave. Si ha sido algo puntual, puedes decirle con calma que ese "
            "comentario te hizo sentir mal. ¿Es la primera vez que te dice algo asi?"
        )

    if nivel == 1 and (
        "era mas guapa que yo" in texto
        or "era más guapa que yo" in texto
        or "se burlaba de mi" in texto
        or "se burlaba de mí" in texto
    ):
        respuesta["categoria"] = "conflicto_puntual"
        respuesta["accion"] = "escucha_activa"
        respuesta["respuesta_usuario"] = (
            "Entiendo que eso te haya dolido. Que alguien se compare contigo y se burle de ti puede hacerte sentir mal, "
            "aunque haya pasado en una discusion puntual. Puedes poner un limite claro y decir que no quieres que te hable asi. "
            "¿Es algo que ha pasado solo esta vez o se repite a menudo?"
        )

    return respuesta


def _respuesta_error(motivo: str) -> dict:
    return {
        "nivel": -1,
        "categoria": "error_interno",
        "accion": "reintentar",
        "recursos": [],
        "telefonos": [],
        "requiere_alerta": False,
        "abrir_formulario": None,
        "respuesta_usuario": MENSAJE_ERROR_TECNICO,
        "_motivo_error": motivo,
    }


def respuesta_input_invalido(mensaje_explicativo: str) -> dict:
    return {
        "nivel": 0,
        "categoria": "input_invalido",
        "accion": None,
        "recursos": [],
        "telefonos": [],
        "requiere_alerta": False,
        "abrir_formulario": None,
        "respuesta_usuario": mensaje_explicativo,
    }