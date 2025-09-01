from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import asyncio
import uuid
import importlib.util
import os

from state import (
    sessions, session_states, previous_states, session_last_full_sync,
    opc_adapters, SERVER_URL, SESSIONS_DIR
)
from logic import control_logic
from opc_utils import send_to_server
from opc_adapter import OPCAdapter
from background_tasks import update_loop

api_router = APIRouter(prefix="/api")

@api_router.get("/simulation/{session_id}/state")
def get_simulation_state(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Сессия '{session_id}' не найдена или еще не загружена.")
    
    return {"status": "running" if session_states.get(session_id, {}).get("running") else "paused"}

@api_router.get("/simulation/{session_id}/control_modes")
def get_modes(session_id: str):
     return control_logic.control_modes.get(session_id, {})

@api_router.get("/simulation/{session_id}/status")
def get_state(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Сессия '{session_id}' не найдена или еще не загружена.")
    return sessions[session_id].get_status()


@api_router.post("/simulation/{session_id}/pause")
def pause_simulation(session_id: str):
    if session_states[session_id]["running"] == False:
        return {"status": "already_paused"}
    session_states[session_id]["running"] = False
    print("[SYSTEM] Симуляция поставлена на паузу.")
    return {"status": "paused"}

@api_router.post("/simulation/{session_id}/resume")
def resume_simulation(session_id: str):
    if session_states[session_id]["running"] == True:
        return {"status": "already_running"}
    session_states[session_id]["running"] = True
    print("[SYSTEM] Симуляция возобновлена.")
    return {"status": "resumed"}


class ManualParamCommand(BaseModel):
    source: str
    component: str
    param: str
    value: float

@api_router.post("/simulation/{session_id}/control/manual")
def manual_cmd(session_id: str, cmd: ManualParamCommand):
    return control_logic.process_command(session_id, cmd.source, cmd.component, cmd.param, cmd.value)

@api_router.post("/simulation/{session_id}/sync")
async def sync(session_id: str, background_tasks: BackgroundTasks):
    adapter = opc_adapters.get(session_id)
    if not adapter or not adapter.is_running:
        return {"status": "ERROR", "message": "OPC не подключен"}
    background_tasks.add_task(send_to_server, session_id, force_send_all=True)
    return {"status": "ACCEPTED"}



class ControlSourceCommand(BaseModel):
    source: str
    component: str

@api_router.post("/simulation/{session_id}/control/set_source")
def set_control_source(session_id: str, cmd: ControlSourceCommand):
    if session_id not in sessions: raise HTTPException(status_code=404, detail="Сессия не найдена")
    # ИСПРАВЛЕНИЕ: Убран мертвый код после return
    return control_logic.set_control_source(session_id, cmd.component, cmd.source)


        
@api_router.post("/simulation/{session_id}/control/overrides/set")
def set_manual_overrides(session_id: str, payload: dict):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
        
    # Упрощаем и делаем логику более строгой
    component = payload.get("component")
    param = payload.get("param")
    value = payload.get("value")

    if not all([component, param, value is not None]):
        raise HTTPException(status_code=400, detail="Неверный формат. Требуются 'component', 'param', 'value'.")
    

    control_logic.set_manual_override(session_id, component, param, value)
    print(f"[OVERRIDE] Для сессии {session_id} установлено: {component}.{param} = {value}")
    return {"status": "OK"}
    
@api_router.post("/simulation/{session_id}/control/overrides/clear")
def clear_manual_override(session_id: str, payload: dict):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
        
    # Упрощаем и делаем логику более строгой
    component = payload.get("component")
    param = payload.get("param")

    if not all([component, param is not None]):
        raise HTTPException(status_code=400, detail="Неверный формат. Требуются 'component', 'param'")
    
    control_logic.clear_manual_override(session_id, component, param)
    print(f"[OVERRIDE] Для сессии {session_id} сброщено значение параметра: {component}.{param}")
    return {"status": "OK"}

@api_router.get("/simulation/debug/overrides")
def debug_overrides():
    # Форматируем вывод так, чтобы было понятно, где какая сессия
    all_overrides = {}
    for session_id, overrides in control_logic.manual_overrides.items():
        all_overrides[session_id] = {
            f"{k[0]}.{k[1]}": v for k, v in overrides.items()
        }
    return all_overrides


class LoadSessionRequest(BaseModel):
    session_name: str

@api_router.post("/simulation/session/load")
async def load_session(data: LoadSessionRequest):

    session_id = data.session_name

    if session_id in sessions:
        raise HTTPException(status_code=409, detail=f"Сессия '{session_id}' уже загружена и активна.")

    try:
        config_filename = "config.py"
        full_path = f"./sessions/{session_id}/{config_filename}"

        if not os.path.exists(full_path):
             raise FileNotFoundError(f"Конфигурационный файл не найден: {full_path}")

        spec = importlib.util.spec_from_file_location(session_id, full_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)

        model = config_module.MODEL

        sessions[session_id] = model
        session_states[session_id] = {"running": True}
        previous_states[session_id] = {}
        session_last_full_sync[session_id] = 0
        control_logic.control_modes[session_id] = {}
        control_logic.manual_overrides[session_id] = {}

        opc_adapter = OPCAdapter(SERVER_URL, control_logic, sessions, send_to_server, session_id)
        opc_adapters[session_id] = opc_adapter
        asyncio.create_task(opc_adapter.run())

        asyncio.create_task(update_loop(session_id))

        print(f"[SYSTEM] Сессия '{session_id}' успешно загружена из папки.")
        return {"session_id": session_id, "status": "loaded"}

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА при загрузке сессии '{session_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка при загрузке сессии: {e}")
    
    
@api_router.get("/simulation/sessions/available")
def get_available_sessions():
    """Сканирует папку с сессиями и возвращает их список со статусами."""
    available_sessions = []
    try:
        # Получаем все элементы в директории сессий
        session_folders = [f for f in os.listdir(SESSIONS_DIR) if os.path.isdir(os.path.join(SESSIONS_DIR, f))]
        
        for session_name in session_folders:
            # Проверяем, активна ли сессия (загружена ли она в память)
            is_active = session_name in sessions
            available_sessions.append({
                "name": session_name,
                "status": "active" if is_active else "inactive"
            })
            
        return available_sessions
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Директория сессий '{SESSIONS_DIR}' не найдена.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сканировании сессий: {e}")
        