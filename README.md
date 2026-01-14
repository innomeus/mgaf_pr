# mgaf_pr
Multimodal Game Agent Framework for Pokémon Red

Puntos de Éxito (Lo que funciona muy bien):
Arquitectura de Capas: El sistema jerárquico (Estratégico -> Táctico -> Atómico) permite que la IA entienda qué está haciendo a gran escala (ej. "Ganar la medalla Roca") mientras ejecuta pasos pequeños.

Ingeniería Inversa de RAM: El mapeo de direcciones de memoria en events.json es extremadamente preciso, permitiendo al sistema saber exactamente dónde está el jugador y qué eventos ha activado sin margen de error.

Detección de Diálogos: El módulo dialog_detector.py gestiona eficientemente las interrupciones de texto, evitando que el LLM intente "moverse" cuando el juego está bloqueado por un mensaje.

Detección de Estancamiento: El MemoryBuffer identifica con éxito cuando el agente choca repetidamente contra el mismo obstáculo.

Puntos de Fracaso (Retos no superados):
Razonamiento Espacial en Modelos Vision: Los modelos actuales (como Llama-3-Vision) presentan dificultades para mapear coordenadas 2D relativas solo con una imagen de baja resolución, lo que causa confusiones entre "arriba" y "abajo" cuando hay obstáculos cerca.

Anclaje de Respuestas (Looping): Ante la falta de progreso, el modelo tiende a repetir la última acción exitosa almacenada en su contexto, ignorando las instrucciones negativas de "no repitas este botón".

Navegación entre Mapas: El paso de una zona interior (Casa) a una exterior (Pueblo) confunde la lógica de coordenadas, ya que el sistema de visión no percibe el cambio de escala del mapa de forma intuitiva.
