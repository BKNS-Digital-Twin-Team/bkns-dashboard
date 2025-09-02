// Файл: src/components/ComponentCard.js

import React, { useState } from 'react';
// --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
// Импортируем нашу НОВУЮ функцию в единственном числе
import * as api from '../api/twinApi';
// "Красивые" имена для параметров на русском языке
const PARAM_NAMES = {
  // Команды управления насосом
  'start': { name: 'Команда на запуск насоса', unit: '' },
  'stop': { name: 'Команда на стоп насоса', unit: '' },
  'on': { name: 'Насос включен', unit: '' },
  'off': { name: 'Насос выключен', unit: '' },
  
  // Параметры двигателя
  'motor_i': { name: 'Рабочий ток двигателя', unit: 'А' },
  
  // Давления
  'pressure_in': { name: 'Давление на входе', unit: 'бар' },
  'pressure_out': { name: 'Давление на выходе', unit: 'бар' },
  'AI_P_Oil_Nas_n': { name: 'Давление в маслосистеме насоса', unit: 'бар' },
  
  // Температуры насоса
  'AI_T_1_n': { name: 'Температура рабочего подшипника насоса', unit: '°C' },
  'AI_T_2_n': { name: 'Температура полевого подшипника насоса', unit: '°C' },
  
  // Температуры двигателя
  'AI_T_3_n': { name: 'Температура рабочего подшипника двигателя', unit: '°C' },
  'AI_T_4_n': { name: 'Температура полевого подшипника двигателя', unit: '°C' },
  
  // Температуры системы
  'AI_T_5_n': { name: 'Температура воды в гидропяте', unit: '°C' },
  
  // Расход
  'AI_Qmom_n': { name: 'Мгновенный расход жидкости', unit: 'м³/ч' },
  
  // Состояния и флаги
  'DI_kojuh': { name: 'Открытие кожуха муфты', unit: '' },
  'DI_FL_MS': { name: 'Флаг работы маслосистемы', unit: '' },
  'DI_FL_MS_P': { name: 'Флаг достаточного давления в маслосистеме', unit: '' },
  
  // Задвижки
  'DI_Zadv_Open': { name: 'Концевик открытия задвижки', unit: '' },
  'DI_Zadv_Close': { name: 'Концевик закрытия задвижки', unit: '' },
  'CMD_Zadv_Open': { name: 'Команда на открытие задвижки', unit: '' },
  'CMD_Zadv_Close': { name: 'Команда на закрытие задвижки', unit: '' },
  
  // Управление маслосистемой
  'oil_motor_start': { name: 'Команда на запуск маслонасоса', unit: '' },
  'oil_motor_stop': { name: 'Команда на остановку маслонасоса', unit: '' }
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
                      <td>{PARAM_NAMES[key.split('_',1)]?.name}</td>
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