// Файл: src/components/ComponentCard.js

import React, { useState } from 'react';
// --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
// Импортируем нашу НОВУЮ функцию в единственном числе
import * as api from '../api/twinApi';
// "Красивые" имена для параметров на русском языке
const PARAM_NAMES = {

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
      <div>
        <h3 className="component-label">{name.replace(/_/g, ' ')}</h3>
        
        <div className="component-params">
          {data && Object.entries(data).map(([key, value]) => {
            if (typeof value !== 'number' && typeof value !== 'boolean') return null;

            const isOverridable = typeof value === 'number';

            return (
              <div key={key} className="line">
                
                <div className="param">
                  <span className="param-name">{PARAM_NAMES[key] || key}:</span>
                  <span className={`param-value ${typeof value === 'boolean' ? (value ? 'text-green-600' : 'text-red-600') : 'text-gray-900'}`}>
                    {typeof value === 'boolean' ? (value ? 'Да' : 'Нет') : value.toFixed(3)}
                  </span>
                  {isOverridable && (
                    <input
                      type="number"
                      placeholder="num"
                      className="param-override-input"
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