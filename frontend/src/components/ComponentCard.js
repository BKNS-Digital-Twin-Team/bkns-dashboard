// Файл: src/components/ComponentCard.js

import React, { useState } from 'react';
// --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
// Импортируем нашу НОВУЮ функцию в единственном числе
import * as api from '../api/twinApi';
// "Красивые" имена для параметров на русском языке
const PARAM_NAMES = {
  // Параметры насоса
  'na_on': { name: 'Насос включен', unit: '' },
  'na_off': { name: 'Насос выключен', unit: '' },
  'motor_current': { name: 'Ток двигателя', unit: 'А' },
  'flow_rate': { name: 'Расход', unit: 'м³/ч' },
  'pressure_in': { name: 'Давление на входе', unit: 'бар' },
  'pressure_out': { name: 'Давление на выходе', unit: 'бар' },
  'temp_bearing_1': { name: 'Температура подшипника 1', unit: '°C' },
  'temp_bearing_2': { name: 'Температура подшипника 2', unit: '°C' },
  'temp_motor_1': { name: 'Температура двигателя 1', unit: '°C' },
  'temp_motor_2': { name: 'Температура двигателя 2', unit: '°C' },
  'temp_water': { name: 'Температура воды', unit: '°C' },
  'cover_open': { name: 'Крышка открыта', unit: '' },
  
  // Параметры задвижек
  'valve_open': { name: 'Задвижка открыта', unit: '' },
  'valve_closed': { name: 'Задвижка закрыта', unit: '' },
  
  // Параметры маслосистемы
  'oil_sys_running': { name: 'Маслосистема работает', unit: '' },
  'oil_sys_pressure_ok': { name: 'Давление в норме', unit: '' },
  'oil_pressure': { name: 'Давление масла', unit: 'бар' },
  'temperature': { name: 'Температура', unit: '°C' }
};




// Пропсы `type`, `mode`, `onModeToggle` не используются в новой версии,
// но я оставлю их, если они нужны для другой логики.
const ComponentCard = ({ name, data, sessionId, onUpdate }) => {
  // Локальное состояние для хранения значений из полей ввода
  const [overrides, setOverrides] = useState({});
  const [appliedOverrides, setAppliedOverrides] = useState({});

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

    const successfullyApplied = {};
    const overridesToReset = []; 


    for (const [param, value] of Object.entries(overrides)) {
      
      if (value === '') {
        await api.clearManualOverride(sessionId, name, param);
        overridesToReset.push(param);

        setAppliedOverrides(prev => ({
          ...prev,
          [param]: false,
        }));

        continue;
      } 
      
      const parsedValue = parseFloat(value);
      if (!isNaN(parsedValue)) {
        try {
          // Вызываем ИСПРАВЛЕННУЮ функцию с правильными аргументами
          await api.setManualOverride(sessionId, name, param, parsedValue);
          console.log(`[OVERRIDE] Успешно: ${name}.${param} = ${parsedValue}`);
          successfullyApplied[param] = true;
        } catch (error) {
          console.error(`Ошибка отправки оверрайда для ${name}.${param}:`, error);
        }
      }
    }

    setAppliedOverrides(prev => ({
        ...prev,
        ...successfullyApplied
    }));

    // Просим родителя обновить все данные, чтобы увидеть результат
    if (onUpdate) {
      onUpdate();
    }
  };

  // Функция для проверки, было ли значение применено
  const isValueApplied = (param) => {
    return appliedOverrides[param] === true;
  };

  
  return (
    <div className="component-card">
      <div className="component-data">
        <h3 className="component-label">{name.replace(/_/g, ' ')}</h3>
        
        <table>
          <thead>
            <tr>
              <th>Параметр</th>
              <th>Название</th>
              <th>Знач.</th>
              <th>Ед.изм.</th>
              <th>Замена</th>
            </tr>
          </thead>

          <tbody>
            {data && Object.entries(data).map(([key, value]) => {
                if (typeof value !== 'number' && typeof value !== 'boolean') return null;

                const isOverridable = typeof value === 'number';
              
                if (overrides[key] !== undefined && overrides[key] !== '') {
                  // Для данного ключа есть переопределение
                  console.log(`Для ${key} установлено значение: ${overrides[key]}`);
                }

                const isOverride = (overrides[key] !== undefined && overrides[key] !== '');
                const isApplied = isValueApplied(key);

                return (
                  <tr key={key} className={`table-row 
                    ${isOverride ? 'overrided-row' : ''} 
                    ${isApplied ? 'accepted-overrided-row' : ''}`
                  } >
                      <td className="param-name">{key}:</td>
                      <td>{PARAM_NAMES[key]?.name}</td>
                      <td className={`param-value`}>
                        {typeof value === 'boolean' ? (value ? 'Да' : 'Нет') : value.toFixed(1)}
                      </td>
                      <td>{PARAM_NAMES[key]?.unit}</td>
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