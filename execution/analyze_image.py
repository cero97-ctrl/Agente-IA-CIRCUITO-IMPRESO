#!/usr/bin/env python3
import argparse
import os
import sys
import json
import warnings

warnings.filterwarnings("ignore")

# Intentar importar SDK de Google y Pillow
try:
    import google.generativeai as genai
    import PIL.Image
except ImportError:
    print(json.dumps({"status": "error", "message": "Faltan librerías. Ejecuta: pip install google-generativeai pillow"}), file=sys.stderr)
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

def clean_response(text):
    """Limpia bloques de código markdown y espacios en blanco."""
    if not text:
        return ""
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    return text

def main():
    parser = argparse.ArgumentParser(description="Analizar una imagen usando Gemini Vision.")
    parser.add_argument("--image", required=True, help="Ruta local de la imagen.")
    parser.add_argument("--prompt", default="Describe esta imagen en detalle.", help="Instrucción para el modelo.")
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print(json.dumps({"status": "error", "message": "Falta GOOGLE_API_KEY en .env"}))
        sys.exit(1)

    if not os.path.exists(args.image):
        print(json.dumps({"status": "error", "message": f"Imagen no encontrada: {args.image}"}))
        sys.exit(1)

    try:
        genai.configure(api_key=api_key)
        
        img = PIL.Image.open(args.image)
        
        # Estrategia de Fallback: Probar varios modelos de visión si el principal falla
        models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
        
        response = None
        last_error = None

        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                # Generar contenido enviando texto + imagen
                response = model.generate_content([args.prompt, img])
                if response:
                    break
            except Exception as e:
                last_error = e
                continue
        
        if not response:
            raise Exception(f"Todos los modelos de visión fallaron. Último error: {last_error}")
        
        print(json.dumps({
            "status": "success",
            "description": clean_response(response.text)
        }))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()