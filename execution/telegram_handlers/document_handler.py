def handle_document(msg, sender_id, run_tool):
    import os
    import json
    import shutil
    reply_text = ""
    parts = msg.replace("__DOCUMENT__:", "").split("|||")
    file_id = parts[0]
    file_name = parts[1]
    caption = parts[2] if len(parts) > 2 else ""
    
    print(f"   📄 Documento recibido: {file_name}. Descargando...")
    run_tool("telegram_tool.py", ["--action", "send", "--message", f"📂 Recibí `{file_name}`. Leyendo contenido...", "--chat-id", sender_id])
    
    local_path = os.path.join(".tmp", file_name)
    run_tool("telegram_tool.py", ["--action", "download", "--file-id", file_id, "--dest", local_path])
    
    # Asegurar que el archivo esté disponible en el volumen del Sandbox (.out)
    shutil.copy(local_path, os.path.join(".out", file_name))
    path_in_sandbox = f"/mnt/out/{file_name}"

    # --- Lógica de Integración de Ruteado (Specctra Session .ses) ---
    if file_name.lower().endswith(".ses"):
        run_tool("telegram_tool.py", ["--action", "send", "--message", "🛰️ Archivo de sesión de DeepPCB detectado. Fusionando pistas...", "--chat-id", sender_id])
        
        merge_code = f'''
import os
import subprocess
import time
import sys

# Asegurar entorno headless para el motor de KiCad
os.environ["DISPLAY"] = ":99"
if os.system("pgrep Xvfb > /dev/null") != 0:
    subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1024x768x24", "-ac", "+extension", "GLX", "+render", "-noreset"])
    time.sleep(1)

try:
    import pcbnew
    pcb_path = "/mnt/out/circuito_generado.kicad_pcb"
    ses_path = "{path_in_sandbox}"
    if not os.path.exists(pcb_path):
        print("MERGE_FAIL: No se encontró el archivo .kicad_pcb original.")
    else:
        board = pcbnew.LoadBoard(pcb_path)
        if pcbnew.ImportSpecctraSession(board, ses_path):
            pcbnew.SaveBoard(pcb_path, board)
            print("MERGE_OK")
        else:
            print("MERGE_FAIL: Error en la importación de la sesión.")
except Exception as e:
    print(f"MERGE_EXCEPTION: {{str(e)}}")
'''
        res_exec = run_tool("run_sandbox.py", ["--code", merge_code])
        
        if "MERGE_OK" in res_exec.get("stdout", ""):
            pcb_updated = os.path.join(".out", "circuito_generado.kicad_pcb")
            run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", pcb_updated, "--chat-id", sender_id, "--caption", "✅ ¡Enrutado completado!\\nHe integrado las pistas de DeepPCB en tu diseño. Ya puedes usar `/fabricar`."])
            return "Placa actualizada con éxito."
        else:
            error_msg = res_exec.get("stdout", "") or res_exec.get("message", "Error desconocido")
            return f"❌ Falló la integración de pistas: `{error_msg[:300]}`"

    # --- Lógica de Resumen de Documentos Técnicos (PDF) ---
    if file_name.lower().endswith(".pdf"):
        read_code = (
            f"from pypdf import PdfReader; "
            f"reader = PdfReader('{path_in_sandbox}'); "
            f"print('\\n'.join([page.extract_text() for page in reader.pages]))"
        )
        res_sandbox = run_tool("run_sandbox.py", ["--code", read_code])
        if res_sandbox and res_sandbox.get("status") == "success":
            content = res_sandbox.get("stdout", "")
            if not content.strip():
                return "⚠️ El PDF parece ser una imagen o está vacío."
            
            analysis_prompt = f"Resume los puntos clave de este documento técnico de ingeniería:\n\n{content[:12000]}"
            run_tool("telegram_tool.py", ["--action", "send", "--message", "🧠 Analizando documento...", "--chat-id", sender_id])
            llm_res = run_tool("chat_with_llm.py", ["--prompt", analysis_prompt])
            return llm_res.get("content", "❌ Error al generar el resumen.")
        else:
            return f"❌ Error leyendo el PDF: {res_sandbox.get('message')}"

    return f"📂 Archivo `{file_name}` recibido y guardado en el servidor."
