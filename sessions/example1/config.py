import time

class BKNS:
    def __init__(self):
        self.last_update_time = time.time()
        self.current_state = {
            "pump_0": {
                "na_on": False,
                "pressure_out": 0.0,
                "flow_rate": 0.0
            },
            "pump_1": {
                "na_on": False,
                "pressure_out": 0.0,
                "flow_rate": 0.0
            },
            "oil_system_0": {
                "oil_sys_running": False,
                "oil_pressure": 0.0
            },
            "oil_system_1": {
                "oil_sys_running": False,
                "oil_pressure": 0.0
            },
            "valve_out_0": {
                "valve_open": False
            },
            "valve_out_1": {
                "valve_open": False
            }
        }

    def update_system(self):
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        for component, params in self.current_state.items():
            for param, value in params.items():
                if isinstance(value, (int, float)):
                    params[param] = value + 0.1 * dt

    def get_status(self):
        print(f"[{time.strftime('%H:%M:%S')}] get_status called for session 'example': {self.current_state}")
        return self.current_state

MODEL = BKNS()