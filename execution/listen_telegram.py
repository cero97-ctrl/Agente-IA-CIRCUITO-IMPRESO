#!/usr/bin/env python3
import time
import subprocess
import json
import sys
import os
import datetime
from dotenv import load_dotenv

# Añadir directorio raíz al path para permitir imports absolutos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from execution.db_manager import init_db

load_dotenv()

# Helpers extraídos
from listen_telegram_helpers import (
    save_user, get_current_persona, set_persona, check_reminders, run_tool
)
# Handler Principal refactorizado
from telegram_handlers.main_handler import handle_message

def main():
    print("📡 Escuchando Telegram... (Presiona Ctrl+C para detener)")
    print("   El agente responderá a cualquier mensaje que le envíes.")
    
    # --- INICIALIZAR BASE DE DATOS ---
    init_db()
    
    # --- DIAGNÓSTICO DE INICIO ---
    allowed = os.getenv("TELEGRAM_ALLOWED_USERS", os.getenv("TELEGRAM_CHAT_ID", ""))
    print(f"   🔒 Usuarios permitidos: {allowed if allowed else '⚠️ NINGUNO (Revisa .env)'}")
    
    offset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "telegram_offset.txt")
    if os.path.exists(offset_path):
        print(f"   ℹ️  Archivo de sesión encontrado. Si el bot ignora mensajes, bórralo: rm {offset_path}")
    # -----------------------------

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
                        print(f"⚠️ Formato de mensaje inesperado (sin '|'): {msg}")
                        sender_id = None
                        content = msg

                    save_user(sender_id)
                    print(f"\n📩 Mensaje recibido de {sender_id}: '{content}'")
                    
                    # Llamar al Handler refactorizado
                    reply_text, is_voice_interaction, voice_lang_short, final_msg = handle_message(content, sender_id, run_tool)
                    
                    # 3. Enviar respuesta a Telegram
                    if reply_text:
                        print(f"   📤 Enviando respuesta: '{reply_text[:60]}...'")
                        res = run_tool("telegram_tool.py", ["--action", "send", "--message", reply_text, "--chat-id", sender_id])
                        if res and res.get("status") == "error":
                            print(f"   ❌ Error al enviar mensaje: {res.get('message')}")
                            if res.get('details'):
                                print(f"      Detalle: {res.get('details')}")
                        
                        # 4. Si fue interacción por voz, enviar también audio en el idioma correcto
                        if is_voice_interaction and reply_text:
                            print("   🗣️ Generando respuesta de voz...")
                            audio_path = os.path.join(".tmp", f"reply_{int(time.time())}.ogg")
                            # Generar audio
                            tts_res = run_tool("text_to_speech.py", ["--text", reply_text[:500], "--output", audio_path, "--lang", voice_lang_short]) 
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