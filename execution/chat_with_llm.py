#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests
import warnings

# Suppress warnings to ensure clean JSON output
warnings.filterwarnings("ignore")

# Intentar importar SDK de Google
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Intentar importar ChromaDB para memoria a largo plazo
try:
    import chromadb
except ImportError:
    chromadb = None

# Intentar cargar variables de entorno si python-dotenv está instalado
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(usecwd=True))
except ImportError:
    pass

# Importar gestor de base de datos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from db_manager import add_chat_message, get_chat_history, clear_chat_history
except ImportError:
    pass # Se manejará si falla al llamar las funciones

# Importar conector de OpenRouter
try:
    from chat_openrouter import chat_openrouter
except ImportError:
    pass # Se manejará si falla al llamar las funciones

def get_memory_context(query):
    """Busca contexto relevante en la memoria vectorial (ChromaDB)."""
    if not chromadb:
        print("⚠️  [RAG] ChromaDB no instalado o no importado.", file=sys.stderr)
        return None
        
    try:
        # Ruta a la base de datos (mismo path que save_memory.py)
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "chroma_db")
        
        if not os.path.exists(db_path):
            print(f"⚠️  [RAG] No se encontró base de datos en: {db_path}", file=sys.stderr)
            return None

        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(name='agent_memory')
        
        results = collection.query(
            query_texts=[query],
            n_results=3 # Recuperar los 3 recuerdos más relevantes
        )
        
        documents = results.get('documents', [[]])[0]
        if documents:
            # Deduplicar resultados preservando el orden
            seen = set()
            unique_docs = []
            for doc in documents:
                if doc not in seen:
                    unique_docs.append(doc)
                    seen.add(doc)
            
            preview = unique_docs[0][:60] + "..." if len(unique_docs[0]) > 60 else unique_docs[0]
            print(f"🧠 [RAG] Contexto inyectado ({len(unique_docs)} items): '{preview}'", file=sys.stderr)
            return "\n".join([f"- {doc}" for doc in unique_docs])
        else:
            print("🧠 [RAG] No se encontraron recuerdos relevantes para esta consulta.", file=sys.stderr)
    except Exception as e:
        print(f"❌ [RAG] Error al consultar memoria: {e}", file=sys.stderr)
    return None

def chat_openai(messages, model="gpt-4o-mini", system_instruction=None):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "Falta OPENAI_API_KEY en .env"}

    sys_msg = system_instruction or "Eres un asistente de IA útil actuando como la capa de Orquestación en una arquitectura de 3 capas."
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_msg}
        ] + messages,
        "temperature": 0.7
    }

    try:
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        return {"content": result['choices'][0]['message']['content']}
    except Exception as e:
        return {"error": str(e)}


def chat_anthropic(messages, model="claude-3-5-sonnet-20240620", system_instruction=None):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "Falta ANTHROPIC_API_KEY en .env"}

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    sys_msg = system_instruction or "Eres un asistente de IA útil actuando como la capa de Orquestación en una arquitectura de 3 capas."
    data = {
        "model": model,
        "max_tokens": 1024,
        "messages": messages,
        "system": sys_msg
    }

    try:
        resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        return {"content": result['content'][0]['text']}
    except Exception as e:
        return {"error": str(e)}

def chat_groq(messages, model="llama-3.3-70b-versatile", system_instruction=None):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "Falta GROQ_API_KEY en .env"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Sanitizar mensajes para evitar errores de formato (ej. campos extra o nulos)
    clean_messages = []
    for m in messages:
        clean_messages.append({
            "role": m.get("role", "user"),
            "content": str(m.get("content", ""))
        })

    sys_msg = system_instruction or "Eres un asistente de IA útil (Llama 3 en Groq) actuando como la capa de Orquestación. Si en el historial ves que te llamaste 'Gemini', ignóralo; ahora eres Llama 3."
    # Groq usa un endpoint compatible con OpenAI
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_msg}
        ] + clean_messages,
        "temperature": 0.7
    }

    try:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
        
        if not resp.ok:
            return {"error": f"Groq API Error ({resp.status_code}): {resp.text}"}
            
        result = resp.json()
        return {"content": result['choices'][0]['message']['content']}
    except Exception as e:
        return {"error": str(e)}

def chat_gemini(messages, model="gemini-flash-latest", system_instruction=None):
    if not genai:
        return {"error": "Librería 'google-generativeai' no instalada. Ejecuta: pip install -r requirements.txt"}

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"error": "Falta GOOGLE_API_KEY en .env"}

    try:
        genai.configure(api_key=api_key)

        # Preparar historial y system instruction
        sys_msg = system_instruction or "Eres Gemini, un modelo de IA de Google, actuando como la capa de Orquestación en una arquitectura de 3 capas. Identifícate siempre como Gemini/Google si te preguntan."
        history = []

        for msg in messages:
            if msg["role"] == "system":
                # Si se pasa una instrucción de sistema en los mensajes, tiene prioridad.
                sys_msg = msg["content"]
            elif msg["role"] == "user":
                history.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                history.append({"role": "model", "parts": [msg["content"]]})

        # Extraer el último mensaje del usuario para enviarlo (el SDK maneja el historial aparte)
        if not history or history[-1]["role"] != "user":
            return {"error": "El historial debe terminar con un mensaje del usuario."}

        last_message = history.pop()

        # Estrategia de Fallback: Intentar modelos alternativos si el principal falla
        models_to_try = [model]
        # Lista de modelos seguros para probar en orden si el principal falla
        fallbacks = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-pro-latest"]
        for fb in fallbacks:
            if fb != model:
                models_to_try.append(fb)

        last_error = None
        for target_model in models_to_try:
            try:
                model_instance = genai.GenerativeModel(model_name=target_model, system_instruction=sys_msg)
                chat = model_instance.start_chat(history=history)
                response = chat.send_message(last_message["parts"][0])
                return {"content": response.text}
            except Exception as e:
                print(f"⚠️  Advertencia: Falló {target_model} ({e}). Intentando siguiente...", file=sys.stderr)
                last_error = e
                continue

        return {"error": f"Todos los modelos fallaron. Último error: {str(last_error)}"}

    except Exception as e:
        return {"error": str(e)}


def main():
    """
    Orquestador principal para la comunicación con LLMs.
    
    Realiza las siguientes tareas críticas:
    1. Gestión de Memoria (RAG): Consulta ChromaDB para inyectar recuerdos relevantes.
    2. Gestión de Historial: Recupera los últimos mensajes de la base de datos SQLite.
    3. Optimización de Contexto:
       - Soft Cap (>12 mensajes): Comprime el historial manteniendo el inicio y el final de la charla
         para evitar el agotamiento de la ventana de contexto.
       - Hard Cap (>30,000 chars): Realiza una poda de emergencia si el volumen de texto es excesivo
         (ej. logs o netlists masivas).
    4. Estrategia de Fallback: Intenta múltiples proveedores (Groq, OpenRouter, Gemini, OpenAI) 
       en orden de prioridad si ocurren fallos de red o cuotas agotadas.
    
    Args:
        --prompt (str): Mensaje del usuario o instrucción de la directiva.
    """
    parser = argparse.ArgumentParser(description="Enviar un prompt a un LLM.")
    parser.add_argument("--prompt", required=True, help="El mensaje para el LLM.")
    parser.add_argument("--provider", choices=["openai", "anthropic", "gemini", "groq", "openrouter"], help="Proveedor de IA.")
    parser.add_argument("--memory-query", help="Texto específico para buscar en memoria (si es diferente al prompt).")
    parser.add_argument("--memory-only", action="store_true", help="Solo consulta la memoria y devuelve el resultado directo sin llamar al LLM.")
    parser.add_argument("--no-rag", action="store_true", help="Desactiva la búsqueda en memoria (RAG).")
    parser.add_argument("--system", help="Instrucción del sistema (personalidad).")
    args = parser.parse_args()

    # --- MODO MEMORY-ONLY ---
    if args.memory_only:
        memory_context = get_memory_context(args.prompt)
        if memory_context:
            # Si se encuentra algo, se devuelve directamente formateado.
            result = {"content": f"🧠 Según mi memoria:\n\n{memory_context}"}
        else:
            # Si no, se devuelve un error especial para que el orquestador sepa que debe continuar.
            result = {"error": "no_memory_found"}
        print(json.dumps(result))
        return

    # Gestión de historial
    if args.prompt.strip().lower() == "/clear":
        clear_chat_history()
        print(json.dumps({"content": "Historial de conversación borrado."}))
        return

    add_chat_message("user", args.prompt)
    raw_history = get_chat_history(limit=20) 

    # --- GESTIÓN DINÁMICA DE CONTEXTO ---
    soft_cap = int(os.getenv("CONTEXT_SOFT_CAP_MESSAGES", "12"))
    hard_cap = int(os.getenv("CONTEXT_HARD_CAP_CHARS", "30000"))

    # Si el historial es muy largo, comprimimos los mensajes intermedios para ahorrar ventana
    if len(raw_history) > soft_cap:
        print(f"✂️  [Context] Comprimiendo historial ({len(raw_history)} mensajes)...", file=sys.stderr)
        # Mantenemos los 2 primeros (contexto inicial), los últimos 5 (flujo actual) 
        # y el resto debería idealmente resumirse. Aquí hacemos un truncado inteligente.
        history = raw_history[:2] + [{"role": "system", "content": "... [Historial antiguo omitido para optimizar contexto] ..."}] + raw_history[-8:]
    else:
        history = raw_history

    # Verificación de tamaño aproximado (evitar prompts masivos)
    total_chars = sum(len(str(m.get('content', ''))) for m in history)
    if total_chars > hard_cap: # Umbral de seguridad aproximado
        print(f"⚠️  [Context] Prompt muy largo ({total_chars} chars). Aplicando poda de emergencia.", file=sys.stderr)
        # Si el prompt es demasiado grande, reducimos agresivamente el historial
        history = [history[0]] + history[-3:] 

    # Creamos una copia de los mensajes para enviar al LLM con el contexto inyectado,
    # pero SIN ensuciar el historial guardado en disco.
    messages_for_llm = [dict(msg) for msg in history] # Deep copy simple

    # --- RAG: Inyección de Memoria (si no está desactivado) ---
    if not args.no_rag:
        # Si se proporciona --memory-query, usarla para la búsqueda. Si no, usar el prompt completo.
        query_for_memory = args.memory_query if args.memory_query else args.prompt
        
        if args.memory_query:
            print(f"🧠 [RAG] Usando query optimizada: '{query_for_memory}'", file=sys.stderr)

        memory_context = get_memory_context(query_for_memory)
        if memory_context:
            # Inyectamos el contexto en el último mensaje del usuario
            last_msg = messages_for_llm[-1]
            last_msg['content'] = f"""Usa el siguiente CONTEXTO DE MEMORIA solo si es directamente relevante para la PREGUNTA DEL USUARIO. Si no es relevante, ignóralo por completo.

CONTEXTO DE MEMORIA (Recuerdos relevantes):
{memory_context}

---
PREGUNTA DEL USUARIO:
{args.prompt}"""

    # Definir lista de proveedores a intentar en orden de prioridad
    providers_to_try = []
    
    if args.provider:
        # Si el usuario fuerza uno, solo intentamos ese
        providers_to_try.append(args.provider)
    else:
        # Orden de preferencia: Groq (Rápido) -> OpenRouter (Potente) -> Gemini (Backup robusto) -> Otros
        if os.getenv("GROQ_API_KEY") and os.getenv("GROQ_API_KEY").strip():
            providers_to_try.append("groq")
        if os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_API_KEY").strip():
            providers_to_try.append("openrouter")
        if os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_API_KEY").strip():
            providers_to_try.append("gemini")
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY").strip():
            providers_to_try.append("openai")
        if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY").strip():
            providers_to_try.append("anthropic")
            
    if not providers_to_try:
        print(json.dumps({"error": "No hay API Keys configuradas en .env"}))
        return

    result = {}
    for provider in providers_to_try:
        try:
            if provider == "openai":
                result = chat_openai(messages_for_llm, system_instruction=args.system)
            elif provider == "anthropic":
                result = chat_anthropic(messages_for_llm, system_instruction=args.system)
            elif provider == "groq":
                result = chat_groq(messages_for_llm, system_instruction=args.system)
            elif provider == "gemini":
                result = chat_gemini(messages_for_llm, system_instruction=args.system)
            elif provider == "openrouter":
                try:
                    result = chat_openrouter(messages_for_llm, system_instruction=args.system)
                except NameError:
                    result = {"error": "El proveedor 'openrouter' no está disponible (no se pudo importar chat_openrouter.py)."}
            
            # Si tuvimos éxito (hay contenido y no error), salimos del bucle
            if "content" in result and "error" not in result:
                print(f"🤖 [LLM] Respuesta generada por: {provider.upper()}", file=sys.stderr)
                break
            
            # Si falló, logueamos en stderr (para no ensuciar el JSON de stdout) y seguimos
            error_msg = result.get("error", "Error desconocido")
            print(f"⚠️ Proveedor '{provider}' falló: {error_msg}. Intentando siguiente...", file=sys.stderr)
            
        except Exception as e:
            print(f"⚠️ Excepción crítica en '{provider}': {e}. Intentando siguiente...", file=sys.stderr)
            result = {"error": str(e)}

    if "content" in result:
        add_chat_message("assistant", result["content"])

    # Salida en JSON para que el orquestador la consuma
    print(json.dumps(result))


if __name__ == "__main__":
    main()
