current_state = {}

class Test_Object:
    def __init__():
        current_state = {
            "component1": {
                "parametr1": 2,
                "parametr2": 2,
                "parametr3": 2
            },
            "component2": {
                "parametr1": 2,
                "parametr2": 2,
                "parametr3": 2
            },
            # и так далее
        }

    def update_system():
        for component, params in current_state.items():
            for param, value in params.items():
                value = value + 0.001
             
        
    def get_status():
        return current_state
    
MODEL = Test_Object()