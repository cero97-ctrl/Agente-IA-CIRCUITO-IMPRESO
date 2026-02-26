import os
import time
import json
import datetime
from execution.listen_telegram_helpers import get_current_persona
from execution.telegram_handlers.photo_handler import handle_photo
from execution.telegram_handlers.document_handler import handle_document
from execution.telegram_handlers.voice_handler import handle_voice
from execution.telegram_handlers.command_handler import handle_command_text

def handle_message(original_msg, sender_id, run_tool):
    reply_text = ""
    msg = original_msg
    is_voice_interaction = False
    voice_lang_short = "es"

    if msg.startswith("__PHOTO__:"):
        reply_text = handle_photo(msg, sender_id, run_tool)
    elif msg.startswith("__DOCUMENT__:"):
        try:
            reply_text = handle_document(msg, sender_id, run_tool)
        except Exception as e:
            reply_text = f"❌ Error procesando documento: {e}"
    elif msg.startswith("__VOICE__:"):
        try:
            reply, is_voice, lang, parsed_msg = handle_voice(msg, sender_id, run_tool)
            is_voice_interaction = is_voice
            voice_lang_short = lang
            if reply: # Error during transcription
                reply_text = reply
            else:
                msg = parsed_msg # Pass transcribed text as the new command
        except Exception as e:
            reply_text = f"❌ Error procesando audio: {e}"
            is_voice_interaction = False
            
    # Si no hubo error en los media, e interceptamos mensajes que son comandos o chat
    if not reply_text:
        # Check command handler
        if msg.startswith("/"):
            reply_text = handle_command_text(msg, sender_id, run_tool)
        
        # Greetings and common interactions
        elif msg.strip() and msg.lower().split()[0].strip(".,!¡?") in ["hola", "hi", "hello", "buenas", "start"]:
            print(f"   👋 Saludo detectado de {sender_id}")
            reply_text = (
                "👋 ¡Hola! Soy un Agente de IA especializado en la fabricación de PCBs con CNC.\n\n"
                "Fui entrenado por el prof. *César Rodríguez* y el equipo *Tecnología Venezolana* para asistirte en todo el flujo de trabajo, desde el diseño hasta la fabricación.\n\n"
                "Usa */ayuda* para ver todos los comandos disponibles."
            )
        elif msg.lower().strip() in ["gracias", "gracias!", "thanks", "thank you"]:
            reply_text = "¡De nada! Estoy aquí para ayudar. 🤖"
        
        # General AI Chat Interaction
        else:
            print("   🤔 Consultando al Agente (con memoria)...")
            current_sys = get_current_persona()
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_sys += f"\n[Contexto Temporal: Fecha y Hora actual del servidor: {now_str}]"
            if is_voice_interaction and voice_lang_short != "es":
                current_sys += f"\nIMPORTANT: The user is speaking in '{voice_lang_short}'. You MUST respond in '{voice_lang_short}', regardless of your default instructions."
            
            llm_response = run_tool("chat_with_llm.py", ["--prompt", msg, "--system", current_sys])
            if llm_response and "content" in llm_response:
                reply_text = llm_response["content"]
            else:
                error_msg = llm_response.get('error', 'Respuesta vacía') if llm_response else "Error desconocido"
                reply_text = f"⚠️ Error del Modelo: {error_msg}"

    return reply_text, is_voice_interaction, voice_lang_short, msg
