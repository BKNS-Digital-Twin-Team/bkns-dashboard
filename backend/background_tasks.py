import asyncio
from state import sessions, session_states, previous_states
from opc_utils import update_opc_from_model_state

async def update_loop(session_id: str):

    print(f">>> update_loop для сессии '{session_id}' стартует <<<")
    
    model = sessions.get(session_id)
    if not model:
        print(f"[ERROR] Модель для сессии {session_id} не найдена в update_loop.")
        return

    while session_id in sessions:
        try:
            if session_states.get(session_id, {}).get("running", False):
                model.update_system()
                
                current_state = model.get_status()
                
                await update_opc_from_model_state(session_id, current_state)
                
                previous_states[session_id] = current_state

            await asyncio.sleep(1)
        except asyncio.CancelledError:
            print(f"Update loop для сессии {session_id} остановлен.")
            break
        except Exception as e:
            print(f"ОШИБКА в цикле обновления для сессии {session_id}: {e}")
            await asyncio.sleep(5) # Пауза перед повторной попыткой в случае ошибки