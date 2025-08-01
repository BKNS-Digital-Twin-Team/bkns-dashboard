// src/components/SystemStatus.js

import React from 'react';

const SystemStatus = ({ inletPressure, outletPressure }) => {
  // Проверяем, что данные пришли, чтобы не отображать NaN
  const hasInletData = inletPressure !== undefined && inletPressure !== null;
  const hasOutletData = outletPressure !== undefined && outletPressure !== null;

  return (
    <div className="system-status-panel">
      <h2>Общее состояние системы</h2>
      <div className="status-metrics">
        <div className="metric-item">
          <span className="metric-label">Давление на входе:</span>
          <span className="metric-value">
            {hasInletData ? inletPressure.toFixed(2) : '---'} МПа
          </span>
        </div>
        <div className="metric-item">
          <span className="metric-label">Давление на выходе:</span>
          <span className="metric-value">
            {hasOutletData ? outletPressure.toFixed(2) : '---'} МПа
          </span>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;