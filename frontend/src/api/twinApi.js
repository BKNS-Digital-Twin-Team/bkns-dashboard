// src/api/twinApi.js

import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000/api",
});

export default api;

// Получить полное состояние модели
export const getSimulationStatus = () => {
  return api.get('/simulation/status');
};

// Получить режимы управления
export const getControlModes = () => {
  return api.get('/simulation/control_modes');
};

// Получить режим работы симуляции (running/paused)
export const getSimulationMode = () => {
  return api.get('/simulation/mode');
};

// Поставить симуляцию на паузу
export const pauseSimulation = () => {
  return api.post('/simulation/pause');
};

// Возобновить симуляцию
export const resumeSimulation = () => {
  return api.post('/simulation/resume');
};

export const setControlMode = (componentName, source) => {
  // Отправляем на новый, специальный эндпоинт для смены режима
  return api.post('/simulation/control/set_source', {
	source: source, 
	component: componentName,
  });
};

export const syncWithOpc = () => {
  return api.post('/simulation/sync');
};

export const sendManualCommand = (component, param, value) => {
  return api.post('/simulation/control/manual', {
    source: 'MANUAL',
    component,
    param,
    value
  });
};

export const sendManualOverrides = (component, overrides) => {
  return api.post('/simulation/control/overrides', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      component: component,
      overrides: overrides
    })
  });
};
