import json
import os
import datetime
import time
from execution.listen_telegram_helpers import load_config, save_config, PERSONAS, set_persona
from execution.db_manager import add_reminder, delete_reminders_for_user, get_all_users, get_reminders_by_user, delete_reminder_by_id

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
        filename = f"Reporte_Medico_{safe_topic}.md"
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
    print("   🔄 Reiniciando sesión...")
    run_tool("chat_with_llm.py", ["--prompt", "/clear"])
    set_persona("default")
    return "🔄 *Sistema reiniciado.*\n\n- Historial de conversación borrado.\n- Personalidad restablecida a 'Default'."

def _handle_ayuda(msg, sender_id, run_tool):
    return (
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
    output_net = os.path.join(".tmp", "circuito_generado.kicad_sch")
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
        expected_png = os.path.join(".tmp", "sch_preview.png")
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

        expected_pcb = os.path.join(".tmp", "circuito_generado.kicad_pcb")
        if res_exec.get("status") == "success" and os.path.exists(expected_pcb):
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", expected_pcb, "--chat-id", sender_id, "--caption", "✅ PCB Generado Automáticamente (.kicad_pcb)"])
            
            run_tool("telegram_tool.py", ["--action", "send", "--message", "🎨 Generando vista previa de la placa...", "--chat-id", sender_id])
            render_script_path = os.path.join("execution", "render_pcb.py")
            if os.path.exists(render_script_path):
                with open(render_script_path, "r") as f:
                    render_code = f.read()
                inj_render = "import sys\nsys.argv = ['render_pcb.py', '/mnt/out/circuito_generado.kicad_pcb', '/mnt/out/pcb_preview.png']\n"
                res_render = run_tool("run_sandbox.py", ["--code", inj_render + render_code])
                expected_png = os.path.join(".tmp", "pcb_preview.png")
                if res_render.get("status") == "success" and os.path.exists(expected_png):
                    final_caption = "👁️ Vista Previa (Top Layer)"
                    if routing_summary:
                        final_caption += f"\n\n{routing_summary}"
                    run_tool("telegram_tool.py", ["--action", "send-photo", "--file-path", expected_png, "--chat-id", sender_id, "--caption", final_caption])
            return "¡Éxito! He generado el archivo de placa automáticamente usando el motor de KiCad en el servidor."
        else:
            err_log = res_exec.get("stderr", "") or res_exec.get("message", "")
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", output_script_path, "--chat-id", sender_id, "--caption", "Script de KiCad PCB (Python) - Fallback"])
            return (
                f"⚠️ No pude generar el PCB automáticamente (¿Falta instalar `kicad` en el entorno Docker?).\n"
                f"Error: `{err_log[:100]}...`\n\n"
                "Te envío el script para que lo ejecutes manualmente en KiCad > Consola de Scripting."
            )
    except Exception as e:
        return f"❌ Error interno ejecutando script: {e}"

def _handle_fabricar(msg, sender_id, run_tool):
    pcb_file_host = os.path.join(".tmp", "circuito_generado.kicad_pcb")
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
        expected_zip_path = os.path.join(".tmp", output_zip_name)

        if res_exec.get("status") == "success" and os.path.exists(expected_zip_path):
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", expected_zip_path, "--chat-id", sender_id, "--caption", "✅ Paquete de Fabricación (ZIP)\nListo para enviar a JLCPCB, PCBWay, etc."])
            return "¡Éxito! Tu paquete de fabricación está listo."
        else:
            err_log = res_exec.get("stderr", "") or res_exec.get("message", "")
            return f"❌ Error generando los Gerbers: `{err_log[:200]}...`"
    except Exception as e:
        return f"❌ Error interno preparando la generación de Gerbers: {e}"

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
                local_path = os.path.join(".tmp", filename)
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

    # 1. Usar LLM para extraer parámetros
    prompt = f"""
    Analiza la siguiente descripción de un objeto 3D y extrae sus parámetros en formato JSON.
    Los tipos de 'shape' válidos son: "box", "cylinder", "sphere", "cone".
    Si es una caja, extrae 'length', 'width', 'height'.
    Si es un cilindro, extrae 'radius', 'height'.
    Si es una esfera, extrae 'radius'.
    Si es un cono, extrae 'radius1' (radio de la base), 'radius2' (radio superior, 0 si no se especifica), y 'height'.
    Si no se especifica una forma, asume 'box'.
    Si faltan dimensiones, usa 10 como valor por defecto.
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

    expected_stl = os.path.join(".tmp", "modelo_3d.stl")
    if os.path.exists(expected_stl):
        # --- Generar Vista Previa (Render) ---
        run_tool("telegram_tool.py", ["--action", "send", "--message", "🎨 Generando vista previa del modelo...", "--chat-id", sender_id])
        
        # Buscamos el PNG generado directamente por FreeCADGui dentro del sandbox
        expected_png = os.path.join(".tmp", "modelo_3d.png")
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
            
            run_tool("telegram_tool.py", ["--action", "send", "--message", f"⚠️ No se generó el archivo PNG de vista previa.\n\n📍 Ubicación esperada: `.tmp/modelo_3d.png`\n🔍 Diagnóstico: `{diag_msg}`", "--chat-id", sender_id])

        run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", expected_stl, "--chat-id", sender_id, "--caption", "✅ Modelo 3D (STL) para impresión."])
        return "¡Éxito! He generado tu modelo 3D."
    else:
        return "⚠️ Se ejecutó el script pero no se encontraron los archivos de salida."

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
    "/modo": _handle_modo,
    "/reiniciar": _handle_reiniciar,
    "/reset": _handle_reiniciar,
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
}

def handle_command_text(msg, sender_id, run_tool):
    if msg.startswith("/py "):
        return _handle_py(msg, sender_id, run_tool)

    command = msg.split(" ", 1)[0].lower()
    handler = COMMAND_HANDLERS.get(command)

    if handler:
        return handler(msg, sender_id, run_tool)

    return ""