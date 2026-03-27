#!/usr/bin/env python3
import sqlite3
import argparse
import json
import os
import sys
from datetime import datetime

DB_PATH = "data/chat_history.db"
# Base de datos activa gestionada por db_manager.py
ACTIVE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "agent_database.db")

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id TEXT, 
                  timestamp DATETIME, 
                  summary TEXT, 
                  context_json TEXT)''')
    conn.commit()
    conn.close()

def list_history(user_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, timestamp, summary FROM sessions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10", (user_id,))
    rows = c.fetchall()
    conn.close()
    
    history = [{"id": r["id"], "date": r["timestamp"], "summary": r["summary"]} for r in rows]
    return {"status": "success", "history": history}

def search_history(user_id, query):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Búsqueda parcial usando LIKE en el resumen
    c.execute("SELECT id, timestamp, summary FROM sessions WHERE user_id = ? AND summary LIKE ? ORDER BY timestamp DESC", (user_id, f"%{query}%"))
    rows = c.fetchall()
    conn.close()
    
    history = [{"id": r["id"], "date": r["timestamp"], "summary": r["summary"]} for r in rows]
    return {"status": "success", "history": history}

def save_session(user_id, summary):
    init_db()
    if not os.path.exists(ACTIVE_DB_PATH):
        return {"status": "error", "message": "No hay base de datos de chat activa."}

    try:
        # Extraer mensajes actuales de la base de datos de db_manager
        conn_active = sqlite3.connect(ACTIVE_DB_PATH)
        conn_active.row_factory = sqlite3.Row
        cursor = conn_active.cursor()
        cursor.execute("SELECT role, content, timestamp FROM chat_history ORDER BY id ASC")
        rows = cursor.fetchall()
        conn_active.close()

        if not rows:
            return {"status": "error", "message": "No hay mensajes en la sesión actual para guardar."}

        messages = [{"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]} for r in rows]
        context_json = json.dumps(messages)

        # Guardar en el archivo histórico
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO sessions (user_id, timestamp, summary, context_json) VALUES (?, ?, ?, ?)",
                  (user_id, datetime.now().strftime("%Y-%m-%d %H:%M"), summary, context_json))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def resume_session(user_id, session_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT context_json FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {"status": "error", "message": "Sesión no encontrada."}

    try:
        messages = json.loads(row["context_json"])

        # Restaurar mensajes en la base de datos activa
        conn_active = sqlite3.connect(ACTIVE_DB_PATH)
        cursor = conn_active.cursor()
        cursor.execute("DELETE FROM chat_history")
        for m in messages:
            cursor.execute("INSERT INTO chat_history (role, content, timestamp) VALUES (?, ?, ?)",
                          (m["role"], m["content"], m["timestamp"]))
        conn_active.commit()
        conn_active.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def delete_session(user_id, session_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
    rows = c.rowcount
    conn.commit()
    conn.close()
    if rows > 0:
        return {"status": "success"}
    return {"status": "error", "message": "Sesión no encontrada o no pertenece al usuario."}

def export_session(user_id, session_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT summary, timestamp, context_json FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {"status": "error", "message": "Sesión no encontrada."}
    
    filename = f"Export_Sesion_{session_id}_{user_id}.md"
    filepath = os.path.join("docs", filename)
    os.makedirs("docs", exist_ok=True)
    
    try:
        messages = json.loads(row["context_json"])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Exportación de Sesión {session_id}\n\n")
            f.write(f"- **Fecha:** {row['timestamp']}\n")
            f.write(f"- **Resumen:** {row['summary']}\n\n---\n\n")
            for msg in messages:
                role = "🤖 Agente" if msg.get("role") == "assistant" else "👤 Usuario"
                f.write(f"### {role}\n{msg.get('content')}\n\n")
        return {"status": "success", "file": filepath}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True, choices=["list", "save", "resume", "delete", "search", "export"])
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--session-id", type=int)
    parser.add_argument("--summary", default="Sesión sin resumen")
    parser.add_argument("--query", default="")
    args = parser.parse_args()
    
    actions = {"list": lambda: list_history(args.user_id), "save": lambda: save_session(args.user_id, args.summary), "resume": lambda: resume_session(args.user_id, args.session_id), "delete": lambda: delete_session(args.user_id, args.session_id), "search": lambda: search_history(args.user_id, args.query), "export": lambda: export_session(args.user_id, args.session_id)}
    print(json.dumps(actions[args.action]()))