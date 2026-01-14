"""
Agente principal para jugar Pokémon Red usando Groq + Llama 4 Scout
VERSIÓN DEBUG - Con prints para diagnosticar problemas
"""

import time
import base64
import cv2
import numpy as np
from pyboy import PyBoy
from pyboy.utils import WindowEvent
import sys
import os

# Importar componentes del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.llm_planner import LLMPlanner
from core.memory_buffer import MemoryBuffer
from core.event_checker import EventChecker
from core.progress_tracker import ProgressTracker
from core.dialog_detector import DialogDetector

# ============================================================================
# CONFIGURACIÓN (EDITAR AQUÍ)
# ============================================================================

GROQ_API_KEY = "GROQ_API_KEY"

ROM_PATH = "pokemon_red.gb"
OBJECTIVES_FILE = "config/objectives.json"
SKILLS_FILE = "config/skills.json"
EVENTS_FILE = "config/events.json"
WAYPOINTS_FILE = "config/waypoints.json"

RECORD_VIDEO = True
VIDEO_OUTPUT = "agent_playthrough.mp4"
VIDEO_FPS = 2

MAX_STEPS = 10000
RATE_LIMIT_DELAY = 2

# ============================================================================
# MAPEO DE ACCIONES
# ============================================================================

ACTION_MAP = {
    "UP": WindowEvent.PRESS_ARROW_UP,
    "DOWN": WindowEvent.PRESS_ARROW_DOWN,
    "LEFT": WindowEvent.PRESS_ARROW_LEFT,
    "RIGHT": WindowEvent.PRESS_ARROW_RIGHT,
    "A": WindowEvent.PRESS_BUTTON_A,
    "B": WindowEvent.PRESS_BUTTON_B,
    "START": WindowEvent.PRESS_BUTTON_START,
    "SELECT": WindowEvent.PRESS_BUTTON_SELECT,
}

# ============================================================================
# LECTURA DE ESTADO DEL JUEGO
# ============================================================================

MEMORY_ADDRESSES = {
    'map_id': 0xD35E,
    'player_x': 0xD361,
    'player_y': 0xD362,
    'badges': 0xD356,
    'party_count': 0xD163,
    'money_bcd1': 0xD347,
    'money_bcd2': 0xD348,
    'money_bcd3': 0xD349,
    'in_battle': 0xD057,
}

def read_game_state(emu):
    """Lee el estado actual del juego desde la memoria"""
    mem = emu.memory
    
    # Leer dinero (formato BCD)
    money_h = mem[MEMORY_ADDRESSES['money_bcd1']]
    money_m = mem[MEMORY_ADDRESSES['money_bcd2']]
    money_l = mem[MEMORY_ADDRESSES['money_bcd3']]
    money = ((money_h >> 4) * 100000 + (money_h & 0xF) * 10000 +
             (money_m >> 4) * 1000 + (money_m & 0xF) * 100 +
             (money_l >> 4) * 10 + (money_l & 0xF))
    
    # Nivel máximo del equipo
    party_count = mem[MEMORY_ADDRESSES['party_count']]
    max_level = 0
    if 0 < party_count <= 6:
        for i in range(party_count):
            level_addr = 0xD18C + (i * 44)
            level = mem[level_addr]
            max_level = max(max_level, level)
    
    return {
        'map_id': mem[MEMORY_ADDRESSES['map_id']],
        'x': mem[MEMORY_ADDRESSES['player_x']],
        'y': mem[MEMORY_ADDRESSES['player_y']],
        'badges': bin(mem[MEMORY_ADDRESSES['badges']]).count('1'),
        'party_count': party_count if 0 < party_count <= 6 else 0,
        'max_level': max_level,
        'money': money,
        'in_battle': mem[MEMORY_ADDRESSES['in_battle']] > 0
    }

# ============================================================================
# MAIN LOOP
# ============================================================================

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       POKÉMON RED - GROQ AGENT (DEBUG MODE)             ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Verificar archivos
    print("🔍 Verificando archivos...")
    required_files = [
        (ROM_PATH, "ROM"),
        (OBJECTIVES_FILE, "objectives.json"),
        (SKILLS_FILE, "skills.json"),
        (EVENTS_FILE, "events.json"),
        (WAYPOINTS_FILE, "waypoints.json")
    ]
    
    for filepath, name in required_files:
        if not os.path.exists(filepath):
            print(f"❌ ERROR: No se encuentra '{name}' en '{filepath}'")
            return
        else:
            print(f"   ✅ {name} encontrado")
    
    # Inicializar componentes
    print("\n🎮 Inicializando emulador...")
    emu = PyBoy(ROM_PATH, window_type="SDL2")
    emu.set_emulation_speed(0)
    print("   ✅ Emulador iniciado")
    
    print("\n🤖 Inicializando LLM Planner...")
    planner = LLMPlanner(GROQ_API_KEY, OBJECTIVES_FILE, SKILLS_FILE, WAYPOINTS_FILE)
    print(f"   ✅ Planner iniciado")
    print(f"   DEBUG: Waypoints en planner: {len(planner.waypoints)} fases")
    if planner.waypoints:
        print(f"   DEBUG: Primera fase: {list(planner.waypoints.keys())[0]}")
    
    print("\n💾 Inicializando Memory Buffer...")
    memory = MemoryBuffer(max_size=20)
    print("   ✅ Memory Buffer iniciado")
    
    print("\n✅ Inicializando Event Checker...")
    event_checker = EventChecker(EVENTS_FILE)
    print("   ✅ Event Checker iniciado")
    
    print("\n📈 Inicializando Progress Tracker...")
    progress_tracker = ProgressTracker(WAYPOINTS_FILE)
    print(f"   ✅ Progress Tracker iniciado")
    print(f"   DEBUG: Waypoints cargados: {len(progress_tracker.all_waypoints)} fases")
    if progress_tracker.all_waypoints:
        print(f"   DEBUG: Primera fase: {list(progress_tracker.all_waypoints.keys())[0]}")
    
    print("\n💬 Inicializando Dialog Detector...")
    dialog_detector = DialogDetector()
    print("   ✅ Dialog Detector iniciado")
    
    # Video recorder
    video = None
    if RECORD_VIDEO:
        print("\n🎬 Inicializando grabación de video...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(VIDEO_OUTPUT, fourcc, VIDEO_FPS, (160, 144))
        print("   ✅ Video recorder iniciado")
    
    # Skip intro MANUAL
    print("\n⏩ Saltando intro del juego...")
    
    # Esperar a pantalla de título
    for _ in range(300):
        emu.tick()
    
    # Presionar START para entrar
    emu.send_input(WindowEvent.PRESS_BUTTON_START)
    for _ in range(10):
        emu.tick()
    emu.send_input(WindowEvent.RELEASE_BUTTON_START)
    for _ in range(50):
        emu.tick()
    
    # Presionar START repetidamente
    for _ in range(100):
        emu.send_input(WindowEvent.PRESS_BUTTON_START)
        for _ in range(2): 
            emu.tick()
        emu.send_input(WindowEvent.RELEASE_BUTTON_START)
        for _ in range(2): 
            emu.tick()
    
    # Presionar A para continuar
    for _ in range(100):
        emu.send_input(WindowEvent.PRESS_BUTTON_A)
        for _ in range(2): 
            emu.tick()
        emu.send_input(WindowEvent.RELEASE_BUTTON_A)
        for _ in range(2): 
            emu.tick()
    
    # Esperar estabilización
    for _ in range(30): 
        emu.tick()
    
    print("   ✅ Intro saltada")
    
    # Obtener objetivo inicial
    context = planner.get_current_context()
    print(f"\n🎯 OBJETIVO INICIAL:")
    print(f"   Strategic: {context['strategic_goal']}")
    print(f"   Tactical: {context['tactical_goal']}")
    print(f"   Current: {context['current_step']}\n")
    
    print("="*70)
    print("🚀 INICIANDO AGENTE\n")
    
    step = 0
    
    try:
        while step < MAX_STEPS:
            # Leer estado ANTES
            state_before = read_game_state(emu)
            
            # DEBUG: Mostrar estado cada 10 steps
            if step % 10 == 0:
                print(f"\n   🔍 DEBUG STATE: Map={state_before['map_id']}, Pos=({state_before['x']},{state_before['y']})")
            
            # Capturar screenshot
            screen = emu.screen.image
            screen.save("temp.png")
            with open("temp.png", "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            
            # SISTEMA DE DECISIÓN JERÁRQUICO
            action = None
            action_source = "LLM"
            
            # PRIORIDAD 1: Detectar diálogos
            #is_dialog = dialog_detector.is_in_dialog(emu)
            #if is_dialog:
            #    print(f"   💬 DEBUG: Dialog detected (counter={dialog_detector.dialog_counter})")
            #    if dialog_detector.should_auto_advance():
            #        action = "A"
            #        action_source = "DIALOG"
            
            # PRIORIDAD 2: Verificar progreso
            if action is None:
                context = planner.get_current_context()
                if context:
                    if step % 5 == 0:  # Debug cada 5 steps
                        print(f"   📊 DEBUG: Checking progress for '{context['current_step']}'")
                    
                    progress_status = progress_tracker.check_progress(
                        state_before, 
                        context['current_step']
                    )
                    
                    if step % 5 == 0:
                        print(f"   📊 DEBUG: Progress status = {progress_status}")
                    
                    if progress_status == 'stuck':
                        action = memory.get_stuck_suggestion()
                        action_source = "NO_PROGRESS"
                        print(f"   🔄 DEBUG: No progress, forcing {action}")
                    elif memory.detect_stuck() or memory.detect_loop():
                        action = memory.get_stuck_suggestion()
                        action_source = "STUCK/LOOP"
                        print(f"   ⚠️ DEBUG: Stuck/loop (counter={memory.stuck_counter}), forcing {action}")
            
            # PRIORIDAD 3: Decisión normal con LLM
            if action is None:
                memory_summary = memory.get_recent_summary()
                action = planner.decide_action(img_b64, state_before, memory_summary)
                action_source = "LLM"
            
            # Mostrar info con source
            source_icons = {
                "LLM": "🤖",
                "DIALOG": "💬",
                "STUCK/LOOP": "⚠️",
                "NO_PROGRESS": "🔄"
            }
            icon = source_icons.get(action_source, "")
            
            print(f"[{step:04d}] {icon} {action:6s} | Pos: ({state_before['x']:3d},{state_before['y']:3d}) Map: {state_before['map_id']:3d} | Badges: {state_before['badges']}/8")
            
            # Ejecutar acción
            if action in ACTION_MAP:
                emu.send_input(ACTION_MAP[action])
                for _ in range(30):
                    emu.tick()
                emu.send_input(ACTION_MAP[action] + 8)  # Release
            else:
                print(f"   ⚠️ WARNING: Invalid action '{action}', defaulting to A")
                emu.send_input(ACTION_MAP["A"])
                for _ in range(30):
                    emu.tick()
                emu.send_input(ACTION_MAP["A"] + 8)
            
            # Estado DESPUÉS
            state_after = read_game_state(emu)
            
            # Guardar en memoria
            memory.add(action, state_before, state_after)
            
            # Verificar si completó objetivo actual
            context = planner.get_current_context()
            if context:
                obj_complete = event_checker.check_objective_complete(
                    context['current_step'], 
                    state_after, 
                    emu.memory
                )
                if obj_complete:
                    print(f"\n✅ COMPLETADO: {context['current_step']}")
                    planner.advance_objective()
                    progress_tracker.reset_for_new_objective()
                    context = planner.get_current_context()
                    if context:
                        print(f"➡️ NUEVO: {context['current_step']}\n")
                    else:
                        print("\n🎉 ¡TODOS LOS OBJETIVOS COMPLETADOS!\n")
                        break
            
            # Grabar frame
            if video:
                frame = np.array(emu.screen.image.convert('RGB'))
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                video.write(frame_bgr)
            
            # Incrementar contador de planner
            planner.increment_step_counter()
            
            step += 1
            time.sleep(RATE_LIMIT_DELAY)
    
    except KeyboardInterrupt:
        print("\n\n⏸️ Interrumpido por el usuario")
    
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if video:
            video.release()
            print(f"\n✅ Video guardado: {VIDEO_OUTPUT}")
        
        emu.stop()
        
        progress = planner.get_progress_info()
        print(f"\n📊 PROGRESO FINAL:")
        print(f"   - Steps ejecutados: {step}")
        print(f"   - Fase: {progress['phase']}")
        print(f"   - Objetivo táctico: {progress['tactical']}")
        print(f"   - Paso atómico: {progress['atomic']}")
        print(f"\n📜 Eventos completados:")
        for event in event_checker.get_completed_events():
            print(f"   ✅ {event}")
        
        print("\n👋 Sesión terminada")

if __name__ == "__main__":
    main()
