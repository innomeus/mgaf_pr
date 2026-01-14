"""
Progress Tracker - Sistema de progreso basado en waypoints.json
"""
import json

class ProgressTracker:
    def __init__(self, waypoints_file):
        with open(waypoints_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.all_waypoints = data['waypoints']
        
        self.checkpoints = []
        self.last_progress_step = 0
        self.no_progress_counter = 0
        
    def check_progress(self, current_state, objective_name):
        """
        Verifica si hubo progreso hacia el objetivo actual
        
        Returns:
            'progress', 'stuck', o 'neutral'
        """
        # Buscar waypoints relevantes
        waypoints = self._get_waypoints(objective_name)
        
        if not waypoints:
            return 'neutral'
        
        current_pos = (current_state['map_id'], current_state['x'], current_state['y'])
        
        # Verificar si alcanzó algún waypoint
        for waypoint in waypoints:
            if self._near_waypoint(current_pos, waypoint):
                waypoint_tuple = (waypoint['map'], waypoint['x'], waypoint['y'])
                if waypoint_tuple not in self.checkpoints:
                    self.checkpoints.append(waypoint_tuple)
                    self.no_progress_counter = 0
                    print(f"   ✨ WAYPOINT: {waypoint.get('description', 'Unknown')}")
                    return 'progress'
        
        # Si no hay progreso en 30 steps
        self.no_progress_counter += 1
        if self.no_progress_counter > 30:
            return 'stuck'
        
        return 'neutral'
    
    def _get_waypoints(self, objective_name):
        """Busca waypoints relevantes según el objetivo"""
        objective_lower = objective_name.lower()
        
        # Buscar en todas las fases
        for phase_name, objectives in self.all_waypoints.items():
            for obj_key, waypoints in objectives.items():
                if obj_key.lower() in objective_lower or objective_lower in obj_key.lower():
                    return waypoints
        
        return []
    
    def _near_waypoint(self, current, waypoint, threshold=3):
        """Verifica si está cerca de un waypoint"""
        map_id, x, y = current
        w_map = waypoint['map']
        w_x = waypoint['x']
        w_y = waypoint['y']
        
        if map_id != w_map:
            return False
        
        distance = abs(x - w_x) + abs(y - w_y)
        return distance <= threshold
    
    def reset_for_new_objective(self):
        """Resetea cuando cambia de objetivo"""
        self.checkpoints = []
        self.no_progress_counter = 0