#!/usr/bin/env python3
import os
import json
import requests
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

def chat_openrouter(messages, model="anthropic/claude-3.5-sonnet", system_instruction=None):
    """
    Envía mensajes a la API de OpenRouter.
    
    Args:
        messages (list): Lista de diccionarios con roles y contenido.
        model (str): ID del modelo en OpenRouter (ej. 'anthropic/claude-3.5-sonnet').
        system_instruction (str, optional): Instrucción de sistema.
    
    Returns:
        dict: {'content': str} o {'error': str}
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {"error": "Falta la variable OPENROUTER_API_KEY en el archivo .env"}

    # OpenRouter es compatible con la API de OpenAI, pero usamos requests directo
    # para no depender de librerías específicas y controlar los headers extra.
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # OpenRouter recomienda estos headers para identificar tu app en sus rankings
        "HTTP-Referer": "https://github.com/cero-etage/Agente-IA-CIRCUITO-IMPRESO",
        "X-Title": "Agente IA Circuito Impreso"
    }

    sys_msg = system_instruction or "Eres un asistente de IA útil actuando como la capa de Orquestación, accediendo a través de OpenRouter."
    
    # OpenRouter es compatible con la API de OpenAI, así que podemos inyectar el system prompt
    final_messages = [
        {"role": "system", "content": sys_msg}
    ] + messages

    payload = {
        "model": model,
        "messages": final_messages,
        "temperature": 0.2, # Bajo para tareas de ingeniería/precisión
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
        
        if response.status_code != 200:
            return {"error": f"Error {response.status_code}: {response.text}"}
            
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            return {"content": clean_response(data["choices"][0]["message"]["content"])}
        else:
            return {"error": "OpenRouter devolvió una respuesta vacía."}

    except Exception as e:
        return {"error": f"Excepción de conexión: {str(e)}"}

if __name__ == "__main__":
    test_msg = [{"role": "user", "content": "Responde solo con: Conexión Exitosa"}]
    print(chat_openrouter(test_msg, model="anthropic/claude-3.5-sonnet"))