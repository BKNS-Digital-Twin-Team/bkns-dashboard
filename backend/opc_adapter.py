# opc_adapter.py (ФИНАЛЬНАЯ, ПРАВИЛЬНАЯ ВЕРСИЯ)
import asyncio
from asyncua import Client, ua, Node

class OPCAdapter:
    def __init__(self, server_url, control_logic, simulation_manager):
        self.client = Client(url=server_url)
        self.last_sent_values = {}  # {(component_id, param): last_value}
        self.control_logic = control_logic
        self.simulation_manager = simulation_manager
        self.is_running = False 
        # ИСПРАВЛЕНО: Теперь все component_id начинаются с 'pump_'
        # Это нужно, чтобы проверка прав доступа в process_command работала правильно
        self.OPC_NODE_MAPPING = {
            # === НАСОС NA4 ===
            "ns=1;i=101": {"mode": "control", "component_id": "pump_0", "param": "na_start"},
            "ns=1;i=102": {"mode": "control", "component_id": "pump_0", "param": "na_stop"},
            "ns=1;i=103": {"mode": "status",  "component_id": "pump_0", "param": "na_on"},
            "ns=1;i=104": {"mode": "status",  "component_id": "pump_0", "param": "na_off"},
            "ns=1;i=105": {"mode": "monitor", "component_id": "pump_0", "param": "motor_current"},
            "ns=1;i=106": {"mode": "monitor", "component_id": "pump_0", "param": "pressure_in"},
            "ns=1;i=107": {"mode": "monitor", "component_id": "pump_0", "param": "pressure_out"},
            "ns=1;i=108": {"mode": "monitor", "component_id": "pump_0", "param": "temp_bearing_1"},
            "ns=1;i=109": {"mode": "monitor", "component_id": "pump_0", "param": "cover_open"},
            "ns=1;i=110": {"mode": "status",  "component_id": "pump_0", "param": "oil_sys_running"},
            "ns=1;i=111": {"mode": "status",  "component_id": "pump_0", "param": "oil_sys_pressure_ok"},
            "ns=1;i=112": {"mode": "monitor", "component_id": "pump_0", "param": "oil_pressure"},
            "ns=1;i=113": {"mode": "monitor", "component_id": "pump_0", "param": "temp_bearing_2"},
            "ns=1;i=114": {"mode": "monitor", "component_id": "pump_0", "param": "temp_motor_1"},
            "ns=1;i=115": {"mode": "monitor", "component_id": "pump_0", "param": "temp_motor_2"},
            "ns=1;i=116": {"mode": "monitor", "component_id": "pump_0", "param": "temp_water"},
            "ns=1;i=117": {"mode": "monitor", "component_id": "pump_0", "param": "flow_rate"},
            "ns=1;i=118": {"mode": "status",  "component_id": "valve_out_0", "param": "valve_open"},
            "ns=1;i=119": {"mode": "status",  "component_id": "valve_out_0", "param": "valve_closed"},
            "ns=1;i=120": {"mode": "control", "component_id": "valve_out_0", "param": "valve_open_cmd"},
            "ns=1;i=121": {"mode": "control", "component_id": "valve_out_0", "param": "valve_close_cmd"},
            "ns=1;i=122": {"mode": "control", "component_id": "oil_system_0", "param": "oil_pump_start"},
            "ns=1;i=123": {"mode": "control", "component_id": "oil_system_0", "param": "oil_pump_stop"},

            # === НАСОС NA2 ===
            "ns=1;i=201": {"mode": "control", "component_id": "pump_1", "param": "na_start"},
            "ns=1;i=202": {"mode": "control", "component_id": "pump_1", "param": "na_stop"},
            "ns=1;i=203": {"mode": "status",  "component_id": "pump_1", "param": "na_on"},
            "ns=1;i=204": {"mode": "status",  "component_id": "pump_1", "param": "na_off"},
            "ns=1;i=205": {"mode": "monitor", "component_id": "pump_1", "param": "motor_current"},
            "ns=1;i=206": {"mode": "monitor", "component_id": "pump_1", "param": "pressure_in"},
            "ns=1;i=207": {"mode": "monitor", "component_id": "pump_1", "param": "pressure_out"},
            "ns=1;i=208": {"mode": "monitor", "component_id": "pump_1", "param": "temp_bearing_1"},
            "ns=1;i=209": {"mode": "monitor", "component_id": "pump_1", "param": "cover_open"},
            "ns=1;i=210": {"mode": "status",  "component_id": "pump_1", "param": "oil_sys_running"},
            "ns=1;i=211": {"mode": "status",  "component_id": "pump_1", "param": "oil_sys_pressure_ok"},
            "ns=1;i=212": {"mode": "monitor", "component_id": "pump_1", "param": "oil_pressure"},
            "ns=1;i=213": {"mode": "monitor", "component_id": "pump_1", "param": "temp_bearing_2"},
            "ns=1;i=214": {"mode": "monitor", "component_id": "pump_1", "param": "temp_motor_1"},
            "ns=1;i=215": {"mode": "monitor", "component_id": "pump_1", "param": "temp_motor_2"},
            "ns=1;i=216": {"mode": "monitor", "component_id": "pump_1", "param": "temp_water"},
            "ns=1;i=217": {"mode": "monitor", "component_id": "pump_1", "param": "flow_rate"},
            "ns=1;i=218": {"mode": "status",  "component_id": "valve_out_1", "param": "valve_open"},
            "ns=1;i=219": {"mode": "status",  "component_id": "valve_out_1", "param": "valve_closed"},
            "ns=1;i=220": {"mode": "control", "component_id": "valve_out_1", "param": "valve_open_cmd"},
            "ns=1;i=221": {"mode": "control", "component_id": "valve_out_1", "param": "valve_close_cmd"},
            "ns=1;i=222": {"mode": "control", "component_id": "oil_system_1", "param": "oil_pump_start"},
            "ns=1;i=223": {"mode": "control", "component_id": "oil_system_1", "param": "oil_pump_stop"},
        }


    async def connect(self):
        print("[OPC Adapter] Подключение...")
        await self.client.connect()
        self.is_running = True
        print("[OPC Adapter] Успешно подключено!")

    async def disconnect(self):
        if self.is_running:
            await self.client.disconnect()
            self.is_running = False
            print("[OPC Adapter] Отключено.")

    async def setup_subscriptions(self):
        class DataChangeHandler:
            def __init__(self, adapter_instance):
                self.adapter = adapter_instance
                
            def datachange_notification(self, node: Node, val, data: ua.DataChangeNotification):
                node_id = node.nodeid.to_string()
                print(f"[OPC] Получено: Node={node_id}, Value={val}")
                if not val: return

                command_info = self.adapter.OPC_NODE_MAPPING.get(node_id)
                if command_info:
                    self.adapter.control_logic.process_command(
                        mode=command_info["mode"],
                        source="OPC",
                        component=command_info["component_id"], 
                        param=command_info["param"],
                        value=val
                    )

        handler = DataChangeHandler(self)
        subscription = await self.client.create_subscription(500, handler)
        
        nodes_to_subscribe = [self.client.get_node(node_id) for node_id in self.OPC_NODE_MAPPING.keys()]
        
        if nodes_to_subscribe:
            await subscription.subscribe_data_change(nodes_to_subscribe)
            print(f"[OPC Adapter] Успешно подписан на {len(nodes_to_subscribe)} тегов.")
            
    async def sync_with_opc_state(self):
        if not self.is_running:
            print("[SYNC] Ошибка: адаптер не подключен.")
            return

        print("\n--- [SYNC] Начало синхронизации с OPC... ---\n")
        
        # Сначала выполняем "включающие" и "открывающие" команды
        priority_params = ["start", "open"]
        
        commands_to_execute = []
        for node_id, command_info in self.OPC_NODE_MAPPING.items():
            try:
                node = self.client.get_node(node_id)
                current_value = await node.get_value()
                # Мы обрабатываем команду, только если ее тег равен True
                if current_value:
                    commands_to_execute.append(command_info)
            except Exception as e:
                print(f"[SYNC ERROR] Не удалось прочитать {node_id}: {e}")

        # Сортируем команды: сначала start/open, потом все остальное (stop/close)
        # `False` идет раньше `True` при сортировке, поэтому "stop" in param будет False (0), а "start" - True (1)
        # Чтобы сделать наоборот, инвертируем результат.
        sorted_commands = sorted(
            commands_to_execute, 
            key=lambda cmd: not any(p in cmd["param"] for p in priority_params)
        )

        for command_info in sorted_commands:
            print(f"[SYNC] Выполнение команды: {command_info['component_id']} -> {command_info['param']}")
            self.control_logic.process_command(
                source="OPC",
                component=command_info["component_id"],
                param=command_info["param"],
                value=True
            )
        
        print("\n--- [SYNC] Синхронизация завершена. ---\n")
    
    async def send_to_opc(self, component_id, param, value):
        if not self.is_running:
            print("[OPC WRITE] Адаптер не подключен.")
            return

        key = (component_id, param)
        if self.last_sent_values.get(key) == value:
            print(f"[OPC WRITE] Значение {component_id}.{param} уже = {value}, пропуск.")
            return

        # Найдём NodeId по компоненту и параметру
        node_id = None
        for nid, info in self.OPC_NODE_MAPPING.items():
            if info["component_id"] == component_id and info["param"] == param:
                node_id = nid
                break

        if node_id is None:
            print(f"[OPC WRITE] Не найден NodeId для {component_id}.{param}")
            return

        try:
            node = self.client.get_node(node_id)
            await node.write_value(value)
            self.last_sent_values[key] = value
            print(f"[OPC WRITE] {component_id}.{param} → {value}")
        except Exception as e:
            print(f"[OPC WRITE ERROR] Ошибка записи {component_id}.{param}: {e}")

    async def run(self):
        while True:
            try:
                await self.connect()
                await self.setup_subscriptions()
                while self.is_running:
                    await asyncio.sleep(3600)
            except Exception as e:
                print(f"[OPC Adapter CRITICAL] Ошибка: {e}. Переподключение через 10с.")
                if self.is_running: await self.disconnect()
                await asyncio.sleep(10)