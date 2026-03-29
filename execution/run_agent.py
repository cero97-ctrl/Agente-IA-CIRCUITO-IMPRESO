#!/usr/bin/env python3
import sys
import os
import subprocess
import time
import json

# Colores ANSI para la terminal


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Ruta base para ejecución robusta (directorio donde reside este script)
EXECUTION_DIR = os.path.dirname(os.path.abspath(__file__))

def type_effect(text, delay=0.01):
    """Simula el efecto de escritura de una IA."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print("")


def run_script(script_name, args=[]):
    """Ejecuta un script de la carpeta execution/."""
    script_path = os.path.join(EXECUTION_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"{Colors.FAIL}❌ Error: Script {script_name} no encontrado.{Colors.ENDC}")
        return

    print(f"{Colors.WARNING}⚙️  Ejecutando {script_name}...{Colors.ENDC}")
    try:
        subprocess.run([sys.executable, script_path] + args)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  Ejecución interrumpida manualmente.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}Error crítico: {e}{Colors.ENDC}")


def main():
    os.system('cls' if os.name == 'nt' else 'clear')

    print(f"{Colors.HEADER}{Colors.BOLD}🤖 GEMINI AGENT CLI (Simulated Mode){Colors.ENDC}")
    print(f"{Colors.HEADER}======================================{Colors.ENDC}")
    print("Bienvenido a la interfaz de orquestación.")
    print("Tú actúas como el 'Cerebro' (Layer 2). Usa este CLI para invocar herramientas.")
    print(f"Escribe {Colors.BOLD}/help{Colors.ENDC} para ver comandos disponibles o {Colors.BOLD}/exit{Colors.ENDC} para salir.\n")

    while True:
        try:
            # Input del usuario
            user_input = input(f"{Colors.GREEN}You (Orchestrator) > {Colors.ENDC}").strip()

            if not user_input:
                continue

            # Comandos del sistema
            if user_input.lower() in ["/exit", "exit", "quit"]:
                print(f"{Colors.BLUE}Gemini >{Colors.ENDC} Cerrando sesión. ¡Hasta luego!")
                break

            elif user_input.lower() in ["/help", "help"]:
                print(f"\n{Colors.BOLD}Comandos Disponibles:{Colors.ENDC}")
                print("  /list    -> Listar todas las directivas disponibles")
                print("  /memory  -> Listar los recuerdos guardados en la memoria")
                print("  /check   -> Verificar salud del sistema")
                print("  /run [script] [args] -> Ejecutar un script específico")
                print("  /ask [prompt] -> Consultar al LLM real (OpenAI/Anthropic)")
                print("  /ingest [archivo] -> Ingestar documento de docs/ a la memoria")
                print("  /telegram -> Iniciar modo escucha de Telegram (Bot)")
                print("  [texto]  -> Simular chat (echo)\n")

            elif user_input.lower() in ["/list", "list"]:
                run_script("list_directives.py")

            elif user_input.lower() in ["/check", "check"]:
                run_script("check_system_health.py")

            elif user_input.lower() in ["/memory", "/memories"]:
                run_script("list_memories.py")

            elif user_input.lower().startswith("/ingest"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print(f"{Colors.FAIL}Uso: /ingest <nombre_archivo_en_docs>{Colors.ENDC}")
                    continue
                filename = parts[1]
                
                print(f"{Colors.WARNING}⚙️  Procesando documento {filename}...{Colors.ENDC}")
                
                # 1. Leer archivo (usando Sandbox para consistencia con directiva)
                path_in_container = f"/mnt/docs/{filename}"
                
                if filename.lower().endswith(".pdf"):
                    read_code = (
                        f"from pypdf import PdfReader; "
                        f"reader = PdfReader('{path_in_container}'); "
                        f"print('\\n'.join([page.extract_text() for page in reader.pages]))"
                    )
                else:
                    read_code = f"with open('{path_in_container}', 'r', encoding='utf-8') as f: print(f.read())"
                
                # Ejecutar run_sandbox.py
                sandbox_script = os.path.join(EXECUTION_DIR, "run_sandbox.py")
                proc_read = subprocess.run(
                    [sys.executable, sandbox_script, "--code", read_code],
                    capture_output=True, text=True
                )
                
                try:
                    res_read = json.loads(proc_read.stdout)
                    if res_read.get("status") == "success":
                        content = res_read.get("stdout", "")
                        if not content.strip():
                             print(f"{Colors.FAIL}❌ El archivo está vacío o no se pudo leer.{Colors.ENDC}")
                        else:
                            # 2. Guardar en memoria
                            full_text = f"Contenido del documento '{filename}':\n\n{content}"
                            save_script = os.path.join(EXECUTION_DIR, "save_memory.py")
                            
                            print(f"{Colors.WARNING}💾 Guardando en memoria vectorial...{Colors.ENDC}")
                            proc_save = subprocess.run(
                                [sys.executable, save_script, "--text", full_text, "--category", "document_knowledge"],
                                capture_output=True, text=True
                            )
                            res_save = json.loads(proc_save.stdout)
                            
                            if res_save.get("status") == "success":
                                print(f"{Colors.GREEN}✅ Documento '{filename}' ingestado correctamente.{Colors.ENDC}")
                            else:
                                print(f"{Colors.FAIL}❌ Error al guardar: {res_save.get('error_message')}{Colors.ENDC}")
                    else:
                        print(f"{Colors.FAIL}❌ Error leyendo archivo: {res_read.get('message')}\nStderr: {res_read.get('stderr')}{Colors.ENDC}")
                except json.JSONDecodeError:
                     print(f"{Colors.FAIL}❌ Error decodificando salida del sandbox.{Colors.ENDC}")

            elif user_input.lower() in ["/telegram", "telegram"]:
                run_script("listen_telegram.py")

            elif user_input.lower().startswith("/run"):
                parts = user_input.split()
                if len(parts) < 2:
                    print(f"{Colors.FAIL}Uso: /run <nombre_script.py> [argumentos]{Colors.ENDC}")
                else:
                    script = parts[1]
                    args = parts[2:]
                    run_script(script, args)

            elif user_input.lower().startswith("/ask") or user_input.lower().startswith("/llm"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print(f"{Colors.FAIL}Uso: /ask <tu consulta>{Colors.ENDC}")
                    continue
                prompt = parts[1]

                # Conexión con LLM Real
                chat_script = os.path.join(EXECUTION_DIR, "chat_with_llm.py")

                if os.path.exists(chat_script):
                    sys.stdout.write(f"{Colors.BLUE}Gemini (Thinking...) > {Colors.ENDC}")
                    sys.stdout.flush()

                    # Ejecutar el script de chat capturando la salida
                    proc = subprocess.run(
                        [sys.executable, chat_script, "--prompt", prompt],
                        capture_output=True, text=True
                    )

                    # Borrar mensaje de "Thinking..."
                    print("\r" + " " * 50 + "\r", end="")
                    sys.stdout.write(f"{Colors.BLUE}Gemini > {Colors.ENDC}")

                    try:
                        data = json.loads(proc.stdout)
                        if "error" in data:
                            print(f"{Colors.FAIL}Error API: {data['error']}{Colors.ENDC}")
                        else:
                            type_effect(data.get("content", "No response."))
                    except json.JSONDecodeError:
                        # Fallback si el script falló y no devolvió JSON limpio
                        print(f"{Colors.FAIL}Error script: {proc.stderr or proc.stdout}{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}❌ Error: Script execution/chat_with_llm.py no encontrado.{Colors.ENDC}")

            else:
                # Modo Simulado (Default)
                response = f"Recibido: '{user_input}'.\n(Estoy en modo simulado. Si necesitas inteligencia real, usa /ask <pregunta>)"
                sys.stdout.write(f"{Colors.BLUE}Gemini > {Colors.ENDC}")
                type_effect(response)

        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Interrupción detectada. Usa /exit para salir.{Colors.ENDC}")
            continue
        except Exception as e:
            print(f"\n{Colors.FAIL}Error inesperado: {e}{Colors.ENDC}")
            continue


if __name__ == "__main__":
    main()
