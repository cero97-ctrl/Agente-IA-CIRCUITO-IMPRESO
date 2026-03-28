def handle_photo(msg, sender_id, run_tool):
    import time
    import os
    import json
    
    parts = msg.replace("__PHOTO__:", "").split("|||")
    file_id = parts[0]
    caption = parts[1] if len(parts) > 1 else "Describe esta imagen."
    if not caption.strip(): caption = "Describe qué ves en esta imagen."
    
    print(f"   📸 Foto recibida. Caption: '{caption}'")
    
    # Descargar
    filename = f"photo_{int(time.time())}.jpg"
    local_path = os.path.join(".tmp", filename)
    run_tool("telegram_tool.py", ["--action", "download", "--file-id", file_id, "--dest", local_path])
    
    # DECISIÓN: ¿Analizar, G-Code o Gerber?
    caption_lower = caption.lower()
    
    reply_text = ""
    
    # Prioridad 1: Diseño de Circuitos (Comando explícito)
    if "/diseñar" in caption_lower or "/disenar" in caption_lower or "/design" in caption_lower:
        design_prompt = caption.lower().replace("/diseñar", "").replace("/disenar", "").replace("/design", "").strip()
        if not design_prompt:
            design_prompt = "un circuito electrónico genérico. Identifica componentes y conexiones."
            run_tool("telegram_tool.py", ["--action", "send", "--message", "⚠️ No incluiste una descripción, así que intentaré deducir la función del circuito.", "--chat-id", sender_id])

        run_tool("telegram_tool.py", ["--action", "send", "--message", f"🤖 ¡Entendido! Analizando tu dibujo para: '{design_prompt}'.\nDame un momento para pensar como ingeniero...", "--chat-id", sender_id])
        
        # Usamos el script específico de análisis de circuitos
        res = run_tool("analyze_circuit_drawing.py", ["--image", local_path, "--prompt", design_prompt])
        
        if res and res.get("description"):
            json_content = res.get("description")
            if "```" in json_content:
                json_content = json_content.replace("```json", "").replace("```", "").strip()

            is_valid_json = False
            for i in range(3): 
                try:
                    json.loads(json_content)
                    is_valid_json = True
                    break 
                except json.JSONDecodeError as e:
                    print(f"   ⚠️ JSON inválido detectado (intento {i+1}). Pidiendo corrección al LLM. Error: {e}")
                    if i == 0: 
                        run_tool("telegram_tool.py", ["--action", "send", "--message", "🤔 El formato de mi respuesta inicial no era correcto. Intentando corregirlo...", "--chat-id", sender_id])
                    
                    correction_prompt = f"El siguiente texto JSON es inválido. Corrígelo y devuelve SÓLO el JSON.\nJSON Inválido:\n{json_content}"
                    
                    correction_res = run_tool("chat_with_llm.py", ["--prompt", correction_prompt])
                    if correction_res and "content" in correction_res:
                        json_content = correction_res["content"]
                        if "```" in json_content:
                            json_content = json_content.replace("```json", "").replace("```", "").strip()
                    else:
                        break 
            
            if not is_valid_json:
                reply_text = f"❌ No pude generar una netlist válida. El formato JSON es incorrecto.\n\nÚltimo intento:\n```\n{json_content}\n```"
            else:
                design_json_path = os.path.join(".tmp", "current_design.json")
                with open(design_json_path, "w") as f:
                    f.write(json_content)
                reply_text = f"✅ *Análisis Completado (Fase 1)*:\n\nHe interpretado tu diseño y he generado la siguiente netlist.\n\n```json\n{json_content}\n```\n\nEl siguiente paso sería generar el esquemático en KiCad con esta información."
        else:
            reply_text = f"❌ No pude interpretar el circuito. Asegúrate de que el dibujo sea claro. Error: {res}"

    elif "paquete" in caption_lower or "fabricar" in caption_lower or "zip" in caption_lower:
        run_tool("telegram_tool.py", ["--action", "send", "--message", "🏭 Generando paquete completo de fabricación (Gerber + Drill)...", "--chat-id", sender_id])
        
        try:
            with open("execution/img_to_gerber.py", "r") as f: script_gerber = f.read()
            inj_gerber = f"import sys\nsys.argv = ['img_to_gerber.py', '--image', '{filename}', '--output', '{filename}.gbr', '--size', '50']\n"
            res_gerber = run_tool("run_sandbox.py", ["--code", inj_gerber + script_gerber])
            
            with open("execution/img_to_drill.py", "r") as f: script_drill = f.read()
            inj_drill = f"import sys\nsys.argv = ['img_to_drill.py', '--image', '{filename}', '--output', '{filename}.drl', '--size', '50']\n"
            res_drill = run_tool("run_sandbox.py", ["--code", inj_drill + script_drill])
            
            if res_gerber.get("status") == "success" and res_drill.get("status") == "success":
                zip_name = f"PCB_Pack_{int(time.time())}.zip"
                with open("execution/create_manufacturing_zip.py", "r") as f: script_zip = f.read()
                
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
        except Exception as e:
            reply_text = f"❌ Error interno en el proceso de empaquetado: {e}"

    elif "gerber" in caption_lower or "pcbway" in caption_lower or "jlcpcb" in caption_lower:
        run_tool("telegram_tool.py", ["--action", "send", "--message", "🏭 Generando archivo Gerber (Top Copper)...", "--chat-id", sender_id])
        
        try:
            with open("execution/img_to_gerber.py", "r") as f: script_content = f.read()
            injection = f"import sys\nsys.argv = ['img_to_gerber.py', '--image', '{filename}', '--output', '{filename}.gbr', '--size', '50']\n"
            full_code = injection + script_content
            
            res_sandbox = run_tool("run_sandbox.py", ["--code", full_code])
            
            if res_sandbox and res_sandbox.get("status") == "success":
                reply_text = "✅ Archivo Gerber generado."
                generated_file = local_path + ".gbr"
                if os.path.exists(generated_file):
                    run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", generated_file, "--chat-id", sender_id, "--caption", "Gerber Top Copper"])
            else:
                err_msg = res_sandbox.get('stderr') or res_sandbox.get('message') or "Error desconocido"
                reply_text = f"❌ Error en conversión Gerber: {err_msg}"
        except Exception as e:
            reply_text = f"❌ Error interno: {e}"

    elif "taladro" in caption_lower or "drill" in caption_lower or "agujeros" in caption_lower:
        run_tool("telegram_tool.py", ["--action", "send", "--message", "🔩 Detectando agujeros y generando Excellon (.drl)...", "--chat-id", sender_id])
        
        try:
            with open("execution/img_to_drill.py", "r") as f: script_content = f.read()
            injection = f"import sys\nsys.argv = ['img_to_drill.py', '--image', '{filename}', '--output', '{filename}.drl', '--size', '50']\n"
            full_code = injection + script_content
            res_sandbox = run_tool("run_sandbox.py", ["--code", full_code])
            
            if res_sandbox and res_sandbox.get("status") == "success":
                reply_text = "✅ Archivo de Taladrado generado."
                generated_file = local_path + ".drl"
                if os.path.exists(generated_file):
                    run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", generated_file, "--chat-id", sender_id, "--caption", "Excellon Drill File"])
            else:
                err_msg = res_sandbox.get('stderr') or "Error desconocido"
                reply_text = f"❌ Error detectando taladros: {err_msg}"
        except Exception as e:
            reply_text = f"❌ Error interno: {e}"

    elif "gcode" in caption_lower or "cnc" in caption_lower:
        run_tool("telegram_tool.py", ["--action", "send", "--message", "⚙️ Convirtiendo imagen a G-Code...", "--chat-id", sender_id])
        try:
            with open("execution/img_to_gcode.py", "r") as f: script_content = f.read()
            injection = f"import sys\nsys.argv = ['img_to_gcode.py', '--image', '{filename}', '--output', '{filename}.nc', '--size', '50']\n"
            full_code = injection + script_content
            res_sandbox = run_tool("run_sandbox.py", ["--code", full_code])

            if res_sandbox and res_sandbox.get("status") == "success":
                reply_text = "✅ Conversión completada."
                generated_file = local_path + ".nc"
                if os.path.exists(generated_file):
                    run_tool("telegram_tool.py", ["--action", "send-document", "--file-path", generated_file, "--chat-id", sender_id, "--caption", "G-Code generado desde imagen"])
            else:
                err_msg = res_sandbox.get('stderr') or "Error desconocido"
                reply_text = f"❌ Error en conversión: {err_msg}"
        except Exception as e:
            reply_text = f"❌ Error interno: {e}"
    
    else:
        run_tool("telegram_tool.py", ["--action", "send", "--message", "👀 Analizando imagen...", "--chat-id", sender_id])
        res = run_tool("analyze_image.py", ["--image", local_path, "--prompt", caption])
        if res and res.get("status") == "success":
            reply_text = f"👁️ *Análisis Visual:*\n{res.get('description')}"
        else:
            reply_text = f"❌ Error analizando imagen: {res.get('message')}"
    
    return reply_text
