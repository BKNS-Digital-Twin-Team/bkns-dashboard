// src/App.js

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom'; // Импортируем useParams и Link
import * as api from '../api/twinApi';
import ComponentCard from '../components/ComponentCard';
import SimulationControls from '../components/SimulationControls';
import SystemStatus from '../components/SystemStatus';

function Dashboard() {
  const { sessionId } = useParams(); // Получаем ID сессии из URL
  const [modelStatus, setModelStatus] = useState({});
  const [controlModes, setControlModes] = useState({});
  const [simulationMode, setSimulationMode] = useState(null);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    if (!sessionId) return;
    try {
      const [statusRes, modesRes, simModeRes] = await Promise.all([
        api.getSimulationStatus(sessionId),
        api.getControlModes(sessionId),
        api.getSimulationMode(sessionId),
      ]);

      const flatData = statusRes.data;

      const grouped = {
        pumps: {},
        valves: {},
        oil_systems: {}
      };

      for (const [key, value] of Object.entries(flatData)) {
        if (key.startsWith("pump_")) grouped.pumps[key] = value;
        else if (key.startsWith("valve_out_")) grouped.valves[key] = value;
        else if (key.startsWith("oil_system_")) grouped.oil_systems[key] = value;
      }

      setModelStatus(grouped);
      setControlModes(modesRes.data);
      setSimulationMode(simModeRes.data.status);
      setError(null);
    } catch (err) {
      console.error("Ошибка при получении данных с сервера:", err);
      setError(`Не удалось подключиться к сессии '${sessionId}'. Убедитесь, что она запущена.`);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <div className="App">
      <h1 className="text-2xl font-bold mb-4">Панель управления цифровым двойником БКНС</h1>

      <SimulationControls
      sessionId={sessionId}
      fetchData={fetchData}
      controlModes={controlModes}
      simulationMode={simulationMode}
      setSimulationMode={setSimulationMode}
      onPause={async () => {
        await api.pauseSimulation(sessionId);
        fetchData();
      }}
      onResume={async () => {
        console.log("onResume вызван");
        try {
          const response = await api.resumeSimulation(sessionId);
          console.log("Ответ от /resume:", response.data);

          // Подождать чуть-чуть, чтобы сервер успел обновить состояние
          await new Promise((resolve) => setTimeout(resolve, 300));

          await fetchData();
        } catch (err) {
          console.error("Ошибка при возобновлении:", err);
        }
      }}
    />

      {error && <div className="text-red-500">{error}</div>}

      <SystemStatus status={modelStatus} />

      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Насосы</h2>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(modelStatus.pumps || {}).map(([key, value]) => (
            <ComponentCard key={key} name={key} data={value} sessionId={sessionId}/>
          ))}
        </div>
      </div>

      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Клапаны</h2>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(modelStatus.valves || {}).map(([key, value]) => (
            <ComponentCard key={key} name={key} data={value} sessionId={sessionId}/>
          ))}
        </div>
      </div>

      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Маслосистемы</h2>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(modelStatus.oil_systems || {}).map(([key, value]) => (
            <ComponentCard key={key} name={key} data={value} sessionId={sessionId}/>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
