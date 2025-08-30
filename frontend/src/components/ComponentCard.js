// Файл: src/components/ComponentCard.js

import React, { useState } from 'react';
// --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
// Импортируем нашу НОВУЮ функцию в единственном числе
import * as api from '../api/twinApi';
// "Красивые" имена для параметров на русском языке
const PARAM_NAMES = {
  // Параметры насоса
  'na_on': 'Насос включен',
  'na_off': 'Насос выключен',
  'motor_current': 'Ток двигателя, А',
  'flow_rate': 'Расход, м³/ч',
  'pressure_in': 'Давление на входе, бар',
  'pressure_out': 'Давление на выходе, бар',
  'temp_bearing_1': 'Температура подшипника 1, °C',
  'temp_bearing_2': 'Температура подшипника 2, °C',
  'temp_motor_1': 'Температура двигателя 1, °C',
  'temp_motor_2': 'Температура двигателя 2, °C',
  'temp_water': 'Температура воды, °C',
  'cover_open': 'Крышка открыта',
  
  // Параметры задвижек
  'valve_open': 'Задвижка открыта',
  'valve_closed': 'Задвижка закрыта',
  
  // Параметры маслосистемы
  'oil_sys_running': 'Маслосистема работает',
  'oil_sys_pressure_ok': 'Давление в маслосистеме в норме',
  'oil_pressure': 'Давление масла, бар',
  'temperature': 'Температура, °C' // Общая температура для маслосистемы
};

// Пропсы `type`, `mode`, `onModeToggle` не используются в новой версии,
// но я оставлю их, если они нужны для другой логики.
const ComponentCard = ({ name, data, sessionId, onUpdate }) => {
  // Локальное состояние для хранения значений из полей ввода
  const [overrides, setOverrides] = useState({});

  // Обработчик для обновления локального состояния при вводе
  const handleOverrideChange = (param, value) => {
    setOverrides(prev => ({
      ...prev,
      [param]: value,
    }));
  };

  // Функция для отправки данных на сервер по нажатию кнопки
  const applyOverrides = async () => {
    console.log(`Применение оверрайдов для ${name}:`, overrides);

    for (const [param, value] of Object.entries(overrides)) {
      const parsedValue = parseFloat(value);
      if (!isNaN(parsedValue)) {
        try {
          // Вызываем ИСПРАВЛЕННУЮ функцию с правильными аргументами
          await api.sendManualOverride(sessionId, name, param, parsedValue);
          console.log(`[OVERRIDE] Успешно: ${name}.${param} = ${parsedValue}`);
        } catch (error) {
          console.error(`Ошибка отправки оверрайда для ${name}.${param}:`, error);
        }
      }
    }
    // Просим родителя обновить все данные, чтобы увидеть результат
    if (onUpdate) {
      onUpdate();
    }
  };
  
  return (
    <div className="component-card">
      <div className="component-data">
        <h3 className="component-label">{name.replace(/_/g, ' ')}</h3>
        
        <table>
          <thead>
            <tr>
              <th>Параметр</th>
              <th>Элиас</th>
              <th>Значение</th>
              <th>Переопределение</th>
            </tr>
          </thead>

          <tbody>
            {data && Object.entries(data).map(([key, value]) => {
                if (typeof value !== 'number' && typeof value !== 'boolean') return null;

                const isOverridable = typeof value === 'number';
                
                

                return (
                  <tr key={key}>
                      <td className="param-name">{key}:</td>
                      <td>{PARAM_NAMES[key]} </td>
                      <td className={`param-value`}>
                        {typeof value === 'boolean' ? (value ? 'Да' : 'Нет') : value.toFixed(3)}
                      </td>
                      {isOverridable && (
                        <td>
                        <input
                          type="number"
                          placeholder="num"
                          className="param-override-input"
                          value={overrides[key] || ''}
                          onChange={(e) => handleOverrideChange(key, e.target.value)}
                        />
                        </td>
                      )}
                  </tr>
                );
                
                

            })}
          </tbody>

        </table>


      </div>
      
      <div className="button">
        <button
          onClick={applyOverrides}
          className="enter-button"
        >
          Применить ручные значения
        </button>
      </div>
    </div>
  );



  
};

export default ComponentCard;