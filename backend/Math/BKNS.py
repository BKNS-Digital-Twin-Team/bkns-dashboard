import time
from typing import Dict, List
from .OilSystem import OilSystem
from .Pump import CentrifugalPump
from .Pipe import PipeModel
from .Valve import Valve

class BKNS:
    """
    Одна установка состоит из 2 насосов. 
    Каждый насос имеет входную задвижку и выходную;
    После задвижек идут трубы -входная и выходная.
    Трубы выходят в общую выходную и общую входную.
    Каждый насос подключен к маслосистеме.
    Итог: 2 насоса
        2 маслосистемы
        4 задвижки
        6 труб (2 входные, 2 выходные, 1 общая входная, 1 общая выходная)
    """

    def __init__(self,inlet_pressure=1.9, inlet_temperature=25.0):
        
        #Параметры для входной трубы (если труба откуда-то идет)
        self.inlet_pressure = inlet_pressure  # По умолчанию 1.9 (относительное давление)
        self.inlet_temperature = inlet_temperature  # По умолчанию 25°C

        # Инициализация маслосистем для каждого насоса
        self.oil_systems = [
            OilSystem(0),  # Маслосистема для насоса NA4
            OilSystem(1)   # Маслосистема для насоса NA2
        ]

        # Команды управления маслонасосами: 
        # для каждого маслонасоса отдельные флаги запуска/остановки
        self.oil_pump_commands = [
            {'start': False, 'stop': True},  # Маслонасос для NA4
            {'start': False, 'stop': True}   # Маслонасос для NA2
        ]

        # Инициализация насосов с привязкой к соответствующим маслосистемам
        self.pumps = [
            CentrifugalPump(self.oil_systems[0],'NA4'),  # Насос NA4
            CentrifugalPump(self.oil_systems[1],'NA2')   # Насос NA2
        ]

        # Задвижки: входные и выходные для каждого насоса
        self.valves = {
            'in_0': Valve(),  # Входная задвижка NA4
            'out_0': Valve(), # Выходная задвижка NA4
            'in_1': Valve(),  # Входная задвижка NA2
            'out_1': Valve()  # Выходная задвижка NA2
        }

        # Трубы входные и выходные для каждого насоса, а также общие
        self.pipes = {
            'in_0': PipeModel(),   # Входная труба NA4
            'out_0': PipeModel(),  # Выходная труба NA4
            'in_1': PipeModel(),   # Входная труба NA2
            'out_1': PipeModel(),  # Выходная труба NA2
            'main_inlet': PipeModel(),  # Общая входная труба (до разделения)
            'main_outlet': PipeModel()  # Общая выходная труба (после объединения)
        }

        # Физические параметры жидкости
        self.rho = 1000       # Плотность жидкости [кг/м3]
        self.mu = 1e-3        # Динамическая вязкость [Па·с]
        self.m_dot_A = 0.5      # Массовый расход [кг/с]
        self.m_dot_B = 0.5      # Массовый расход [кг/с]
        
        # Таймер для обновления состояния
        self.last_update_time = time.time()


    def  update_system(self):
        """
        Основной метод обновления состояния всей системы.
        Выполняется циклически для симуляции работы БКНС.

        """

        #Для большей плавности и корректной работы модели
        current_time = time.time()  # Получаем текущее время в секундах с начала эпохи
        dt = current_time - self.last_update_time  # Вычисляем разницу с предыдущим обновлением
        self.last_update_time = current_time  # Обновляем время последнего обновления

        # Обновляем состояние всех задвижек
        for valve in self.valves.values():
            valve.update(dt)



        # Обновляем общую входную трубу (рассчитываем давление и температуру)
        self.pipes['main_inlet'].compute_output_pressure(
            p_in=self.inlet_pressure,  # Входное давление в систему
            m_dot_A=self.m_dot_A,      # Массовый расход в порту A
            m_dot_B=self.m_dot_B,      # Массовый расход в порту B
            mu=self.mu,                # Вязкость жидкости
            rho=self.rho,              # Плотность жидкости
            temperature=self.inlet_temperature  # Температура жидкости на входе
        )

        # Обновляем маслосистемы с учётом команд запуска/остановки маслонасосов
        # Важно: маслосистема запускается только по команде, без автоматического запуска
        for pump_id, oil_system in enumerate(self.oil_systems):
            cmd = self.oil_pump_commands[pump_id]
            oil_system.update(
                command_main_run=cmd['start'],
                command_main_stop=cmd['stop'],
                command_reserve_run=False,  # Резервный маслонасос всегда выключен
                command_reserve_stop=True,
                dt=dt
            )

        # Обновляем насосы, трубы и задвижки
        for pump_id, pump in enumerate(self.pumps):

            # Параметры для труб и задвижек данного насоса
            in_valve = self.valves[f'in_{pump_id}']
            out_valve = self.valves[f'out_{pump_id}']
            in_pipe = self.pipes[f'in_{pump_id}']
            out_pipe = self.pipes[f'out_{pump_id}']
                
            # Обновляем входную трубу насоса (от общей входной трубы)
            in_pipe.compute_output_pressure(
                p_in=self.pipes['main_inlet'].p_out,
                m_dot_A=self.m_dot_A,
                m_dot_B=self.m_dot_B,
                mu=self.mu,
                rho=self.rho,
                temperature=self.pipes['main_inlet'].T
            )
                
            # Обновляем насос
            target_omega = pump.reference_shaft_speed if pump.na_on else 0.0
            q = pump.nominal_capacity * 0.8  # Рабочий расход (80% от номинального)
            # Получаем состояния задвижек (True - открыта, False - закрыта)
            inlet_open = self.valves[f'in_{pump_id}'].state == "open"
            outlet_open = self.valves[f'out_{pump_id}'].state == "open"
            pump.step(target_omega, q, self.rho, inlet_open, outlet_open)
                
            # Обновляем давление и температуру в выходной трубе
            out_pipe.compute_output_pressure(
                p_in=pump.p_out,
                m_dot_A=self.m_dot_A,
                m_dot_B=self.m_dot_B,
                mu=self.mu,
                rho=self.rho,
                temperature=self.inlet_temperature
            )
                
            # Обновляем состояние задвижек
            in_valve.update_conditions(
                pressure=in_pipe.p_out,
                temperature=in_pipe.T
            )
            out_valve.update_conditions(
                pressure=out_pipe.p_out,
                temperature=out_pipe.T
            )
            
        # Обновляем общую выходную трубу (объединяем выходы насосов)
        # Для упрощения считаем, что давление в общей трубе - среднее от выходных труб
        avg_pressure = (self.pipes['out_0'].p_out + self.pipes['out_1'].p_out) / 2
        avg_temp = (self.pipes['out_0'].T + self.pipes['out_1'].T) / 2
        
        self.pipes['main_outlet'].compute_output_pressure(
            p_in=avg_pressure,
            m_dot_A=self.m_dot_A,
            m_dot_B=self.m_dot_B,
            mu=self.mu,
            rho=self.rho,
            temperature=avg_temp
        )
        
    def control_pump(self, pump_id: int, start: bool):
        """
        Управление насосом (включение/выключение)

        """
        if pump_id not in [0, 1]:
            raise ValueError("Invalid pump_id. Must be 0 or 1.")
            
        if start:
            
            self.pumps[pump_id].na_start = True
            self.pumps[pump_id].na_stop = False

        else:
            self.pumps[pump_id].na_start = False
            self.pumps[pump_id].na_stop = True
    
    def control_oil_pump(self, pump_id: int, start: bool):
        """
        Управление маслонасосом, отдельное от основного насоса.
        start=True — запустить маслонасос, False — остановить.
        """
        if pump_id not in [0, 1]:
            raise ValueError("Invalid pump_id. Must be 0 or 1.")

        self.oil_pump_commands[pump_id]['start'] = start
        self.oil_pump_commands[pump_id]['stop'] = not start

    def control_valve(self, valve_key: str, open_valve: bool):
        """
        Управление задвижкой
        """
        if valve_key not in self.valves:
            raise ValueError(f"Invalid valve lock key: {valve_key}")
        valve = self.valves[valve_key]
        if open_valve:
            valve.control("open")
        else:
            valve.control("close")
    
    # Вставьте этот код в класс BKNS, заменив старую версию get_status

    def get_status(self) -> Dict:
        """
        Возвращает текущее состояние системы в виде словаря.
        Доработан для полного соответствия с OPC_NODE_MAPPING.
        """
        status = {
            'pumps': {},
            'valves': {},
            'pipes': {},
            'oil_systems': {},
            'alarms': {},
            'active_alarms': [],
            'inlet_conditions': {
                'pressure': self.inlet_pressure,
                'temperature': self.inlet_temperature,
            }
        }
        
        # Собираем данные по каждому насосу
        for pump_id, pump in enumerate(self.pumps):
            # Входное давление для насоса берем из соответствующей входной трубы
            inlet_pipe_pressure = self.pipes[f'in_{pump_id}'].p_out

            status['pumps'][str(pump_id)] = {
                "is_running": pump.na_on,
                "is_off": not pump.na_on,  # <-- ДОБАВЛЕНО: Инверсия от 'is_running'
                "speed": pump.current_omega,
                "current": pump.current_motor_i,
                "pressure_in": inlet_pipe_pressure, # <-- ДОБАВЛЕНО: Давление на входе в насос
                "outlet_pressure": pump.p_out,
                "flow_rate": pump.NA_AI_Qmom_n,
                "di_kojuh_status": True,  # <-- ДОБАВЛЕНО: Заглушка, т.к. нет логики в модели
                "temperatures": {
                    "T2": pump.NA_AI_T_2_n,
                    "T3": pump.NA_AI_T_3_n,
                    "T4": pump.NA_AI_T_4_n,
                    "T5": pump.NA_AI_T_5_n,
                },
            }
        
        for valve_key, valve in self.valves.items():
            status['valves'][valve_key] = {
                "is_open": valve.state == "open",
                "is_closed": valve.state == "closed", # <-- ДОБАВЛЕНО
                "is_moving": valve.is_moving,
                "target_state": valve.target_position == 100.0,
                "pressure": valve.pressure,
                "temperature": valve.temperature,
            }

        for pipe_key, pipe in self.pipes.items():
            status['pipes'][pipe_key] = {
                "pressure": pipe.p_out,
                "temperature": pipe.T
            }

        for pump_id, oil_system in enumerate(self.oil_systems):
            status['oil_systems'][str(pump_id)] = {
                "is_running": oil_system.running,
                "pressure": oil_system.pressure,
                "flow_rate": oil_system.flow_rate,
                "temperature": oil_system.temperature,
                "viscosity": oil_system.viscosity,
                "pressure_ok": oil_system.pressure_ok, # Используется для тега DI_FL_MS
            }

        return status
    
    def __str__(self):
        """
        Возвращает текстовое представление состояния системы.

        """
        status = self.get_status()
        output = []
        
        # Общая информация
        output.append("=== Состояние БКНС ===")
        output.append(f"Входные параметры: Давление={status['main_inlet']['pressure']:.4f} МПа")
        output.append(f"Выходные параметры: Давление={status['main_outlet']['pressure']:.4f} МПа\n")

        # Детальная информация по каждому насосу
        for pump_name, pump_data in status['pumps'].items():
            output.append(
                f"Насос {pump_name} (ID {pump_data['pump_id']}):\n"
                f"  Режим работы: {pump_data['operation_mode']}\n"
                f"  Старт: {pump_data['start']}, Стоп: {pump_data['stop']}, "
                f"Вкл: {pump_data['on']}, Выкл: {pump_data['off']}\n"
                f"  Ток двигателя: {pump_data['motor_i']:.2f} А\n"
                f"  Давление вход: {pump_data['pressure_in']:.3f} МПа, "
                f"выход: {pump_data['pressure_out']:.3f} МПа\n"
                f"  Температуры:\n"
                f"    Подшипник (раб.): {pump_data['bearing_work_temp']:.1f}°C\n"
                f"    Подшипник (поле): {pump_data['bearing_field_temp']:.1f}°C\n"
                f"    Мотор (раб.): {pump_data['motor_bearing_work_temp']:.1f}°C\n"
                f"    Мотор (поле): {pump_data['motor_bearing_field_temp']:.1f}°C\n"
                f"    Гидроподшипник: {pump_data['hydro_support_temp']:.1f}°C\n"
                f"  Маслосистема: {'запущена' if pump_data['oil_system_running'] else 'остановлена'}, "
                f"Давление: {pump_data['oil_pressure']:.2f} бар ,"
                f"Температура масла: {pump_data['oil_temperature']:.1f}°C\n"
                f"  Команды маслонасоса: старт={pump_data['oil_pump_start_cmd']}, стоп={pump_data['oil_pump_stop_cmd']}\n"
                f"  Входная задвижка: состояние: "
                f"{'открыта' if pump_data['in_valve_open'] else 'закрыта' if pump_data['in_valve_closed'] else 'в движении'}, "
                f"команды: открыть={pump_data['in_valve_open_cmd']}, закрыть={pump_data['in_valve_close_cmd']}\n"
                f"  Выходная задвижка: состояние: "
                f"{'открыта' if pump_data['out_valve_open'] else 'закрыта' if pump_data['out_valve_closed'] else 'в движении'}, "
                f"команды: открыть={pump_data['out_valve_open_cmd']}, закрыть={pump_data['out_valve_close_cmd']}\n"
                f"  Расход: {pump_data['flow_rate']:.3f} м³/с\n"
            )
        
        return "\n".join(output)

import time
import sys

# log_file = open("Пример.log", "w", encoding="utf-8")
# sys.stdout = log_file
# if __name__ == "__main__":

#     # Инициализация системы БКНС с параметрами по умолчанию:
#     bkns = BKNS()
    
#     # Открываем все задвижки насосов NA4 и NA2
#     bkns.control_valve('in_0', True)
#     bkns.control_valve('out_0', True)
#     bkns.control_valve('in_1', True)
#     bkns.control_valve('out_1', True)

#     # Запускаем маслонасосы для обоих насосов
#     bkns.control_oil_pump(0, True)
#     bkns.control_oil_pump(1, True)

#     print("=== Начало симуляции БКНС ===")
#     try:
#         for i in range(45):  # Увеличиваем длительность для демонстрации новых сценариев
#             bkns.update_system()
#             print(f"\n=== Состояние БКНС через {i} секунд ===")
#             print(bkns)

#             # --- Режимы работы одного насоса (NA4) ---
#             if i == 5:
#                 print("\n>>> Запускаем насос NA4")
#                 bkns.control_pump(0, True)
#             if i == 10:
#                 print("\n>>> Закрываем выходную задвижку NA4")
#                 bkns.control_valve('out_0', False)
#             if i == 14:
#                 print("\n>>> Повторная попытка закрыть выходную задвижку NA4")
#                 bkns.control_valve('out_0', False)
#             if i == 16:
#                 print("\n>>> Открываем выходную задвижку NA4")
#                 bkns.control_valve('out_0', True)
#             if i == 18:
#                 print("\n>>> Останавливаем насос NA4")
#                 bkns.control_pump(0, False)
#             if i == 20:
#                 print("\n>>> Останавливаем маслонасос NA4")
#                 bkns.control_oil_pump(0, False)

#             # --- Работа двух насосов одновременно ---
#             if i == 22:
#                 print("\n>>> Запускаем насос NA4 и насос NA2 одновременно")
#                 bkns.control_pump(0, True)
#                 bkns.control_pump(1, True)
#                 bkns.control_oil_pump(0, True)
#                 bkns.control_oil_pump(1, True)
#             if i == 25:
#                 print("\n>>> Закрываем входную задвижку NA2 (симуляция 'закрыта входная')")
#                 bkns.control_valve('in_1', False)
#             if i == 28:
#                 print("\n>>> Открываем входную задвижку NA2")
#                 bkns.control_valve('in_1', True)

#             # --- Работа насоса без масла (маслосистема выключена) ---
#             if i == 30:
#                 print("\n>>> Останавливаем маслонасос NA2 (симуляция работы насоса без масла)")
#                 bkns.control_oil_pump(1, False)
#             if i == 32:
#                 print("\n>>> Останавливаем насос NA2")
#                 bkns.control_pump(1, False)
#             if i == 35:
#                 print("\n>>> Запускаем насос NA2 без маслонасоса (опасный режим!)")
#                 bkns.control_pump(1, True)
#             if i == 40:
#                 print("\n>>> Запускаем маслонасос NA2")
#                 bkns.control_oil_pump(1, True)

#             time.sleep(1)

#     except KeyboardInterrupt:
#         print("\nСимуляция остановлена пользователем")
# log_file.close()