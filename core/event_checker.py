"""
Event Checker - Verifica objetivos usando events.json
"""

import json


class EventChecker:
    """
    Verifica eventos mediante memoria del juego usando events.json
    """
    
    def __init__(self, events_file="config/events.json"):
        with open(events_file, 'r') as f:
            self.events = json.load(f)
        
        self.completed_events = set()
    
    def _read_flag(self, memory, address_str, bit=None):
        """Lee un flag de memoria (con soporte para bits)"""
        addr = int(address_str, 16)
        value = memory[addr]
        
        if bit is not None:
            # Leer bit específico
            return (value >> bit) & 1 == 1
        else:
            # Leer valor completo
            return value
    
    def check_story_flag(self, memory, flag_name):
        """Verifica un story flag específico"""
        if flag_name not in self.events['story_flags']:
            return False
        
        flag_data = self.events['story_flags'][flag_name]
        addr = flag_data['address']
        bit = flag_data.get('bit', None)
        
        return self._read_flag(memory, addr, bit) == 1
    
    def check_has_item(self, memory, item_name):
        """Verifica si tiene un item (HM o key item)"""
        # Buscar en HMs
        if item_name in self.events['hms']:
            addr = self.events['hms'][item_name]
            return self._read_flag(memory, addr) > 0
        
        # Buscar en key items
        if item_name in self.events['key_items']:
            addr = self.events['key_items'][item_name]
            return self._read_flag(memory, addr) > 0
        
        return False
    
    def check_badge_count(self, memory, target_count):
        """Verifica número de badges"""
        addr = int(self.events['game_state']['badge_count'], 16)
        badges = bin(memory[addr]).count('1')
        return badges >= target_count
    
    def check_in_location(self, game_state, location_name):
        """Verifica si está en una ubicación específica"""
        if location_name not in self.events['map_ids']:
            return False
        
        target_map = self.events['map_ids'][location_name]
        return game_state['map_id'] == target_map
    
    def check_objective_complete(self, objective_text, game_state, memory):
        """
        Verifica si un objetivo está completo analizando el texto
        
        Args:
            objective_text: Texto del objetivo (del JSON)
            game_state: Estado del juego
            memory: Memoria del emulador
        """
        obj = objective_text.lower()
        
        # === TUTORIAL / PALLET TOWN ===
        if "sacar" in obj and "poción" in obj and "pc" in obj:
            return game_state['map_id'] != self.events['map_ids']['players_house_1f']
        
        if "hierba alta" in obj or "oak te detendrá" in obj:
            return self.check_story_flag(memory, 'got_starter')
        
        if "laboratorio" in obj and "oak" in obj:
            return game_state['map_id'] == self.events['map_ids']['oaks_lab']
        
        if "elegir" in obj and "pokémon inicial" in obj:
            return game_state['party_count'] >= 1
        
        if "derrotar" in obj and "rival" in obj and "laboratorio" in obj:
            return self.check_story_flag(memory, 'rival_battle_lab')
        
        if "viridian city" in obj:
            return self.check_in_location(game_state, 'viridian_city')
        
        if "parcel" in obj and ("recibir" in obj or "tienda" in obj):
            return self.check_has_item(memory, 'ss_ticket') or game_state['map_id'] == self.events['map_ids']['viridian_city']
        
        if "entregar" in obj and "parcel" in obj:
            return self.check_story_flag(memory, 'oak_parcel_delivered')
        
        if "pokédex" in obj or "pokedex" in obj:
            return self.check_story_flag(memory, 'pokedex_obtained')
        
        # === COMPRAS ===
        if "comprar" in obj and ("poké ball" in obj or "pokeball" in obj):
            return game_state.get('money', 3000) < 3000
        
        if "comprar" in obj and "potion" in obj:
            return True  # Simplificado
        
        # === BROCK / PEWTER ===
        if "viridian forest" in obj or "cruzar" in obj and "forest" in obj:
            return game_state['map_id'] != self.events['map_ids']['viridian_forest']
        
        if "pewter city" in obj and "llegar" in obj:
            return self.check_in_location(game_state, 'pewter_city')
        
        if "entrenar" in obj and "nivel" in obj:
            return game_state.get('max_level', 0) >= 12
        
        if ("brock" in obj or "boulder badge" in obj) and "derrotar" in obj:
            return self.check_story_flag(memory, 'defeated_brock')
        
        # === MT. MOON / CERULEAN ===
        if "mt. moon" in obj or "mt moon" in obj:
            return game_state['map_id'] != self.events['map_ids']['mt_moon']
        
        if "cerulean city" in obj or "cerulean" in obj:
            return self.check_in_location(game_state, 'cerulean_city')
        
        if "bill" in obj and "ayudar" in obj:
            return self.check_story_flag(memory, 'bill_helped')
        
        if ("misty" in obj or "cascade badge" in obj) and "derrotar" in obj:
            return self.check_story_flag(memory, 'defeated_misty')
        
        # === VERMILION / LT. SURGE ===
        if "vermilion" in obj:
            return self.check_in_location(game_state, 'vermilion_city')
        
        if "s.s. anne" in obj or "ss anne" in obj:
            return self.check_story_flag(memory, 'ss_anne_left')
        
        if "hm01" in obj or ("cut" in obj and "obtener" in obj):
            return self.check_has_item(memory, 'hm01_cut')
        
        if ("lt. surge" in obj or "surge" in obj or "thunder badge" in obj) and "derrotar" in obj:
            return self.check_story_flag(memory, 'defeated_lt_surge')
        
        # === CELADON / ERIKA ===
        if "rock tunnel" in obj:
            return game_state['map_id'] != self.events['map_ids']['rock_tunnel']
        
        if "celadon" in obj and "llegar" in obj:
            return self.check_in_location(game_state, 'celadon_city')
        
        if ("erika" in obj or "rainbow badge" in obj) and "derrotar" in obj:
            return self.check_story_flag(memory, 'defeated_erika')
        
        if "rocket hideout" in obj or "casino rocket" in obj:
            return self.check_story_flag(memory, 'rocket_hideout_cleared')
        
        if "silph scope" in obj:
            return self.check_has_item(memory, 'silph_scope')
        
        if "pokemon tower" in obj or "pokémon tower" in obj:
            return self.check_story_flag(memory, 'pokemon_tower_cleared')
        
        if "poké flute" in obj or "poke flute" in obj:
            return self.check_has_item(memory, 'poke_flute')
        
        # === FUCHSIA / KOGA ===
        if "fuchsia" in obj:
            return self.check_in_location(game_state, 'fuchsia_city')
        
        if "safari zone" in obj:
            return True  # Simplificado (difícil verificar)
        
        if "hm03" in obj or ("surf" in obj and "obtener" in obj):
            return self.check_has_item(memory, 'hm03_surf')
        
        if "hm04" in obj or ("strength" in obj and "obtener" in obj):
            return self.check_has_item(memory, 'hm04_strength')
        
        if ("koga" in obj or "soul badge" in obj) and "derrotar" in obj:
            return self.check_story_flag(memory, 'defeated_koga')
        
        # === SAFFRON / SABRINA ===
        if "saffron" in obj:
            return self.check_in_location(game_state, 'saffron_city')
        
        if "silph co" in obj:
            return self.check_story_flag(memory, 'silph_co_cleared')
        
        if "master ball" in obj:
            return self.check_story_flag(memory, 'silph_co_cleared')
        
        if ("sabrina" in obj or "marsh badge" in obj) and "derrotar" in obj:
            return self.check_story_flag(memory, 'defeated_sabrina')
        
        # === CINNABAR / BLAINE ===
        if "cinnabar" in obj:
            return self.check_in_location(game_state, 'cinnabar_island')
        
        if ("blaine" in obj or "volcano badge" in obj) and "derrotar" in obj:
            return self.check_story_flag(memory, 'defeated_blaine')
        
        # === VIRIDIAN GYM / GIOVANNI ===
        if "giovanni" in obj and "viridian" in obj:
            return self.check_story_flag(memory, 'defeated_giovanni')
        
        if "earth badge" in obj:
            return self.check_story_flag(memory, 'defeated_giovanni')
        
        # === ELITE FOUR ===
        if "victory road" in obj:
            return game_state['map_id'] != self.events['map_ids']['victory_road']
        
        if "indigo plateau" in obj:
            return self.check_in_location(game_state, 'indigo_plateau')
        
        if "lorelei" in obj or "bruno" in obj or "agatha" in obj or "lance" in obj:
            return self.check_badge_count(memory, 8)  # Simplificado
        
        # Default: no completado
        return False
    
    def mark_event_complete(self, event_name):
        """Marca evento como completado"""
        self.completed_events.add(event_name)
    
    def is_event_completed(self, event_name):
        """Verifica si evento ya fue marcado"""
        return event_name in self.completed_events
    
    def get_completed_events(self):
        """Lista de eventos completados"""
        return list(self.completed_events)
    
    def reset(self):
        """Reset del checker"""
        self.completed_events.clear()
