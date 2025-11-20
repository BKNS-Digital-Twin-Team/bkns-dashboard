// src/pages/SessionSelector.js

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as api from '../api/twinApi';

const SessionSelector = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const [versionInfo, setVersionInfo] = useState(null);
  const [versionLoading, setVersionLoading] = useState(true);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        setLoading(true);
        const response = await api.getAvailableSessions();
        setSessions(response.data);
        setError(null);
      } catch (err) {
        console.error("Ошибка при получении списка сессий:", err);
        setError("Не удалось получить список сессий с сервера.");
      } finally {
        setLoading(false);
      }
    };

    const fetchVersion = async () => {
      try {
        const response = await api.getAppVersion();
        setVersionInfo(response.data);
      } catch (err) {
        console.error("Ошибка при получении версии:", err);
        // Не устанавливаем ошибку, так как версия не критична
      } finally {
        setVersionLoading(false);
      }
    };

    fetchSessions();
    fetchVersion();
  }, []);

  const handleSessionClick = async (sessionName, status) => {
    if (status === 'active') {
      // Если сессия уже активна, просто переходим к её панели управления
      navigate(`/session/${sessionName}`);
    } else {
      // Если неактивна, сначала отправляем запрос на загрузку
      try {
        await api.loadSession(sessionName);
        // После успешной загрузки переходим на страницу сессии
        navigate(`/session/${sessionName}`);
      } catch (err) {
        console.error(`Ошибка при загрузке сессии ${sessionName}:`, err);
        // Отображаем ошибку пользователю
        alert(`Не удалось загрузить сессию: ${err.response?.data?.detail || err.message}`);
      }
    }
  };

  if (loading) return <div>Загрузка списка сессий...</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <div>
      <div className="session-selector-container">
        <h1 className="title">Выбор сессии симуляции</h1>
        <div className="session-list">
          {sessions.length > 0 ? (
            sessions.map(session => (
              <div
                key={session.name}
                className="session-card"
                onClick={() => handleSessionClick(session.name, session.status)}
              >
                <h2 className="session-name">{session.name}</h2>
                <div className="session-status">
                  Статус:
                  <span className={`status-badge status-${session.status}`}>
                    {session.status === 'active' ? 'Активна' : 'Неактивна'}
                  </span>
                </div>
                <button className="enter-button">
                  {session.status === 'active' ? 'Войти' : 'Загрузить и войти'}
                </button>
              </div>
            ))
          ) : (
            <p>Доступных сессий не найдено. Убедитесь, что они есть в папке `backend/sessions`.</p>
          )}
        </div>
      </div>
        <div className="version-info" style={{ 
        marginTop: '20px', 
        textAlign: 'center', 
        color: '#666',
        padding: '10px',
        borderTop: '1px solid #eee'
      }}>
        {versionLoading ? (
          <p>Загрузка информации о версии...</p>
        ) : versionInfo ? (
          <p>
            Версия приложения: <strong>
              {versionInfo.backend_version || versionInfo.version || 'неизвестна'}
            </strong>
            {versionInfo.build_date && ` (сборка от ${versionInfo.build_date})`}
          </p>
        ) : (
          <p>Версия приложения: неизвестна</p>
        )}
      </div>
    </div>  
  );
};

export default SessionSelector;