#!/usr/bin/env python3
import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY no encontrada en .env")
        sys.exit(1)

    genai.configure(api_key=api_key)
    
    print("🔍 Consultando API de Google para listar modelos disponibles...")
    
    try:
        for m in genai.list_models():
            # Compatibilidad con diferentes versiones del SDK
            methods = m.supported_generation_methods
            # Si methods contiene objetos, extraer nombres. Si son strings, usar tal cual.
            if methods and not isinstance(methods[0], str):
                methods = [method.name for method in methods]
            
            if 'generateContent' in methods:
                print(f"✅ {m.name}")
            
    except Exception as e:
        print(f"❌ Error al listar modelos: {e}")

if __name__ == "__main__":
    main()