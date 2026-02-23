import os
import sys
from dotenv import load_dotenv
from execution.bot_manager import run_bot

# Cargar variables de entorno desde el archivo .env
load_dotenv()

if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        print("❌ Error: No se encontró la variable TELEGRAM_TOKEN en el archivo .env")
    else:
        # Delegamos la ejecución al módulo correspondiente
        run_bot(TOKEN)