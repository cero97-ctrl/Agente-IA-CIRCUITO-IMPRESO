def handle_document(msg, sender_id, run_tool):
    import os
    import json
    reply_text = ""
    parts = msg.replace("__DOCUMENT__:", "").split("|||")
    file_id = parts[0]
    file_name = parts[1]
    caption = parts[2] if len(parts) > 2 else ""
    
    print(f"   📄 Documento recibido: {file_name}. Descargando...")
    run_tool("telegram_tool.py", ["--action", "send", "--message", f"📂 Recibí `{file_name}`. Leyendo contenido...", "--chat-id", sender_id])
    
    local_path = os.path.join(".tmp", file_name)
    run_tool("telegram_tool.py", ["--action", "download", "--file-id", file_id, "--dest", local_path])
    
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
            reply_text = "⚠️ El documento parece estar vacío o es una imagen escaneada sin texto."
        else:
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
    return reply_text
