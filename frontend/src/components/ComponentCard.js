// src/components/ComponentCard.js
import React from 'react';

// --- Вспомогательные функции (остаются без изменений) ---

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
  is_running: 'В работе',
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

const formatValue = (key, value) => {
  if (typeof value === 'boolean') return value ? 'Да' : 'Нет';
  if (typeof value === 'number') return value.toFixed(2);
  // Объекты мы теперь будем обрабатывать отдельно, так что эта проверка не нужна
  // if (typeof value === 'object' && value !== null) return JSON.stringify(value);
  return String(value);
};


// --- Основной компонент с измененной логикой рендеринга ---

const ComponentCard = ({ name, type, data, mode, onModeToggle }) => {
  
  const isManualMode = mode === 'MANUAL';
  const isButtonDisabled = mode === 'N/A';
  const buttonText = isManualMode ? 'Вернуть в режим OPC' : 'Переключить в ручной';
  const cardClasses = `component-card ${isManualMode ? 'manual-mode' : ''}`;
  const displayName = getDisplayName(name, type);

  return (
    <div className={cardClasses}>
      <h3 className="component-title">{displayName}</h3>
      
      <div className="component-params">
        {data && Object.entries(data).map(([key, value]) => {
          // --- НОВАЯ ЛОГИКА ДЛЯ КРАСИВОГО СПИСКА ---

          // 1. Проверяем, является ли значение вложенным объектом (как temperatures)
          if (typeof value === 'object' && value !== null) {
            return (
              // Используем React.Fragment, чтобы не создавать лишний div
              <React.Fragment key={key}>
                <div className="param-row param-group-header">
                  <span>{PARAM_NAMES[key] || key}:</span>
                </div>
                <div className="param-nested-list">
                  {Object.entries(value).map(([nestedKey, nestedValue]) => (
                    <div key={nestedKey} className="param-row nested">
                      <span>{nestedKey}:</span>
                      <strong>{formatValue(nestedKey, nestedValue)}</strong>
                    </div>
                  ))}
                </div>
              </React.Fragment>
            );
          }
          
          // 2. Если это обычный параметр, рендерим его как и раньше
          return (
            <div key={key} className="param-row">
              <span>{PARAM_NAMES[key] || key}:</span>
              <strong>{formatValue(key, value)}</strong>
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