def handle_voice(msg, sender_id, run_tool):
    import os
    import time
    from execution.listen_telegram_helpers import load_config
    reply_text = ""
    is_voice_interaction = True
    file_id = msg.replace("__VOICE__:", "")
    print(f"   🎤 Nota de voz recibida. Descargando ID: {file_id}...")

    run_tool("telegram_tool.py", ["--action", "send", "--message", "👂 Escuchando...", "--chat-id", sender_id])
    
    local_path = os.path.join(".tmp", f"voice_{int(time.time())}.ogg")
    run_tool("telegram_tool.py", ["--action", "download", "--file-id", file_id, "--dest", local_path])
    
    config = load_config()
    lang_code = config.get("voice_lang", "es-ES")
    voice_lang_short = lang_code.split('-')[0]
    
    res = run_tool("transcribe_audio.py", ["--file", local_path, "--lang", lang_code])
    new_msg = msg
    if res and res.get("status") == "success":
        new_msg = res.get("text")
        print(f"   📝 Transcripción: '{new_msg}'")
        run_tool("telegram_tool.py", ["--action", "send", "--message", f"🗣️ Dijiste: \"{new_msg}\"", "--chat-id", sender_id])
    else:
        err_msg = res.get("message", "Error desconocido") if res else "Falló el script de transcripción"
        reply_text = f"❌ No pude entender el audio. Detalle: {err_msg}"
        is_voice_interaction = False

    return reply_text, is_voice_interaction, voice_lang_short, new_msg
