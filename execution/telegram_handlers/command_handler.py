import json
import os
import datetime
import time
from execution.listen_telegram_helpers import load_config, save_config, PERSONAS, set_persona
from execution.db_manager import add_reminder, delete_reminders_for_user, get_all_users, get_reminders_by_user, delete_reminder_by_id
import shutil
import glob
import zipfile

def _handle_investigar(msg, sender_id, run_tool):
    topic = msg.split(" ", 1)[1] if " " in msg else ""
    if not topic:
        return "⚠️ Uso: /investigar [tema]"

    print(f"   🔍 Ejecutando investigación sobre: {topic}")
    run_tool("telegram_tool.py", ["--action", "send", "--message", f"🕵️‍♂️ Investigando sobre '{topic}'... dame unos segundos.", "--chat-id", sender_id])

    res = run_tool("research_topic.py", ["--query", topic, "--output-file", ".tmp/tg_research.txt"])

    if not (res and res.get("status") == "success"):
        return "❌ Error al ejecutar la herramienta de investigación."

    try:
        with open(".tmp/tg_research.txt", "r", encoding="utf-8") as f:
            data = f.read()
        print("   🧠 Resumiendo resultados...")

        summarization_prompt = f"""Considerando lo que ya sabes en tu memoria y los siguientes resultados de búsqueda sobre '{topic}', crea un resumen conciso para Telegram.

Resultados de Búsqueda:
---
{data}"""
        llm_res = run_tool("chat_with_llm.py", ["--prompt", summarization_prompt, "--memory-query", topic])

        if llm_res and "content" in llm_res:
            return llm_res["content"]
        elif llm_res and "error" in llm_res:
            return f"⚠️ Error del modelo: {llm_res['error']}"
        else:
            return "❌ No se pudo generar el resumen (Respuesta vacía o inválida)."
    except Exception as e:
        return f"Error procesando resultados: {e}"

def _handle_reporte(msg, sender_id, run_tool):
    topic = msg.split(" ", 1)[1] if " " in msg else ""
    if not topic:
        return "⚠️ Uso: /reporte [tema técnico o de ingeniería]"

    print(f"   ️ Generando reporte técnico sobre: {topic}")
    run_tool("telegram_tool.py", ["--action", "send", "--message", f"👷 Iniciando investigación técnica sobre '{topic}'... Esto tomará unos segundos.", "--chat-id", sender_id])

    query = f"especificaciones técnicas tutoriales y documentación para {topic}"
    res_search = run_tool("research_topic.py", ["--query", query, "--output-file", ".tmp/tech_research.txt"])

    if not (res_search and res_search.get("status") == "success"):
        return "❌ Error en la fase de investigación (Búsqueda)."

    try:
        with open(".tmp/tech_research.txt", "r", encoding="utf-8") as f:
            search_data = f.read()

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

        llm_res = run_tool("chat_with_llm.py", ["--prompt", report_prompt, "--memory-query", topic])

        if not (llm_res and "content" in llm_res):
            return "❌ Error al redactar el reporte con el modelo."

        report_content = llm_res["content"]
        safe_topic = "".join([c if c.isalnum() else "_" for c in topic])[:30]
        filename = f"Reporte_Tecnico_{safe_topic}.md"
        docs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", filename)

        with open(docs_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        return f"✅ *Reporte Generado Exitosamente*\n\nHe guardado el informe detallado en:\n`docs/{filename}`\n\nAquí tienes un resumen:\n\n" + report_content[:400] + "...\n\n_(Lee el archivo completo en tu carpeta docs)_"

    except Exception as e:
        return f"❌ Error procesando el reporte: {e}"

def _handle_recordatorio(msg, sender_id, run_tool):
    try:
        parts = msg.split(" ", 2)
        if len(parts) < 3:
            return "⚠️ Uso: /recordatorio HH:MM Mensaje\nEj: `/recordatorio 08:00 Tomar antibiótico`"
        
        time_str, note = parts[1], parts[2]
        datetime.datetime.strptime(time_str, "%H:%M")
        
        add_reminder(sender_id, time_str, note)
        return f"✅ Recordatorio configurado en la base de datos.\nTe avisaré todos los días a las {time_str}: '{note}'."
    except ValueError:
        return "❌ Hora inválida. Usa formato 24h (HH:MM), ej: 14:30."

def _handle_borrar_recordatorios(msg, sender_id, run_tool):
    rows_deleted = delete_reminders_for_user(sender_id)
    if rows_deleted > 0:
        return f"✅ {rows_deleted} recordatorio(s) eliminado(s) de la base de datos."
    else:
        return "🤔 No tienes recordatorios configurados para borrar."

def _handle_borrar_recordatorio_id(msg, sender_id, run_tool):
    try:
        parts = msg.split(" ")
        if len(parts) < 2:
            return "⚠️ Uso: /borrar_recordatorio [ID]\nUsa /mis_recordatorios para ver los IDs."
        
        reminder_id = int(parts[1])
        rows = delete_reminder_by_id(reminder_id, sender_id)
        
        if rows > 0:
            return f"✅ Recordatorio {reminder_id} eliminado."
        else:
            return f"❌ No se encontró el recordatorio {reminder_id} o no te pertenece."
    except ValueError:
        return "❌ El ID debe ser un número."

def _handle_mis_recordatorios(msg, sender_id, run_tool):
    reminders = get_reminders_by_user(sender_id)
    if not reminders:
        return "📭 No tienes recordatorios activos."
    
    reply = "📅 *Tus Recordatorios:*\n"
    for r in reminders:
        reply += f"- 🆔 `{r['id']}` | ⏰ {r['reminder_time']}: {r['message']}\n"
    reply += "\nPara borrar uno: `/borrar_recordatorio [ID]`"
    return reply

def _handle_traducir(msg, sender_id, run_tool):
    content = msg.split(" ", 1)[1].strip() if " " in msg else ""
    if not content:
        return "⚠️ Uso: /traducir [texto | nombre_archivo]"

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
            return "✅ Archivo traducido enviado."
        else:
            err = res.get("message", "Error desconocido") if res else "Error en script"
            return f"❌ Error al traducir archivo: {err}"
    else:
        print(f"   🔤 Traduciendo texto...")
        prompt = f"Traduce el siguiente texto al Español. Devuelve solo la traducción:\n\n{content}"
        llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt])
        if llm_res and "content" in llm_res:
            return f"🇪🇸 *Traducción:*\n\n{llm_res['content']}"
        else:
            return "❌ Error al traducir texto."

def _handle_idioma(msg, sender_id, run_tool):
    parts = msg.split(" ")
    if len(parts) < 2:
        return "⚠️ Uso: /idioma [es/en]\nEj: `/idioma en` (para inglés)"
    
    lang_map = {"es": "es-ES", "en": "en-US", "fr": "fr-FR", "pt": "pt-BR"}
    selection = parts[1].lower()
    code = lang_map.get(selection, "es-ES")
    config = load_config()
    config["voice_lang"] = code
    save_config(config)
    return f"✅ Idioma de voz cambiado a: `{code}`.\nAhora te escucharé en ese idioma."

def _handle_ayuda_cnc(msg, sender_id, run_tool):
    manual_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "CNC.md")
    if os.path.exists(manual_path):
        print(f"   🛠️ Enviando documentación CNC a {sender_id}...")
        run_tool("telegram_tool.py", ["--action", "send", "--message", "📘 Aquí tienes la documentación sobre el flujo de trabajo CNC.", "--chat-id", sender_id])
        run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", manual_path, "--chat-id", sender_id, "--caption", "Documentación CNC (Markdown)"])
        return "" # El mensaje ya se envió
    else:
        return "⚠️ El archivo `docs/CNC.md` no se encuentra."

def _handle_ingestar(msg, sender_id, run_tool):
    filename = msg.split(" ", 1)[1].strip() if " " in msg else ""
    if not filename:
        return "⚠️ Uso: /ingestar [nombre_archivo_en_docs]"

    print(f"   📥 Ingestando archivo: {filename}")
    run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Procesando `{filename}` para RAG...", "--chat-id", sender_id])

    path_in_container = f"/mnt/docs/{filename}"
    if filename.lower().endswith(".pdf"):
        read_code = f"from pypdf import PdfReader; reader = PdfReader('{path_in_container}'); print('\\n'.join([page.extract_text() for page in reader.pages]))"
    else:
        read_code = f"with open('{path_in_container}', 'r', encoding='utf-8') as f: print(f.read())"

    read_res = run_tool("run_sandbox.py", ["--code", read_code])

    if read_res and read_res.get("status") == "success" and read_res.get("stdout"):
        content = read_res.get("stdout")
        if not content.strip():
            return "⚠️ El archivo parece estar vacío o no se pudo extraer texto."
        
        full_text = f"Contenido del documento '{filename}':\n\n{content}"
        save_res = run_tool("save_memory.py", ["--text", full_text, "--category", "document_knowledge"])
        if save_res and save_res.get("status") == "success":
            return f"✅ Documento `{filename}` agregado a la memoria a largo plazo."
        else:
            return "❌ Error al guardar en memoria."
    else:
        error_details = read_res.get("stderr") or read_res.get("message", "No se pudo leer.")
        return f"❌ Error leyendo `{filename}`: {error_details}"

def _handle_resumir_archivo(msg, sender_id, run_tool):
    filename = msg.split(" ", 1)[1].strip() if " " in msg else ""
    if not filename:
        return "⚠️ Uso: /resumir_archivo [nombre_del_archivo_en_docs]"

    print(f"   📄 Resumiendo archivo local: {filename}")
    run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Leyendo y resumiendo `{filename}`...", "--chat-id", sender_id])

    path_in_container = f"/mnt/docs/{filename}"
    if filename.lower().endswith(".pdf"):
        read_code = f"from pypdf import PdfReader; reader = PdfReader('{path_in_container}'); print('\\n'.join([page.extract_text() for page in reader.pages]))"
    else:
        read_code = f"with open('{path_in_container}', 'r', encoding='utf-8') as f: print(f.read())"

    read_res = run_tool("run_sandbox.py", ["--code", read_code])

    if read_res and read_res.get("status") == "success" and read_res.get("stdout"):
        content = read_res.get("stdout")
        if len(content) > 10000:
            content = content[:10000] + "... (truncado)"

        prompt = f"Resume el siguiente documento llamado '{filename}':\n\n{content}"
        llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt])
        return llm_res.get("content", "❌ Error generando el resumen.")
    else:
        error_details = read_res.get("stderr") or read_res.get("message", "No se pudo leer el archivo.")
        return f"❌ Error al leer el archivo `{filename}` desde el Sandbox:\n`{error_details}`"

def _handle_resumir(msg, sender_id, run_tool):
    url = msg.split(" ", 1)[1] if " " in msg else ""
    if not url:
        return "⚠️ Uso: /resumir [url]"

    print(f"   🌐 Resumiendo URL: {url}")
    run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏳ Leyendo {url}...", "--chat-id", sender_id])

    scrape_res = run_tool("scrape_single_site.py", ["--url", url, "--output-file", ".tmp/web_content.txt"])

    if not (scrape_res and scrape_res.get("status") == "success"):
        err = scrape_res.get("message") if scrape_res else "Error desconocido"
        if "No scheme supplied" in str(err):
            filename = url.split('/')[-1]
            return f"🤔 El comando `/resumir` es para URLs (ej: `https://...`).\n\nSi querías resumir el archivo local `{filename}`, el comando correcto es:\n`/resumir_archivo {filename}`"
        else:
            return f"❌ Error leyendo la web: {err}"

    try:
        with open(".tmp/web_content.txt", "r", encoding="utf-8") as f:
            content = f.read()

        if len(content) > 10000:
            content = content[:10000] + "... (truncado)"

        prompt = f"Resume el siguiente contenido web para Telegram:\n\n{content}"
        llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt])

        if llm_res and "content" in llm_res:
            return llm_res["content"]
        elif llm_res and "error" in llm_res:
            return f"⚠️ Error del modelo: {llm_res['error']}"
        else:
            return "❌ Error generando resumen."
    except Exception as e:
        return f"❌ Error leyendo contenido: {e}"

def _handle_recordar(msg, sender_id, run_tool):
    memory_text = msg.split(" ", 1)[1] if " " in msg else ""
    if not memory_text:
        return "⚠️ Uso: /recordar [dato a guardar]"

    print(f"   💾 Guardando en memoria: {memory_text}")
    run_tool("telegram_tool.py", ["--action", "send", "--message", "💾 Guardando nota...", "--chat-id", sender_id])

    res = run_tool("save_memory.py", ["--text", memory_text, "--category", "telegram_note"])
    if res and res.get("status") == "success":
        return "✅ Nota guardada en memoria a largo plazo."
    else:
        return "❌ Error al guardar. (Verifica que save_memory.py exista y funcione)."

def _handle_memorias(msg, sender_id, run_tool):
    print("   🧠 Consultando lista de recuerdos...")
    run_tool("telegram_tool.py", ["--action", "send", "--message", "🧠 Consultando base de datos...", "--chat-id", sender_id])

    res = run_tool("list_memories.py", ["--limit", "5"])
    if not (res and res.get("status") == "success"):
        return "❌ Error al consultar la memoria."

    memories = res.get("memories", [])
    if not memories:
        return "📭 No tengo recuerdos guardados aún."
    
    reply_text = "🧠 *Últimos recuerdos:*\n"
    for m in memories:
        date = m.get("timestamp", "").replace("T", " ").split(".")[0]
        content = m.get("content", "")
        mem_id = m.get("id", "N/A")
        reply_text += f"🆔 `{mem_id}`\n📅 {date}: {content}\n\n"
    return reply_text

def _handle_olvidar(msg, sender_id, run_tool):
    mem_id = msg.split(" ", 1)[1] if " " in msg else ""
    if not mem_id:
        return "⚠️ Uso: /olvidar [ID]"
    
    print(f"   🗑️ Eliminando recuerdo: {mem_id}")
    res = run_tool("delete_memory.py", ["--id", mem_id])
    if res and res.get("status") == "success":
        return "✅ Recuerdo eliminado."
    else:
        return f"❌ Error al eliminar: {res.get('message', 'Desconocido')}"

def _handle_versiones(msg, sender_id, run_tool):
    print("   🔍 Verificando versiones de herramientas en el Sandbox...")
    run_tool("telegram_tool.py", ["--action", "send", "--message", "🔍 Auditando versiones instaladas en el entorno Docker...", "--chat-id", sender_id])

    script_path = os.path.join("execution", "check_tool_versions.py")
    if not os.path.exists(script_path):
        return "❌ Error: No encuentro el script `execution/check_tool_versions.py`."

    with open(script_path, "r") as f:
        code = f.read()

    # Ejecutar dentro del contenedor
    res = run_tool("run_sandbox.py", ["--code", code])

    if res and res.get("status") == "success":
        versions = json.loads(res.get("stdout", "{}"))
        reply = "🛠️ **Versiones Instaladas (Sandbox):**\n\n"
        for tool, ver in versions.items():
            reply += f"🔹 *{tool}:* `{ver}`\n"
        return reply
    else:
        return f"❌ Error obteniendo versiones: {res.get('stderr')}"

def _handle_broadcast(msg, sender_id, run_tool):
    announcement = msg.split(" ", 1)[1] if " " in msg else ""
    if not announcement:
        return "⚠️ Uso: /broadcast [mensaje para todos]"

    users = get_all_users()
    if not users:
        return "⚠️ No tengo usuarios registrados aún."

    count = 0
    for uid in users:
        if uid.strip():
            run_tool("telegram_tool.py", ["--action", "send", "--message", f"📢 *ANUNCIO:*\n{announcement}", "--chat-id", uid])
            count += 1
    return f"✅ Mensaje enviado a {count} usuarios."

def _handle_status(msg, sender_id, run_tool):
    print("   📊 Verificando estado del sistema...")
    run_tool("telegram_tool.py", ["--action", "send", "--message", "🔍 Escaneando sistema...", "--chat-id", sender_id])

    res = run_tool("monitor_resources.py", [])
    if not res:
        return "❌ Error al obtener métricas."

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
    return reply_text

def _handle_usuarios(msg, sender_id, run_tool):
    users = get_all_users()
    last_users = users[-5:]
    if not last_users:
        return "📭 No hay usuarios registrados."
    
    return f"👥 *Últimos {len(last_users)} usuarios registrados:*\n" + "\n".join([f"- `{u}`" for u in last_users])

def _handle_modo(msg, sender_id, run_tool):
    mode = msg.split(" ", 1)[1].lower().strip() if " " in msg else ""
    if mode in PERSONAS:
        set_persona(mode)
        return f"🎭 *Modo cambiado a:* {mode.capitalize()}\n\n_{PERSONAS[mode]}_"
    else:
        opts = ", ".join([f"`{k}`" for k in PERSONAS.keys()])
        return (
            "⚠️ Modo no reconocido.\n"
            f"Opciones disponibles: {opts}\n"
            "Uso: `/modo [opcion]`"
        )

def _handle_reiniciar(msg, sender_id, run_tool):
    print("   🔄 Preparando reinicio de sesión y guardado de historial...")
    
    # Generar un resumen rápido de la sesión actual antes de borrarla
    summary_prompt = "Genera un resumen de una sola frase (máx 15 palabras) de nuestra conversación actual para el historial."
    res_summary = run_tool("chat_with_llm.py", ["--prompt", summary_prompt, "--no-rag"])
    summary = res_summary.get("content", "Conversación finalizada") if res_summary else "Conversación finalizada"
    
    # Guardar en la base de datos de historial
    run_tool("chat_history.py", ["--action", "save", "--user-id", sender_id, "--summary", summary])
    
    # Proceder con el reinicio
    run_tool("chat_with_llm.py", ["--prompt", "/clear"])
    set_persona("default")
    
    return f"🔄 *Sistema reiniciado.*\n\n- Sesión anterior guardada: _{summary}_\n- Historial de conversación borrado.\n- Personalidad restablecida a 'Default'."

def _handle_resume(msg, sender_id, run_tool):
    parts = msg.split()
    if len(parts) == 1:
        # Si el usuario solo escribe /resume, listamos sus sesiones anteriores
        print(f"   📜 Consultando historial de sesiones para {sender_id}...")
        run_tool("telegram_tool.py", ["--action", "send", "--message", "📜 Buscando tus conversaciones anteriores...", "--chat-id", sender_id])
        
        res = run_tool("chat_history.py", ["--action", "list", "--user-id", sender_id])
        if res and res.get("status") == "success":
            history = res.get("history", [])
            if not history:
                return "📭 No tienes conversaciones guardadas para reanudar."
            
            reply = "📜 *Tus Conversaciones Recientes:*\n\n"
            for session in history:
                reply += f"🆔 `{session['id']}` | 📅 {session['date']}\n"
                reply += f"💬 _{session['summary']}_\n\n"
            reply += "Usa `/resume [ID]` para retomar una charla específica."
            return reply
        return "❌ Error al recuperar el historial de conversaciones."

    session_id = parts[1]
    res = run_tool("chat_history.py", ["--action", "resume", "--user-id", sender_id, "--session-id", session_id])
    if res and res.get("status") == "success":
        return f"🔄 *Conversación {session_id} reanudada.*\n\nHe cargado el contexto de esa sesión. ¿En qué nos habíamos quedado?"
    return f"❌ No se pudo encontrar la conversación con ID `{session_id}`."

def _handle_borrar_sesion(msg, sender_id, run_tool):
    parts = msg.split()
    if len(parts) < 2:
        return "⚠️ Uso: `/borrar_sesion [ID]`\nUsa `/resume` para ver tus IDs de sesión."
    
    session_id = parts[1]
    res = run_tool("chat_history.py", ["--action", "delete", "--user-id", sender_id, "--session-id", session_id])
    if res and res.get("status") == "success":
        return f"🗑️ *Sesión {session_id} eliminada* de tu historial."
    return f"❌ No se pudo borrar la sesión `{session_id}`."

def _handle_buscar_sesion(msg, sender_id, run_tool):
    parts = msg.split(" ", 1)
    if len(parts) < 2:
        return "⚠️ Uso: `/buscar_sesion [palabra clave]`"
    
    query = parts[1].strip()
    print(f"   🔍 Buscando sesiones con la palabra: '{query}'...")
    
    res = run_tool("chat_history.py", ["--action", "search", "--user-id", sender_id, "--query", query])
    if res and res.get("status") == "success":
        history = res.get("history", [])
        if not history:
            return f"🔎 No encontré sesiones que mencionen *'{query}'*."
        
        reply = f"🔎 *Resultados para '{query}':*\n\n"
        for session in history:
            reply += f"🆔 `{session['id']}` | 📅 {session['date']}\n"
            reply += f"💬 _{session['summary']}_\n\n"
        reply += "Usa `/resume [ID]` para cargar una de estas sesiones."
        return reply
    return "❌ Error al realizar la búsqueda."

def _handle_exportar_sesion(msg, sender_id, run_tool):
    parts = msg.split()
    if len(parts) < 2:
        return "⚠️ Uso: `/exportar_sesion [ID]`\nUsa `/resume` para ver los IDs."
    
    session_id = parts[1]
    print(f"   📂 Exportando sesión {session_id} a Markdown...")
    run_tool("telegram_tool.py", ["--action", "send", "--message", f"📂 Generando archivo Markdown para la sesión {session_id}...", "--chat-id", sender_id])
    
    res = run_tool("chat_history.py", ["--action", "export", "--user-id", sender_id, "--session-id", session_id])
    if res and res.get("status") == "success":
        filepath = res.get("file")
        run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", filepath, "--chat-id", sender_id, "--caption", f"📄 Exportación Sesión {session_id}"])
        return f"✅ Sesión exportada correctamente a `docs/{os.path.basename(filepath)}`."
    return f"❌ Error al exportar la sesión: {res.get('message', 'Desconocido')}"

def _handle_limpiar(msg, sender_id, run_tool):
    print("   🧹 Ejecutando limpieza de archivos temporales...")
    run_tool("telegram_tool.py", ["--action", "send", "--message", "🧹 Limpiando archivos temporales, cachés y logs...", "--chat-id", sender_id])
    
    res = run_tool("clean_project.py", [])
    
    if res and res.get("status") == "success":
        return "✅ Limpieza completada. Se han eliminado archivos temporales y cachés."
    else:
        err_msg = res.get("message") if res else "Error desconocido durante la limpieza."
        return f"❌ Error durante la limpieza: {err_msg}"

def _handle_ayuda(msg, sender_id, run_tool):
    return (
        "🤖 *Comandos Disponibles:*\n\n"
        "--- *Diseño y Fabricación* ---\n"
        "🔹 */freecad [descripción]*: Crea un modelo 3D (caja, cono, engranaje, etc).\n"
        "🔹 */disenar* (con foto): Analiza un dibujo de circuito.\n"
        "🔹 */kicad*: Genera el esquemático KiCad desde un diseño.\n"
        "🔹 */pcb*: Genera el layout PCB desde un diseño.\n"
        "🔹 */fabricar*: Crea el paquete de Gerbers (.zip) para manufactura.\n"
        "🔹 */gcode*: Genera el G-Code (.nc) para fresado CNC desde los Gerbers.\n"
        "🔹 */send_cnc [puerto] [archivo]*: Envía G-Code a la CNC.\n"
        "🔹 */ayuda_cnc*: Envía la documentación sobre CNC.\n\n"
        "--- *Utilidades Generales* ---\n"
        "🔹 */investigar [tema]*: Busca en internet y resume.\n"
        "🔹 */reporte [tema]*: Genera un informe técnico detallado en docs/.\n"
        "🔹 */resumir [url]*: Lee una web y te dice de qué trata.\n"
        "🔹 */resumir_archivo [nombre]*: Lee un archivo de `docs/` y lo resume.\n"
        "🔹 */traducir [texto/archivo]*: Traduce al español.\n\n"
        "--- *Memoria y Recordatorios* ---\n"
        "🔹 */recordar [dato]*: Guarda una nota en mi memoria.\n"
        "🔹 */memorias*: Lista tus últimos recuerdos guardados.\n"
        "🔹 */olvidar [ID]*: Borra un recuerdo específico.\n"
        "🔹 */ingestar [archivo]*: Agrega un PDF de `docs/` a la memoria RAG.\n"
        "🔹 */recordatorio [HH:MM] [msg]*: Configura una alarma diaria.\n"
        "🔹 */mis_recordatorios*: Muestra tus alarmas activas.\n"
        "🔹 */borrar_recordatorio [ID]*: Elimina una alarma específica.\n\n"
        "--- *Administración y Estado* ---\n"
        "🔹 */status*: Muestra CPU y RAM del servidor.\n"
        "🔹 */limpiar*: Elimina archivos temporales y cachés.\n"
        "🔹 */reiniciar*: Borra historial y restablece personalidad.\n"
        "🔹 */resume [ID]*: Lista o reanuda una charla del historial.\n"
        "🔹 */borrar_sesion [ID]*: Elimina una charla del historial.\n"
        "🔹 */buscar_sesion [palabra]*: Busca charlas por palabra clave.\n"
        "🔹 */exportar_sesion [ID]*: Exporta una charla a un archivo MD.\n"
        "🔹 */modo [tipo]*: Cambia mi personalidad (serio, sarcastico...).\n"
        "🔹 */idioma [es/en]*: Cambia el idioma en el que te escucho.\n"
        "🔹 */usuarios*: Muestra los últimos 5 IDs registrados.\n"
        "🔹 */broadcast [msg]*: Envía un mensaje a todos (Admin).\n"
        "🔹 */ayuda*: Muestra este menú."
    )

def _handle_send_cnc(msg, sender_id, run_tool):
    parts = msg.split()
    if len(parts) < 3:
        return "⚠️ Uso: `/send_cnc [puerto] [archivo.nc]`\nEj: `/send_cnc /dev/ttyUSB0 mi_logo.nc`"
    
    port, gcode_file = parts[1], parts[2]
    run_tool("telegram_tool.py", ["--action", "send", "--message", f"🚨 *¡ATENCIÓN!* 🚨\nIniciando envío de `{gcode_file}` a la CNC en el puerto `{port}`.\n\n*Asegúrate de que la fresa esté en una posición segura.*", "--chat-id", sender_id])
    time.sleep(2)

    res = run_tool("send_gcode.py", ["--port", port, "--file", gcode_file])
    if res and res.get("status") == "success":
        return f"✅ Proceso de fresado para `{gcode_file}` completado."
    else:
        return "❌ Error durante el envío a la CNC. Revisa los logs de la terminal."

def _handle_kicad(msg, sender_id, run_tool):
    design_file = os.path.join(".tmp", "current_design.json")
    if not os.path.exists(design_file):
        return "⚠️ No hay un diseño activo en memoria. Primero usa `/diseñar` con una foto de tu circuito."

    run_tool("telegram_tool.py", ["--action", "send", "--message", "⚙️ Generando Netlist para KiCad...", "--chat-id", sender_id])
    output_net = os.path.join(".out", "circuito_generado.kicad_sch")
    res = run_tool("json_to_kicad_netlist.py", ["--json", design_file, "--output", output_net])

    if not (res and res.get("status") == "success" and os.path.exists(output_net)):
        err = res.get("message") if res else "Error desconocido"
        details = res.get("details", "")
        return f"❌ Error generando la netlist: {err}\n{details}"

    run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", output_net, "--chat-id", sender_id, "--caption", "KiCad File (.kicad_sch)\nGenerado para KiCad 9.0"])
    
    run_tool("telegram_tool.py", ["--action", "send", "--message", "🎨 Generando vista previa del esquemático...", "--chat-id", sender_id])
    render_script_path = os.path.join("execution", "render_sch.py")
    if os.path.exists(render_script_path):
        with open(render_script_path, "r") as f:
            render_code = f.read()
        
        inj_render = "import sys\nsys.argv = ['render_sch.py', '/mnt/out/circuito_generado.kicad_sch', '/mnt/out/sch_preview.png']\n"
        res_render = run_tool("run_sandbox.py", ["--code", inj_render + render_code])
        expected_png = os.path.join(".out", "sch_preview.png")
        if res_render.get("status") == "success" and os.path.exists(expected_png):
            run_tool("telegram_tool.py", ["--action", "send-photo", "--file-path", expected_png, "--chat-id", sender_id, "--caption", "👁️ Vista Previa Esquemático"])

    return "✅ Archivo generado como `circuito_generado.kicad_sch`. Listo para importar en KiCad 9.0."

def _handle_pcb(msg, sender_id, run_tool):
    design_file = os.path.join(".tmp", "current_design.json")
    if not os.path.exists(design_file):
        return "⚠️ No hay un diseño activo en memoria. Primero usa `/diseñar` con una foto de tu circuito."

    run_tool("telegram_tool.py", ["--action", "send", "--message", "⚙️ Generando archivo PCB (.kicad_pcb) automáticamente...", "--chat-id", sender_id])
    output_script_path = os.path.join(".tmp", "create_pcb_script.py")
    res_gen = run_tool("generate_kicad_pcb_script.py", ["--json", design_file, "--output", output_script_path])

    if not (res_gen and res_gen.get("status") == "success" and os.path.exists(output_script_path)):
        err = res_gen.get("message") if res_gen else "Error desconocido"
        return f"❌ Error generando script de PCB: {err}"

    try:
        with open(output_script_path, "r") as f:
            script_content = f.read()

        res_exec = run_tool("run_sandbox.py", ["--code", script_content])
        routing_summary = ""
        if res_exec.get("stdout"):
            for line in res_exec.get("stdout").splitlines():
                if "ROUTING_SUMMARY:" in line:
                    summary_data = line.replace("ROUTING_SUMMARY:", "").strip()
                    try:
                        parts = {p.split('=')[0].strip(): int(p.split('=')[1]) for p in summary_data.split(',')}
                        routed, failed = parts.get('Routed', 0), parts.get('Failed', 0)
                        total = parts.get('Total', routed + failed)
                        if total > 0:
                            success_rate = (routed / total) * 100
                            emoji = "✅" if success_rate == 100 else ("⚠️" if success_rate > 50 else "❌")
                            routing_summary = f"{emoji} *Resumen de Enrutado:*\n- Conexiones Trazadas: {routed}/{total} ({success_rate:.0f}%)\n- Conexiones Fallidas: {failed}"
                    except Exception as e:
                        print(f"   [!] Error parsing routing summary: {e}")
                        routing_summary = f"📊 Resumen: {summary_data}"
                    break

        expected_pcb = os.path.join(".out", "circuito_generado.kicad_pcb")
        if res_exec.get("status") == "success" and os.path.exists(expected_pcb):
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", expected_pcb, "--chat-id", sender_id, "--caption", "✅ PCB Generado Automáticamente (.kicad_pcb)"])
            
            run_tool("telegram_tool.py", ["--action", "send", "--message", "🎨 Generando vista previa de la placa...", "--chat-id", sender_id])
            render_script_path = os.path.join("execution", "render_pcb.py")
            if os.path.exists(render_script_path):
                with open(render_script_path, "r") as f:
                    render_code = f.read()
                inj_render = "import sys\nsys.argv = ['render_pcb.py', '/mnt/out/circuito_generado.kicad_pcb', '/mnt/out/pcb_preview.png']\n"
                res_render = run_tool("run_sandbox.py", ["--code", inj_render + render_code])
                expected_png = os.path.join(".out", "pcb_preview.png")
                if res_render.get("status") == "success" and os.path.exists(expected_png):
                    final_caption = "👁️ Vista Previa (Top Layer)"
                    if routing_summary:
                        final_caption += f"\n\n{routing_summary}"
                    run_tool("telegram_tool.py", ["--action", "send-photo", "--file-path", expected_png, "--chat-id", sender_id, "--caption", final_caption])
                if routing_summary and "❌" in routing_summary:
                    return "⚠️ El archivo PCB fue generado, pero algunas conexiones no pudieron enrutarse automáticamente. Revisa la ubicación de los componentes."
                return "¡Éxito! He generado el archivo de placa y las pistas automáticamente."
        else:
            stdout = res_exec.get("stdout", "")
            stderr = res_exec.get("stderr", "")
            msg_err = res_exec.get("message", "")
            err_log = f"{stdout}\n{msg_err}\n{stderr}".strip()
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", output_script_path, "--chat-id", sender_id, "--caption", "Script de KiCad PCB (Python) - Fallback"])
            return (
                f"⚠️ Error en la generación automática de la placa (PCB).\n"
                f"Detalle del error:\n```\n{err_log[-1000:] if err_log else 'Error desconocido'}\n```\n\n"
                "Te envío el script para que lo ejecutes manualmente en KiCad > Consola de Scripting."
            )
    except Exception as e:
        return f"❌ Error interno ejecutando script: {e}"

def _handle_fabricar(msg, sender_id, run_tool):
    pcb_file_host = os.path.join(".out", "circuito_generado.kicad_pcb")
    if not os.path.exists(pcb_file_host):
        return "⚠️ No hay un archivo de placa (.kicad_pcb) activo. Primero usa `/pcb` para generar uno."

    run_tool("telegram_tool.py", ["--action", "send", "--message", "🏭 Generando paquete de fabricación (Gerbers + Drills)...", "--chat-id", sender_id])
    output_zip_name = f"Fab_Pack_{int(time.time())}.zip"
    board_file_sandbox = "circuito_generado.kicad_pcb"

    try:
        gerber_script_path = os.path.join("execution", "generate_gerbers.py")
        with open(gerber_script_path, "r") as f:
            script_content = f.read()

        argv_injection = f"import sys\nimport argparse\nsys.argv = ['generate_gerbers.py', '--board', '/mnt/out/{board_file_sandbox}', '--output-zip', '/mnt/out/{output_zip_name}']\n"
        code_to_run = argv_injection + script_content
        res_exec = run_tool("run_sandbox.py", ["--code", code_to_run])
        expected_zip_path = os.path.join(".out", output_zip_name)

        if res_exec.get("status") == "success" and os.path.exists(expected_zip_path):
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", expected_zip_path, "--chat-id", sender_id, "--caption", "✅ Paquete de Fabricación (ZIP)\nListo para enviar a JLCPCB, PCBWay, etc."])
            return "¡Éxito! Tu paquete de fabricación está listo."
        else:
            err_log = res_exec.get("stderr", "") or res_exec.get("message", "")
            return f"❌ Error generando los Gerbers: `{err_log[:200]}...`"
    except Exception as e:
        return f"❌ Error interno preparando la generación de Gerbers: {e}"

def _handle_gcode(msg, sender_id, run_tool):
    # Encontrar el último paquete de fabricación
    fab_packs = glob.glob(os.path.join(".out", "Fab_Pack_*.zip"))
    if not fab_packs:
        return "⚠️ No se encontró un paquete de fabricación. Primero usa `/fabricar` para generar los Gerbers."
    
    latest_fab_pack = max(fab_packs, key=os.path.getctime)
    print(f"   ⚙️ Usando el paquete de fabricación más reciente: {os.path.basename(latest_fab_pack)}")

    run_tool("telegram_tool.py", ["--action", "send", "--message", f"⚙️ Procesando Gerbers de `{os.path.basename(latest_fab_pack)}` para generar G-Code...", "--chat-id", sender_id])

    # Directorio temporal para descomprimir los Gerbers (DENTRO de .out para que el Sandbox lo vea)
    temp_gerber_dir = os.path.join(".out", "unzipped_gerbers")
    if os.path.exists(temp_gerber_dir):
        shutil.rmtree(temp_gerber_dir)
    os.makedirs(temp_gerber_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(latest_fab_pack, 'r') as zip_ref:
            zip_ref.extractall(temp_gerber_dir)
        
        output_nc_filename = f"CNC_Milling_{int(time.time())}.nc"
        output_nc_path = os.path.join(".out", output_nc_filename)

        # Preparamos la ejecución en el Sandbox
        gcode_script_path = os.path.join("execution", "generate_gcode.py")
        if not os.path.exists(gcode_script_path):
            return "❌ Error: No se encontró el script `execution/generate_gcode.py`."

        with open(gcode_script_path, "r") as f:
            script_content = f.read()

        # Inyectamos los argumentos para que el script funcione dentro del Docker
        # Las rutas deben ser las que el contenedor ve (/mnt/out/...)
        container_input_dir = "/mnt/out/unzipped_gerbers"
        container_output_file = f"/mnt/out/{output_nc_filename}"
        
        argv_injection = (
            f"import sys\n"
            f"sys.argv = ['generate_gcode.py', '--input-dir', '{container_input_dir}', '--output-file', '{container_output_file}']\n"
        )
        
        res = run_tool("run_sandbox.py", ["--code", argv_injection + script_content])

        if res and res.get("status") == "success" and os.path.exists(output_nc_path):
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", output_nc_path, "--chat-id", sender_id, "--caption", "✅ G-Code de fresado (.nc) generado."])
            
            # Enviar vista previa si existe
            preview_path_container = res.get("preview")
            if preview_path_container:
                preview_filename = os.path.basename(preview_path_container)
                preview_path_host = os.path.join(".out", preview_filename)
                if os.path.exists(preview_path_host):
                    run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", preview_path_host, "--chat-id", sender_id, "--caption", "👁️ Vista Previa de Rutas (SVG)"])

            return "¡Éxito! Tu G-Code está listo. He adjuntado una vista previa SVG para que veas las rutas de corte."
        else:
            err_msg = res.get("message", "Error desconocido.") if res else "El script no devolvió respuesta."
            
            # Intentar limpiar el mensaje si es JSON (para mostrar el error real de pcb2gcode)
            try:
                err_json = json.loads(err_msg)
                if isinstance(err_json, dict) and "message" in err_json:
                    err_msg = err_json["message"]
            except:
                pass

            # Si el error es FileNotFoundError de pcb2gcode, damos un mensaje más claro
            if "pcb2gcode" in err_msg and "not found" in err_msg.lower():
                return "❌ Error: `pcb2gcode` no está instalado en el sandbox. Por favor, ejecuta `python execution/build_sandbox.py` para reconstruir la imagen."
            return f"❌ Error generando el G-Code:\n`{err_msg[:300]}`"

    finally:
        if os.path.exists(temp_gerber_dir):
            shutil.rmtree(temp_gerber_dir)

def _handle_py(msg, sender_id, run_tool):
    raw_input = msg.split(" ", 1)[1].strip()

    forbidden = ["build_sandbox.py", "listen_telegram.py", "init_project.py", "deploy_to_github.py", "check_system_health.py"]
    if any(f in raw_input for f in forbidden):
        return "⛔ *Acción Denegada*: Este script es administrativo y debe ejecutarse en la terminal del servidor (Host), no dentro del Sandbox."

    parts = raw_input.split()
    script_candidate = parts[0]
    script_args = parts[1:]
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
            argv_injection = f"import sys\nsys.argv = {['script.py'] + script_args}\n"
            code_to_run = argv_injection + script_content
            print(f"   🐍 Enviando script al Sandbox (Docker 🐳) con args: {script_args}")
        except Exception as e:
            code_to_run = raw_input
            print(f"   ⚠️ Error leyendo script: {e}")
    else:
        code_to_run = raw_input
        print(f"   🐍 Ejecutando código raw en Sandbox (Docker 🐳): {code_to_run}")

    res = run_tool("run_sandbox.py", ["--code", code_to_run])
    reply_text = ""

    if not (res and res.get("status") == "success"):
        return f"❌ *Error en Sandbox:*\n{res.get('message', 'Error desconocido.')}"

    stdout = res.get("stdout", "")
    stderr = res.get("stderr", "")
    sent_file = False
    clean_stdout_lines = []

    if stdout:
        for line in stdout.splitlines():
            potential_path = line.strip()
            if potential_path.startswith('/mnt/out/'):
                filename = os.path.basename(potential_path)
                local_path = os.path.join(".out", filename)
                if os.path.exists(local_path):
                    is_image = any(filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp'])
                    action = "send-photo" if is_image else "send-document"
                    caption = f"{'Imagen' if is_image else 'Archivo'} generado: {filename}"
                    run_tool("telegram_tool.py", ["--action", action, "--file-path", local_path, "--chat-id", sender_id, "--caption", caption])
                    sent_file = True
                    continue
            clean_stdout_lines.append(line)

    clean_stdout = "\n".join(clean_stdout_lines)
    if clean_stdout or stderr:
        reply_text = "📦 *Resultado del Sandbox:*\n\n"
        if clean_stdout:
            reply_text += f"*Salida:*\n```\n{clean_stdout}\n```\n"
        if stderr:
            reply_text += f"*Errores:*\n```\n{stderr}\n```\n"
    elif not sent_file:
        reply_text = "📦 *Resultado del Sandbox:*\n\n_El código se ejecutó sin producir salida._"
    
    return reply_text

def _handle_freecad(msg, sender_id, run_tool):
    description = msg.split(" ", 1)[1] if " " in msg else ""
    if not description:
        return "⚠️ Uso: /freecad [descripción del objeto 3D]\nEj: `/freecad una caja de 20x30x10 mm`"

    run_tool("telegram_tool.py", ["--action", "send", "--message", f"🧠 Interpretando tu diseño 3D: '{description}'...", "--chat-id", sender_id])

    # 0. Cargar contexto anterior (si existe)
    last_params_path = os.path.join(".tmp", "last_3d_params.json")
    last_params_context = "Ninguno"
    if os.path.exists(last_params_path):
        try:
            with open(last_params_path, "r") as f:
                last_params_context = f.read()
        except:
            pass

    # 1. Usar LLM para extraer parámetros
    prompt = f"""
    Analiza la siguiente descripción de un objeto 3D y extrae sus parámetros en formato JSON.
    
    CONTEXTO ACTUAL (Último objeto creado):
    {last_params_context}
    
    INSTRUCCIONES:
    - Si el usuario pide una MODIFICACIÓN (ej: "hazlo más alto", "ahora rojo", "cambia radio a 5"), toma el JSON del CONTEXTO ACTUAL y modifica solo los valores mencionados.
    - Si el usuario pide un OBJETO NUEVO (ej: "crea un cubo", "un cilindro"), ignora el contexto y genera un JSON nuevo.

    Los tipos de 'shape' válidos son: "box", "cylinder", "sphere", "cone", "torus", "gear".
    - Para 'box': 'length', 'width', 'height'.
    - Para 'cylinder': 'radius', 'height'.
    - Para 'sphere': 'radius'.
    - Para 'cone': 'radius1' (base), 'radius2' (superior, 0 si no se especifica), 'height'.
    - Para 'torus': 'radius1' (anillo), 'radius2' (tubo).
    - Para 'gear': 'teeth' (int), 'module' (float, default 1.0), 'height' (float, default 5.0), 'pressure_angle' (float, default 20.0). Si se menciona un agujero central, extrae 'hole_diameter' (float, diámetro).
    
    PARÁMETROS OPCIONALES (para cualquier forma):
    - 'hole_radius': para un agujero central genérico (no aplica a 'gear' si se usa 'hole_diameter').
    - 'stud_radius', 'stud_height': para un pivote superior (default height 10).
    - 'rotate_axis' ('x','y','z'), 'rotate_angle' (grados).
    - 'fillet_radius': para redondear bordes.
    - 'color': 'Red', 'Blue', 'Green', etc.
    - 'draw_axes': true, si se pide mostrar los ejes.

    REGLAS DE VALORES:
    - Si no se especifica una forma, asume 'box'.
    - Si faltan dimensiones, usa 10.0 como valor por defecto, a menos que la forma tenga su propio default (ej. 'gear').
    - Usa siempre números (int o float), no strings con "mm".
    
    Descripción: "{description}"
    
    Ejemplo de salida para "un cubo de 15mm":
    {{
      "shape": "box",
      "length": 15,
      "width": 15,
      "height": 15
    }}
    
    Ejemplo de salida para "un cilindro de radio 5 y altura 20":
    {{
      "shape": "cylinder",
      "radius": 5,
      "height": 20
    }}
    
    Ejemplo de salida para "una esfera de 10mm":
    {{
      "shape": "sphere",
      "radius": 10
    }}

    Ejemplo de salida para "un cono de altura 30 con radio 10":
    {{
      "shape": "cone",
      "radius1": 10,
      "radius2": 0,
      "height": 30
    }}
    
    Ejemplo de salida para "un cono truncado de radio 20 a 5 y altura 50":
    {{
      "shape": "cone",
      "radius1": 20,
      "radius2": 5,
      "height": 50
    }}
    
    Ejemplo de salida para "una dona de radio 20 y grosor 5":
    {{
      "shape": "torus",
      "radius1": 20,
      "radius2": 5
    }}
    
    Ejemplo de salida para "un cilindro de radio 10 y altura 30 con un agujero de 4mm":
    {{
      "shape": "cylinder",
      "radius": 10,
      "height": 30,
      "hole_radius": 4
    }}
    
    Ejemplo de salida para "un cubo de 20mm con un pivote de 5mm arriba":
    {{
      "shape": "box",
      "length": 20,
      "width": 20,
      "height": 20,
      "stud_radius": 5,
      "stud_height": 10
    }}
    
    Ejemplo de salida para "un cubo rojo de 20mm rotado 45 grados en Z con bordes redondeados de 2mm":
    {{
      "shape": "box",
      "length": 20,
      "width": 20,
      "height": 20,
      "color": "Red",
      "rotate_axis": "z",
      "rotate_angle": 45,
      "fillet_radius": 2
    }}
    
    Ejemplo de salida para "un cono de radio 10 mostrando los ejes":
    {{
      "shape": "cone",
      "radius1": 10,
      "radius2": 0,
      "height": 10,
      "draw_axes": true
    }}

    Ejemplo de salida para "un engranaje de 25 dientes con agujero central de 5mm":
    {{
      "shape": "gear",
      "teeth": 25,
      "module": 1.0,
      "height": 5.0,
      "pressure_angle": 20.0,
      "hole_diameter": 5.0
    }}

    Ejemplo de salida para "un piñón de 15 dientes, módulo 2":
    {{
      "shape": "gear",
      "teeth": 15,
      "module": 2.0,
      "height": 5.0,
      "pressure_angle": 20.0
    }}

    JSON de salida:
    """
    
    llm_res = run_tool("chat_with_llm.py", ["--prompt", prompt, "--no-rag"])
    
    params_json_str = ""
    if llm_res and "content" in llm_res:
        try:
            content = llm_res['content']
            if "```json" in content:
                params_json_str = content.split('```json')[1].split('```')[0].strip()
            elif "```" in content:
                params_json_str = content.split('```')[1].split('```')[0].strip()
            else:
                params_json_str = content.strip()
            
            json.loads(params_json_str) # Validar
            
            # Guardar contexto para la próxima
            with open(last_params_path, "w") as f:
                f.write(params_json_str)
        except (IndexError, json.JSONDecodeError):
             return f"❌ No pude interpretar los parámetros del diseño. El modelo devolvió: {llm_res['content']}"
    else:
        return "❌ Error al contactar al LLM para interpretar el diseño."

    run_tool("telegram_tool.py", ["--action", "send", "--message", f"⚙️ Generando modelo 3D con parámetros: `{params_json_str}`...", "--chat-id", sender_id])

    output_script_path = os.path.join(".tmp", "create_model_script.py")
    res_gen = run_tool("generate_freecad_script.py", ["--params", params_json_str, "--output", output_script_path])

    if not (res_gen and res_gen.get("status") == "success"):
        return f"❌ Error generando el script de FreeCAD: {res_gen.get('message', 'Error desconocido')}"

    with open(output_script_path, "r") as f:
        script_content = f.read()
    
    res_exec = run_tool("run_sandbox.py", ["--code", script_content])

    if not (res_exec and res_exec.get("status") == "success"):
        err_log = res_exec.get("stderr", "") or res_exec.get("message", "")
        return f"❌ Error ejecutando el script de FreeCAD en el Sandbox: `{err_log[:200]}...`"

    # Extraer propiedades físicas del log
    phys_props = ""
    if res_exec.get("stdout"):
        for line in res_exec.get("stdout").splitlines():
            if "PROPERTIES:" in line:
                phys_props = line.replace("PROPERTIES:", "").strip()

    expected_stl = os.path.join(".out", "modelo_3d.stl")
    if os.path.exists(expected_stl):
        # --- Generar Vista Previa (Render) ---
        run_tool("telegram_tool.py", ["--action", "send", "--message", "🎨 Generando vista previa del modelo...", "--chat-id", sender_id])
        
        # Buscamos el PNG generado directamente por FreeCADGui dentro del sandbox
        expected_png = os.path.join(".out", "modelo_3d.png")
        if os.path.exists(expected_png):
            run_tool("telegram_tool.py", ["--action", "send-photo", "--file-path", expected_png, "--chat-id", sender_id, "--caption", "👁️ Vista Previa 3D (Renderizado Nativo)"])
            # Enviar también como documento para visualización externa (Solicitud del usuario)
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", expected_png, "--chat-id", sender_id, "--caption", "🖼️ Render PNG (Alta Calidad)"])
        else:
            # Extraer diagnóstico del stderr para informar al usuario
            stderr = res_exec.get("stderr", "")
            diag_msg = "Error desconocido en renderizado."
            for line in stderr.splitlines():
                if "Warning:" in line or "Error:" in line:
                    diag_msg = line.strip()
            
            run_tool("telegram_tool.py", ["--action", "send", "--message", f"⚠️ No se generó el archivo PNG de vista previa.\n\n📍 Ubicación esperada: `.out/modelo_3d.png`\n🔍 Diagnóstico: `{diag_msg}`", "--chat-id", sender_id])

        # Enviar STL
        caption_stl = "✅ Modelo 3D (STL) para impresión."
        if phys_props:
            caption_stl += f"\n\n📏 {phys_props}"
        run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", expected_stl, "--chat-id", sender_id, "--caption", caption_stl])

        # Enviar OBJ si existe
        expected_obj = os.path.join(".out", "modelo_3d.obj")
        if os.path.exists(expected_obj):
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", expected_obj, "--chat-id", sender_id, "--caption", "📦 Modelo 3D (OBJ)"])
            
        # Enviar STEP si existe
        expected_step = os.path.join(".out", "modelo_3d.step")
        if os.path.exists(expected_step):
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", expected_step, "--chat-id", sender_id, "--caption", "⚙️ Modelo CAD (STEP)"])

        return "¡Éxito! He generado tu modelo 3D."
    else:
        return "⚠️ Se ejecutó el script pero no se encontraron los archivos de salida."

def _handle_disenar_sin_foto(msg, sender_id, run_tool):
    return "📸 El comando `/disenar` necesita una *foto adjunta*.\n\nEnvía una foto de tu circuito con el caption `/disenar [descripción]`.\nEjemplo: adjunta la foto y escribe `/disenar amplificador de audio`."

COMMAND_HANDLERS = {
    "/investigar": _handle_investigar,
    "/research": _handle_investigar,
    "/reporte": _handle_reporte,
    "/report": _handle_reporte,
    "/recordatorio": _handle_recordatorio,
    "/remind": _handle_recordatorio,
    "/borrar_recordatorios": _handle_borrar_recordatorios,
    "/clear_reminders": _handle_borrar_recordatorios,
    "/borrar_recordatorio": _handle_borrar_recordatorio_id,
    "/delete_reminder": _handle_borrar_recordatorio_id,
    "/mis_recordatorios": _handle_mis_recordatorios,
    "/my_reminders": _handle_mis_recordatorios,
    "/traducir": _handle_traducir,
    "/translate": _handle_traducir,
    "/idioma": _handle_idioma,
    "/lang": _handle_idioma,
    "/ayuda_cnc": _handle_ayuda_cnc,
    "/ingestar": _handle_ingestar,
    "/ingest": _handle_ingestar,
    "/resumir_archivo": _handle_resumir_archivo,
    "/summarize_file": _handle_resumir_archivo,
    "/resumir": _handle_resumir,
    "/summarize": _handle_resumir,
    "/recordar": _handle_recordar,
    "/remember": _handle_recordar,
    "/memorias": _handle_memorias,
    "/memories": _handle_memorias,
    "/olvidar": _handle_olvidar,
    "/forget": _handle_olvidar,
    "/broadcast": _handle_broadcast,
    "/anuncio": _handle_broadcast,
    "/status": _handle_status,
    "/usuarios": _handle_usuarios,
    "/users": _handle_usuarios,
    "/versiones": _handle_versiones,
    "/modo": _handle_modo,
    "/reiniciar": _handle_reiniciar,
    "/reset": _handle_reiniciar,
    "/resume": _handle_resume,
    "/borrar_sesion": _handle_borrar_sesion,
    "/delete_session": _handle_borrar_sesion,
    "/buscar_sesion": _handle_buscar_sesion,
    "/search_session": _handle_buscar_sesion,
    "/exportar_sesion": _handle_exportar_sesion,
    "/export_session": _handle_exportar_sesion,
    "/limpiar": _handle_limpiar,
    "/clean": _handle_limpiar,
    "/disenar": _handle_disenar_sin_foto,
    "/diseñar": _handle_disenar_sin_foto,
    "/ayuda": _handle_ayuda,
    "/help": _handle_ayuda,
    "/send_cnc": _handle_send_cnc,
    "/netlist": _handle_kicad,
    "/kicad": _handle_kicad,
    "/pcb": _handle_pcb,
    "/layout": _handle_pcb,
    "/freecad": _handle_freecad,
    "/3d": _handle_freecad,
    "/fabricar": _handle_fabricar,
    "/gerbers": _handle_fabricar,
    "/gcode": _handle_gcode,
}

def handle_command_text(msg, sender_id, run_tool):
    if msg.startswith("/py "):
        return _handle_py(msg, sender_id, run_tool)

    command = msg.split(" ", 1)[0].lower()
    handler = COMMAND_HANDLERS.get(command)

    if handler:
        return handler(msg, sender_id, run_tool)

    return ""