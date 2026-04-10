Hola, soy **Gemini**. Como Ingeniero de Software Senior y tu profesor para esta sesión, voy a desglosar el script `chat_with_llm.py`. Este código no es solo un cliente de chat; es una **Capa de Orquestación** robusta diseñada para ser el "Cerebro" de un sistema complejo de diseño electrónico.

### Resumen General
El script actúa como un puente inteligente entre el usuario (o procesos automáticos) y múltiples proveedores de Modelos de Lenguaje de Gran Escala (LLM). Su propósito es gestionar la persistencia de datos, la recuperación de memoria relevante (RAG) y garantizar que las respuestas sean procesables por otros scripts mediante un formateo estricto.

---

### Análisis Detallado del Código

#### 1. Gestión de Dependencias y Entorno
El código utiliza bloques `try-except` para las importaciones de `google.generativeai`, `chromadb` y `dotenv`. Esta es una práctica de **diseño resiliente**: permite que el script se ejecute incluso si algunas bibliotecas opcionales no están instaladas, manejando los errores de forma elegante durante el tiempo de ejecución.

#### 2. La Instrucción del Sistema (`DEFAULT_SYSTEM_INSTRUCTION`)
Aquí se define la "personalidad" y las reglas operativas del agente. Lo más crítico es la **restricción de formato**:
- Obliga a la IA a entregar JSON puro si se solicita, eliminando el "ruido" (texto explicativo o bloques markdown) que rompería un parser automático.

#### 3. Funciones de Utilidad y Limpieza
*   **`clean_llm_response(text)`**: Es una función de saneamiento. Utiliza manipulación de strings para detectar y remover los delimitadores de bloque de código (```json ... ```). Esto es vital para asegurar que la salida estándar (`stdout`) sea JSON válido cuando se requiere integración entre sistemas.

#### 4. Memoria de Largo Plazo: RAG (`get_memory_context`)
Esta función implementa **Retrieval-Augmented Generation (RAG)** utilizando `ChromaDB`:
- **Lógica**: Toma el prompt del usuario y busca en una base de datos vectorial los 3 "recuerdos" o documentos más similares semánticamente.
- **Flujo de Datos**: Si encuentra coincidencias, las devuelve como una lista formateada que luego se inyectará en el prompt actual para darle contexto histórico al modelo.

#### 5. Adaptadores de Proveedores (`chat_openai`, `chat_gemini`, etc.)
El script implementa el patrón de diseño **Adapter**. Cada función normaliza la interfaz de una API distinta:
- **`chat_gemini`**: Destaca por su **Estrategia de Fallback Interna**, intentando modelos alternativos (como `gemini-2.0-flash` o `gemini-pro`) si el modelo principal falla.
- **`chat_groq`**: Se enfoca en la velocidad y compatibilidad con la estructura de OpenAI.

#### 6. El Orquestador Principal (`main`)
Aquí reside la lógica de negocio más compleja:

*   **Gestión de Historial y Ventana de Contexto**: 
    - **Soft Cap**: Si la conversación supera los 12 mensajes, el script "comprime" el historial manteniendo los mensajes iniciales (contexto) y los finales (flujo actual), eliminando el medio.
    - **Hard Cap**: Si el texto total supera los 30,000 caracteres, realiza una poda de emergencia para evitar errores de "token limit" en las APIs.
*   **Inyección de RAG**: Si el RAG no está desactivado (`--no-rag`), el contexto recuperado de ChromaDB se inserta directamente en el último mensaje del usuario antes de enviarlo al LLM.
*   **Sistema de Reintentos (Multi-Provider Fallback)**: Si el proveedor preferido falla (por cuotas agotadas o errores de red), el bucle `for provider in providers_to_try` intenta automáticamente con el siguiente proveedor configurado (Gemini -> Groq -> OpenRouter -> etc.).

#### 7. Monitoreo de Recursos y Soporte ZRAM
El script incluye un módulo de telemetría preventiva (usando `psutil`) específicamente diseñado para la ejecución local:
- **Load Average**: Monitorea si la CPU está saturada por la compresión/descompresión.
- **Detección de Swap Activo**: Informa al usuario si el sistema ha empezado a comprimir memoria (ZRAM), lo cual es un indicador de que el modelo de IA está demandando el máximo de recursos.
- **Alertas de Memoria**: Emite avisos críticos antes de que el proceso sea terminado por el OOM-Killer del sistema operativo.

---

### Conclusión

Este script es un ejemplo de **ingeniería de prompts programática**. No solo envía texto; gestiona el ciclo de vida completo de la interacción:
1.  **Contextualiza**: Busca en la memoria vectorial.
2.  **Optimiza**: Recorta el historial para ahorrar costos y tokens.
3.  **Resiste**: Cambia de proveedor si uno falla.
4.  **Normaliza**: Limpia la salida para que sea consumible por máquinas.

Es una pieza fundamental para un sistema de fabricación digital donde la precisión del JSON es tan importante como la lógica del diseño electrónico.