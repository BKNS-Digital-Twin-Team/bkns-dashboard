# opc_utils.py
import time

from state import (
    sessions, session_states, previous_states, session_last_full_sync,
    opc_adapters, FULL_SYNC_INTERVAL
)
from logic import control_logic


async def send_to_server(session_id, force_send_all=False):
    model = sessions[session_id]
    current_state = model.get_status()
    
    now = time.time()
    
    if force_send_all:
        session_last_full_sync[session_id] = now
        print("[SYNC] Запуск принудительной полной синхронизации...")   
    elif not force_send_all:
        last_sync_time = session_last_full_sync.get(session_id, 0)
        if now - last_sync_time >= FULL_SYNC_INTERVAL:
            force_send_all = True
            print(f"[SYNC] Автоматическая полная синхронизация для {session_id}...")
    
    for (component, param), override_value in control_logic.manual_overrides.get(session_id, {}).items():
        control_logic.send_command_to_opc(session_id, component, param, override_value)
    
    for component, params in current_state.items():
        for param, value in params.items():
            key = (component, param)
            if force_send_all or previous_states[session_id].get(key) != value:
               # await opc_adapters[session_id].send_to_opc(component, param, value)
                control_logic.send_command_to_opc(session_id, component, param, value)
                previous_states[session_id][key] = value
                
    if force_send_all:
        print("[SYNC] Полная синхронизация завершена.")
                