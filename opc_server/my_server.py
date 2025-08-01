import asyncio
import logging
from asyncua import Server, ua

OPC_NODE_MAPPING = {
    "ns=2;i=28": {"mode": "control", "component_id": "pump_0", "param": "na_start"},
    "ns=2;i=29": {"mode": "control", "component_id": "pump_0", "param": "na_stop"},
    "ns=2;i=45": {"mode": "control", "component_id": "valve_out_0", "param": "valve_open"}, 
    "ns=2;i=46": {"mode": "control", "component_id": "valve_out_0", "param": "valve_close"},
    "ns=2;i=35": {"mode": "control","component_id": "oil_system_0", "param": "oil_pump_start"},
    "ns=2;i=2":  {"mode": "control", "component_id": "pump_1", "param": "na_start"},
    "ns=2;i=3":  {"mode": "control", "component_id": "pump_1", "param": "na_stop"},
    "ns=2;i=21": {"mode": "control", "component_id": "valve_out_1", "param": "valve_open"},
    "ns=2;i=22": {"mode": "control", "component_id": "valve_out_1", "param": "valve_close"},
    "ns=2;i=23": {"mode": "control", "component_id": "oil_system_1", "param": "oil_pump_start"},
}

async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("opcua")

    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    
    uri = "http://example.org/my-opcua"
    idx = await server.register_namespace(uri)

    objects = server.nodes.objects
    control_obj = await objects.add_object(idx, "PumpControlSystem")

    # Создаем переменные по OPC_NODE_MAPPING
    nodeid_map = {}
    for nodeid_str, info in OPC_NODE_MAPPING.items():
        component = info["component_id"]
        param = info["param"]
        name = f"{component}_{param}"

        # Добавляем переменную (изначально False)
        var = await control_obj.add_variable(idx, name, False)
        await var.set_writable()

        # Принудительно задаем NodeId (по строке "ns=2;i=...") — требует правильную настройку клиента
        var.nodeid = ua.NodeId.from_string(nodeid_str)
        nodeid_map[nodeid_str] = var

        logger.info(f"Added {name} with NodeId {nodeid_str}")

    logger.info("OPC UA server is running...")
    async with server:
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
