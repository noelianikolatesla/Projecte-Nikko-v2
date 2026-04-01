# 1. Usamos una imagen ligera de Python
FROM python:3.11-slim

# 2. Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiamos el archivo de requisitos primero (optimiza la caché de Docker)
COPY requirements.txt .

# 4. Instalamos las librerías necesarias
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos el resto del código (tu main.py adaptado)
COPY . .

# 6. Exponemos el puerto que usa FastAPI
EXPOSE 8000

# 7. Comando para arrancar la API con Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]