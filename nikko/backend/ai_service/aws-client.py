import os
import boto3
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# 1. Cargar configuración (AWS Academy necesita Session Token)
load_dotenv()

app = FastAPI(title="Nikko AI Gateway")

# 2. Configurar el cliente de SageMaker
# Importante: En SageMaker real, el servicio se llama 'sagemaker-runtime'
sm_client = boto3.client(
    'sagemaker-runtime',
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN") # Clave en entornos de estudiante
)

class Query(BaseModel):
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 500

@app.post("/v1/chat")
async def chat_with_nikko(data: Query):
    endpoint_name = os.getenv("SAGEMAKER_ENDPOINT_NAME")
    
    # El formato del payload depende de cómo configures el contenedor en SageMaker
    # Generalmente para modelos tipo Llama/GGUF se usa este esquema:
    payload = {
        "inputs": data.prompt,
        "parameters": {
            "temperature": data.temperature,
            "max_new_tokens": data.max_tokens,
            "stop": ["User:", "\n\n"]
        }
    }

    try:
        response = sm_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        
        result = json.loads(response['Body'].read().decode())
        return {"status": "success", "data": result}

    except Exception as e:
        print(f"Error llamando a SageMaker: {e}")
        raise HTTPException(status_code=500, detail="Error en la conexión con el modelo")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)