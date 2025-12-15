import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function SplineCyclegramDialog() {
  const { dialogs, closeDialog, calculationResult } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.splineCyclegram);
  
  const [data, setData] = useState({ t: [], q1: [], q2: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [splineEnabled, setSplineEnabled] = useState(false);

  useEffect(() => {
    if (dialogs.splineCyclegram) {
      loadSplineData();
    }
  }, [dialogs.splineCyclegram]);

  const loadSplineData = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch('/api/robot/spline-cyclegram');
      const result = await response.json();
      
      if (result.success) {
        setData(result.data);
        setSplineEnabled(result.spline_enabled);
      } else {
        setError('Не удалось загрузить данные');
      }
    } catch (err) {
      setError('Ошибка при загрузке данных: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const formatNumber = (num, decimals = 5) => {
    if (num === null || num === undefined) return '-';
    return Number(num).toFixed(decimals);
  };

  const maxLen = Math.max(data.t.length, data.q1.length, data.q2.length);

  if (!dialogs.splineCyclegram) return null;

  return (
    <dialog 
      ref={dialogRef} 
      className="dlg-spline-cyclegram" 
      onClick={(e) => handleBackdropClick(e, () => closeDialog('splineCyclegram'))}
    >
      <div className="dlg" style={{ width: '900px', maxHeight: '80vh' }}>
        <div className="dlg-header" ref={dragRef}>Циклограмма сплайна</div>
        
        <div className="dlg-form" style={{ padding: '16px' }}>
          {error && (
            <div style={{
              color: '#e53e3e',
              background: '#fed7d7',
              padding: '8px 12px',
              borderRadius: '6px',
              marginBottom: '12px',
            }}>
              {error}
            </div>
          )}

          {!calculationResult && (
            <div style={{
              color: '#718096',
              textAlign: 'center',
              padding: '24px',
            }}>
              Сначала выполните расчёт траектории со включённым сплайном.
            </div>
          )}

          {isLoading && (
            <div style={{ textAlign: 'center', padding: '24px', color: '#718096' }}>
              Загрузка данных...
            </div>
          )}

          {!isLoading && maxLen > 0 && (
            <div style={{ 
              maxHeight: '400px', 
              overflowY: 'auto',
              fontFamily: 'monospace',
              fontSize: '13px',
              background: '#1a202c',
              color: '#e2e8f0',
              borderRadius: '8px',
              padding: '12px',
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ 
                    borderBottom: '2px solid #4a5568',
                    position: 'sticky',
                    top: 0,
                    background: '#1a202c',
                  }}>
                    <th style={{ padding: '8px 16px', textAlign: 'right', color: '#63b3ed', minWidth: '120px' }}>t</th>
                    <th style={{ padding: '8px 16px', textAlign: 'right', color: '#68d391', minWidth: '180px' }}>q1</th>
                    <th style={{ padding: '8px 16px', textAlign: 'right', color: '#f6ad55', minWidth: '180px' }}>q2</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length: maxLen }).map((_, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #2d3748' }}>
                      <td style={{ padding: '6px 16px', textAlign: 'right', minWidth: '120px' }}>
                        {i < data.t.length ? formatNumber(data.t[i], 2) : '-'}
                      </td>
                      <td style={{ padding: '6px 16px', textAlign: 'right', minWidth: '180px' }}>
                        {i < data.q1.length ? formatNumber(data.q1[i], 5) : '-'}
                      </td>
                      <td style={{ padding: '6px 16px', textAlign: 'right', minWidth: '180px' }}>
                        {i < data.q2.length ? formatNumber(data.q2[i], 5) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!isLoading && maxLen === 0 && calculationResult && (
            <div style={{
              color: '#718096',
              textAlign: 'center',
              padding: '24px',
            }}>
              {!splineEnabled 
                ? 'Сплайн не включён. Включите опцию "Показать сплайн" в настройках графика и пересчитайте траекторию.'
                : 'Данные сплайна отсутствуют. Выполните расчёт траектории с включённым сплайном.'}
            </div>
          )}

          <div style={{ 
            marginTop: '12px', 
            fontSize: '13px', 
            color: '#718096',
            textAlign: 'center',
          }}>
            {maxLen > 0 && `Всего точек: ${maxLen}`}
          </div>
        </div>

        <div className="dlg-footer" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
            <button
              onClick={loadSplineData}
              disabled={isLoading}
              style={{
                padding: '10px 24px',
                borderRadius: '6px',
                border: '1px solid #cbd5e0',
                background: 'white',
                color: '#4a5568',
                cursor: isLoading ? 'not-allowed' : 'pointer',
              }}
            >
              Обновить
            </button>
            <button
              onClick={() => closeDialog('splineCyclegram')}
              style={{
                padding: '10px 24px',
                borderRadius: '6px',
                border: 'none',
                background: '#e53e3e',
                color: 'white',
                cursor: 'pointer',
              }}
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default SplineCyclegramDialog;

