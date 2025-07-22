# test_import.py
print("--- Начинаю проверку импорта ---")
try:
    from Math.BKNS import BKNS
    print("\n[УСПЕХ] Модуль BKNS и класс BKNS успешно импортированы!")
    
    print("--- Пробую создать экземпляр класса ---")
    instance = BKNS()
    print("[УСПЕХ] Экземпляр класса BKNS успешно создан!")

except Exception as e:
    print("\n[ОШИБКА!] Проблема обнаружена. Вот настоящий traceback:")
    # Печатаем полный traceback, чтобы увидеть настоящую ошибку
    import traceback
    traceback.print_exc()

print("\n--- Проверка завершена ---")