// src/App.js

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SessionSelector from './pages/SessionSelector';
import Dashboard from './pages/Dashboard'; // Мы создадим его на следующем шаге
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Главная страница - выбор сессии */}
          <Route path="/" element={<SessionSelector />} />
          
          {/* Страница с панелью управления для конкретной сессии */}
          <Route path="/session/:sessionId" element={<Dashboard />} />

          {/* Редирект на главную, если введен некорректный путь */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;