"""
LLM Planner - Adaptado para Groq (Llama-3.2-90B-Vision)
Gestiona la toma de decisiones del agente basado en objetivos jerárquicos
"""

import json
from groq import Groq


class LLMPlanner:
    def __init__(self, api_key, objectives_file, skills_file, waypoints_file=None):
        """
        Inicializa el planificador con acceso a Groq
        
        Args:
            api_key: API key de Groq
            objectives_file: Ruta a objectives.json
            skills_file: Ruta a skills.json
            waypoints file: Ruta a waypoints.json
        """
        self.client = Groq(api_key=api_key)
        
        # Cargar archivos de configuración
        with open(objectives_file, 'r', encoding='utf-8') as f:
            self.objectives = json.load(f)
        
        with open(skills_file, 'r', encoding='utf-8') as f:
            self.skills = json.load(f)
            
        #Cargar waypoints
        self.waypoints = {}
        if waypoints_file:
            try:
                with open (waypoints_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.waypoints = data.get('waypoints', {})
                print(f"    DEBUG: Waypoint loaded in planner: {len(self.waypoints)} phases")
                if self.waypoints:
                    print(f"    DEBUG: First phase key : {list(self.waypoints.keys())[0]}")
            except Exception as e:
                print(f"    ERROR: loading waypoints: {e}")
                pass
        
        # Estado actual en la jerarquía
        self.current_phase = 0  # Layer 1
        self.current_tactical = 0  # Layer 2
        self.current_atomic = 0  # Layer 3
        
        # Contador de pasos sin progreso
        self.steps_since_advance = 0
        self.max_steps_per_objective = 500  # Máximo de acciones por objetivo atómico
    
    def get_current_context(self):
        """Obtiene el contexto actual del objetivo"""
        try:
            phase = self.objectives['objective_hierarchy']['layer_1_strategic'][self.current_phase]
            tactical = phase['layer_2_tactical'][self.current_tactical]
            atomic_step = tactical['layer_3_atomic'][self.current_atomic]
            
            return {
                'strategic_goal': phase['goal'],
                'tactical_goal': tactical['goal'],
                'current_step': atomic_step,
                'phase_id': phase['id'],
                'tactical_id': tactical['id']
            }
        except (IndexError, KeyError):
            # Llegamos al final
            return None
    
    def build_prompt(self, game_state, memory_summary):
        """Prompt minimalista - solo lo esencial"""
        context = self.get_current_context()
    
        if not context:
            return "Game completed!"
    
        waypoint_hint = self._get_waypoint_hint(context['current_step'], game_state)
    
        # PROMPT ULTRA SIMPLE
        prompt = f"""Pokemon Red. Position: ({game_state['x']}, {game_state['y']}) Map {game_state['map_id']}
        
Try to reach {waypoint_hint}
Try get to the given coordinates.
Answer with ONE KEY, select one at each prompt to reach the objetive:  DOWN, UP, LEFT, RIGHT, A, B.
Try not to repeat the same KEY to move.
JUST ONE WORD, NO MORE.
Do not add a dot at the end of the answer.
Your response:"""

        
        return prompt
    
    def _select_relevant_skills(self, game_state):
        """Selecciona skills relevantes según el contexto"""
        skills_text = []
        
        # Si está en batalla, incluir battle_logic
        if game_state.get('in_battle', False):
            skills_text.append("BATTLE:")
            skills_text.extend([f"  - {s}" for s in self.skills['battle_logic'][:3]])
        else:
            # Si no está en batalla, incluir exploration
            skills_text.append("EXPLORATION:")
            skills_text.extend([f"  - {s}" for s in self.skills['exploration_logic'][:3]])
        
        # Siempre incluir navegación de menú
        skills_text.append("MENU:")
        skills_text.extend([f"  - {s}" for s in self.skills['menu_navigation'][:2]])
        
        return "\n".join(skills_text)
    
    def decide_action(self, screenshot_b64, game_state, memory_summary):
        """
        Llama al LLM para decidir la siguiente acción
        
        Args:
            screenshot_b64: Screenshot en base64
            game_state: Estado actual del juego
            memory_summary: Resumen de acciones recientes
            
        Returns:
            String con el nombre del botón (UP, DOWN, A, etc.)
        """
        prompt = self.build_prompt(game_state, memory_summary)
        # --- CAMBIO 1: IMPRIMIR PROMPT PARA DEPURAR ---
        print("\n" + "="*40)
        print("🔍 PROMPT ENVIADO AL LLM:")
        print(prompt)
        print("="*40 + "\n")
        # ----------------------------------------------
        # 1. Detectar si estamos atascados (misma posición que antes)
        # Accedemos a la última acción de la memoria para prohibirla
        last_action = memory_summary[-1] if memory_summary else ""
        
        try:
            # Usar el modelo con visión más rápido disponible
            # llama-3.2-11b-vision-preview: Más rápido, gratis, 30 req/min
            # llama-3.2-90b-vision-preview: Más preciso pero lento
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct", # Tu modelo
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}},
                        {"type": "text", "text": prompt + f"\nIMPORTANT: Do NOT use {last_action}. Try a DIFFERENT direction to explore."}
                    ]
                }],
                max_tokens=5,
                temperature=0.7 # Subimos temperatura para que no sea tan repetitivo
            )
            
            action = response.choices[0].message.content.strip().upper()
            
            
            
            # Limpieza rápida
            for v in ["UP", "DOWN", "LEFT", "RIGHT", "A", "B"]:
                if v in action: return v
            
            return "A"
            
        except Exception as e:
            print(f"Error: {e}")
            return "A"
    
    def advance_objective(self):
        """Avanza al siguiente objetivo atómico"""
        self.steps_since_advance = 0
        self.current_atomic += 1
        
        # Verificar si completamos el objetivo táctico
        phase = self.objectives['objective_hierarchy']['layer_1_strategic'][self.current_phase]
        tactical = phase['layer_2_tactical'][self.current_tactical]
        
        if self.current_atomic >= len(tactical['layer_3_atomic']):
            # Avanzar al siguiente objetivo táctico
            self.current_atomic = 0
            self.current_tactical += 1
            
            # Verificar si completamos la fase estratégica
            if self.current_tactical >= len(phase['layer_2_tactical']):
                self.current_tactical = 0
                self.current_phase += 1
                
                print(f"\n🎉 PHASE {self.current_phase} COMPLETED!\n")
        
        context = self.get_current_context()
        if context:
            print(f"\n➡️  NEW OBJECTIVE: {context['current_step']}\n")
    
    def increment_step_counter(self):
        """Incrementa el contador de pasos sin progreso"""
        self.steps_since_advance += 1
        
        # Si lleva demasiado tiempo en un objetivo, forzar avance
        if self.steps_since_advance >= self.max_steps_per_objective:
            print(f"\n⏭️  Objective timeout, forcing advance...\n")
            self.advance_objective()
            return True
        
        return False
    
    def get_progress_info(self):
        """Retorna información del progreso actual"""
        return {
            'phase': self.current_phase,
            'tactical': self.current_tactical,
            'atomic': self.current_atomic,
            'steps_since_advance': self.steps_since_advance
        }
        
        
    def _get_waypoint_hint(self, objective_name, game_state):
        """Genera hint basado en waypoints cercanos"""
        if not self.waypoints:
            return "No waypoint data available"
            
        objective_lower = objective_name.lower()
        
        #Buscar waypoints relevantes
        relevant_waypoints = []
        
        # Debug: mostrar qué se está buscando
        print(f"   🔍 Searching waypoints for: '{objective_lower}'")

        for phase_name, objectives in self.waypoints.items():
            print(f"      Checking phase: {phase_name}")  # ← DEBUG
            for obj_key, waypoints in objectives.items():
                print(f"         Checking objective: {obj_key}")  # ← DEBUG
                if obj_key.lower() in objective_lower or objective_lower in obj_key.lower() or any(word in obj_key.lower() for word in objective_lower.split()):
                    relevant_waypoints = waypoints
                    print(f"         ✅ MATCH FOUND: {obj_key}")  # ← DEBUG
                    break
            if relevant_waypoints:
                break
                
        if not relevant_waypoints:
            return "Navigate towards your objetive"
            
        #Encontrar waypoint mas cercano no visitado
        current_pos = (game_state['map_id'], game_state['x'], game_state['y'])
        
        closest = None
        min_distance = float('inf')
        
        for wp in relevant_waypoints:
            if wp['map'] != current_pos[0]:
                continue    #Diferente mapa, skip
       
            distance = abs(wp['x'] - current_pos[1]) + abs(wp['y'] - current_pos[2])
            if distance < min_distance:
                min_distance = distance
                closest = wp
                
        if closest:
            direction_hint = self._get_direction_hint(current_pos, closest)
            return f"Target: {closest['description']} at ({closest['x']}, {closest['y']}) - {direction_hint}"

        # Si no hay waypoint en este mapa, comprobamos si el objetivo está en otro mapa
        if relevant_waypoints:
            first_wp = relevant_waypoints[0]
            
            # --- CAMBIO CRÍTICO: DETECTAR CAMBIO DE MAPA ---
            # Si el objetivo está en otro mapa (ej: Mapa 0) y nosotros en otro (Mapa 38)
            # las coordenadas NO sirven y solo confunden al robot causando bucles.
            if first_wp['map'] != current_pos[0]:
                return " You are currently inside a room or building. The objective is OUTSIDE. IGNORE COORDINATES. Look for STAIRS, a DOOR, or a carpet to EXIT this map."
            # -----------------------------------------------

            # Si estamos en el mismo mapa, damos coordenadas precisas
            return f" TARGET COORDINATES: X={first_wp['x']}, Y={first_wp['y']} (on Map {first_wp['map']}). Move to reach that specific point."

        return "Navigate towards your objective"
        
    def _get_direction_hint(self, current, waypoint):
        """Genera hint direccional simple"""
        dx = waypoint['x'] - current[1]
        dy = waypoint['y'] - current[2]
        
        hints = []
        if dy < -2:
            hints.append("Go UP")
        elif dy > 2:
            hints.append("Go DOWN")
            
        if dx < -2:
            hints.append("Go LEFT")
        elif dx > 2:
            hints.append("Go RIGHT")
            
        if not hints:
            return "You are close!"
            
        return " then ".join(hints)
