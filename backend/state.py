import os
SERVER_URL = os.getenv("OPC_SERVER_URL", "opc.tcp://localhost:4840/freeopcua/server/")
if SERVER_URL == "opc.tcp://localhost:4840/freeopcua/server/":
    print("OPC_SERVER_URL from Docker compose is None, using default")
FULL_SYNC_INTERVAL = 30

sessions = {}
session_states = {}  # session_id -> {"running": True/False}
previous_states = {}  # session_id -> dict previous values
session_last_full_sync = {}

manual_overrides = {}  # session_id -> { (component, param): value }
control_modes = {} 

opc_adapters = {}  # session_id -> OPCAdapter