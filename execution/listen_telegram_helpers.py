import time
import subprocess
import json
import sys
import os
import datetime
from dotenv import load_dotenv
from execution.db_manager import add_user, get_all_reminders, update_reminder_sent_date

load_dotenv()

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
    add_user(chat_id)

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

def check_reminders():
    """Comprueba y envía los recordatorios pendientes desde la base de datos."""
    try:
        reminders = get_all_reminders()
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_time_str = now.strftime("%H:%M")

        for reminder in reminders:
            # reminder es ahora un objeto sqlite3.Row, accesible como un diccionario
            if reminder['reminder_time'] == current_time_str and reminder['last_sent_date'] != today_str:
                chat_id = reminder['chat_id']
                message = reminder['message']
                
                print(f"   ⏰ [DB] Enviando recordatorio a {chat_id}: '{message}'")
                res = run_tool("telegram_tool.py", ["--action", "send", "--message", f"⏰ *RECORDATORIO:*\n{message}", "--chat-id", chat_id])
                
                if res and res.get("status") == "success":
                    # Actualizar la base de datos para no volver a enviar hoy
                    update_reminder_sent_date(reminder['id'], today_str)
                else:
                    print(f"   ⚠️ Error enviando recordatorio: {res.get('message') if res else 'Desconocido'}")
    except Exception as e:
        print(f"   [!] Error en check_reminders: {e}")

def run_tool(script, args):
    """Ejecuta una herramienta del framework y devuelve su salida JSON."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
    cmd = [sys.executable, script_path] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
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
