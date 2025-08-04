# =============================================================================
# 1. ИМПОРТЫ И КОНФИГУРАЦИЯ
# =============================================================================
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from Math.BKNS import BKNS
from opc_adapter import OPCAdapter

# Глобальные переменные и конфигурация
SERVER_URL = os.getenv("OPC_SERVER_URL", "opc.tcp://0.0.0.0:4840")
if SERVER_URL == "opc.tcp://0.0.0.0:4840":
    print("OPC_SERVER_URL from Docker compose is None, using default")

simulation_is_running = asyncio.Event()
simulation_manager = {"main_bkns": BKNS()}
previous_model_state = {}


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

async def update_opc_from_model_state(force_send_all=False):
    """
    Универсальная функция, которая синхронизирует состояние модели с OPC-сервером.
    """
    global previous_model_state
    model = simulation_manager["main_bkns"]
    if force_send_all:
        print("[SYNC] Запуск принудительной полной синхронизации...")
    
    # === НОВЫЙ НАДЕЖНЫЙ СПОСОБ ===
    # 1. Получаем ОДИН раз данные, как для фронтенда. Это наш "источник правды".
    raw_status = model.get_status()
    # 2. Конвертируем их в плоский вид для OPC.
    current_state = flatten_status_for_opc(raw_status)
    # ================================
    
    for component, params in current_state.items():
        for param, value in params.items():
            key = (component, param)
            if force_send_all or previous_model_state.get(key) != value:
                control_logic.process_command("MODEL", component, param, value)
                previous_model_state[key] = value
    
    if force_send_all:
        print("[SYNC] Полная синхронизация завершена.")

# =============================================================================
# 2. ОСНОВНАЯ БИЗНЕС-ЛОГИКА
# =============================================================================
class ControlLogic:
    def __init__(self):
        self.state_cache = {}
        self.control_modes = {
            "pump_0": "MODEL",
            "pump_1": "MODEL",
            "valve_in_0": "MODEL",
            "valve_out_0": "MODEL",
            "valve_in_1": "MODEL",
            "valve_out_1": "MODEL",
            "oil_system_0": "MODEL",
            "oil_system_1": "MODEL",
        }

    def get_control_modes(self):
        return self.control_modes

    def set_control_source(self, component, source):
        if source not in ["MODEL", "MANUAL"]:
            return {"status": "ERROR", "message": "Неверный режим"}
        self.control_modes[component] = source
        return {"status": "OK"}

    def process_command(self, source, component, param, value):
        print(f"[CONTROL] source={source}, component={component}, param={param}, value={value}")

        if self.control_modes.get(component) != source:
            print(f"[CONTROL] Игнор: режим компонента - {self.control_modes.get(component)}")
            return {"status": "IGNORED"}

        # Просто передаем команду дальше. Адаптер сам разберется, отправлять или нет.
        if source == "MODEL" and opc_adapter and opc_adapter.is_running:
            asyncio.create_task(opc_adapter.send_to_opc(component, param, value))

        model = simulation_manager["main_bkns"]
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
opc_adapter = OPCAdapter(SERVER_URL, control_logic, simulation_manager, update_opc_from_model_state)


# =============================================================================
# 4. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И ФОНОВЫЕ ЗАДАЧИ
# =============================================================================
async def update_loop():
    """Основной цикл обновления модели и отправки изменений в OPC."""
    print(">>> update_loop стартует <<<", flush=True)
    while True:
        await simulation_is_running.wait()
        simulation_manager["main_bkns"].update_system()
        await update_opc_from_model_state(force_send_all=False)
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
    return simulation_manager["main_bkns"].get_status()

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
    return {"status": "running" if simulation_is_running.is_set() else "paused"}

# main.py -> Секция 5

@api_router.post("/simulation/pause")
def pause_simulation():
    if not simulation_is_running.is_set():
        return {"status": "already_paused"}
    simulation_is_running.clear()
    print("[SYSTEM] Симуляция поставлена на паузу.")
    return {"status": "paused"}

@api_router.post("/simulation/resume")
def resume_simulation():
    if simulation_is_running.is_set():
        return {"status": "already_running"}
    simulation_is_running.set()
    print("[SYSTEM] Симуляция возобновлена.")
    return {"status": "resumed"}

class ControlSourceCommand(BaseModel):
    source: str
    component: str

@api_router.post("/simulation/control/set_source")
def set_control_source(cmd: ControlSourceCommand):
    return control_logic.set_control_source(cmd.component, cmd.source)


# =============================================================================
# 6. СБОРКА И ЗАПУСК ПРИЛОЖЕНИЯ FASTAPI
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управляет фоновыми задачами во время жизни приложения."""
    simulation_is_running.set()
    opc_task = asyncio.create_task(opc_adapter.run())
    model_task = asyncio.create_task(update_loop())
    yield
    print("Завершение работы, остановка фоновых задач...")
    await opc_adapter.disconnect()
    model_task.cancel()
    opc_task.cancel()
    await asyncio.gather(model_task, opc_task, return_exceptions=True)

app = FastAPI(lifespan=lifespan)

### Подключем к фронтенду 
app.include_router(api_router)

STATIC_FILES_DIR = os.getenv("STATIC_FILES_DIR")

if STATIC_FILES_DIR is None:
    STATIC_FILES_DIR = "./backend/build/"
    
app.mount("/", StaticFiles(directory=STATIC_FILES_DIR, html=True), name="static")
