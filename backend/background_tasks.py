import asyncio
from state import sessions, session_states, previous_states
from opc_utils import update_opc_from_model_state

# Эта функция теперь живет здесь
async def update_loop(session_id: str):
    """
    Главный цикл обновления состояния модели для одной сессии.
    """
    print(f">>> update_loop для сессии '{session_id}' стартует <<<")
    
    model = sessions.get(session_id)
    if not model:
        print(f"[ERROR] Модель для сессии {session_id} не найдена в update_loop.")
        return

    while session_id in sessions:
        try:
            if session_states.get(session_id, {}).get("running", False):
                # Обновляем состояние модели (логика шага симуляции)
                model.step(1)
                
                # Копируем текущее состояние для отправки в OPC
                current_state = model.get_status()
                
                # Отправляем изменения в OPC, если они есть
                await update_opc_from_model_state(session_id, current_state)
                
                # Сохраняем текущее состояние для следующей итерации
                previous_states[session_id] = current_state

            await asyncio.sleep(1)
        except asyncio.CancelledError:
            print(f"Update loop для сессии {session_id} остановлен.")
            break
        except Exception as e:
            print(f"ОШИБКА в цикле обновления для сессии {session_id}: {e}")
            await asyncio.sleep(5) # Пауза перед повторной попыткой в случае ошибки