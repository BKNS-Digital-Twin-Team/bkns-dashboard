// src/App.test.js

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import App from './App';
import * as api from './api/twinApi';

// --- ИЗМЕНЕНИЕ 1: Включаем фальшивые таймеры для всего файла ---
// Это позволит нам контролировать setInterval и setTimeout в тестах.
jest.useFakeTimers();

jest.mock('./api/twinApi');

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should render dashboard with data after successful fetch', async () => {
    const mockStatus = {
      pumps: { pump_1: { status: 'on' } },
      valves: { valve_1: { status: 'open' } },
      oil_systems: { oil_1: { level: 'normal' } },
      pipes: {
        main_inlet: { pressure: 1.5 }, // <-- Данные остаются прежними
        main_outlet: { pressure: 5.2 },
      },
    };
    const mockModes = { pump_1: 'MANUAL' };
    const mockSimMode = { status: 'running' };

    api.getSimulationStatus.mockResolvedValueOnce({ data: mockStatus });
    api.getControlModes.mockResolvedValueOnce({ data: mockModes });
    api.getSimulationMode.mockResolvedValueOnce({ data: mockSimMode });

    render(<App />);

    expect(screen.getByText(/Загрузка данных с симуляции/i)).toBeInTheDocument();

    await screen.findByText(/Насосы/i);

    expect(screen.getByText(/Панель управления цифровым двойником БКНС/i)).toBeInTheDocument();
    expect(screen.getByText(/Клапаны/i)).toBeInTheDocument();

    // --- ИЗМЕНЕНИЕ 2: Исправляем проверку текста в соответствии с реальным выводом ---
    expect(screen.getByText(/Давление на входе:/i).nextSibling).toHaveTextContent('1.50 МПа');
    expect(screen.getByText(/Давление на выходе:/i).nextSibling).toHaveTextContent('5.20 МПа');

    expect(screen.queryByText(/Загрузка данных с симуляции/i)).not.toBeInTheDocument();
  });

  test('should display error message on API failure', async () => {
    // --- ИЗМЕНЕНИЕ 3: Временно "отключаем" console.error, чтобы не засорять лог ---
    // Это хорошая практика для тестов, где мы намеренно вызываем ошибку.
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    api.getSimulationStatus.mockRejectedValueOnce(new Error('Network Error'));
    api.getControlModes.mockResolvedValueOnce({ data: {} });
    api.getSimulationMode.mockResolvedValueOnce({ data: { status: 'stopped' } });
    
    render(<App />);

    const errorMessage = await screen.findByText(/Не удалось подключиться к серверу симуляции/i);
    expect(errorMessage).toBeInTheDocument();
    expect(screen.queryByText(/Насосы/i)).not.toBeInTheDocument();
    
    // Возвращаем console.error к нормальной работе
    consoleErrorSpy.mockRestore();
  });

  test('should call pauseSimulation API when pause button is clicked', async () => {
    api.getSimulationStatus.mockResolvedValue({ data: { pipes: {} } });
    api.getControlModes.mockResolvedValue({ data: {} });
    api.getSimulationMode.mockResolvedValue({ data: { status: 'running' } });
    api.pauseSimulation.mockResolvedValue({ data: { status: 'paused' } });

    render(<App />);
    
    const pauseButton = await screen.findByRole('button', { name: /Пауза/i });
    fireEvent.click(pauseButton);

    expect(api.pauseSimulation).toHaveBeenCalledTimes(1);
  });
});