# opc_utils.py
import time

from state import (
    sessions, session_states, previous_states, session_last_full_sync,
    opc_adapters, FULL_SYNC_INTERVAL
)
from logic import control_logic

def flatten_status_for_opc(status_dict: dict) -> dict:
    """
    Тупой конвертер. Берет словарь от get_status() и делает его плоским для OPC.
    Не лезет в модель. Гарантирует, что данные те же, что и на фронте.
    """
    flat = {}

    # Насосы
    for pump_id, pump_data in status_dict.get('pumps', {}).items():
        prefix = f"pump_{pump_id}"
        flat[prefix] = {
            "na_on": pump_data.get('is_running', False),
            "na_off": pump_data.get('is_off', True),
            "motor_current": pump_data.get('current', 0.0),
            "pressure_in": pump_data.get('pressure_in', 0.0),  # <--- БЕРЕТ ИЗ ТОГО ЖЕ МЕСТА, ЧТО И ФРОНТ
            "pressure_out": pump_data.get('outlet_pressure', 0.0),
            "flow_rate": pump_data.get('flow_rate', 0.0),
            "cover_open": pump_data.get('di_kojuh_status', True),
            "temp_bearing_1": pump_data.get('temperatures', {}).get('T2', 0.0),
            "temp_bearing_2": pump_data.get('temperatures', {}).get('T3', 0.0),
            "temp_motor_1": pump_data.get('temperatures', {}).get('T4', 0.0),
            "temp_motor_2": pump_data.get('temperatures', {}).get('T5', 0.0),
            "temp_water": pump_data.get('temperatures', {}).get('T5', 0.0) # Используем T5 как температуру воды
        }

    # Маслосистемы
    for oil_id, oil_data in status_dict.get('oil_systems', {}).items():
        prefix = f"oil_system_{oil_id}"
        flat[prefix] = {
            "oil_sys_running": oil_data.get('is_running', False),
            "oil_sys_pressure_ok": oil_data.get('pressure_ok', False),
            "oil_pressure": oil_data.get('pressure', 0.0),
            "temperature": oil_data.get('temperature', 0.0),
        }

    # Задвижки
    for valve_key, valve_data in status_dict.get('valves', {}).items():
        prefix = f"valve_{valve_key}"
        flat[prefix] = {
            "valve_open": valve_data.get('is_open', False),
            "valve_closed": valve_data.get('is_closed', True),
        }

    return flat

async def update_opc_from_model_state(session_id, force_send_all=False):
    model = sessions[session_id]
    raw_status = model.get_status()
    current_state = flatten_status_for_opc(raw_status)
    
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
        control_logic.process_command(session_id, "MODEL", component, param, override_value)
    
    for component, params in current_state.items():
        for param, value in params.items():
            key = (component, param)
            if force_send_all or previous_states[session_id].get(key) != value:
                opc_adapters[session_id].process_command("MODEL", component, param, value)
                previous_states[session_id][key] = value
                
    if force_send_all:
        print("[SYNC] Полная синхронизация завершена.")
                