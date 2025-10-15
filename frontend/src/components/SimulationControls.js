// src/components/SimulationControls.js
import React from 'react';

const SimulationControls = ({ simulationMode, onPause, onResume, onSync }) => {
  const isRunning = simulationMode === 'running';

  return (
    <div className="simulation-controls">
      <h2>Управление симуляцией</h2>
      <p>
        Статус: <strong>{isRunning ? 'Работает' : 'На паузе'}</strong>
      </p>
      <div className="buttons">
        <button onClick={onPause} disabled={!isRunning}>
          Пауза
        </button>
        <button onClick={onResume} disabled={isRunning}>
          Возобновить
        </button>
        <button onClick={onSync} className="sync-button">
          Синхронизировать с OPC
        </button>
      </div>
    </div>
  );
}; // <-- ВОТ ИСПРАВЛЕНИЕ. Закрывающая скобка и точка с запятой возвращены.

export default SimulationControls;