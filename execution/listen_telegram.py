#!/usr/bin/env python3
import time
import subprocess
import json
import sys
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_users.txt")
REMINDERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_reminders.json")
PERSONA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_persona.txt")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_config.json")

PERSONAS = {
    "default": "Eres un asistente de IA creado por el Prof. César Rodríguez con Gemini Code Assist. Tu propósito es apoyar a estudiantes de informática y al equipo de investigación 'Tecnología Venezolana'. Resides en una PC con GNU/Linux. Responde de forma amable, clara y concisa, y si te preguntan quién eres, menciona estos detalles.",
    "serio": "Eres un asistente corporativo, extremadamente formal y serio. No usas emojis ni coloquialismos. Vas directo al grano.",
    "sarcastico": "Eres un asistente con humor negro y sarcasmo. Te burlas sutilmente de las preguntas obvias, pero das la respuesta correcta al final.",
    "profesor": "Eres un profesor universitario paciente y didáctico. Explicas todo con ejemplos, analogías y un tono educativo.",
    "pirata": "¡Arrr! Eres un pirata informático de los siete mares. Usas jerga marinera y pirata en todas tus respuestas.",
    "frances": "Tu es un assistant IA créé par le Prof. César Rodríguez. Tu résides sur un PC GNU/Linux. Réponds toujours en français, de manière gentille, claire et concise."
}

def get_current_persona():
    if os.path.exists(PERSONA_FILE):
        with open(PERSONA_FILE, 'r') as f:
            return f.read().strip()
    return PERSONAS["default"]

def set_persona(persona_key):
    with open(PERSONA_FILE, 'w') as f:
        f.write(PERSONAS.get(persona_key, PERSONAS["default"]))

def save_user(chat_id):
    """Registra el ID del usuario para futuros broadcasts."""
    if not chat_id: return
    users = set()
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = set(f.read().splitlines())
    if str(chat_id) not in users:
        with open(USERS_FILE, 'a') as f:
            f.write(f"{chat_id}\n")

def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def save_reminders(reminders):
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders, f)

def check_reminders():
    reminders = load_reminders()
    if not reminders: return

    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M")
    today_str = now.strftime("%Y-%m-%d")
    updated = False

    for r in reminders:
        # Si coincide la hora y NO se ha enviado hoy
        if r.get('time') == current_time and r.get('last_sent') != today_str:
            print(f"   ⏰ Enviando recordatorio a {r['chat_id']}: {r['message']}")
            run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏰ *RECORDATORIO:*\n\n{r['message']}", "--chat-id", r['chat_id']])
            r['last_sent'] = today_str
            updated = True
    
    if updated:
        save_reminders(reminders)

def run_tool(script, args):
    """Ejecuta una herramienta del framework y devuelve su salida JSON."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
    cmd = [sys.executable, script_path] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        # Mostrar stderr para depuración (RAG, errores, etc.)
        if result.stderr:
            print(f"   🛠️  [LOG {script}]: {result.stderr.strip()}")
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": f"La salida de '{script}' no es un JSON válido.",
                "details": result.stdout[:500]
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Excepción crítica al ejecutar '{script}'.",
            "details": str(e)
        }

def main():
    print("📡 Escuchando Telegram... (Presiona Ctrl+C para detener)")
    print("   El agente responderá a cualquier mensaje que le envíes.")
    
    last_health_check = time.time()
    HEALTH_CHECK_INTERVAL = 300  # Verificar cada 5 minutos

    try:
        while True:
            # 1. Consultar nuevos mensajes
            response = run_tool("telegram_tool.py", ["--action", "check"])
            
            if response and response.get("status") == "error":
                print(f"⚠️ Error en Telegram: {response.get('message')}")
                time.sleep(5) # Esperar un poco más si hubo error para no saturar

            if response and response.get("status") == "success":
                messages = response.get("messages", [])
                for msg in messages:
                    # Parsear formato "CHAT_ID|MENSAJE"
                    if "|" in msg:
                        sender_id, content = msg.split("|", 1)
                    else:
                        sender_id = None
                        content = msg

                    save_user(sender_id)
                    print(f"\n📩 Mensaje recibido de {sender_id}: '{content}'")
                    
                    reply_text = ""
                    msg = content # Usamos el contenido limpio para la lógica
                    is_voice_interaction = False # Bandera para saber si responder con audio
                    voice_lang_short = "es" # Default language for TTS
                    
                    # --- COMANDOS ESPECIALES (Capa 3: Ejecución) ---
                    
                    # 1. DETECCIÓN DE FOTOS
                    if msg.startswith("__PHOTO__:"):
                        try:
                            parts = msg.replace("__PHOTO__:", "").split("|||")
                            file_id = parts[0]
                            caption = parts[1] if len(parts) > 1 else "Describe esta imagen."
                            if not caption.strip(): caption = "Describe qué ves en esta imagen."
                            
                            print(f"   📸 Foto recibida. Descargando ID: {file_id}...")
                            
                            # Descargar
                            filename = f"photo_{int(time.time())}.jpg"
                            local_path = os.path.join(".tmp", filename)
                            run_tool("telegram_tool.py", ["--action", "download", "--file-id", file_id, "--dest", local_path])
                            
                            # DECISIÓN: ¿Analizar, G-Code o Gerber?
                            caption_lower = caption.lower()
                            
                            if "paquete" in caption_lower or "fabricar" in caption_lower or "zip" in caption_lower:
                                run_tool("telegram_tool.py", ["--action", "send", "--message", "🏭 Generando paquete completo de fabricación (Gerber + Drill)...", "--chat-id", sender_id])
                                
                                try:
                                    # 1. Generar Gerber
                                    with open("execution/img_to_gerber.py", "r") as f: script_gerber = f.read()
                                    inj_gerber = f"import sys\nsys.argv = ['img_to_gerber.py', '--image', '{filename}', '--output', '{filename}.gbr', '--size', '50']\n"
                                    res_gerber = run_tool("run_sandbox.py", ["--code", inj_gerber + script_gerber])
                                    
                                    # 2. Generar Drill
                                    with open("execution/img_to_drill.py", "r") as f: script_drill = f.read()
                                    inj_drill = f"import sys\nsys.argv = ['img_to_drill.py', '--image', '{filename}', '--output', '{filename}.drl', '--size', '50']\n"
                                    res_drill = run_tool("run_sandbox.py", ["--code", inj_drill + script_drill])
                                    
                                    # 3. Empaquetar en ZIP
                                    if res_gerber.get("status") == "success" and res_drill.get("status") == "success":
                                        zip_name = f"PCB_Pack_{int(time.time())}.zip"
                                        with open("execution/create_manufacturing_zip.py", "r") as f: script_zip = f.read()
                                        
                                        # Pasamos los nombres de los archivos generados
                                        files_args = f"'{filename}.gbr', '{filename}.drl'"
                                        inj_zip = f"import sys\nsys.argv = ['create_manufacturing_zip.py', '--files', {files_args}, '--output', '{zip_name}']\n"
                                        
                                        res_zip = run_tool("run_sandbox.py", ["--code", inj_zip + script_zip])
                                        
                                        if res_zip.get("status") == "success":
                                            reply_text = "✅ Paquete de fabricación listo. Contiene Gerber (Cobre) y Excellon (Taladros)."
                                            generated_zip = os.path.join(".tmp", zip_name)
                                            if os.path.exists(generated_zip):
                                                run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", generated_zip, "--chat-id", sender_id, "--caption", "📦 Manufacturing Pack (ZIP)"])
                                        else:
                                            reply_text = f"❌ Error al crear el ZIP: {res_zip.get('stderr')}"
                                    else:
                                        reply_text = "❌ Error en la generación de archivos intermedios (Gerber o Drill)."
                                        print(f"Debug Gerber: {res_gerber}")
                                        print(f"Debug Drill: {res_drill}")

                                except Exception as e:
                                    reply_text = f"❌ Error interno en el proceso de empaquetado: {e}"

                            elif "gerber" in caption_lower or "pcbway" in caption_lower or "jlcpcb" in caption_lower:
                                run_tool("telegram_tool.py", ["--action", "send", "--message", "🏭 Generando archivo Gerber (Top Copper) para fabricación industrial...", "--chat-id", sender_id])
                                
                                try:
                                    with open("execution/img_to_gerber.py", "r") as f:
                                        script_content = f.read()
                                    
                                    # Inyectamos argumentos: nombre de la foto y salida .gbr
                                    injection = f"import sys\nsys.argv = ['img_to_gerber.py', '--image', '{filename}', '--output', '{filename}.gbr', '--size', '50']\n"
                                    full_code = injection + script_content
                                    
                                    res_sandbox = run_tool("run_sandbox.py", ["--code", full_code])
                                    
                                    if res_sandbox and res_sandbox.get("status") == "success":
                                        reply_text = "✅ Archivo Gerber generado. Este archivo (.gbr) corresponde a la capa 'Top Copper' y es compatible con fabricantes como JLCPCB o PCBWay."
                                        generated_file = local_path + ".gbr"
                                        if os.path.exists(generated_file):
                                            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", generated_file, "--chat-id", sender_id, "--caption", "Gerber Top Copper"])
                                    else:
                                        err_msg = res_sandbox.get('stderr') or res_sandbox.get('message') or res_sandbox.get('details') or "Error desconocido"
                                        reply_text = f"❌ Error en conversión Gerber: {err_msg}"
                                except Exception as e:
                                    reply_text = f"❌ Error interno: {e}"

                            elif "taladro" in caption_lower or "drill" in caption_lower or "agujeros" in caption_lower:
                                run_tool("telegram_tool.py", ["--action", "send", "--message", "🔩 Detectando agujeros y generando archivo Excellon (.drl)...", "--chat-id", sender_id])
                                
                                try:
                                    with open("execution/img_to_drill.py", "r") as f:
                                        script_content = f.read()
                                    
                                    injection = f"import sys\nsys.argv = ['img_to_drill.py', '--image', '{filename}', '--output', '{filename}.drl', '--size', '50']\n"
                                    full_code = injection + script_content
                                    
                                    res_sandbox = run_tool("run_sandbox.py", ["--code", full_code])
                                    
                                    if res_sandbox and res_sandbox.get("status") == "success":
                                        reply_text = "✅ Archivo de Taladrado generado. Este archivo (.drl) contiene las coordenadas de los agujeros detectados."
                                        generated_file = local_path + ".drl"
                                        if os.path.exists(generated_file):
                                            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", generated_file, "--chat-id", sender_id, "--caption", "Excellon Drill File"])
                                    else:
                                        err_msg = res_sandbox.get('stderr') or res_sandbox.get('message') or "Error desconocido"
                                        reply_text = f"❌ Error detectando taladros: {err_msg}"
                                except Exception as e:
                                    reply_text = f"❌ Error interno: {e}"

                            elif "gcode" in caption_lower or "cnc" in caption_lower:
                                run_tool("telegram_tool.py", ["--action", "send", "--message", "⚙️ Convirtiendo imagen a G-Code...", "--chat-id", sender_id])
                                
                                # Ejecutar conversión en Sandbox
                                # Leemos el script local para inyectarlo en el contenedor
                                try:
                                    with open("execution/img_to_gcode.py", "r") as f:
                                        script_content = f.read()
                                    
                                    # Inyectamos argumentos: nombre de la foto (que está en /mnt/out/) y salida
                                    injection = f"import sys\nsys.argv = ['img_to_gcode.py', '--image', '{filename}', '--output', '{filename}.nc', '--size', '50']\n"
                                    full_code = injection + script_content
                                    
                                    res_sandbox = run_tool("run_sandbox.py", ["--code", full_code])
                                    
                                    # La lógica de respuesta genérica del sandbox (más abajo en el código) no aplica aquí
                                    # porque estamos dentro del bloque de fotos. Manejamos la respuesta manualmente:
                                    if res_sandbox and res_sandbox.get("status") == "success":
                                        # El script imprime la ruta del archivo generado
                                        reply_text = "✅ Conversión completada. Te envío el archivo G-Code y puedes visualizarlo con `/py execution/visualize_gcode.py ...`"
                                        # El archivo generado estará en .tmp/{filename}.nc
                                        generated_file = local_path + ".nc"
                                        if os.path.exists(generated_file):
                                            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", generated_file, "--chat-id", sender_id, "--caption", "G-Code generado desde imagen"])
                                    else:
                                        err_msg = res_sandbox.get('stderr') or res_sandbox.get('message') or res_sandbox.get('details') or "Error desconocido"
                                        reply_text = f"❌ Error en conversión: {err_msg}"
                                except Exception as e:
                                    reply_text = f"❌ Error interno: {e}"
                            
                            else:
                                # Analizar con IA (Comportamiento por defecto)
                                run_tool("telegram_tool.py", ["--action", "send", "--message", "👀 Analizando imagen...", "--chat-id", sender_id])
                                res = run_tool("analyze_image.py", ["--image", local_path, "--prompt", caption])
                                if res and res.get("status") == "success":
                                    reply_text = f"👁️ *Análisis Visual:*\n{res.get('description')}"
                                else:
                                    reply_text = f"❌ Error analizando imagen: {res.get('message')}"
                                
                        except Exception as e:
                            reply_text = f"❌ Error procesando foto: {e}"

                    # 1.2 DETECCIÓN DE DOCUMENTOS (PDF)
                    elif msg.startswith("__DOCUMENT__:"):
                        try:
                            parts = msg.replace("__DOCUMENT__:", "").split("|||")
                            file_id = parts[0]
                            file_name = parts[1]
                            caption = parts[2] if len(parts) > 2 else ""
                            
                            print(f"   📄 Documento recibido: {file_name}. Descargando...")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", f"📂 Recibí `{file_name}`. Leyendo contenido...", "--chat-id", sender_id])
                            
                            # Descargar a .tmp (que se monta en /mnt/out en el sandbox)
                            local_path = os.path.join(".tmp", file_name)
                            run_tool("telegram_tool.py", ["--action", "download", "--file-id", file_id, "--dest", local_path])
                            
                            # Extraer texto usando el Sandbox (ya tiene pypdf)
                            # Nota: .tmp está montado en /mnt/out dentro del contenedor
                            path_in_sandbox = f"/mnt/out/{file_name}"
                            
                            read_code = (
                                f"from pypdf import PdfReader; "
                                f"reader = PdfReader('{path_in_sandbox}'); "
                                f"print('\\n'.join([page.extract_text() for page in reader.pages]))"
                            )
                            
                            res_sandbox = run_tool("run_sandbox.py", ["--code", read_code])
                            
                            if res_sandbox and res_sandbox.get("status") == "success":
                                content = res_sandbox.get("stdout", "")
                                if len(content) > 15000:
                                    content = content[:15000] + "... (truncado)"
                                
                                if not content.strip():
                                    reply_text = "⚠️ El documento parece estar vacío o es una imagen escaneada sin texto (OCR no disponible en sandbox)."
                                else:
                                    # Analizar con LLM
                                    analysis_prompt = f"""Actúa como un Asistente Médico experto y empático. Analiza el siguiente informe médico proporcionado por el usuario.
                                    
CONTEXTO DEL USUARIO: {caption}

CONTENIDO DEL DOCUMENTO:
{content}

TAREA:
1. Resume los hallazgos principales.
2. Explica los términos técnicos en lenguaje sencillo para un paciente.
3. Si hay diagnósticos o tratamientos, explícalos brevemente.
4. IMPORTANTE: Termina con un disclaimer: "Nota: Soy una IA. Este análisis es informativo y no sustituye la opinión de un médico."
"""
                                    run_tool("telegram_tool.py", ["--action", "send", "--message", "🧠 Analizando informe médico...", "--chat-id", sender_id])
                                    
                                    llm_res = run_tool("chat_with_llm.py", ["--prompt", analysis_prompt])
                                    
                                    if llm_res and "content" in llm_res:
                                        reply_text = llm_res["content"]
                                    else:
                                        reply_text = "❌ Error al analizar el documento con la IA."
                            else:
                                err = res_sandbox.get("stderr") or res_sandbox.get("message")
                                reply_text = f"❌ Error leyendo el PDF: {err}"

                        except Exception as e:
                            reply_text = f"❌ Error procesando documento: {e}"

                    # 1.5 DETECCIÓN DE VOZ
                    elif msg.startswith("__VOICE__:"):
                        try:
                            is_voice_interaction = True
                            file_id = msg.replace("__VOICE__:", "")
                            print(f"   🎤 Nota de voz recibida. Descargando ID: {file_id}...")

                            run_tool("telegram_tool.py", ["--action", "send", "--message", "👂 Escuchando...", "--chat-id", sender_id])
                            
                            local_path = os.path.join(".tmp", f"voice_{int(time.time())}.ogg")
                            run_tool("telegram_tool.py", ["--action", "download", "--file-id", file_id, "--dest", local_path])
                            
                            # Transcribir
                            # Cargar idioma configurado (default es-ES)
                            config = load_config()
                            lang_code = config.get("voice_lang", "es-ES")
                            voice_lang_short = lang_code.split('-')[0] # 'es-ES' -> 'es'
                            
                            res = run_tool("transcribe_audio.py", ["--file", local_path, "--lang", lang_code])
                            if res and res.get("status") == "success":
                                text = res.get("text")
                                print(f"   📝 Transcripción: '{text}'")
                                # ¡Truco! Reemplazamos el mensaje de voz por su texto y dejamos que el flujo continúe
                                msg = text
                                run_tool("telegram_tool.py", ["--action", "send", "--message", f"🗣️ Dijiste: \"{text}\"", "--chat-id", sender_id])
                            else:
                                err_msg = res.get("message", "Error desconocido") if res else "Falló el script de transcripción"
                                reply_text = f"❌ No pude entender el audio. Detalle: {err_msg}"
                        except Exception as e:
                            reply_text = f"❌ Error procesando audio: {e}"

                    # 2. COMANDOS DE TEXTO
                    # (Nota: usamos 'if' aquí en lugar de 'elif' para que el texto transcrito de voz pueda entrar)
                    if msg.startswith("/investigar") or msg.startswith("/research"):
                        topic = msg.split(" ", 1)[1] if " " in msg else ""
                        if not topic:
                            reply_text = "⚠️ Uso: /investigar [tema]"
                        else:
                            print(f"   🔍 Ejecutando investigación sobre: {topic}")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", f"🕵️‍♂️ Investigando sobre '{topic}'... dame unos segundos.", "--chat-id", sender_id])
                            
                            # Ejecutar herramienta de research
                            res = run_tool("research_topic.py", ["--query", topic, "--output-file", ".tmp/tg_research.txt"])
                            
                            if res and res.get("status") == "success":
                                # Leer y resumir resultados
                                try:
                                    with open(".tmp/tg_research.txt", "r", encoding="utf-8") as f:
                                        data = f.read()
                                    print("   🧠 Resumiendo resultados...")
                                    
                                    # Prompt mejorado: pide al LLM que use su memoria (RAG) y los resultados de la búsqueda.
                                    summarization_prompt = f"""Considerando lo que ya sabes en tu memoria y los siguientes resultados de búsqueda sobre '{topic}', crea un resumen conciso para Telegram.

Resultados de Búsqueda:
---
{data}"""
                                    llm_res = run_tool("chat_with_llm.py", ["--prompt", summarization_prompt, "--memory-query", topic])
                                    
                                    if llm_res and "content" in llm_res:
                                        reply_text = llm_res["content"]
                                    elif llm_res and "error" in llm_res:
                                        reply_text = f"⚠️ Error del modelo: {llm_res['error']}"
                                    else:
                                        reply_text = "❌ No se pudo generar el resumen (Respuesta vacía o inválida)."
                                except Exception as e:
                                    reply_text = f"Error procesando resultados: {e}"
                            else:
                                reply_text = "❌ Error al ejecutar la herramienta de investigación."
                    
                    elif msg.startswith("/reporte") or msg.startswith("/report"):
                        topic = msg.split(" ", 1)[1] if " " in msg else ""
                        if not topic:
                            reply_text = "⚠️ Uso: /reporte [tema técnico o de ingeniería]"
                        else:
                            print(f"   ️ Generando reporte técnico sobre: {topic}")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", f"👷 Iniciando investigación técnica sobre '{topic}'... Esto tomará unos segundos.", "--chat-id", sender_id])
                            
                            # 1. Investigar (Search)
                            query = f"especificaciones técnicas tutoriales y documentación para {topic}"
                            res_search = run_tool("research_topic.py", ["--query", query, "--output-file", ".tmp/tech_research.txt"])
                            
                            if res_search and res_search.get("status") == "success":
                                try:
                                    with open(".tmp/tech_research.txt", "r", encoding="utf-8") as f:
                                        search_data = f.read()
                                    
                                    # 2. Generar Reporte (LLM)
                                    report_prompt = f"""Actúa como un Asistente de Ingeniería experto en Fabricación Digital y Electrónica.
Basado en los siguientes resultados de búsqueda, genera un REPORTE TÉCNICO DETALLADO en formato Markdown sobre '{topic}'.

Estructura sugerida:
1. 📋 Resumen Ejecutivo
2. ⚙️ Especificaciones Técnicas y Requisitos
3. 🛠️ Guía de Implementación / Paso a Paso
4. ⚠️ Posibles Problemas y Soluciones (Troubleshooting)
5. 📚 Referencias y Recursos Adicionales

RESULTADOS DE BÚSQUEDA:
{search_data}

IMPORTANTE:
 Usa un tono profesional, técnico y preciso.
 Enfócate en la practicidad y la implementación con herramientas libres (Open Source) si aplica.
"""
                                    run_tool("telegram_tool.py", ["--action", "send", "--message", "🧠 Analizando datos y redactando informe...", "--chat-id", sender_id])
                                    
                                    # Usamos --memory-query para que busque en memoria solo el tema, no el prompt entero
                                    llm_res = run_tool("chat_with_llm.py", ["--prompt", report_prompt, "--memory-query", topic])
                                    
                                    if llm_res and "content" in llm_res:
                                        report_content = llm_res["content"]
                                        
                                        # 3. Guardar en docs/
                                        safe_topic = "".join([c if c.isalnum() else "_" for c in topic])[:30]
                                        filename = f"Reporte_Medico_{safe_topic}.md"
                                        # Construir ruta absoluta a docs/
                                        docs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", filename)
                                        
                                        with open(docs_path, "w", encoding="utf-8") as f:
                                            f.write(report_content)
                                            
                                        reply_text = f"✅ *Reporte Generado Exitosamente*\n\nHe guardado el informe detallado en:\n`docs/{filename}`\n\nAquí tienes un resumen:\n\n" + report_content[:400] + "...\n\n_(Lee el archivo completo en tu carpeta docs)_"
                                    else:
                                        reply_text = "❌ Error al redactar el reporte con el modelo."
                                        
                                except Exception as e:
                                    reply_text = f"❌ Error procesando el reporte: {e}"
                            else:
                                reply_text = "❌ Error en la fase de investigación (Búsqueda)."

                    elif msg.startswith("/recordatorio") or msg.startswith("/remind"):
                        try:
                            parts = msg.split(" ", 2)
                            if len(parts) < 3:
                                reply_text = "⚠️ Uso: /recordatorio HH:MM Mensaje\nEj: `/recordatorio 08:00 Tomar antibiótico`"
                            else:
                                time_str = parts[1]
                                note = parts[2]
                                # Validar formato de hora
                                datetime.datetime.strptime(time_str, "%H:%M")
                                
                                reminders = load_reminders()
                                reminders.append({
                                    "chat_id": str(sender_id),
                                    "time": time_str,
                                    "message": note,
                                    "last_sent": ""
                                })
                                save_reminders(reminders)
                                reply_text = f"✅ Recordatorio configurado.\nTe avisaré todos los días a las {time_str}: '{note}'."
                        except ValueError:
                            reply_text = "❌ Hora inválida. Usa formato 24h (HH:MM), ej: 14:30."

                    elif msg.startswith("/borrar_recordatorios") or msg.startswith("/clear_reminders"):
                        reminders = load_reminders()
                        # Filtrar, manteniendo solo los recordatorios de OTROS usuarios
                        reminders_to_keep = [r for r in reminders if r.get('chat_id') != str(sender_id)]
                        if len(reminders) == len(reminders_to_keep):
                            reply_text = "🤔 No tienes recordatorios configurados para borrar."
                        else:
                            save_reminders(reminders_to_keep)
                            reply_text = "✅ Todos tus recordatorios han sido eliminados."

                    elif msg.startswith("/traducir") or msg.startswith("/translate"):
                        content = msg.split(" ", 1)[1].strip() if " " in msg else ""
                        if not content:
                            reply_text = "⚠️ Uso: /traducir [texto | nombre_archivo]"
                        else:
                            # Verificar si es un archivo local (docs o .tmp)
                            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                            docs_file = os.path.join(base_dir, "docs", content)
                            tmp_file = os.path.join(base_dir, ".tmp", content)
                            
                            target_file = None
                            if os.path.exists(docs_file): target_file = docs_file
                            elif os.path.exists(tmp_file): target_file = tmp_file
                            
                            if target_file:
                                print(f"   📄 Traduciendo archivo: {content}")
                                run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Traduciendo `{content}` al español...", "--chat-id", sender_id])
                                
                                res = run_tool("translate_text.py", ["--file", target_file, "--lang", "Español"])
                                
                                if res and res.get("status") == "success":
                                    out_path = res.get("file_path")
                                    run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", out_path, "--chat-id", sender_id, "--caption", "📄 Traducción al Español"])
                                    reply_text = "✅ Archivo traducido enviado."
                                else:
                                    err = res.get("message", "Error desconocido") if res else "Error en script"
                                    reply_text = f"❌ Error al traducir archivo: {err}"
                            else:
                                # Traducir texto plano
                                print(f"   🔤 Traduciendo texto...")
                                prompt = f"Traduce el siguiente texto al Español. Devuelve solo la traducción:\n\n{content}"
                                llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt])
                                if llm_res and "content" in llm_res:
                                    reply_text = f"🇪🇸 *Traducción:*\n\n{llm_res['content']}"
                                else:
                                    reply_text = "❌ Error al traducir texto."

                    elif msg.startswith("/idioma") or msg.startswith("/lang"):
                        parts = msg.split(" ")
                        if len(parts) < 2:
                            reply_text = "⚠️ Uso: /idioma [es/en]\nEj: `/idioma en` (para inglés)"
                        else:
                            lang_map = {"es": "es-ES", "en": "en-US", "fr": "fr-FR", "pt": "pt-BR"}
                            selection = parts[1].lower()
                            code = lang_map.get(selection, "es-ES")
                            config = load_config()
                            config["voice_lang"] = code
                            save_config(config)
                            reply_text = f"✅ Idioma de voz cambiado a: `{code}`.\nAhora te escucharé en ese idioma."

                    elif msg.startswith("/ayuda_cnc"):
                        manual_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "CNC.md")
                        if os.path.exists(manual_path):
                            print(f"   🛠️ Enviando documentación CNC a {sender_id}...")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", "📘 Aquí tienes la documentación sobre el flujo de trabajo CNC.", "--chat-id", sender_id])
                            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", manual_path, "--chat-id", sender_id, "--caption", "Documentación CNC (Markdown)"])
                        else:
                            reply_text = "⚠️ El archivo `docs/CNC.md` no se encuentra."

                    elif msg.startswith("/ingestar") or msg.startswith("/ingest"):
                        filename = msg.split(" ", 1)[1].strip() if " " in msg else ""
                        if not filename:
                            reply_text = "⚠️ Uso: /ingestar [nombre_archivo_en_docs]"
                        else:
                            print(f"   📥 Ingestando archivo: {filename}")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Procesando `{filename}` para RAG...", "--chat-id", sender_id])

                            # 1. Leer el archivo desde el Sandbox
                            path_in_container = f"/mnt/docs/{filename}"
                            
                            if filename.lower().endswith(".pdf"):
                                read_code = (
                                    f"from pypdf import PdfReader; "
                                    f"reader = PdfReader('{path_in_container}'); "
                                    f"print('\\n'.join([page.extract_text() for page in reader.pages]))"
                                )
                            else:
                                read_code = f"with open('{path_in_container}', 'r', encoding='utf-8') as f: print(f.read())"
                            
                            read_res = run_tool("run_sandbox.py", ["--code", read_code])

                            if read_res and read_res.get("status") == "success" and read_res.get("stdout"):
                                content = read_res.get("stdout")
                                if not content.strip():
                                    reply_text = "⚠️ El archivo parece estar vacío o no se pudo extraer texto."
                                else:
                                    # 2. Guardar en memoria
                                    # Prefijamos con el nombre del archivo para dar contexto al RAG
                                    full_text = f"Contenido del documento '{filename}':\n\n{content}"
                                    save_res = run_tool("save_memory.py", ["--text", full_text, "--category", "document_knowledge"])
                                    
                                    if save_res and save_res.get("status") == "success":
                                        reply_text = f"✅ Documento `{filename}` agregado a la memoria a largo plazo."
                                    else:
                                        reply_text = "❌ Error al guardar en memoria."
                            else:
                                error_details = read_res.get("stderr") or read_res.get("message", "No se pudo leer.")
                                reply_text = f"❌ Error leyendo `{filename}`: {error_details}"

                    elif msg.startswith("/resumir_archivo") or msg.startswith("/summarize_file"):
                        filename = msg.split(" ", 1)[1].strip() if " " in msg else ""
                        if not filename:
                            reply_text = "⚠️ Uso: /resumir_archivo [nombre_del_archivo_en_docs]"
                        else:
                            print(f"   📄 Resumiendo archivo local: {filename}")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Leyendo y resumiendo `{filename}`...", "--chat-id", sender_id])

                            # 1. Leer el archivo desde el Sandbox
                            path_in_container = f"/mnt/docs/{filename}"
                            
                            if filename.lower().endswith(".pdf"):
                                # Código para extraer texto de PDF usando pypdf
                                read_code = (
                                    f"from pypdf import PdfReader; "
                                    f"reader = PdfReader('{path_in_container}'); "
                                    f"print('\\n'.join([page.extract_text() for page in reader.pages]))"
                                )
                            else:
                                read_code = f"with open('{path_in_container}', 'r', encoding='utf-8') as f: print(f.read())"
                            
                            read_res = run_tool("run_sandbox.py", ["--code", read_code])

                            if read_res and read_res.get("status") == "success" and read_res.get("stdout"):
                                content = read_res.get("stdout")
                                
                                if len(content) > 10000:
                                    content = content[:10000] + "... (truncado)"
                                
                                # 2. Enviar a LLM para resumir
                                prompt = f"Resume el siguiente documento llamado '{filename}':\n\n{content}"
                                llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt])

                                if llm_res and "content" in llm_res:
                                    reply_text = llm_res["content"]
                                else:
                                    reply_text = "❌ Error generando el resumen."
                            else:
                                error_details = read_res.get("stderr") or read_res.get("message", "No se pudo leer el archivo.")
                                reply_text = f"❌ Error al leer el archivo `{filename}` desde el Sandbox:\n`{error_details}`"

                    elif msg.startswith("/resumir") or msg.startswith("/summarize"):
                        url = msg.split(" ", 1)[1] if " " in msg else ""
                        if not url:
                            reply_text = "⚠️ Uso: /resumir [url]"
                        else:
                            print(f"   🌐 Resumiendo URL: {url}")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Leyendo {url}...", "--chat-id", sender_id])
                            
                            # 1. Scrape
                            scrape_res = run_tool("scrape_single_site.py", ["--url", url, "--output-file", ".tmp/web_content.txt"])
                            
                            if scrape_res and scrape_res.get("status") == "success":
                                # 2. Summarize
                                try:
                                    with open(".tmp/web_content.txt", "r", encoding="utf-8") as f:
                                        content = f.read()
                                    
                                    # Truncar si es muy largo (ej. 10k caracteres) para no saturar CLI args
                                    if len(content) > 10000:
                                        content = content[:10000] + "... (truncado)"
                                        
                                    prompt = f"Resume el siguiente contenido web para Telegram:\n\n{content}"
                                    llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt])
                                    
                                    if llm_res and "content" in llm_res:
                                        reply_text = llm_res["content"]
                                    elif llm_res and "error" in llm_res:
                                        reply_text = f"⚠️ Error del modelo: {llm_res['error']}"
                                    else:
                                        reply_text = "❌ Error generando resumen."
                                        
                                except Exception as e:
                                    reply_text = f"❌ Error leyendo contenido: {e}"
                            else:
                                err = scrape_res.get("message") if scrape_res else "Error desconocido"
                                # Ayuda contextual si el usuario intenta usar /resumir con un archivo local
                                if "No scheme supplied" in str(err):
                                    filename = url.split('/')[-1]
                                    reply_text = f"🤔 El comando `/resumir` es para URLs (ej: `https://...`).\n\nSi querías resumir el archivo local `{filename}`, el comando correcto es:\n`/resumir_archivo {filename}`"
                                else:
                                    reply_text = f"❌ Error leyendo la web: {err}"

                    elif msg.startswith("/recordar") or msg.startswith("/remember"):
                        memory_text = msg.split(" ", 1)[1] if " " in msg else ""
                        if not memory_text:
                            reply_text = "⚠️ Uso: /recordar [dato a guardar]"
                        else:
                            print(f"   💾 Guardando en memoria: {memory_text}")
                            run_tool("telegram_tool.py", ["--action", "send", "--message", "💾 Guardando nota...", "--chat-id", sender_id])
                            
                            # Ejecutar herramienta de memoria (save_memory.py)
                            res = run_tool("save_memory.py", ["--text", memory_text, "--category", "telegram_note"])
                            
                            if res and res.get("status") == "success":
                                reply_text = "✅ Nota guardada en memoria a largo plazo."
                            else:
                                reply_text = "❌ Error al guardar. (Verifica que save_memory.py exista y funcione)."

                    elif msg.startswith("/memorias") or msg.startswith("/memories"):
                        print("   🧠 Consultando lista de recuerdos...")
                        run_tool("telegram_tool.py", ["--action", "send", "--message", "🧠 Consultando base de datos...", "--chat-id", sender_id])
                        
                        res = run_tool("list_memories.py", ["--limit", "5"])
                        if res and res.get("status") == "success":
                            memories = res.get("memories", [])
                            if not memories:
                                reply_text = "📭 No tengo recuerdos guardados aún."
                            else:
                                reply_text = "🧠 *Últimos recuerdos:*\n"
                                for m in memories:
                                    date = m.get("timestamp", "").replace("T", " ").split(".")[0]
                                    content = m.get("content", "")
                                    mem_id = m.get("id", "N/A")
                                    reply_text += f"🆔 `{mem_id}`\n📅 {date}: {content}\n\n"
                        else:
                            reply_text = "❌ Error al consultar la memoria."

                    elif msg.startswith("/olvidar") or msg.startswith("/forget"):
                        mem_id = msg.split(" ", 1)[1] if " " in msg else ""
                        if not mem_id:
                            reply_text = "⚠️ Uso: /olvidar [ID]"
                        else:
                            print(f"   🗑️ Eliminando recuerdo: {mem_id}")
                            res = run_tool("delete_memory.py", ["--id", mem_id])
                            if res and res.get("status") == "success":
                                reply_text = "✅ Recuerdo eliminado."
                            else:
                                reply_text = f"❌ Error al eliminar: {res.get('message', 'Desconocido')}"

                    elif msg.startswith("/broadcast") or msg.startswith("/anuncio"):
                        announcement = msg.split(" ", 1)[1] if " " in msg else ""
                        if not announcement:
                            reply_text = "⚠️ Uso: /broadcast [mensaje para todos]"
                        else:
                            if os.path.exists(USERS_FILE):
                                with open(USERS_FILE, 'r') as f:
                                    users = f.read().splitlines()
                                count = 0
                                for uid in users:
                                    if uid.strip():
                                        run_tool("telegram_tool.py", ["--action", "send", "--message", f"📢 *ANUNCIO:*\n{announcement}", "--chat-id", uid])
                                        count += 1
                                reply_text = f"✅ Mensaje enviado a {count} usuarios."
                            else:
                                reply_text = "⚠️ No tengo usuarios registrados aún."

                    elif msg.startswith("/status"):
                        print("   📊 Verificando estado del sistema...")
                        run_tool("telegram_tool.py", ["--action", "send", "--message", "🔍 Escaneando sistema...", "--chat-id", sender_id])
                        
                        res = run_tool("monitor_resources.py", [])
                        # monitor_resources devuelve JSON incluso si hay alertas (exit code 1)
                        if res:
                            metrics = res.get("metrics", {})
                            alerts = res.get("alerts", [])
                            
                            status_emoji = "✅" if not alerts else "⚠️"
                            reply_text = (
                                f"{status_emoji} *Estado del Servidor:*\n\n"
                                f"💻 *CPU:* {metrics.get('cpu_percent', 0)}%\n"
                                f"🧠 *RAM:* {metrics.get('memory_percent', 0)}% ({metrics.get('memory_used_gb', 0)}GB / {metrics.get('memory_total_gb', 0)}GB)\n"
                                f"💾 *Disco:* {metrics.get('disk_percent', 0)}% (Libre: {metrics.get('disk_free_gb', 0)}GB)\n"
                            )
                            if alerts:
                                reply_text += "\n🚨 *Alertas:*\n" + "\n".join([f"- {a}" for a in alerts])
                        else:
                            reply_text = "❌ Error al obtener métricas."

                    elif msg.startswith("/usuarios") or msg.startswith("/users"):
                        if os.path.exists(USERS_FILE):
                            with open(USERS_FILE, 'r') as f:
                                users = [line.strip() for line in f if line.strip()]
                            last_users = users[-5:]
                            if last_users:
                                reply_text = f"👥 *Últimos {len(last_users)} usuarios registrados:*\n" + "\n".join([f"- `{u}`" for u in last_users])
                            else:
                                reply_text = "📭 No hay usuarios registrados."
                        else:
                            reply_text = "📭 No hay archivo de usuarios aún."

                    elif msg.startswith("/modo"):
                        mode = msg.split(" ", 1)[1].lower().strip() if " " in msg else ""
                        if mode in PERSONAS:
                            set_persona(mode)
                            reply_text = f"🎭 *Modo cambiado a:* {mode.capitalize()}\n\n_{PERSONAS[mode]}_"
                        else:
                            opts = ", ".join([f"`{k}`" for k in PERSONAS.keys()])
                            reply_text = (
                                "⚠️ Modo no reconocido.\n"
                                f"Opciones disponibles: {opts}\n"
                                "Uso: `/modo [opcion]`"
                            )

                    elif msg.startswith("/reiniciar") or msg.startswith("/reset"):
                        print("   🔄 Reiniciando sesión...")
                        # 1. Borrar historial de chat
                        run_tool("chat_with_llm.py", ["--prompt", "/clear"])
                        
                        # 2. Resetear personalidad
                        set_persona("default")
                        
                        reply_text = "🔄 *Sistema reiniciado.*\n\n- Historial de conversación borrado.\n- Personalidad restablecida a 'Default'."

                    elif msg.startswith("/ayuda") or msg.startswith("/help"):
                        reply_text = (
                            "🤖 *Comandos Disponibles:*\n\n"
                            "🔹 */investigar [tema]*: Busca en internet y resume.\n"
                            "🔹 */reporte [tema]*: Genera un informe técnico detallado en docs/.\n"
                            "🔹 */recordatorio [hora] [msg]*: Configura una alarma diaria.\n"
                            "🔹 */traducir [texto/archivo]*: Traduce al español.\n"
                            "🔹 */idioma [es/en]*: Cambia el idioma en el que te escucho.\n"
                            "🔹 */borrar_recordatorios*: Elimina todas tus alarmas.\n"
                            "🔹 */ayuda_cnc*: Envía la documentación sobre CNC.\n"
                            "🔹 */resumir [url]*: Lee una web y te dice de qué trata.\n"
                            "🔹 */ingestar [archivo]*: Agrega un PDF de `docs/` a la memoria RAG.\n"
                            "🔹 */resumir_archivo [nombre]*: Lee un archivo de `docs/` y lo resume.\n"
                            "🔹 */recordar [dato]*: Guarda una nota en mi memoria.\n"
                            "🔹 */memorias*: Lista tus últimos recuerdos guardados.\n"
                            "🔹 */olvidar [ID]*: Borra un recuerdo específico.\n"
                            "🔹 */status*: Muestra CPU y RAM del servidor.\n"
                            "🔹 */usuarios*: Muestra los últimos 5 IDs registrados.\n"
                            "🔹 */modo [tipo]*: Cambia mi personalidad (serio, sarcastico, profesor...).\n"
                            "🔹 */reiniciar*: Borra historial y restablece personalidad.\n"
                            "🔹 */broadcast [msg]*: Envía un mensaje a todos (Admin).\n"
                            "🔹 */ayuda*: Muestra este menú.\n\n"
                            "🔹 *Chat normal*: Háblame sobre PCBs, KiCad o G-Code."
                        )

                    elif msg.startswith("/send_cnc"):
                        parts = msg.split()
                        if len(parts) < 3:
                            reply_text = "⚠️ Uso: `/send_cnc [puerto] [archivo.nc]`\nEj: `/send_cnc /dev/ttyUSB0 mi_logo.nc`"
                        else:
                            port = parts[1]
                            gcode_file = parts[2]
                            
                            # Advertencia de seguridad
                            run_tool("telegram_tool.py", ["--action", "send", "--message", f"🚨 *¡ATENCIÓN!* 🚨\nIniciando envío de `{gcode_file}` a la CNC en el puerto `{port}`.\n\n*Asegúrate de que la fresa esté en una posición segura.*", "--chat-id", sender_id])
                            time.sleep(2) # Dar tiempo al usuario para leer

                            # Ejecutar el sender.py en el host (NO en sandbox)
                            res = run_tool("send_gcode.py", ["--port", port, "--file", gcode_file])
                            
                            if res and res.get("status") == "success":
                                reply_text = f"✅ Proceso de fresado para `{gcode_file}` completado."
                            else:
                                reply_text = f"❌ Error durante el envío a la CNC. Revisa los logs de la terminal."
                    
                    elif msg.startswith("/py "):
                        raw_input = msg.split(" ", 1)[1].strip()
                        
                        # Seguridad: Bloquear scripts administrativos que requieren acceso al Host
                        forbidden = ["build_sandbox.py", "listen_telegram.py", "init_project.py", "deploy_to_github.py", "check_system_health.py"]
                        if any(f in raw_input for f in forbidden):
                            reply_text = "⛔ *Acción Denegada*: Este script es administrativo y debe ejecutarse en la terminal del servidor (Host), no dentro del Sandbox."
                        else:
                            # Lógica para detectar si es un script local (ej: execution/script.py args)
                            parts = raw_input.split()
                            script_candidate = parts[0]
                            script_args = parts[1:]
                            
                            # Intentar localizar el script en la ruta actual o en execution/
                            script_path = None
                            if os.path.exists(script_candidate) and script_candidate.endswith(".py"):
                                script_path = script_candidate
                            elif os.path.exists(os.path.join("execution", script_candidate)) and script_candidate.endswith(".py"):
                                script_path = os.path.join("execution", script_candidate)
                                
                            if script_path:
                                print(f"   📜 Detectado script local: {script_path}")
                                try:
                                    with open(script_path, "r", encoding="utf-8") as f:
                                        script_content = f.read()
                                    
                                    # Inyectar argumentos en sys.argv para que argparse funcione dentro del sandbox
                                    # El primer argumento de argv suele ser el nombre del script
                                    argv_injection = f"import sys\nsys.argv = {['script.py'] + script_args}\n"
                                    code_to_run = argv_injection + script_content
                                    print(f"   🐍 Enviando script al Sandbox (Docker 🐳) con args: {script_args}")
                                except Exception as e:
                                    code_to_run = raw_input # Fallback
                                    print(f"   ⚠️ Error leyendo script: {e}")
                            else:
                                code_to_run = raw_input
                                print(f"   🐍 Ejecutando código raw en Sandbox (Docker 🐳): {code_to_run}")

                            res = run_tool("run_sandbox.py", ["--code", code_to_run])

                            reply_text = "" # Resetear
                            if res and res.get("status") == "success":
                                stdout = res.get("stdout", "")
                                stderr = res.get("stderr", "")
                                
                                # --- Manejo de Salida de Archivos ---
                                sent_file = False
                                clean_stdout_lines = []
                                if stdout:
                                    for line in stdout.splitlines():
                                        potential_path_in_container = line.strip()
                                        if potential_path_in_container.startswith('/mnt/out/'):
                                            filename = os.path.basename(potential_path_in_container)
                                            local_path = os.path.join(".tmp", filename)
                                            if os.path.exists(local_path):
                                                # Determinar si es imagen o documento
                                                image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
                                                is_image = any(filename.lower().endswith(ext) for ext in image_extensions)
                                                
                                                if is_image:
                                                    print(f"   🖼️  Detectado archivo de imagen: {local_path}. Enviando...")
                                                    run_tool("telegram_tool.py", ["--action", "send-photo", "--file-path", local_path, "--chat-id", sender_id, "--caption", f"Imagen generada: {filename}"])
                                                else:
                                                    print(f"   📄  Detectado archivo de documento: {local_path}. Enviando...")
                                                    run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", local_path, "--chat-id", sender_id, "--caption", f"Archivo generado: {filename}"])
                                                
                                                sent_file = True
                                                continue # No añadir esta línea a la respuesta de texto
                                        clean_stdout_lines.append(line)
                                
                                clean_stdout = "\n".join(clean_stdout_lines)

                                # --- Manejo de Salida de Texto ---
                                text_output_exists = clean_stdout or stderr
                                if text_output_exists:
                                    reply_text = "📦 *Resultado del Sandbox:*\n\n"
                                    if clean_stdout:
                                        reply_text += f"*Salida:*\n```\n{clean_stdout}\n```\n"
                                    if stderr:
                                        reply_text += f"*Errores:*\n```\n{stderr}\n```\n"
                                elif not sent_file: # No hay salida de texto Y no se envió archivo
                                    reply_text = "📦 *Resultado del Sandbox:*\n\n_El código se ejecutó sin producir salida._"
                            else:
                                reply_text = f"❌ *Error en Sandbox:*\n{res.get('message', 'Error desconocido.')}"

                    # Detección de saludos mejorada (maneja puntuación y frases como "Hola a todos")
                    elif msg.strip() and msg.lower().split()[0].strip(".,!¡?") in ["hola", "hi", "hello", "/start"]:
                        reply_text = (
                            "👋 ¡Hola! Soy un Agente de IA especializado en la fabricación de PCBs con CNC.\n\n"
                            "Fui entrenado por el prof. *César Rodríguez* y el equipo *Tecnología Venezolana* para asistirte en todo el flujo de trabajo, desde el diseño hasta la fabricación:\n\n"
                            "🔹 *Diseño*: Te puedo guiar en el uso de *KiCad* para crear tus esquemas y layouts.\n"
                            "🔹 *Optimización*: Puedo ayudarte a programar en *Python* para encontrar las rutas óptimas de tus pistas (auto-routing).\n"
                            "🔹 *Fabricación*: Soy capaz de generar el *G-Code* final que tu máquina CNC necesita para fresar las placas.\n\n"
                            "Mi objetivo es demostrar cómo se puede lograr un ecosistema de fabricación de alta tecnología utilizando únicamente software libre.\n\n"
                            "Usa */ayuda* para ver todos los comandos disponibles."
                        )

                    elif msg.lower().strip() in ["gracias", "gracias!", "thanks", "thank you"]:
                        reply_text = "¡De nada! Estoy aquí para ayudar. 🤖"

                    # --- CHAT GENERAL (Capa 2: Orquestación) ---
                    elif not reply_text: # Solo si no se ha generado respuesta por un comando anterior
                        # Estrategia Directa con RAG:
                        # Enviamos el mensaje al LLM. El script chat_with_llm.py se encarga de
                        # buscar en la memoria e inyectar el contexto si es relevante.
                        print("   🤔 Consultando al Agente (con memoria)...")
                        current_sys = get_current_persona()
                        
                        # Inyectar fecha y hora actual para que el LLM lo sepa
                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        current_sys += f"\n[Contexto Temporal: Fecha y Hora actual del servidor: {now_str}]"

                        # Si la interacción fue por voz, instruir al LLM que responda en ese idioma
                        if is_voice_interaction and voice_lang_short != "es":
                            current_sys += f"\nIMPORTANT: The user is speaking in '{voice_lang_short}'. You MUST respond in '{voice_lang_short}', regardless of your default instructions."

                        llm_response = run_tool("chat_with_llm.py", ["--prompt", msg, "--system", current_sys])
                        
                        if llm_response and "content" in llm_response:
                            reply_text = llm_response["content"]
                        else:
                            error_msg = llm_response.get('error', 'Respuesta vacía') if llm_response else "Error desconocido"
                            reply_text = f"⚠️ Error del Modelo: {error_msg}"
                    
                    # 3. Enviar respuesta a Telegram
                    if reply_text:
                        print(f"   📤 Enviando respuesta: '{reply_text[:60]}...'")
                        res = run_tool("telegram_tool.py", ["--action", "send", "--message", reply_text, "--chat-id", sender_id])
                        if res and res.get("status") == "error":
                            print(f"   ❌ Error al enviar mensaje: {res.get('message')}")
                        
                        # 4. Si fue interacción por voz, enviar también audio
                        if is_voice_interaction and reply_text:
                            print("   🗣️ Generando respuesta de voz...")
                            audio_path = os.path.join(".tmp", f"reply_{int(time.time())}.ogg")
                            # Generar audio
                            tts_res = run_tool("text_to_speech.py", ["--text", reply_text[:500], "--output", audio_path, "--lang", voice_lang_short]) # Limitamos a 500 chars para no hacerlo eterno
                            if tts_res and tts_res.get("status") == "success":
                                run_tool("telegram_tool.py", ["--action", "send-voice", "--file-path", audio_path, "--chat-id", sender_id])
            
            # --- TAREA DE FONDO: RECORDATORIOS ---
            check_reminders()

            # --- TAREA DE FONDO: MONITOREO PROACTIVO ---
            if time.time() - last_health_check > HEALTH_CHECK_INTERVAL:
                last_health_check = time.time()
                # Solo el admin (CHAT_ID del .env) recibe alertas técnicas
                admin_id = os.getenv("TELEGRAM_CHAT_ID")
                if admin_id:
                    res = run_tool("monitor_resources.py", [])
                    if res and res.get("alerts"):
                        alerts = res.get("alerts", [])
                        alert_msg = "🚨 *ALERTA DEL SISTEMA:*\n\n" + "\n".join([f"- {a}" for a in alerts])
                        print(f"   ⚠️ Detectada alerta de sistema. Notificando a {admin_id}...")
                        run_tool("telegram_tool.py", ["--action", "send", "--message", alert_msg, "--chat-id", admin_id])
            
            # Esperar un poco antes del siguiente chequeo para no saturar la CPU/API
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Desconectando servicio de Telegram.")

if __name__ == "__main__":
    main()