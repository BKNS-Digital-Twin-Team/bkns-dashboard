// src/components/ComponentCard.js
import React, { useState, useEffect } from 'react';
import { sendManualCommand, sendManualOverrides } from '../api/twinApi';

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
  is_running: 'В работее',
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

  const fullComponentName =
    type === 'pump' ? `pump_${name}`
    : type === 'valve' ? `valve_${name}`
    : type === 'oil_system' ? `oil_system_${name}`
    : name;

  const [manualValues, setManualValues] = useState(() => ({}));

  useEffect(() => {
    if (Object.keys(manualValues).length > 0) {
      const filtered = {};
      for (const [key, value] of Object.entries(manualValues)) {
        const parsed = parseFloat(value);
        if (!isNaN(parsed)) {
          filtered[key] = parsed;
        }
      }
      if (Object.keys(filtered).length > 0) {
        sendManualOverrides(fullComponentName, filtered)
          .then(() => console.log(`[OVERRIDE] отправлено: ${fullComponentName}`, filtered))
          .catch((err) => console.error('Ошибка при отправке overrides:', err));
      }
    }
  }, [manualValues]);

  const handleOverrideChange = (key, value) => {
    const updated = { ...manualValues, [key]: value };
    setManualValues(updated);

    if (value.trim() === '') {
      console.log(`[OVERRIDE-CLEAR] ${fullComponentName}.${key} → сброс`);
      return;
    }

    const parsed = parseFloat(value);
    if (!isNaN(parsed)) {
      console.log(`[OVERRIDE] ${fullComponentName}.${key} = ${parsed}`);
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
              <div key={key} className="param-block">
                <div className="param-label">{PARAM_NAMES[key] || key}</div>

                <div className="param-value">
                  {(() => {
                    if (typeof value === 'boolean') return value ? 'True' : 'False';
                    if (typeof value === 'number') return value.toFixed(2);
                    return String(value);
                  })()}
                </div>

                <input
                  className="param-override-input"
                  type="number"
                  placeholder="введите значение"
                  value={manualValues[key] ?? ''}
                  onChange={(e) => handleOverrideChange(key, e.target.value)}
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
