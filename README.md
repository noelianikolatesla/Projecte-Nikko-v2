# Projecte Nikko: Asistente Conversacional con IA y Voz

![Estado](https://img.shields.io/badge/Estado-En_Desarrollo-yellow)
![Stack](https://img.shields.io/badge/Stack-MERN%20%2B%20AWS-orange)
![AWS](https://img.shields.io/badge/AWS-Bedrock%20%7C%20Polly%20%7C%20Transcribe-232F3E)

**Nikko** es una aplicación web interactiva diseñada para ofrecer un asistente conversacional empático, orientado a la escucha activa, el apoyo emocional y la prevención del acoso escolar (bullying).

El sistema permite al usuario interactuar mediante **texto o voz**, analizando la gravedad de la situación en tiempo real y ofreciendo respuestas adaptadas mediante Inteligencia Artificial Generativa.

---

## Descripción del Proyecto

Nikko no pretende sustituir la ayuda humana, sino servir como un primer apoyo cercano y comprensible. Combina tecnologías web modernas con servicios Cloud de AWS para crear una experiencia fluida:

1.  **Escucha:** Convierte la voz del niño a texto (STT).
2.  **Procesa:** Analiza el sentimiento y gravedad con IA (Bedrock).
3.  **Responde:** Genera una respuesta empática y la convierte a audio (TTS).

### Funcionalidades Clave
* **Chat en tiempo real:** Interfaz accesible y segura.
* **Entrada/Salida por Voz:** Integración bidireccional de audio.
* **Análisis de Gravedad:** Clasificación automática de riesgos (Leve, Moderado, Grave).
* **Guardrails & Seguridad:** Filtros de contenido para garantizar un entorno seguro.
* **Protocolos de Emergencia:** Detección de peligro vital y derivación a recursos oficiales (Teléfono 900 018 018).

---

## Arquitectura del Sistema

El proyecto sigue una arquitectura **desacoplada** (Frontend-Backend) integrada con servicios de AWS.

```mermaid
graph TD
    User((Usuario)) -->|Voz/Texto| Frontend[React Frontend]
    Frontend -->|HTTP JSON/Multipart| Backend[Node.js + Express]
    Backend -->|Subida Audio| S3[AWS S3]
    S3 -->|Input Audio| Transcribe[AWS Transcribe]
    Transcribe -->|Texto| Backend
    Backend -->|Contexto + Texto| Bedrock[AWS Bedrock - IA]
    Bedrock -->|Respuesta Texto| Polly[AWS Polly - TTS]
    Polly -->|Audio MP3| Backend
    Backend -->|Respuesta + Audio| Frontend
