import asyncio
import logging
from asyncua import Server, ua
# === Карта переменных OPC UA ===
# === ЕДИНЫЙ И ПОЛНЫЙ СПИСОК ПЕРЕМЕННЫХ (из Сигналы_v3.txt) ===
OPC_NODE_MAPPING = {
    # === НАСОС 0 (NA4) ===
    "ns=1;i=101": {"mode": "control", "component_id": "pump_0", "param": "na_start"},
    "ns=1;i=102": {"mode": "control", "component_id": "pump_0", "param": "na_stop"},
    "ns=1;i=103": {"mode": "status",  "component_id": "pump_0", "param": "na_on"},
    "ns=1;i=104": {"mode": "status",  "component_id": "pump_0", "param": "na_off"},
    "ns=1;i=105": {"mode": "monitor", "component_id": "pump_0", "param": "motor_current"},
    "ns=1;i=106": {"mode": "monitor", "component_id": "pump_0", "param": "pressure_in"},
    "ns=1;i=107": {"mode": "monitor", "component_id": "pump_0", "param": "pressure_out"},
    "ns=1;i=108": {"mode": "monitor", "component_id": "pump_0", "param": "temp_bearing_1"},
    "ns=1;i=109": {"mode": "monitor", "component_id": "pump_0", "param": "cover_open"},
    "ns=1;i=113": {"mode": "monitor", "component_id": "pump_0", "param": "temp_bearing_2"},
    "ns=1;i=114": {"mode": "monitor", "component_id": "pump_0", "param": "temp_motor_1"},
    "ns=1;i=115": {"mode": "monitor", "component_id": "pump_0", "param": "temp_motor_2"},
    "ns=1;i=116": {"mode": "monitor", "component_id": "pump_0", "param": "temp_water"},
    "ns=1;i=117": {"mode": "monitor", "component_id": "pump_0", "param": "flow_rate"},

    # === ЗАДВИЖКА 0 (Выходная) ===
    "ns=1;i=118": {"mode": "status",  "component_id": "valve_out_0", "param": "valve_open"},
    "ns=1;i=119": {"mode": "status",  "component_id": "valve_out_0", "param": "valve_closed"},
    "ns=1;i=120": {"mode": "control", "component_id": "valve_out_0", "param": "valve_open_cmd"},
    "ns=1;i=121": {"mode": "control", "component_id": "valve_out_0", "param": "valve_close_cmd"},

    # === МАСЛОСИСТЕМА 0 ===
    "ns=1;i=110": {"mode": "status",  "component_id": "oil_system_0", "param": "oil_sys_running"},
    "ns=1;i=111": {"mode": "status",  "component_id": "oil_system_0", "param": "oil_sys_pressure_ok"},
    "ns=1;i=112": {"mode": "monitor", "component_id": "oil_system_0", "param": "oil_pressure"},
    "ns=1;i=122": {"mode": "control", "component_id": "oil_system_0", "param": "oil_pump_start"},
    "ns=1;i=123": {"mode": "control", "component_id": "oil_system_0", "param": "oil_pump_stop"},
    # Дополнительные параметры, если они есть в модели
    "ns=1;i=304": {"mode": "monitor", "component_id": "oil_system_0", "param": "temperature"},

    # === НАСОС 1 (NA2) ===
    "ns=1;i=201": {"mode": "control", "component_id": "pump_1", "param": "na_start"},
    "ns=1;i=202": {"mode": "control", "component_id": "pump_1", "param": "na_stop"},
    "ns=1;i=203": {"mode": "status",  "component_id": "pump_1", "param": "na_on"},
    "ns=1;i=204": {"mode": "status",  "component_id": "pump_1", "param": "na_off"},
    "ns=1;i=205": {"mode": "monitor", "component_id": "pump_1", "param": "motor_current"},
    "ns=1;i=206": {"mode": "monitor", "component_id": "pump_1", "param": "pressure_in"},
    "ns=1;i=207": {"mode": "monitor", "component_id": "pump_1", "param": "pressure_out"},
    "ns=1;i=208": {"mode": "monitor", "component_id": "pump_1", "param": "temp_bearing_1"},
    "ns=1;i=209": {"mode": "monitor", "component_id": "pump_1", "param": "cover_open"},
    "ns=1;i=213": {"mode": "monitor", "component_id": "pump_1", "param": "temp_bearing_2"},
    "ns=1;i=214": {"mode": "monitor", "component_id": "pump_1", "param": "temp_motor_1"},
    "ns=1;i=215": {"mode": "monitor", "component_id": "pump_1", "param": "temp_motor_2"},
    "ns=1;i=216": {"mode": "monitor", "component_id": "pump_1", "param": "temp_water"},
    "ns=1;i=217": {"mode": "monitor", "component_id": "pump_1", "param": "flow_rate"},

    # === ЗАДВИЖКА 1 (Выходная) ===
    "ns=1;i=218": {"mode": "status",  "component_id": "valve_out_1", "param": "valve_open"},
    "ns=1;i=219": {"mode": "status",  "component_id": "valve_out_1", "param": "valve_closed"},
    "ns=1;i=220": {"mode": "control", "component_id": "valve_out_1", "param": "valve_open_cmd"},
    "ns=1;i=221": {"mode": "control", "component_id": "valve_out_1", "param": "valve_close_cmd"},

    # === МАСЛОСИСТЕМА 1 ===
    "ns=1;i=210": {"mode": "status",  "component_id": "oil_system_1", "param": "oil_sys_running"},
    "ns=1;i=211": {"mode": "status",  "component_id": "oil_system_1", "param": "oil_sys_pressure_ok"},
    "ns=1;i=212": {"mode": "monitor", "component_id": "oil_system_1", "param": "oil_pressure"},
    "ns=1;i=222": {"mode": "control", "component_id": "oil_system_1", "param": "oil_pump_start"},
    "ns=1;i=223": {"mode": "control", "component_id": "oil_system_1", "param": "oil_pump_stop"},
    # Дополнительные параметры, если они есть в модели
    "ns=1;i=404": {"mode": "monitor", "component_id": "oil_system_1", "param": "temperature"},
}
# === Логгирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opcua")

# === Кэш значений (для отслеживания изменений вручную) ===
last_values = {}

async def main():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    uri = "http://example.org/my-opcua"
    idx = await server.register_namespace(uri)

    # Главный объект
    objects = server.nodes.objects
    control_obj = await objects.add_object(idx, "PumpControlSystem")

    # === Создание переменных ===
    nodeid_map = {}
    for nodeid_str, info in OPC_NODE_MAPPING.items():
        name = f"{info['component_id']}_{info['param']}"
        initial_value = False if info['mode'] in ["control", "status"] else 0.0
        data_type = ua.VariantType.Boolean if info['mode'] in ["control", "status"] else ua.VariantType.Float
        
        nodeid = ua.NodeId.from_string(nodeid_str)
        var = await control_obj.add_variable(nodeid, name, initial_value, datatype=data_type)
        await var.set_writable()

        nodeid_map[nodeid_str] = var
        last_values[nodeid_str] = initial_value
        logger.info(f"✅ Added {name} with NodeId {nodeid_str}")


    logger.info("🚀 OPC UA server is running...")

    async with server:
        while True:
            # === Ручная проверка изменений ===
            for nodeid_str, var in nodeid_map.items():
                try:
                    current_val = await var.get_value()
                    if current_val != last_values[nodeid_str]:
                        info = OPC_NODE_MAPPING.get(nodeid_str)
                        logger.info(
                            f"[🔄 SERVER VALUE CHANGED] {info['component_id']}.{info['param']} → {current_val}"
                        )
                        last_values[nodeid_str] = current_val
                except Exception as e:
                    logger.warning(f"[READ ERROR] {nodeid_str}: {e}")
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
