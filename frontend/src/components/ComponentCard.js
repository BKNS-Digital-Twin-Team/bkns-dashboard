// Файл: src/components/ComponentCard.js

import React, { useState } from 'react';
// --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
// Импортируем нашу НОВУЮ функцию в единственном числе
import * as api from '../api/twinApi';
// "Красивые" имена для параметров на русском языке
const PARAM_NAMES = {
  // ... (весь ваш объект PARAM_NAMES остается без изменений)
  na_on: 'Насос включен',
  na_off: 'Насос выключен',
  motor_current: 'Ток двигателя (А)',
  pressure_in: 'Давление на входе (МПа)',
  pressure_out: 'Давление на выходе (МПа)',
  flow_rate: 'Расход (м³/с)',
  temp_bearing_1: 'T подшипника 1 (°C)',
  temp_bearing_2: 'T подшипника 2 (°C)',
  temp_motor_1: 'T мотора 1 (°C)',
  temp_motor_2: 'T мотора 2 (°C)',
  temp_water: 'T воды (°C)',
  cover_open: 'Крышка открыта',
  oil_sys_running: 'Маслосистема в работе',
  oil_sys_pressure_ok: 'Давление масла в норме',
  oil_pressure: 'Давление масла (бар)',
  temperature: 'Температура (°C)',
  valve_open: 'Задвижка открыта',
  valve_closed: 'Задвижка закрыта',
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
    // Очищаем локальные оверрайды после применения
    setOverrides({});
  };
  
  return (
    <div className="component-card flex flex-col justify-between">
      <div>
        <h3 className="font-bold text-lg mb-2 text-gray-800 capitalize">{name.replace(/_/g, ' ')}</h3>
        
        <div className="space-y-2">
          {data && Object.entries(data).map(([key, value]) => {
            if (typeof value !== 'number' && typeof value !== 'boolean') return null;

            const isOverridable = typeof value === 'number';

            return (
              <div key={key} className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{PARAM_NAMES[key] || key}:</span>
                <div className="flex items-center">
                  <span className={`font-semibold mr-2 ${typeof value === 'boolean' ? (value ? 'text-green-600' : 'text-red-600') : 'text-gray-900'}`}>
                    {typeof value === 'boolean' ? (value ? 'Да' : 'Нет') : value.toFixed(3)}
                  </span>
                  {isOverridable && (
                    <input
                      type="number"
                      placeholder="Override"
                      className="input border rounded px-2 py-1 w-32 text-right"
                      value={overrides[key] || ''}
                      onChange={(e) => handleOverrideChange(key, e.target.value)}
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t">
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