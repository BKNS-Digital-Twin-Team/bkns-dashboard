// src/api/twinApi.js

import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000/api",
});

export default api;

// --- НОВАЯ ФУНКЦИЯ ---
// Получить список всех доступных сессий
export const getAvailableSessions = () => {
  return api.get('/simulation/sessions/available');
};

// --- НОВАЯ ФУНКЦИЯ ---
// Загрузить (активировать) сессию на бэкенде
export const loadSession = (session_name) => {
  return api.post('/simulation/session/load', { session_name });
};


// Получить полное состояние модели
export const getSimulationStatus = (sessionId) => {
  return api.get(`/simulation/${sessionId}/status`);
};

// Получить режимы управления
export const getControlModes = (sessionId) => {
  return api.get(`/simulation/${sessionId}/control_modes`);
};

// Получить режим работы симуляции (running/paused)
export const getSimulationMode = (sessionId) => {
  return api.get(`/simulation/${sessionId}/state`); // ИСПРАВЛЕНО: эндпоинт был /mode, а в коде /state
};


// Поставить симуляцию на паузу
export const pauseSimulation = (sessionId) => {
  return api.post(`/simulation/${sessionId}/pause`);
};

// Возобновить симуляцию
export const resumeSimulation = (sessionId) => {
  return api.post(`/simulation/${sessionId}/resume`);
};


export const setControlMode = (sessionId, componentName, source) => {
  return api.post(`/simulation/${sessionId}/control/set_source`, {
	source: source, 
	component: componentName,
  });
};

export const syncWithOpc = (sessionId) => {
  return api.post(`/simulation/${sessionId}/sync`);
};

export const sendManualCommand = (sessionId, component, param, value) => {
  return api.post(`/simulation/${sessionId}/control/manual`, {
    source: 'MANUAL',
    component,
    param,
    value
  });
};

export const setManualOverride = (sessionId, component, param, value) => {
  return api.post(`/simulation/${sessionId}/control/overrides/set`, {
    component,
    param,
    value
  });
};

export const clearManualOverride = (sessionId, component, param) => {
  return api.post(`/simulation/${sessionId}/control/overrides/clear`, {
    component,
    param,
  });
};