// src/App.test.js

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import App from './App';
// Импортируем наш API, чтобы его "замокать" (подменить)
import * as api from './api/twinApi';

// Говорим Jest: "Каждый раз, когда в коде встречается import * from './api/twinApi',
// используй не настоящий файл, а его поддельную версию".
// Это самый важный шаг для тестирования компонентов с API-вызовами.
jest.mock('./api/twinApi');

// Группа тестов для нашего главного компонента App
describe('App Component', () => {

  // Перед каждым тестом очищаем все предыдущие "моки", чтобы тесты не влияли друг на друга
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Тест №1: Проверяем "счастливый путь" - данные успешно загрузились и отобразились
  test('should render dashboard with data after successful fetch', async () => {
    // --- 1. Arrange (Подготовка) ---
    // Готовим фальшивые данные, которые якобы вернет наш API
    const mockStatus = {
      pumps: { pump_1: { status: 'on' } },
      valves: { valve_1: { status: 'open' } },
      oil_systems: { oil_1: { level: 'normal' } },
      pipes: {
        main_inlet: { pressure: 1.5 },
        main_outlet: { pressure: 5.2 },
      },
    };
    const mockModes = { pump_1: 'MANUAL' };
    const mockSimMode = { status: 'running' };

    // Указываем, что при вызове наши "моки" должны вернуть подготовленные данные
    api.getSimulationStatus.mockResolvedValueOnce({ data: mockStatus });
    api.getControlModes.mockResolvedValueOnce({ data: mockModes });
    api.getSimulationMode.mockResolvedValueOnce({ data: mockSimMode });

    // --- 2. Act (Действие) ---
    // Рендерим наш компонент
    render(<App />);

    // --- 3. Assert (Проверка) ---
    // Сначала проверяем, что пользователь видит текст загрузки
    expect(screen.getByText(/Загрузка данных с симуляции/i)).toBeInTheDocument();

    // Ждем, пока на экране появится заголовок "Насосы".
    // Это будет означать, что асинхронный вызов API завершился и данные отрендерились.
    await screen.findByText(/Насосы/i);

    // Теперь проверяем, что все отображается корректно
    expect(screen.getByText(/Панель управления цифровым двойником БКНС/i)).toBeInTheDocument();
    expect(screen.getByText(/Клапаны/i)).toBeInTheDocument();

    // Проверяем, что данные для SystemStatus (давление) были переданы и отображены
    // Находим метку "Давление на входе:", смотрим на следующий элемент и проверяем его текст
    expect(screen.getByText(/Давление на входе:/i).nextSibling).toHaveTextContent('1.5 МПа');
    expect(screen.getByText(/Давление на выходе:/i).nextSibling).toHaveTextContent('5.2 МПа');

    // Убедимся, что текст загрузки исчез
    expect(screen.queryByText(/Загрузка данных с симуляции/i)).not.toBeInTheDocument();
  });


  // Тест №2: Проверяем "печальный путь" - сервер вернул ошибку
  test('should display error message on API failure', async () => {
    // --- 1. Arrange ---
    // Указываем, что один из вызовов API должен завершиться с ошибкой
    api.getSimulationStatus.mockRejectedValueOnce(new Error('Network Error'));
    api.getControlModes.mockResolvedValueOnce({ data: {} });
    api.getSimulationMode.mockResolvedValueOnce({ data: { status: 'stopped' } });
    
    // --- 2. Act ---
    render(<App />);

    // --- 3. Assert ---
    // Ждем, пока на экране появится наше сообщение об ошибке для пользователя
    const errorMessage = await screen.findByText(/Не удалось подключиться к серверу симуляции/i);
    expect(errorMessage).toBeInTheDocument();

    // Проверяем, что заголовки секций (Насосы, Клапаны) НЕ отображаются,
    // так как данные для них мы не получили
    expect(screen.queryByText(/Насосы/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Клапаны/i)).not.toBeInTheDocument();
  });


  // Тест №3: Проверяем интерактивность - нажатие на кнопку "Пауза"
  test('should call pauseSimulation API when pause button is clicked', async () => {
    // --- 1. Arrange ---
    // Снова настраиваем "счастливый путь", чтобы компонент отрендерился полностью
    api.getSimulationStatus.mockResolvedValue({ data: { pipes: {} } });
    api.getControlModes.mockResolvedValue({ data: {} });
    api.getSimulationMode.mockResolvedValue({ data: { status: 'running' } });
    api.pauseSimulation.mockResolvedValue({ data: { status: 'paused' } }); // Мок для самой кнопки

    // --- 2. Act ---
    render(<App />);
    
    // Ждем, пока кнопка "Пауза" появится на экране
    const pauseButton = await screen.findByRole('button', { name: /Пауза/i });
    
    // Имитируем клик по кнопке
    fireEvent.click(pauseButton);

    // --- 3. Assert ---
    // Проверяем, что наша поддельная функция api.pauseSimulation была вызвана ровно 1 раз
    expect(api.pauseSimulation).toHaveBeenCalledTimes(1);
  });
});