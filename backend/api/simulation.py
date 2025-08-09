# api/simulation.py

# Стандартные импорты FastAPI и Python
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import asyncio
import uuid
import importlib.util

# --- НОВЫЕ ИМПОРТЫ ИЗ НАШИХ МОДУЛЕЙ ---

# Импортируем словари с состоянием
from state import (
    sessions, session_states, previous_states, session_last_full_sync,
    opc_adapters, SERVER_URL
)

# Импортируем экземпляр бизнес-логики
from logic import control_logic

# Импортируем утилиты для OPC
from opc_utils import update_opc_from_model_state

# Импортируем класс OPCAdapter для создания новых экземпляров
from opc_adapter import OPCAdapter

# Импортируем фоновую задачу для обновления модели
# (предполагаем, что она в main.py или будет в session_manager.py)
from main import update_loop

api_router = APIRouter(prefix="/api")

@api_router.get("/simulation/{session_id}/state")
def get_simulation_state(session_id: str):
    return {"status": "running" if session_states[session_id] == "running" else "paused"}

@api_router.get("/simulation/{session_id}/control_modes")
def get_modes(session_id: str):
    return sessions[session_id].get_control_modes()

@api_router.get("/simulation/{session_id}/status")
def get_state(session_id: str):
    return sessions[session_id].get_status()

@api_router.post("/simulation/{session_id}/pause")
def pause_simulation():
    if not session_states[session_id] == "running":
        return {"status": "already_paused"}
    simulation_state["running"] = False
    print("[SYSTEM] Симуляция поставлена на паузу.")
    return {"status": "paused"}

@api_router.post("/simulation/{session_id}/resume")
def resume_simulation():
    if simulation_state["running"]:
        return {"status": "already_running"}
    simulation_state["running"] = True
    print("[SYSTEM] Симуляция возобновлена.")
    return {"status": "resumed"}


class ManualParamCommand(BaseModel):
    source: str
    component: str
    param: str
    value: float

@api_router.post("/simulation/{session_id}/control/manual")
def manual_cmd(cmd: ManualParamCommand):
    return control_logic.process_command(cmd.source, cmd.component, cmd.param, cmd.value)

@api_router.post("/simulation/{session_id}/sync")
async def sync(background_tasks: BackgroundTasks):
    if not opc_adapter or not opc_adapter.is_running:
        return {"status": "ERROR", "message": "OPC не подключен"}
    background_tasks.add_task(update_opc_from_model_state, force_send_all=True)
    return {"status": "ACCEPTED"}



class ControlSourceCommand(BaseModel):
    source: str
    component: str

@api_router.post("/simulation/control/set_source")
def set_control_source(cmd: ControlSourceCommand):
    return control_logic.set_control_source(cmd.component, cmd.source)

@api_router.post("/simulation/control/overrides")
def set_manual_overrides(payload: dict):
    print("[POST /control/overrides] payload:", payload)
    component = payload.get("component")
    overrides = payload.get("overrides", {})

    if not component or not isinstance(overrides, dict):
        return {"status": "ERROR", "message": "Неверный формат запроса"}

    control_logic.set_manual_overrides(component, overrides)
    print("[POST /control/overrides] сохранено:", control_logic.manual_overrides)
    return {"status": "OK"}

        
@api_router.get("/simulation/debug/overrides")
def debug_overrides():
    return {
        "overrides": {
            f"{k[0]}.{k[1]}": v for k, v in control_logic.manual_overrides.items()
        }
    }


class LoadSessionRequest(BaseModel):
    session_name: str
    config_file: str  # имя файла из sessions/

@api_router.post("/simulation/session/load")
async def load_session(data: LoadSessionRequest):
    session_id = f"{data.session_name}_{uuid.uuid4().hex[:6]}"
    
    opc_adapters[session_id] = OPCAdapter(SERVER_URL, control_logic, sessions, update_opc_from_model_state)
    asyncio.create_task(opc_adapters[session_id].run())
    
    session_id = f"{data.session_name}_{uuid.uuid4().hex[:6]}"

    try:
        full_path = f"./sessions/{session_id}/{data.config_file}"

        spec = importlib.util.spec_from_file_location("session_config", full_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)

        # Теперь можно получить данные
        model = config_module.MODEL  # или как у тебя там объект называется
        sessions[session_id] = model
        
        asyncio.create_task(update_loop(session_id))

        return {"session_id": session_id, "status": "created"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        