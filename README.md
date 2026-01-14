# mgaf_pr
Multimodal Game Agent Framework for Pokémon Red

Descripción: "Este proyecto es un framework avanzado para la creación de agentes autónomos capaces de jugar a Pokémon Red utilizando modelos de lenguaje de gran tamaño (LLM) a través de visión artificial y lectura directa de memoria. A diferencia de los bots tradicionales basados en scripts, este agente intenta 'razonar' sus decisiones analizando visualmente el frame del emulador y contrastándolo con una jerarquía de objetivos predefinida. Utiliza PyBoy para la emulación y Groq (Llama-3-Vision) como motor de decisiones, implementando un sistema de memoria de corto plazo para evitar bucles de comportamiento y un rastreador de eventos basado en ingeniería inversa de la RAM del juego."

Puntos de Éxito (Lo que funciona muy bien):
Arquitectura de Capas: El sistema jerárquico (Estratégico -> Táctico -> Atómico) permite que la IA entienda qué está haciendo a gran escala (ej. "Ganar la medalla Roca") mientras ejecuta pasos pequeños.

Ingeniería Inversa de RAM: El mapeo de direcciones de memoria en events.json es extremadamente preciso, permitiendo al sistema saber exactamente dónde está el jugador y qué eventos ha activado sin margen de error.

Detección de Diálogos: El módulo dialog_detector.py gestiona eficientemente las interrupciones de texto, evitando que el LLM intente "moverse" cuando el juego está bloqueado por un mensaje.

Detección de Estancamiento: El MemoryBuffer identifica con éxito cuando el agente choca repetidamente contra el mismo obstáculo.

Puntos de Fracaso (Retos no superados):
Razonamiento Espacial en Modelos Vision: Los modelos actuales (como Llama-3-Vision) presentan dificultades para mapear coordenadas 2D relativas solo con una imagen de baja resolución, lo que causa confusiones entre "arriba" y "abajo" cuando hay obstáculos cerca.

Anclaje de Respuestas (Looping): Ante la falta de progreso, el modelo tiende a repetir la última acción exitosa almacenada en su contexto, ignorando las instrucciones negativas de "no repitas este botón".

Navegación entre Mapas: El paso de una zona interior (Casa) a una exterior (Pueblo) confunde la lógica de coordenadas, ya que el sistema de visión no percibe el cambio de escala del mapa de forma intuitiva.

Cómo instalarlo y prepararlo.
Para que alguien pueda usar tu proyecto, puedes añadir este bloque de "Instalación" en tu repositorio:

Clonar el repo: git clone https://github.com/innomeus/mgaf-pr.git

Instalar dependencias: pip install -r requirements.txt

Configurar API Key.

Añadir ROM: Coloca tu archivo pokemon_red.gb en la carpeta raíz.

Ejecutar: python groq_agent_main.py

Tree del proyecto:
POKEMON-RED-AI-AGENT/
├── core/                       # Lógica principal del sistema
│   ├── dialog_detector.py      # Detección de cajas de texto y menús
│   ├── event_checker.py        # Validador de hitos mediante memoria RAM
│   ├── llm_planner.py          # Cerebro del agente (Conexión con Groq)
│   ├── memory_buffer.py        # Historial de acciones y detección de bucles
│   └── progress_tracker.py     # Seguimiento de waypoints y estancamiento
├── config/                     # Base de conocimientos del juego
│   ├── events.json             # Direcciones de memoria y flags de la ROM
│   ├── objectives.json         # Jerarquía de misiones (Estratégico/Atómico)
│   ├── skills.json             # Guía de batalla y tipos para la IA
│   └── waypoints.json          # Coordenadas exactas para navegación
├── groq_agent_main.py          # Script de ejecución principal
├── test_modules.py             # Suite de pruebas unitarias para cada módulo
├── requirements.txt            # Dependencias (PyBoy, Groq, OpenCV, etc.)
└── README.md                   # Documentación del proyecto
