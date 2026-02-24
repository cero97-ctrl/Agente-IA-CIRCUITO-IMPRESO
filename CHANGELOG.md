# Changelog

Todas las mejoras notables de este proyecto serán documentadas en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Añadido
- Script `execution/check_system_health.py` para validación de entorno (Python, .env, dependencias).
- Mejora en `generate_readme.py`: ahora lee los archivos YAML para incluir la descripción (`goal`) de cada directiva en el prompt del LLM.
- Integración con Telegram: `execution/telegram_tool.py` y directiva `telegram_remote_control.yaml` para control remoto y notificaciones.
- Nueva acción `get-id` en `telegram_tool.py` para facilitar la configuración inicial del Chat ID.
- Nuevos comandos en `listen_telegram.py`: `/recordar` (memoria) y `/ayuda`.
- Activación de RAG en `chat_with_llm.py`: ahora consulta automáticamente ChromaDB para inyectar contexto de memoria en las respuestas.
- Depuración de RAG: `chat_with_llm.py` ahora muestra errores de memoria en stderr.
- Gestión de memoria: añadido `delete_memory.py` y comando `/olvidar` en Telegram.
- Mejora en `listen_telegram.py`: ahora muestra los logs de error (stderr) de los subprocesos para facilitar la depuración.
- Robustez en `telegram_tool.py`: añadido fallback automático a texto plano si falla el envío por formato Markdown.
- **Bug Fix Crítico**: Corregido error en `chat_with_llm.py` donde el contexto de memoria recuperado (RAG) no se enviaba al LLM.
- Nuevo comando `/memory` en `run_agent.py` para consultar la memoria desde el CLI principal.
- Mejora de RAG en `/investigar`: ahora el agente cruza los resultados de búsqueda con su memoria interna antes de resumir.
- Mejora en logs de `chat_with_llm.py`: ahora muestra una previsualización del recuerdo recuperado para facilitar la depuración.
- **Optimización RAG**: Implementado argumento `--memory-query` en `chat_with_llm.py` para separar la búsqueda en memoria del prompt al LLM, solucionando problemas de ruido en `/investigar`.
- **Mejora de UX**: `listen_telegram.py` ahora reporta el error específico del LLM en lugar de un mensaje genérico.
- Nueva capacidad: Comando `/resumir [url]` para análisis de webs (incluye `scrape_single_site.py`).
- **Arquitectura "Memory-First"**: El chat general ahora consulta la memoria local antes de llamar a un LLM externo, permitiendo respuestas offline y más rápidas.
- **Bug Fix**: Implementado argumento `--memory-only` en `chat_with_llm.py` que faltaba en la versión anterior.
- **Bug Fix (API)**: Corregida la lista de modelos de fallback de Gemini en `chat_with_llm.py` para evitar errores 404 con modelos no soportados.
- **Mejora RAG**: Deduplicación automática de recuerdos en `chat_with_llm.py` para evitar respuestas repetitivas.
- **Mejora UX**: El comando `/memorias` en Telegram ahora muestra la hora exacta del recuerdo para facilitar la auditoría.
- **Soporte Multi-Usuario**: `telegram_tool.py` y `listen_telegram.py` actualizados para responder a múltiples usuarios simultáneamente (Mente Colmena).
- **Generación de Gerber**: Script `img_to_gerber.py` para convertir imágenes a formato RS-274X.
- **Detección de Taladros**: Script `img_to_drill.py` usando OpenCV para generar archivos Excellon (.drl) desde imágenes.
- **Empaquetado de Manufactura**: Script `create_manufacturing_zip.py` para crear ZIPs compatibles con PCBWay/JLCPCB.
- **Patrones de Prueba**: Script `generate_test_pattern.py` para validar la detección de taladros.
- **Comandos de Telegram**: Soporte para "gerber", "drill" y "paquete" en el bot.

## [1.0.0] - 2026-02-16
### Añadido
- Arquitectura de 3 capas (Directivas, Orquestación, Ejecución).
- Integración con LLMs (OpenAI, Anthropic, Google Gemini).
- Sistema de memoria vectorial local con ChromaDB.
- Herramientas de desarrollo: `init_project`, `pre_commit_check`, `deploy_to_github`.
- Soporte para interfaz de voz y traducción de documentos.
- Documentación completa y guías de contribución.
