
class Test_Object:
    def __init__(self):
        self.current_state = {
            "pump_0": {
                "na_on": False,
                "na_off": True,
                "motor_current": 0.0,
                "pressure_in": 1.9
            },
            "oil_system_0": {
                "oil_sys_running": False,
                "oil_sys_pressure_ok": False
            }
        }

    def update_system(self):
        for component, params in current_state.items():
            for param, value in params.items():
                params[param] = value + 0.001
             
        
    def get_status(self):
        return self.current_state
    
MODEL = Test_Object()