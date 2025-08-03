// src/api/twinApi.js
import axios from 'axios';

const API_BASE_URL = '/api'; // URL вашего FastAPI сервера

// Создаем экземпляр axios, который будет использоваться для всех запросов
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Получить полное состояние модели
export const getSimulationStatus = () => {
  return apiClient.get('/simulation/status');
};

// Получить режимы управления
export const getControlModes = () => {
  return apiClient.get('/simulation/control_modes');
};

// Получить режим работы симуляции (running/paused)
export const getSimulationMode = () => {
  return apiClient.get('/simulation/mode');
};

// Поставить симуляцию на паузу
export const pauseSimulation = () => {
  return apiClient.post('/simulation/pause');
};

// Возобновить симуляцию
export const resumeSimulation = () => {
  return apiClient.post('/simulation/resume');
};

export const setControlMode = (componentName, source) => {
  // Отправляем на новый, специальный эндпоинт для смены режима
  return apiClient.post('/simulation/control/set_source', {
	source: source, 
	component: componentName,
  });
};

export const syncWithOpc = () => {
  return apiClient.post('/simulation/sync');
};

export const sendManualCommand = (component, param, value) => {
  return apiClient.post('/simulation/control/manual', {
    source: 'MANUAL',
    component,
    param,
    value
  });
};