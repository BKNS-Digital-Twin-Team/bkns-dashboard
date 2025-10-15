# =============================================================================
# 1. ИМПОРТЫ
# =============================================================================
import asyncio
from asyncua import Client, ua, Node


# =============================================================================
# 2. КЛАСС АДАПТЕРА OPC
# =============================================================================
class OPCAdapter:
    """
    Класс для управления подключением, подписками и обменом данными
    с OPC UA сервером.
    """

    # -------------------------------------------------------------------------
    # 2.1. Конструктор и конфигурация
    # -------------------------------------------------------------------------
    def __init__(self, server_url, control_logic, sessions, sync_function, session_id: str):
        self.client = Client(url=server_url)
        self.control_logic = control_logic
        self.simulation_manager = sessions
        self.is_running = False
        self.last_sent_values = {}
        self.sync_function = sync_function
        
        self.sessions = sessions
        self.session_id = session_id 

        # Карта соответствия параметров модели тегам OPC UA сервера.
        # ЗАМЕНИТЕ "REPLACE_ME" НА РЕАЛЬНЫЕ NodeId ВАШЕГО СЕРВЕРА.
        # === ЕДИНЫЙ И ПОЛНЫЙ СПИСОК ПЕРЕМЕННЫХ (из Сигналы_v3.txt) ===
        self.OPC_NODE_MAPPING = {
            # === НАСОС 0 (NA4) ===
            "ns=1;i=101": {"mode": "control", "component_id": "pump_0", "param": "na4_start"},
            "ns=1;i=102": {"mode": "control", "component_id": "pump_0", "param": "na4_stop"},
            "ns=1;i=103": {"mode": "status",  "component_id": "pump_0", "param": "na4_on"},
            "ns=1;i=104": {"mode": "status",  "component_id": "pump_0", "param": "na4_off"},
            "ns=1;i=105": {"mode": "monitor", "component_id": "pump_0", "param": "na4_motor_i"},
            "ns=1;i=106": {"mode": "monitor", "component_id": "pump_0", "param": "na4_pressure_in"},
            "ns=1;i=107": {"mode": "monitor", "component_id": "pump_0", "param": "na4_pressure_out"},
            "ns=1;i=108": {"mode": "monitor", "component_id": "pump_0", "param": "NA4_AI_T_1_n"},
            "ns=1;i=109": {"mode": "monitor", "component_id": "pump_0", "param": "NA4_DI_kojuh"},
            "ns=1;i=113": {"mode": "monitor", "component_id": "pump_0", "param": "NA4_AI_T_2_n"},
            "ns=1;i=114": {"mode": "monitor", "component_id": "pump_0", "param": "NA4_AI_T_3_n"},
            "ns=1;i=115": {"mode": "monitor", "component_id": "pump_0", "param": "NA4_AI_T_4_n"},
            "ns=1;i=116": {"mode": "monitor", "component_id": "pump_0", "param": "NA4_AI_T_5_n"},
            "ns=1;i=117": {"mode": "monitor", "component_id": "pump_0", "param": "NA4_AI_Qmom_n"},

            # === ЗАДВИЖКА 0 (Выходная) ===
            "ns=1;i=118": {"mode": "status",  "component_id": "valve_out_0", "param": "NA4_DI_Zadv_Open"},
            "ns=1;i=119": {"mode": "status",  "component_id": "valve_out_0", "param": "NA4_DI_Zadv_Close"},
            "ns=1;i=120": {"mode": "control", "component_id": "valve_out_0", "param": "NA4_CMD_Zadv_Open"},
            "ns=1;i=121": {"mode": "control", "component_id": "valve_out_0", "param": "NA4_CMD_Zadv_Close"},

            # === МАСЛОСИСТЕМА 0 ===
            "ns=1;i=110": {"mode": "status",  "component_id": "oil_system_0", "param": "NA4_DI_FL_MS"},
            "ns=1;i=111": {"mode": "status",  "component_id": "oil_system_0", "param": "NA4_DI_FL_MS_P"},
            "ns=1;i=112": {"mode": "monitor", "component_id": "oil_system_0", "param": "NA4_AI_P_Oil_Nas_n"},
            "ns=1;i=122": {"mode": "control", "component_id": "oil_system_0", "param": "NA4_oil_motor_start"},
            "ns=1;i=123": {"mode": "control", "component_id": "oil_system_0", "param": "NA4_oil_motor_stop"},
            # Дополнительные параметры, если они есть в модели
            "ns=1;i=304": {"mode": "monitor", "component_id": "oil_system_0", "param": "temperature"},

            # === НАСОС 1 (NA2) ===
            "ns=1;i=201": {"mode": "control", "component_id": "pump_1", "param": "na2_start"},
            "ns=1;i=202": {"mode": "control", "component_id": "pump_1", "param": "na2_stop"},
            "ns=1;i=203": {"mode": "status",  "component_id": "pump_1", "param": "na2_on"},
            "ns=1;i=204": {"mode": "status",  "component_id": "pump_1", "param": "na2_off"},
            "ns=1;i=205": {"mode": "monitor", "component_id": "pump_1", "param": "na2_motor_i"},
            "ns=1;i=206": {"mode": "monitor", "component_id": "pump_1", "param": "na2_pressure_in"},
            "ns=1;i=207": {"mode": "monitor", "component_id": "pump_1", "param": "na2_pressure_out"},
            "ns=1;i=208": {"mode": "monitor", "component_id": "pump_1", "param": "NA2_AI_T_1_n"},
            "ns=1;i=209": {"mode": "monitor", "component_id": "pump_1", "param": "NA2_DI_kojuh"},
            "ns=1;i=213": {"mode": "monitor", "component_id": "pump_1", "param": "NA2_AI_T_2_n"},
            "ns=1;i=214": {"mode": "monitor", "component_id": "pump_1", "param": "NA2_AI_T_3_n"},
            "ns=1;i=215": {"mode": "monitor", "component_id": "pump_1", "param": "NA2_AI_T_4_n"},
            "ns=1;i=216": {"mode": "monitor", "component_id": "pump_1", "param": "NA2_AI_T_5_n"},
            "ns=1;i=217": {"mode": "monitor", "component_id": "pump_1", "param": "NA2_AI_Qmom_n"},

            # === ЗАДВИЖКА 1 (Выходная) ===
            "ns=1;i=218": {"mode": "status",  "component_id": "valve_out_1", "param": "NA2_DI_Zadv_Open"},
            "ns=1;i=219": {"mode": "status",  "component_id": "valve_out_1", "param": "NA2_DI_Zadv_Close"},
            "ns=1;i=220": {"mode": "control", "component_id": "valve_out_1", "param": "NA2_CMD_Zadv_Open"},
            "ns=1;i=221": {"mode": "control", "component_id": "valve_out_1", "param": "NA2_CMD_Zadv_Close"},

            # === МАСЛОСИСТЕМА 1 ===
            "ns=1;i=210": {"mode": "status",  "component_id": "oil_system_1", "param": "NA2_DI_FL_MS"},
            "ns=1;i=211": {"mode": "status",  "component_id": "oil_system_1", "param": "NA2_DI_FL_MS_P"},
            "ns=1;i=212": {"mode": "monitor", "component_id": "oil_system_1", "param": "NA2_AI_P_Oil_Nas_n"},
            "ns=1;i=222": {"mode": "control", "component_id": "oil_system_1", "param": "NA2_oil_motor_start"},
            "ns=1;i=223": {"mode": "control", "component_id": "oil_system_1", "param": "NA2_oil_motor_stop"},
            # Дополнительные параметры, если они есть в модели
            "ns=1;i=404": {"mode": "monitor", "component_id": "oil_system_1", "param": "temperature"},
        }

    # -------------------------------------------------------------------------
    # 2.2. Основной цикл работы и управление подключением
    # -------------------------------------------------------------------------
    async def run(self):
        while True:
            try:
                await self.connect()
                await self.setup_subscriptions()
                
                print("[OPC Adapter] Соединение установлено. Запуск полной синхронизации...")
                
                await self.sync_function(self.session_id, force_send_all=True)
                
                while self.is_running:
                    await asyncio.sleep(3600)
            except Exception as e:
                print(f"[OPC Adapter CRITICAL] Ошибка: {e}. Переподключение через 10с.")
                
                if self.is_running: await self.disconnect()
                await asyncio.sleep(10)

    async def connect(self):
        """Устанавливает соединение с OPC UA сервером."""
        print("[OPC Adapter] Подключение...")
        await self.client.connect()
        self.is_running = True
        print("[OPC Adapter] Успешно подключено!")

    async def disconnect(self):
        """Разрывает соединение с OPC UA сервером."""
        if self.is_running:
            await self.client.disconnect()
            self.is_running = False
            print("[OPC Adapter] Отключено.")

    # -------------------------------------------------------------------------
    # 2.3. Логика обмена данными
    # -------------------------------------------------------------------------
    async def setup_subscriptions(self):
        """Настраивает подписки на изменения control-тегов на сервере."""
        class DataChangeHandler:
            def __init__(self, adapter_instance, session_id): # <--- Принимаем
                self.adapter = adapter_instance
                self.session_id = session_id # <--- Сохраняем

            def datachange_notification(self, node: Node, val, data: ua.DataChangeNotification):
                node_id = node.nodeid.to_string()
                print(f"[OPC] Получено: Node={node_id}, Value={val}")
                if not val:
                    return

                command_info = self.adapter.OPC_NODE_MAPPING.get(node_id)
                if command_info:
                    self.adapter.control_logic.process_command(
                        session_id=self.session_id,
                        component=command_info["component_id"],
                        param=command_info["param"],
                        value=val
                    )

        handler = DataChangeHandler(self, self.session_id)
        subscription = await self.client.create_subscription(500, handler)

        nodes_to_subscribe = [
            self.client.get_node(node_id)
            for node_id, info in self.OPC_NODE_MAPPING.items()
            if info["mode"] == "control"
        ]

        if nodes_to_subscribe:
            await subscription.subscribe_data_change(nodes_to_subscribe)
            print(f"[OPC Adapter] Подписан на {len(nodes_to_subscribe)} control-тегов.")
        else:
            print("[OPC Adapter] Нет тегов управления для подписки.")

    async def send_to_opc(self, component_id, param, value):
        """Находит NodeId по параметру и отправляет значение на сервер."""
        key = (component_id, param)
        # if self.last_sent_values.get(key) == value:
        #     return

        # self.last_sent_values[key] = value

        node_id = None
        for nid, info in self.OPC_NODE_MAPPING.items():
            if info["component_id"] == component_id and info["param"] == param:
                variant_type = ua.VariantType.Boolean if info["mode"] in ["control", "status"] else ua.VariantType.Double
                node_id = nid
                break

        if not node_id:
            print(f"[OPC WRITE] Не найден NodeId для {component_id}.{param}")
            return

        try:

            # 2. Создаем переменную `variant` нужного OPC UA типа
            variant = ua.Variant(value, variant_type)
            # =======================================================

            # 3. Получаем ноду и записываем в нее созданный `variant`
            node = self.client.get_node(node_id)
            await node.write_value(variant)
            
            print(f"[OPC WRITE] {component_id}.{param} = {value}")
        except Exception as e:
            # Теперь эта ошибка точно исчезнет
            print(f"[OPC WRITE ERROR] Не удалось записать {component_id}.{param} -> {value}: {e}")