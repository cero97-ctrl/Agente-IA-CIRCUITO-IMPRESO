#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

ENV_NAME="pcb_env"

echo "🚀 Iniciando configuración del entorno para el Bot de CNC..."

# 1. Verificar Conda
if ! command -v conda &> /dev/null; then
    echo "❌ Error: Conda no está instalado o no está en el PATH."
    exit 1
fi

# 3. Crear Entorno
echo "📦 Creando entorno Conda: $ENV_NAME..."
# Usamos || true para que no falle si el entorno ya existe
conda create --name $ENV_NAME python=3.10 -y || echo "⚠️  El entorno ya existe, continuando..."

# 4. Activar Entorno (Truco para scripts bash)
echo "🔌 Activando entorno..."
eval "$(conda shell.bash hook)"
conda activate $ENV_NAME

# 5. Instalar Dependencias
echo "⬇️  Instalando dependencias..."
echo "   (Estas son las librerías para el 'orquestador' del bot)"
pip install -r requirements.txt

echo ""
echo "🐳 NOTA: Las herramientas de ejecución como KiCad y FreeCAD no se instalan aquí."
echo "   Se instalan en una imagen Docker aislada para seguridad y estabilidad."
echo "   Si aún no lo has hecho, construye la imagen con: python3 execution/build_sandbox.py"
echo ""
echo "✅ ¡Instalación completada!"
echo "⚠️  IMPORTANTE: No olvides rellenar el archivo .env con tu TOKEN y CHAT_ID de Telegram."
echo "👉 Para activar el entorno en el futuro, usa: 'conda activate $ENV_NAME'"
echo "🤖 Para iniciar el bot, usa: 'python execution/listen_telegram.py'"