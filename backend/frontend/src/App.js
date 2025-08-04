// src/App.js

import React, { useState, useEffect, useCallback } from 'react';
import * as api from './api/twinApi';
import ComponentCard from './components/ComponentCard';
import SimulationControls from './components/SimulationControls';
// --- 1. ИМПОРТИРУЕМ НОВЫЙ КОМПОНЕНТ ---
import SystemStatus from './components/SystemStatus';
import './App.css';

function App() {
  // ... (все твои хуки useState, useEffect, функции-обработчики остаются без изменений) ...
  const [modelStatus, setModelStatus] = useState(null);
  const [controlModes, setControlModes] = useState({});
  const [simulationMode, setSimulationMode] = useState('running');
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [statusRes, modesRes, simModeRes] = await Promise.all([
        api.getSimulationStatus(),
        api.getControlModes(),
        api.getSimulationMode(),
      ]);
      
      setModelStatus(statusRes.data);
      setControlModes(modesRes.data);
      setSimulationMode(simModeRes.data.status);
      setError(null);
    } catch (err) {
      console.error("Ошибка при получении данных с сервера:", err);
      setError("Не удалось подключиться к серверу симуляции. Убедитесь, что он запущен.");
    }
  }, []);

  useEffect(() => {
    fetchData();
    const intervalId = setInterval(fetchData, 2000);
    return () => clearInterval(intervalId);
  }, [fetchData]);

  const handleModeToggle = useCallback(async (fullComponentName, currentMode) => {
    const targetMode = currentMode === 'MANUAL' ? 'MODEL' : 'MANUAL';
    try {
      await api.setControlMode(fullComponentName, targetMode);
      fetchData();
    } catch (err) {
      console.error(`Ошибка при переключении режима для ${fullComponentName}:`, err);
      setError(`Не удалось переключить режим для ${fullComponentName}.`);
    }
  }, [fetchData]);

  const handlePause = async () => {
    try {
      await api.pauseSimulation();
      fetchData();
    } catch (err) {
      console.error("Ошибка при постановке на паузу:", err);
      setError("Не удалось поставить симуляцию на паузу.");
    }
  };

  const handleResume = async () => {
    try {
      await api.resumeSimulation();
      fetchData();
    } catch (err) {
      console.error("Ошибка при возобновлении симуляции:", err);
      setError("Не удалось возобновить симуляцию.");
    }
  };
  
   const handleSync = async () => {
    try {
      console.log("Запускаем синхронизацию...");
      await api.syncWithOpc();
      // Можно добавить уведомление для пользователя
      alert("Синхронизация с OPC-сервером запущена!");
    } catch (err) {
      console.error("Ошибка при запуске синхронизации:", err);
      setError("Не удалось запустить синхронизацию.");
    }
  };

  const renderComponents = (components, type) => {
    if (!components) return null;
    return Object.entries(components).map(([name, data]) => {
      const fullComponentName = `${type}_${name}`;
      const currentMode = controlModes[fullComponentName] || 'N/A';
  
      return (
        <ComponentCard
          key={fullComponentName}
          name={name}
          data={data}
          mode={currentMode}
          type={type}
          onModeToggle={() => handleModeToggle(fullComponentName, controlModes[fullComponentName])}
		  onSync={handleSync}
        />
      );
    });
  };

  // --- 2. ГОТОВИМ ДАННЫЕ ДЛЯ НОВОГО КОМПОНЕНТА ---
  // Безопасно извлекаем данные о давлении. Если modelStatus еще не загрузился,
  // или в нем нет pipes, переменные будут undefined, и компонент это обработает.
  const inletPressure = modelStatus?.pipes?.main_inlet?.pressure;
  const outletPressure = modelStatus?.pipes?.main_outlet?.pressure;

  return (
    <div className="App">
      <header className="App-header">
        <h1>Панель управления цифровым двойником БКНС</h1>
      </header>

      {error && <div className="error-message">{error}</div>}

      <div className="top-panels">
        <SimulationControls
          mode={simulationMode}
          onPause={handlePause}
          onResume={handleResume}
        />
        {/* --- 3. ВСТАВЛЯЕМ НОВЫЙ КОМПОНЕНТ И ПЕРЕДАЕМ ДАННЫЕ --- */}
        <SystemStatus
          inletPressure={inletPressure}
          outletPressure={outletPressure}
        />
      </div>


      {modelStatus ? (
        <>
          <h2>Насосы</h2>
          <div className="components-grid">
            {renderComponents(modelStatus.pumps, 'pump')}
          </div>
          
          <h2>Клапаны</h2>
          <div className="components-grid">
            {renderComponents(modelStatus.valves, 'valve')}
          </div>
          
          <h2>Маслосистемы</h2>
          <div className="components-grid">
            {renderComponents(modelStatus.oil_systems, 'oil_system')}
          </div>
        </>
      ) : (
        !error && <p>Загрузка данных с симуляции...</p>
      )}
    </div>
  );
}

export default App;