import asyncio

# Класс ControlLogic теперь импортирует нужные ему словари из state.py, а не ищет их глобально
from state import control_modes, manual_overrides, opc_adapters, sessions


class ControlLogic:
    def __init__(self):
        self.manual_overrides = manual_overrides
        self.control_modes = control_modes
         
    def set_manual_override(self, session_id, component, param, value):
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

    def process_command(self, session_id, component_id, param, value):
        # self.control_modes.setdefault(session_id, {})
        # self.control_modes[session_id].setdefault(component, "MODEL")
        
        # Выполняем действия в модели
        model = sessions.get(session_id)
        
        if model:
            component_, id_ = component_id.rsplit("_", 1)
            id_ = int(id_)
            pump_name, param = param.split("_", 1)
            
            if component_ == "pump":
                if param == "start": model.control_pump(id_, True)
                elif param == "stop": model.control_pump(id_, False)
            elif component_ == "oil_system":
                if 'NA4_oil_motor_start': model.oil_pump_commands[id_]['start']
                elif 'NA4_oil_motor_stop': model.oil_pump_commands[id_]['stop']
            elif component_ == "valve_out":
                if param == 'CMD_Zadv_Open': model.valves[f'out_{id_}'].target_position == 100.0
                elif param == 'NA4_CMD_Zadv_Close': model.valves[f'out_{id_}'].target_position == 0.0

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