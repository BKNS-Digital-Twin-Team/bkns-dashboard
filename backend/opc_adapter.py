# opc_adapter.py (ФИНАЛЬНАЯ, ПРАВИЛЬНАЯ ВЕРСИЯ)
import asyncio
from asyncua import Client, ua, Node

class OPCAdapter:
    def __init__(self, server_url, control_logic, simulation_manager):
        self.client = Client(url=server_url)
        self.control_logic = control_logic
        self.simulation_manager = simulation_manager
        self.is_running = False 
        # ИСПРАВЛЕНО: Теперь все component_id начинаются с 'pump_'
        # Это нужно, чтобы проверка прав доступа в process_command работала правильно
        self.OPC_NODE_MAPPING = {
            # --- Насос NA4 (ID 0 в модели) ---
            "ns=2;i=28": {"mode": "control", "component_id": "pump_0", "param": "na_start"},
            "ns=2;i=29": {"mode": "control", "component_id": "pump_0", "param": "na_stop"},
            "ns=2;i=45": {"mode": "control", "component_id": "valve_out_0", "param": "valve_open"}, 
            "ns=2;i=46": {"mode": "control", "component_id": "valve_out_0", "param": "valve_close"},
            "ns=2;i=35": {"mode": "control","component_id": "oil_system_0", "param": "oil_pump_start"},
            # "ns=2;i=??": {"component_id": "pump_0", "param": "oil_pump_stop"}, 

            # --- Насос NA2 (ID 1 в модели) ---
            "ns=2;i=2":  {"mode": "control", "component_id": "pump_1", "param": "na_start"},
            "ns=2;i=3":  {"mode": "control", "component_id": "pump_1", "param": "na_stop"},
            "ns=2;i=21": {"mode": "control", "component_id": "valve_out_1", "param": "valve_open"},
            "ns=2;i=22": {"mode": "control", "component_id": "valve_out_1", "param": "valve_close"},
            "ns=2;i=23": {"mode": "control", "component_id": "oil_system_1", "param": "oil_pump_start"},
            # "ns=2;i=24": {"component_id": "pump_1", "param": "oil_pump_stop"},
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