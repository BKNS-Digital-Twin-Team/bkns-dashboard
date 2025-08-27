import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import * as api from '../api/twinApi';
import ComponentCard from '../components/ComponentCard';
import SimulationControls from '../components/SimulationControls';
import SystemStatus from '../components/SystemStatus';

function Dashboard() {
  const { sessionId } = useParams();
  const [modelStatus, setModelStatus] = useState({ pumps: {}, valves: {}, oil_systems: {} });
  const [controlModes, setControlModes] = useState({});
  const [simulationMode, setSimulationMode] = useState(null);
  const [error, setError] = useState(null);

  const [inletPressure, setInletPressure] = useState(115.2);
  const [outletPressure, setOutletPressure] = useState(115.2);

  // Оборачиваем fetchData в useCallback, чтобы функция не создавалась заново при каждом рендере.
  // Это важно для стабильной работы useEffect.
  const fetchData = useCallback(async () => {
    if (!sessionId) return;

    try {
      // Используем Promise.allSettled для параллельного выполнения всех запросов.
      // Он не прервется, если один из запросов завершится с ошибкой.
      const results = await Promise.allSettled([
        api.getSimulationStatus(sessionId),
        api.getControlModes(sessionId),
        api.getSimulationMode(sessionId),
      ]);

      const statusResult = results[0];
      const modesResult = results[1];
      const simModeResult = results[2];
      // Главная проверка: если запрос статуса модели все еще возвращает 404,
      // значит сессия еще не готова.
      if (statusResult.status === 'rejected' && statusResult.reason?.response?.status === 404) {
        console.log(`Сессия '${sessionId}' еще не готова (404 Not Found). Повторная попытка...`);
        setError(`Сессия '${sessionId}' загружается...`);
        return; // Прерываем выполнение до следующей попытки
      }

      // Если запрос статуса вернул любую другую ошибку, сообщаем о ней.
      if (statusResult.status === 'rejected') {
        console.error("Ошибка при получении статуса модели:", statusResult.reason);
        setError(`Не удалось получить статус сессии '${sessionId}'.`);
        return;
      }

      // --- Если мы здесь, значит статус модели успешно получен ---
      setError(null); // Сбрасываем все предыдущие ошибки и сообщения о загрузке.




      // 1. Обрабатываем статус модели (мы знаем, что он успешен)
      const flatData = statusResult.value.data || {}; // Добавлена проверка на components
      const grouped = { pumps: {}, valves: {}, oil_systems: {} };
      for (const [key, value] of Object.entries(flatData)) {
        if (key.startsWith("pump_"))grouped.pumps[key] = value; 
        else if (key.startsWith("valve_out_")) grouped.valves[key] = value;
        else if (key.startsWith("oil_system_")) grouped.oil_systems[key] = value;
      }
      setModelStatus(grouped);

      let totalInPressure = 0;
      let totalOutPressure = 0;
      for (const [pump,param] of Object.entries(grouped.pumps)){
        if (param.pressure_in) totalInPressure += param.pressure_in;
        if (param.pressure_in) totalOutPressure += param.pressure_out;
      }
      setInletPressure(totalInPressure);
      setOutletPressure(totalOutPressure);

      // 2. Обрабатываем режимы управления (если запрос был успешен)
      if (modesResult.status === 'fulfilled') {
        setControlModes(modesResult.value.data);
      }

      // 3. Обрабатываем режим симуляции (если запрос был успешен)
      if (simModeResult.status === 'fulfilled') {
        setSimulationMode(simModeResult.value.data.status);
      }

    } catch (err) {
      console.error("Произошла критическая ошибка в fetchData:", err);
      setError("Произошла непредвиденная ошибка. Проверьте консоль.");
    }
  }, [sessionId]); // Зависимость только от sessionId

  // Хук для периодического вызова fetchData
  useEffect(() => {
    fetchData(); // Вызываем сразу при загрузке
    const interval = setInterval(fetchData, 2000); // И далее каждые 2 секунды

    // Функция очистки при размонтировании компонента
    return () => clearInterval(interval);
  }, [fetchData]); // Зависимость от memoized-функции fetchData

  return (
    <div className="App">
      <h1 >Панель управления: Сессия '{sessionId}'</h1>
      
      <div className="simulation-controls">
        <SimulationControls
          sessionId={sessionId}
          simulationMode={simulationMode}
          onStateChange={fetchData}
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      <SystemStatus 
        status={modelStatus}
        inletPressure={inletPressure}
        outletPressure={outletPressure}
      />

      <div className="component-section">
        <h2 >Насосы</h2>
        <div className="components-grid">
          {Object.entries(modelStatus.pumps || {}).map(([key, value]) => (
            <ComponentCard key={key} name={key} data={value} sessionId={sessionId} controlModes={controlModes} onUpdate={fetchData} />
          ))}
        </div>
      </div>

      <div className="component-section">
        <h2>Выходные задвижки</h2>
        <div className="components-grid">
          {Object.entries(modelStatus.valves || {}).map(([key, value]) => (
            <ComponentCard key={key} name={key} data={value} sessionId={sessionId} controlModes={controlModes} onUpdate={fetchData} />
          ))}
        </div>
      </div>

      <div className="component-section">
        <h2>Маслосистемы</h2>
        <div className="components-grid">
          {Object.entries(modelStatus.oil_systems || {}).map(([key, value]) => (
            <ComponentCard key={key} name={key} data={value} sessionId={sessionId} controlModes={controlModes} onUpdate={fetchData} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;