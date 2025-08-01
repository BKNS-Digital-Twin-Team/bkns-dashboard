import asyncio
import logging
from asyncua import Server, ua
# === Карта переменных OPC UA ===
OPC_NODE_MAPPING = {
    # сюда вставлен весь твой OPC_NODE_MAPPING, он не менялся
    # см. ниже отдельно, если нужно
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

        var = await control_obj.add_variable(idx, name, initial_value)
        await var.set_writable()
        var.nodeid = ua.NodeId.from_string(nodeid_str)
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
