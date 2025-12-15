import React, { useState, useCallback, useEffect } from 'react';
import { useAppState } from '../App';
import * as robotApi from '../services/robotApi';

const { GRAPH_TYPE_TO_API, GRAPH_TYPE_LABELS, GRAPH_TYPE_GROUPS } = robotApi;

function Tabs() {
  const { state, calculationResult, setCalculationResult, addLog, actions, calculateTrajectory, isCalculating } = useAppState();
  const [activeTab, setActiveTab] = useState('tabTrajectory');
  const [isReady, setIsReady] = useState(false);
  
  // Тип графика берём из настроек графика (graphSettings.coordType)
  const selectedGraphType = state.graphSettings?.coordType || 'general';
  const [plotImage, setPlotImage] = useState(null);
  const [workspaceImage, setWorkspaceImage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsReady(true);
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  const tabs = [
    { id: 'tabTrajectory', label: 'Траектория' },
    { id: 'tabWorkspace', label: 'Рабочая область' },
    { id: 'tabLog', label: 'Лог' },
  ];

  const handleTabClick = useCallback((tabId) => {
    setActiveTab(tabId);
  }, []);

  // Загрузить график (только изображение)
  const loadPlot = useCallback(async (graphType) => {
    setIsLoading(true);
    setError(null);
    try {
      // Преобразуем тип графика из настроек в API формат
      const apiPlotType = GRAPH_TYPE_TO_API[graphType] || 'obobshennie_coordinates';
      const result = await robotApi.getPlot(apiPlotType);
      if (result.success) {
        setPlotImage(result.image_base64);
      } else {
        setError('Не удалось загрузить график');
      }
    } catch (err) {
      setError(err.message || 'Ошибка загрузки графика');
      console.error('Error loading plot:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Пересчитать траекторию и обновить график
  const recalculateAndLoadPlot = useCallback(async (graphType) => {
    setIsLoading(true);
    setError(null);
    try {
      // Пересчитываем траекторию с текущими настройками (включая spline)
      await calculateTrajectory();
      
      // Затем загружаем график
      const apiPlotType = GRAPH_TYPE_TO_API[graphType] || 'obobshennie_coordinates';
      const result = await robotApi.getPlot(apiPlotType);
      if (result.success) {
        setPlotImage(result.image_base64);
      } else {
        setError('Не удалось загрузить график');
      }
    } catch (err) {
      setError(err.message || 'Ошибка расчёта/загрузки графика');
      console.error('Error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [calculateTrajectory]);

  // Загрузить рабочую область
  const loadWorkspace = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await robotApi.getWorkspace();
      if (result.success) {
        setWorkspaceImage(result.image_base64);
      } else {
        setError('Не удалось загрузить рабочую область');
      }
    } catch (err) {
      setError(err.message || 'Ошибка загрузки рабочей области');
      console.error('Error loading workspace:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Загрузка графика при изменении типа (из настроек графика)
  useEffect(() => {
    if (activeTab === 'tabTrajectory' && calculationResult) {
      loadPlot(selectedGraphType);
    }
  }, [selectedGraphType, calculationResult, activeTab, loadPlot]);

  // Загрузка рабочей области при переключении на вкладку
  useEffect(() => {
    if (activeTab === 'tabWorkspace' && calculationResult) {
      loadWorkspace();
    }
  }, [activeTab, calculationResult, loadWorkspace]);

  if (!isReady) {
    return (
      <>
        <div id="tabs" role="tablist" aria-label="Вкладки">
          {tabs.map(tab => (
            <div
              key={tab.id}
              className="tab"
              role="tab"
              aria-selected={activeTab === tab.id}
            >
              {tab.label}
            </div>
          ))}
        </div>
        <div id="tabContent" style={{ minHeight: '400px' }}></div>
      </>
    );
  }

  // Форматирование чисел
  const formatNumber = (num, decimals = 4) => {
    if (num === null || num === undefined) return '—';
    return Number(num).toFixed(decimals);
  };

  return (
    <>
      <div id="tabs" role="tablist" aria-label="Вкладки">
        {tabs.map(tab => (
          <div
            key={tab.id}
            className="tab"
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => handleTabClick(tab.id)}
          >
            {tab.label}
          </div>
        ))}
      </div>
      <div id="tabContent">
        {/* Вкладка Траектория */}
        <section id="tabTrajectory" data-active={activeTab === 'tabTrajectory'}>
          <div className="trajectory-controls">
            <div className="current-graph-type">
              <span className="graph-type-label">Тип графика:</span>
              <span className="graph-type-value">
                {GRAPH_TYPE_LABELS[selectedGraphType] || 'Обобщённые от времени'}
                {state.graphSettings?.showSpline && <span className="spline-indicator"> (Сплайн)</span>}
              </span>
            </div>
            
            <button 
              onClick={() => actions.show_graph_settings_dialog()}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                background: '#667eea',
                color: 'white',
                cursor: 'pointer',
              }}
            >
              Настройки графика
            </button>
            
            <button 
              onClick={() => recalculateAndLoadPlot(selectedGraphType)}
              disabled={isLoading || isCalculating}
              style={{
                marginLeft: '8px',
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                background: (isLoading || isCalculating) ? '#a0aec0' : '#4299e1',
                color: 'white',
                cursor: (isLoading || isCalculating) ? 'not-allowed' : 'pointer',
              }}
            >
              {isLoading || isCalculating ? 'Расчёт...' : 'Пересчитать и обновить'}
            </button>
          </div>

          {error && (
            <div style={{ 
              color: '#e53e3e', 
              padding: '12px', 
              background: '#fed7d7', 
              borderRadius: '6px',
              marginTop: '12px'
            }}>
              {error}
            </div>
          )}

          {!calculationResult ? (
            <div className="no-data-message">
              <p>Для отображения графиков необходимо выполнить расчёт траектории.</p>
              <p style={{ fontSize: '14px', color: '#718096' }}>
                Меню → Файл → Расчёт траектории (или настройте параметры и нажмите "Расчёт")
              </p>
            </div>
          ) : (
            <div className="trajectory-content">
              {/* График */}
              <div className="plot-container" style={{ textAlign: 'center', marginTop: '16px' }}>
                {isLoading ? (
                  <div className="loading-spinner">Загрузка графика...</div>
                ) : plotImage ? (
                  <img 
                    src={plotImage} 
                    alt={GRAPH_TYPE_LABELS[selectedGraphType]} 
                    style={{ 
                      maxWidth: '100%', 
                      maxHeight: '500px',
                      borderRadius: '8px',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                ) : null}
              </div>

              {/* Качество регулирования */}
              {calculationResult && (
                <div className="quality-metrics" style={{ marginTop: '24px' }}>
                  <h4 style={{ marginBottom: '12px' }}>Качество регулирования</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div className="quality-card">
                      <h5>Звено 1</h5>
                      <table className="quality-table">
                        <tbody>
                          <tr>
                            <td>Средняя ошибка:</td>
                            <td>{formatNumber(calculationResult.quality_link_1?.avg_error)}</td>
                          </tr>
                          <tr>
                            <td>Медианная ошибка:</td>
                            <td>{formatNumber(calculationResult.quality_link_1?.median_error)}</td>
                          </tr>
                          <tr>
                            <td>Среднее время регулирования:</td>
                            <td>{formatNumber(calculationResult.quality_link_1?.avg_reg_time)} с</td>
                          </tr>
                          <tr>
                            <td>Медианное время регулирования:</td>
                            <td>{formatNumber(calculationResult.quality_link_1?.median_reg_time)} с</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div className="quality-card">
                      <h5>Звено 2</h5>
                      <table className="quality-table">
                        <tbody>
                          <tr>
                            <td>Средняя ошибка:</td>
                            <td>{formatNumber(calculationResult.quality_link_2?.avg_error)}</td>
                          </tr>
                          <tr>
                            <td>Медианная ошибка:</td>
                            <td>{formatNumber(calculationResult.quality_link_2?.median_error)}</td>
                          </tr>
                          <tr>
                            <td>Среднее время регулирования:</td>
                            <td>{formatNumber(calculationResult.quality_link_2?.avg_reg_time)} с</td>
                          </tr>
                          <tr>
                            <td>Медианное время регулирования:</td>
                            <td>{formatNumber(calculationResult.quality_link_2?.median_reg_time)} с</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Вкладка Рабочая область */}
        <section id="tabWorkspace" data-active={activeTab === 'tabWorkspace'}>
          <h3>Рабочая область</h3>
          
          <button 
            onClick={loadWorkspace}
            disabled={isLoading || !calculationResult}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              background: calculationResult ? '#48bb78' : '#a0aec0',
              color: 'white',
              cursor: calculationResult ? 'pointer' : 'not-allowed',
              marginBottom: '16px',
            }}
          >
            {isLoading ? 'Загрузка...' : 'Обновить рабочую область'}
          </button>

          {error && (
            <div style={{ 
              color: '#e53e3e', 
              padding: '12px', 
              background: '#fed7d7', 
              borderRadius: '6px',
              marginBottom: '12px'
            }}>
              {error}
            </div>
          )}

          {!calculationResult ? (
            <div className="no-data-message">
              <p>Для отображения рабочей области необходимо выполнить расчёт траектории.</p>
            </div>
          ) : (
            <div className="workspace-content" style={{ textAlign: 'center' }}>
              {isLoading ? (
                <div className="loading-spinner">Загрузка рабочей области...</div>
              ) : workspaceImage ? (
                <img 
                  src={workspaceImage} 
                  alt="Рабочая область робота" 
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: '500px',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
                  }}
                />
              ) : null}
            </div>
          )}

          {calculationResult && (
            <div className="robot-info" style={{ marginTop: '24px' }}>
              <h4>Информация о роботе</h4>
              <table className="info-table">
                <tbody>
                  <tr>
                    <td>Тип робота:</td>
                    <td><strong>{calculationResult.robot_type}</strong></td>
                  </tr>
                  <tr>
                    <td>Тип управления:</td>
                    <td>{calculationResult.type_of_control}</td>
                  </tr>
                  <tr>
                    <td>Сплайн:</td>
                    <td>{calculationResult.spline ? 'Да' : 'Нет'}</td>
                  </tr>
                  <tr>
                    <td>Точек траектории:</td>
                    <td>{calculationResult.trajectory_length}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Вкладка Лог */}
        <section id="tabLog" data-active={activeTab === 'tabLog'}>
          <h3>Лог</h3>
          <LogViewer />
        </section>
      </div>
    </>
  );
}

// Компонент для отображения логов
function LogViewer() {
  const { logs } = useAppState();

  if (!logs || logs.length === 0) {
    return (
      <div className="log-empty">
        <p>Лог пуст. Выполните расчёт для просмотра логов.</p>
      </div>
    );
  }

  return (
    <div className="log-container">
      {logs.map((log, index) => (
        <div 
          key={index} 
          className={`log-entry log-${log.type || 'info'}`}
          style={{
            padding: '8px 12px',
            borderBottom: '1px solid #e2e8f0',
            fontFamily: 'monospace',
            fontSize: '13px',
          }}
        >
          <span className="log-time" style={{ color: '#718096', marginRight: '12px' }}>
            [{new Date(log.timestamp).toLocaleTimeString()}]
          </span>
          <span className="log-message">{log.message}</span>
        </div>
      ))}
    </div>
  );
}

export default Tabs;
