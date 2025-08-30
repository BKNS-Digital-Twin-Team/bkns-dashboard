import asyncio

# Класс ControlLogic теперь импортирует нужные ему словари из state.py, а не ищет их глобально
from state import control_modes, manual_overrides, opc_adapters, sessions


class ControlLogic:
    def __init__(self):
        self.manual_overrides = manual_overrides
        self.control_modes = control_modes
         
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

    def process_command(self, session_id, component, param, value):
        # self.control_modes.setdefault(session_id, {})
        # self.control_modes[session_id].setdefault(component, "MODEL")
        
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
    
    def send_command_to_opc(self, session_id, component, param, value):
        adapter = opc_adapters.get(session_id)
        if adapter is None or not adapter.is_running:
            print(f"[SKIP OPC] Нет активного OPC для сессии {session_id}")
            return {"status": "NO_OPC"}
        
        # Если есть оверрайд — подменяем значение
        override_value = self.manual_overrides.get(session_id, {}).get((component, param))
        if override_value is not None:
            print(f"[OVERRIDE->OPC] заменяем {component}.{param} на {override_value}")
            value = override_value
            
        # Отправляем в OPC
        asyncio.create_task(adapter.send_to_opc(component, param, value))

control_logic = ControlLogic()