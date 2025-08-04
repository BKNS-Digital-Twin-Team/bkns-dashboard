// src/components/ComponentCard.js
import React, { useState, useEffect } from 'react';
import { sendManualCommand } from '../api/twinApi';

const getDisplayName = (name, type) => {
  if (type === 'pumps') return `Насос ${name}`;
  if (type === 'valves') {
    const [direction, index] = name.split('_');
    const dirText = direction === 'in' ? 'Входной' : 'Выходной';
    return `Клапан ${dirText} ${index}`;
  }
  return name;
};

const PARAM_NAMES = {
  is_running: 'В работеее',
  speed: 'Скорость',
  current: 'Ток (А)',
  outlet_pressure: 'Давление на выходе',
  temperatures: 'Температуры',
  flow_rate: 'Расход',
  is_open: 'Открыт',
  is_moving: 'В движении',
  target_state: 'Целевое состояние',
  pressure: 'Давление',
  temperature: 'Температура',
};

const ComponentCard = ({ name, type, data, mode, onModeToggle }) => {
  const displayName = getDisplayName(name, type);
  const isButtonDisabled = mode === 'N/A';
  const isManualMode = mode === 'MANUAL';
  const buttonText = isManualMode ? 'Вернуть в режим MODEL' : 'Переключить в ручной';

  const [manualValues, setManualValues] = useState({});

  // Обновляем модельные значения, если нет ручного
  useEffect(() => {
    if (!data) return;
    const updated = { ...manualValues };
    Object.entries(data).forEach(([key, value]) => {
      if (typeof value !== 'object' && !(key in manualValues)) {
        updated[key] = String(value);
      }
    });
    setManualValues(updated);
  }, [data]);

  const handleChange = (key, value) => {
    const updated = { ...manualValues, [key]: value };
    setManualValues(updated);

    if (value.trim() === '') {
      // очистка — вернуться к OPC (не отправляем ничего)
      console.log(`[CLEAR] ${name}.${key} → вернется к значению модели`);
      // можно отправить null или просто ничего не делать
    } else {
      const parsed = parseFloat(value);
      if (!isNaN(parsed)) {
        sendManualCommand(name, key, parsed);
      }
    }
  };

  return (
    <div className="component-card">
      <h3 className="component-title">{displayName}</h3>

      <div className="component-params">
        {data &&
          Object.entries(data).map(([key, value]) => {
            if (typeof value === 'object' || value === null) return null;

            return (
              <div key={key} className="param-row">
                <span>{PARAM_NAMES[key] || key}:</span>
                <input
                  type="text"
                  value={manualValues[key] ?? ''}
                  onChange={(e) => handleChange(key, e.target.value)}
                  placeholder={String(value)}
                />
              </div>
            );
          })}
      </div>

      <div className="component-controls">
        <p>Режим: <strong>{mode}</strong></p>
        <button onClick={onModeToggle} disabled={isButtonDisabled}>
          {buttonText}
        </button>
      </div>
    </div>
  );
};

export default ComponentCard;
