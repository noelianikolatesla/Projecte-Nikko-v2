#!/bin/bash

# Función que se ejecutará al pulsar Ctrl+C
function finalizar() {
    echo ""
    echo "🛑 Interrupción detectada (Ctrl+C)."
    echo "🧹 Eliminando imágenes..."
    
    docker compose down --rmi all

    echo "✅ Entorno detenido y limpio. ¡Hasta luego!"
    exit 0
}

trap finalizar SIGINT

echo "🤖 Iniciando Nikko..."
cd "$(dirname "$0")"

echo "📦 Construyendo y levantando contenedores..."
docker compose up -d --build

echo ""
echo "✅ ¡Todo listo!"
echo "----------------------------------------"
echo "🌐 Frontend: http://localhost:8080"
echo "⚙️ Backend:  http://localhost:3001"
echo "----------------------------------------"
echo "⚠️  Nota: Al presionar Ctrl+C, se detendrá todo y SE BORRARÁN LAS IMÁGENES."
echo "📜 Mostrando logs..."

docker compose logs -f