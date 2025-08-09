# =============================================================================
# 1. ИМПОРТЫ И КОНФИГУРАЦИЯ
# =============================================================================
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from fastapi.middleware.cors import CORSMiddleware
import uuid
import importlib.util
import time


from Math.BKNS import BKNS
from opc_adapter import OPCAdapter

# Глобальные переменные и конфигурация
SERVER_URL = os.getenv("OPC_SERVER_URL", "opc.tcp://localhost:4840/freeopcua/server/")
if SERVER_URL == "opc.tcp://localhost:4840/freeopcua/server/":
    print("OPC_SERVER_URL from Docker compose is None, using default")
FULL_SYNC_INTERVAL = 30

sessions = {}
session_states = {}  # session_id -> {"running": True/False}
previous_states = {}  # session_id -> dict previous values
session_last_full_sync = {}

manual_overrides = {}  # session_id -> { (component, param): value }
control_modes = {} 

opc_adapters = {}  # session_id -> OPCAdapter





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
    
    for (component, param), value in control_logic.manual_overrides.items():
        control_logic.process_command("MODEL", component, param, None)
    
    for component, params in current_state.items():
        for param, value in params.items():
            key = (component, param)
            if force_send_all or previous_states[session_id].get(key) != value:
                opc_adapters[session_id].process_command("MODEL", component, param, value)
                previous_states[session_id][key] = value
                
    if force_send_all:
        print("[SYNC] Полная синхронизация завершена.")
                

# =============================================================================
# 2. ОСНОВНАЯ БИЗНЕС-ЛОГИКА
# =============================================================================
class ControlLogic:
    def __init__(self):
        # self.state_cache = {}
        # self.control_modes = {
        #     "pump_0": "MODEL",
        #     "pump_1": "MODEL",
        #     "valve_in_0": "MODEL",
        #     "valve_out_0": "MODEL",
        #     "valve_in_1": "MODEL",
        #     "valve_out_1": "MODEL",
        #     "oil_system_0": "MODEL",
        #     "oil_system_1": "MODEL",
        # }
        # self.manual_overrides = {}
        self.manual_overrides = {}   # session_id -> {(component, param): value}
        self.control_modes = {}      # session_id -> {component: mode}
        


        
    def set_manual_overrides(self, session_id, component, param, value):
        self.manual_overrides.setdefault(session_id, {})
        self.manual_overrides[session_id][(component, param)] = float(value)
    
    def clear_manual_override(self, session_id, component, param):
        if session_id in self.manual_overrides:
            self.manual_overrides[session_id].pop((component, param), None)    

    def debug_print_overrides(self):
        for sid, overrides in self.manual_overrides.items():
            print(f"=== Overrides для сессии {sid} ===")
            for (component, param), val in overrides.items():
                print(f"🔧 {component}.{param} = {val}")
                
    def set_control_source(self, session_id, component, source):
        if source not in ["MODEL", "MANUAL"]:
            return {"status": "ERROR", "message": "Неверный режим"}
        self.control_modes.setdefault(session_id, {})
        self.control_modes[session_id][component] = source
        return {"status": "OK"}
        
    # def get_control_modes(self):
    #     return self.control_modes

    # def set_control_source(self, component, source):
    #     if source not in ["MODEL", "MANUAL"]:
    #         return {"status": "ERROR", "message": "Неверный режим"}
    #     self.control_modes[component] = source
    #     return {"status": "OK"}
    

    def process_command(self, session_id, source, component, param, value):
        self.control_modes.setdefault(session_id, {})
        self.control_modes[session_id].setdefault(component, "MODEL")
        
        adapter = opc_adapters.get(session_id)
        if adapter is None or not adapter.is_running:
            print(f"[SKIP OPC] Нет активного OPC для сессии {session_id}")
            return {"status": "NO_OPC"}
        
        # Если есть оверрайд — подменяем значение
        override_value = self.manual_overrides.get(session_id, {}).get((component, param))
        if override_value is not None:
            print(f"[OVERRIDE->OPC] заменяем {component}.{param} на {override_value}")
            value = override_value

        # # Проверяем режим управления
        # if self.control_modes.get(session_id, {}).get(component) != source:
        #     print(f"[CONTROL] Игнор: режим {self.control_modes.get(session_id, {}).get(component)}")
        #     return {"status": "IGNORED"}
        
        # Отправляем в OPC
        asyncio.create_task(adapter.send_to_opc(component, param, value))
        
        # Выполняем действия в модели
        model = sessions.get(session_id)
        if model:
            type_, id_ = component.rsplit("_", 1)
            id_ = int(id_)
            if type_ == "pump":
                if param == "na_start": model.control_pump(id_, True)
                elif param == "na_stop": model.control_pump(id_, False)
            elif type_ == "valve_out":
                model.control_valve(f"in_{id_}", param == "valve_open")
                model.control_valve(f"out_{id_}", param == "valve_open")
            elif type_ == "oil_system":
                model.control_oil_pump(id_, param == "oil_pump_start")

        return {"status": "OK"}

# =============================================================================
# 3. ИНИЦИАЛИЗАЦИЯ ГЛОБАЛЬНЫХ ОБЪЕКТОВ
# =============================================================================
control_logic = ControlLogic()
opc_adapter = OPCAdapter(SERVER_URL, control_logic, sessions, update_opc_from_model_state)


# =============================================================================
# 4. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И ФОНОВЫЕ ЗАДАЧИ
# =============================================================================
async def update_loop(session_id):
    print(f">>> update_loop стартует для {session_id} <<<", flush=True)
    while True:
        if session_states[session_id]["running"]:
            sessions[session_id].update_system()
            await update_opc_from_model_state(session_id, force_send_all=False)
        await asyncio.sleep(1)


# =============================================================================
# 5. ОПРЕДЕЛЕНИЕ API ЭНДПОИНТОВ
# =============================================================================
api_router = APIRouter(prefix="/api")

class ManualParamCommand(BaseModel):
    source: str
    component: str
    param: str
    value: float

@api_router.get("/simulation/status")
def get_state():
    return sessions["main_bkns"].get_status()

@api_router.get("/simulation/control_modes")
def get_modes():
    return control_logic.get_control_modes()

@api_router.post("/simulation/control/manual")
def manual_cmd(cmd: ManualParamCommand):
    return control_logic.process_command(cmd.source, cmd.component, cmd.param, cmd.value)

@api_router.post("/simulation/sync")
async def sync(background_tasks: BackgroundTasks):
    if not opc_adapter or not opc_adapter.is_running:
        return {"status": "ERROR", "message": "OPC не подключен"}
    background_tasks.add_task(update_opc_from_model_state, force_send_all=True)
    return {"status": "ACCEPTED"}

@api_router.get("/simulation/mode")
def get_simulation_mode():
    """Возвращает текущий режим симуляции (running/paused)."""
    return {"status": "running" if simulation_state["running"] else "paused"}

# main.py -> Секция 5

@api_router.post("/simulation/pause")
def pause_simulation():
    if not simulation_state["running"]:
        return {"status": "already_paused"}
    simulation_state["running"] = False
    print("[SYSTEM] Симуляция поставлена на паузу.")
    return {"status": "paused"}

@api_router.post("/simulation/resume")
def resume_simulation():
    if simulation_state["running"]:
        return {"status": "already_running"}
    simulation_state["running"] = True
    print("[SYSTEM] Симуляция возобновлена.")
    return {"status": "resumed"}

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
        


# =============================================================================
# 6. СБОРКА И ЗАПУСК ПРИЛОЖЕНИЯ FASTAPI
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управляет фоновыми задачами во время жизни приложения."""
    opc_task = asyncio.create_task(opc_adapter.run())
    model_task = asyncio.create_task(update_loop())
    yield
    print("Завершение работы, остановка фоновых задач...")
    await opc_adapter.disconnect()
    model_task.cancel()
    opc_task.cancel()
    await asyncio.gather(model_task, opc_task, return_exceptions=True)

app = FastAPI(lifespan=lifespan)

# Разрешаем CORS в dev-режиме
if os.getenv("DEV_MODE") == "true":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Только в проде монтируем статику
    STATIC_FILES_DIR = os.getenv("STATIC_FILES_DIR")
    if STATIC_FILES_DIR is None:
        STATIC_FILES_DIR = "./backend/build/"
    app.mount("/", StaticFiles(directory=STATIC_FILES_DIR, html=True), name="static")

app.include_router(api_router)
