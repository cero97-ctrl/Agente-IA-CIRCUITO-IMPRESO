import sqlite3
import os
import datetime

# Construir la ruta a la DB de forma robusta para que funcione desde cualquier script
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "agent_database.db")

def get_db_connection():
    """Crea y devuelve una conexión a la base de datos."""
    # Asegurarse de que el directorio .tmp exista
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Crear tabla de recordatorios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                reminder_time TEXT NOT NULL,
                message TEXT NOT NULL,
                last_sent_date TEXT
            )
        ''')
        # Crear tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                chat_id TEXT PRIMARY KEY,
                first_seen TEXT
            )
        ''')
        # Crear tabla de historial de chat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("   [DB] Base de datos SQLite inicializada correctamente.")
    except Exception as e:
        print(f"   [DB] ❌ Error inicializando la base de datos: {e}")

def add_reminder(chat_id, reminder_time, message):
    """Añade un nuevo recordatorio a la base de datos."""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO reminders (chat_id, reminder_time, message) VALUES (?, ?, ?)',
        (str(chat_id), reminder_time, message)
    )
    conn.commit()
    conn.close()

def add_user(chat_id):
    """Añade un nuevo usuario a la base de datos si no existe."""
    conn = get_db_connection()
    try:
        first_seen = datetime.datetime.now().isoformat()
        conn.execute('INSERT OR IGNORE INTO users (chat_id, first_seen) VALUES (?, ?)', (str(chat_id), first_seen))
        conn.commit()
    except Exception as e:
        print(f"   [DB] Error adding user: {e}")
    finally:
        conn.close()

def get_all_users():
    """Obtiene todos los IDs de usuarios registrados."""
    conn = get_db_connection()
    users = conn.execute('SELECT chat_id FROM users').fetchall()
    conn.close()
    return [row['chat_id'] for row in users]

def get_all_reminders():
    """Obtiene todos los recordatorios de la base de datos."""
    conn = get_db_connection()
    reminders = conn.execute('SELECT * FROM reminders').fetchall()
    conn.close()
    return reminders

def get_reminders_by_user(chat_id):
    """Obtiene los recordatorios activos de un usuario."""
    conn = get_db_connection()
    reminders = conn.execute('SELECT * FROM reminders WHERE chat_id = ?', (str(chat_id),)).fetchall()
    conn.close()
    return reminders

def delete_reminders_for_user(chat_id):
    """Elimina todos los recordatorios de un usuario específico."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE chat_id = ?', (str(chat_id),))
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_deleted

def delete_reminder_by_id(reminder_id, chat_id):
    """Elimina un recordatorio específico por ID y usuario."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE id = ? AND chat_id = ?', (reminder_id, str(chat_id)))
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_deleted

def update_reminder_sent_date(reminder_id, date_str):
    """Actualiza la fecha del último envío de un recordatorio."""
    conn = get_db_connection()
    conn.execute(
        'UPDATE reminders SET last_sent_date = ? WHERE id = ?',
        (date_str, reminder_id)
    )
    conn.commit()
    conn.close()

def add_chat_message(role, content):
    """Añade un mensaje al historial de chat."""
    conn = get_db_connection()
    timestamp = datetime.datetime.now().isoformat()
    conn.execute('INSERT INTO chat_history (role, content, timestamp) VALUES (?, ?, ?)', (role, content, timestamp))
    conn.commit()
    conn.close()

def get_chat_history(limit=10):
    """Obtiene los últimos mensajes del historial."""
    conn = get_db_connection()
    rows = conn.execute('SELECT role, content FROM chat_history ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    # Invertimos para tener orden cronológico (antiguo -> nuevo)
    return [{'role': row['role'], 'content': row['content']} for row in rows][::-1]

def clear_chat_history():
    """Borra todo el historial de chat."""
    conn = get_db_connection()
    conn.execute('DELETE FROM chat_history')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()