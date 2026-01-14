"""
Memory Buffer - Almacena historial de acciones y detecta patrones
"""

from collections import deque

class MemoryBuffer:
    """
    Buffer sofisticado para recordar acciones y detectar loops/stuck
    """
    
    def __init__(self, max_size=20):
        self.actions = deque(maxlen=max_size)
        self.states_before = deque(maxlen=max_size)
        self.states_after = deque(maxlen=max_size)
        self.results = deque(maxlen=max_size)
        self.max_size = max_size
        self.stuck_counter = 0
    
    def add(self, action, state_before, state_after):
        """
        Añade una acción al buffer con su resultado
        
        Args:
            action: Nombre del botón presionado (UP, A, etc.)
            state_before: Estado del juego antes de la acción
            state_after: Estado del juego después de la acción
        """
        self.actions.append(action)
        self.states_before.append(state_before)
        self.states_after.append(state_after)
        
        # Calcular resultado
        result = self._compute_result(state_before, state_after)
        self.results.append(result)
    
    def _compute_result(self, before, after):
        """Detecta qué cambió entre estados"""
        changes = []
        
        # Cambio de mapa (más importante)
        if before['map_id'] != after['map_id']:
            changes.append(f"Map {before['map_id']}→{after['map_id']}")
        
        # Cambio de batalla
        if before.get('in_battle') != after.get('in_battle'):
            if after.get('in_battle'):
                changes.append("Entered battle")
            else:
                changes.append("Exited battle")
        
        # Movimiento significativo
        dx = abs(before['x'] - after['x'])
        dy = abs(before['y'] - after['y'])
        
        if dx > 5 or dy > 5:
            changes.append("Teleported")
        elif dx > 0 or dy > 0:
            changes.append("Moved")
        
        # Cambio de badges
        if before['badges'] != after['badges']:
            changes.append(f"Badge earned! ({after['badges']}/8)")
        
        # Si no hubo cambios
        if not changes:
            return "No change"
        
        return " | ".join(changes)
    
    def get_recent_summary(self, n=5):
        """
        Retorna resumen de últimas N acciones
        
        Args:
            n: Número de acciones a incluir
            
        Returns:
            String formateado con el resumen
        """
        if len(self.actions) == 0:
            return "No actions yet"
        
        recent = list(zip(
            list(self.actions)[-n:],
            list(self.results)[-n:]
        ))
        
        summary = []
        for i, (action, result) in enumerate(recent, 1):
            summary.append(f"{i}. {action} → {result}")
        
        return "\n".join(summary)
    
    def detect_loop(self):
        """
        Detecta si está en un loop (repitiendo el mismo patrón)
        
        Returns:
            True si detecta loop, False si no
        """
        if len(self.actions) < 8:
            return False
        
        # Patrón simple: últimas 4 acciones == 4 anteriores
        last_4 = list(self.actions)[-4:]
        prev_4 = list(self.actions)[-8:-4]
        
        if last_4 == prev_4:
            return True
        
        # Detectar oscilación (UP-DOWN-UP-DOWN o LEFT-RIGHT-LEFT-RIGHT)
        if len(self.actions) >= 4:
            last = list(self.actions)[-4:]
            if last == ["UP", "DOWN", "UP", "DOWN"]:
                return True
            if last == ["DOWN", "UP", "DOWN", "UP"]:
                return True
            if last == ["LEFT", "RIGHT", "LEFT", "RIGHT"]:
                return True
            if last == ["RIGHT", "LEFT", "RIGHT", "LEFT"]:
                return True
        
        return False
    
    def detect_stuck(self):
        """
        Detecta si está atascado (misma posición muchas veces)
        
        Returns:
            True si está atascado, False si no
        """
        if len(self.states_after) < 2:
            return False
        
        # Obtener últimas 5 posiciones
        recent_positions = [
            (s['x'], s['y'], s['map_id']) 
            for s in list(self.states_after)[-2:]
        ]
        
        # Si solo hay 2 o menos posiciones únicas, está atascado
        unique_positions = set(recent_positions)
        if len(unique_positions) == 1:
            self.stuck_counter += 1
            return True
        
        self.stuck_counter = 0
        return False
    
    def get_stuck_suggestion(self):
        """
        Sugiere una acción para salir del estado stuck
        
        Returns:
           String con nombre de acción sugerida
        """
        if len(self.actions) < 3:
            return "A"
        
        recent = list(self.actions)[-5:]
        
      # NIVEL 1: Primeros intentos (1-3) - Probar B o A
       #if self.stuck_counter == 0:
       #    return "A"
       #elif self.stuck_counter == 1:
       #    if recent.count("A") >= 2:
       #        return "DOWN"
       #    return "RIGHT"
        
       # NIVEL 2: Intentos 4-8 - Forzar movimiento simple
        if self.stuck_counter <= 5:
        # Alternar entre direcciones no usadas recientemente
            directions = ["UP", "DOWN", "LEFT", "RIGHT"]
        for direction in directions:
            if recent.count(direction) == 0:
                return direction
        return "DOWN"  # Default si todas están usadas
    
    # NIVEL 3: Intentos 9-15 - Movimiento agresivo
        if self.stuck_counter <= 10:
        # Probar la dirección opuesta a la última usada
            last_action = self.actions[-1]
            opposites = {
                "UP": "DOWN",
                "DOWN": "UP",
                "LEFT": "RIGHT",
                "RIGHT": "LEFT"
            }
        if last_action in opposites:
            return opposites[last_action]
        return "DOWN"
    
    # NIVEL 4: Más de 15 intentos - Secuencia de escape
        escape_sequence = ["START", "B", "DOWN", "DOWN", "A"]
        idx = self.stuck_counter % len(escape_sequence)
        return escape_sequence[idx]
    
    
    def get_position_history(self, n=10):
        """
        Retorna historial de posiciones recientes
        
        Args:
            n: Número de posiciones a retornar
            
        Returns:
            Lista de tuplas (x, y, map_id)
        """
        if len(self.states_after) == 0:
            return []
        
        return [
            (s['x'], s['y'], s['map_id'])
            for s in list(self.states_after)[-n:]
        ]
    
    def clear(self):
        """Limpia todo el buffer"""
        self.actions.clear()
        self.states_before.clear()
        self.states_after.clear()
        self.results.clear()