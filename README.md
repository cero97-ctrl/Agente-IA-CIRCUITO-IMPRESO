# Agente IA de Fabricación Digital.

## Estado del Proyecto
El proyecto está en desarrollo activo. Las funcionalidades principales de generación de modelos 3D y PCBs son estables. El versionado se gestiona automáticamente mediante el script `git-update.sh`.

## Descripción del Proyecto

Este repositorio aloja un **Agente de IA para Fabricación Digital**, accesible a través de un bot de Telegram. El agente está diseñado para ser un asistente de ingeniería que puede interpretar lenguaje natural e imágenes para generar archivos de diseño y fabricación.

El núcleo del sistema utiliza un LLM para la orquestación y scripts deterministas en un entorno Docker para ejecutar tareas complejas de forma fiable, incluyendo el uso de software CAD/ECAD como **FreeCAD** y **KiCad** en modo headless.

## Capacidades Principales

El agente puede realizar las siguientes tareas a través de comandos de Telegram:

### 📐 Diseño CAD 3D (con FreeCAD)
- **Generación Paramétrica**: Crea modelos 3D (cubos, cilindros, esferas, conos) a partir de descripciones en lenguaje natural (ej. `/freecad un cono de radio 10 y altura 30`).
- **Exportación Multi-formato**: Genera archivos `.stl` (para impresión 3D), `.step` (formato industrial) y un render realista en `.png`.
- **Análisis Físico**: Calcula y reporta el volumen y la masa estimada (PLA) del objeto generado.

### ⚡ Diseño Electrónico (con KiCad)
- **Interpretación de Dibujos**: Analiza una foto de un circuito dibujado a mano y genera una netlist estructurada en formato JSON.
- **Generación de Esquemáticos**: Crea un archivo de esquemático (`.kicad_sch`) a partir de la netlist interpretada.
- **Auto-enrutado de PCB**: Genera un archivo de placa (`.kicad_pcb`) con pistas trazadas automáticamente.
- **Paquetes de Fabricación**: Crea un archivo `.zip` con todos los archivos Gerber y de taladrado (Drill), listo para enviar a fabricantes como JLCPCB o PCBWay.

### ⚙️ Fabricación CNC
- **Generación de G-Code**: Convierte imágenes en blanco y negro a G-Code (`.nc`) para fresado.
- **Comunicación con Máquina**: Incluye un script para enviar G-Code a máquinas CNC que usan el firmware GRBL.

Para una lista completa de comandos y sus descripciones, consulta la Referencia de Comandos.

## Instalación y Puesta en Marcha

El sistema está diseñado para ejecutarse en un entorno contenerizado para máxima portabilidad.

### 1. Requisitos Previos
- **Docker**: Para ejecutar el sandbox que contiene FreeCAD, KiCad y todas las dependencias.
- **Python 3.10+**: Para ejecutar la lógica del agente.

### 2. Clonar el Repositorio
```bash
git clone https://github.com/cero-etage/Agente-IA-CIRCUITO-IMPRESO.git
cd Agente-IA-CIRCUITO-IMPRESO
```

### 3. Configurar el Entorno
Crea un archivo `.env` en la raíz del proyecto y añade tus claves de API. Puedes usar el siguiente ejemplo como plantilla:
```env
TELEGRAM_BOT_TOKEN="tu_token_de_telegram"
TELEGRAM_CHAT_ID="tu_chat_id"

# Elige al menos un proveedor de LLM
GROQ_API_KEY="tu_api_key_de_groq"
GOOGLE_API_KEY="tu_api_key_de_google"
OPENAI_API_KEY="tu_api_key_de_openai"
ANTHROPIC_API_KEY="tu_api_key_de_anthropic"
```

### 4. Construir el Sandbox de Docker
Este comando crea la imagen de Docker con todas las herramientas CAD/ECAD necesarias. Puede tardar un poco la primera vez.
```bash
python execution/build_sandbox.py
```

### 5. Instalar Dependencias de Python
```bash
pip install -r requirements.txt
```

### 6. Ejecutar el Agente
Una vez configurado, inicia el bot que escuchará los comandos de Telegram.
```bash
python execution/listen_telegram.py
```

## Documentación Detallada

Para una inmersión profunda en el proceso de diseño de PCBs con CNC, las herramientas y los scripts de Python involucrados, consulta el documento principal que originó esta investigación:

Documentación del Flujo de Trabajo CNC con Python