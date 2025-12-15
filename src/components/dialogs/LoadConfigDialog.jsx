import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';
import * as configsApi from '../../services/configsApi';

function LoadConfigDialog() {
  const { dialogs, closeDialog, user, setState, setCurrentConfigId, setCurrentConfigName, addLog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.loadConfig);
  const [configs, setConfigs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  // Загрузка списка конфигураций
  useEffect(() => {
    if (dialogs.loadConfig && user) {
      loadConfigs();
    }
  }, [dialogs.loadConfig, user]);

  const loadConfigs = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await configsApi.getConfigs();
      setConfigs(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoad = async () => {
    if (!selectedId) {
      setError('Выберите конфигурацию');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const data = await configsApi.getConfig(selectedId);
      
      // Обновляем состояние
      setState(prev => ({
        ...prev,
        ...data.config_data,
      }));
      
      setCurrentConfigId(data.id);
      setCurrentConfigName(data.name);
      addLog(`Конфигурация "${data.name}" загружена`, 'success');
      closeDialog('loadConfig');
    } catch (err) {
      setError(err.message);
      addLog(`Ошибка загрузки: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (configId, configName) => {
    if (deleteConfirm !== configId) {
      setDeleteConfirm(configId);
      return;
    }

    setIsLoading(true);
    try {
      await configsApi.deleteConfig(configId);
      setConfigs(configs.filter(c => c.id !== configId));
      setDeleteConfirm(null);
      if (selectedId === configId) {
        setSelectedId(null);
      }
      addLog(`Конфигурация "${configName}" удалена`, 'success');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!dialogs.loadConfig) return null;

  if (!user) {
    return (
      <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('loadConfig'))}>
        <div className="dlg">
          <div className="dlg-header" ref={dragRef}>Загрузить конфигурацию</div>
          <div className="dlg-form" style={{ padding: '24px', textAlign: 'center' }}>
            <p style={{ color: '#e53e3e', marginBottom: '16px' }}>
              Для загрузки сохранённых конфигураций необходимо авторизоваться
            </p>
          </div>
          <div className="dlg-footer">
            <div className="dlg-footer-row">
              <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('loadConfig')}>
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </dialog>
    );
  }

  return (
    <dialog ref={dialogRef} className="dlg-load-configs" onClick={(e) => handleBackdropClick(e, () => closeDialog('loadConfig'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Мои конфигурации</div>
        <div className="dlg-form" style={{ padding: '16px' }}>
          {error && (
            <div style={{ color: '#e53e3e', padding: '8px 12px', background: '#fed7d7', borderRadius: '6px', marginBottom: '12px' }}>
              {error}
            </div>
          )}

          {isLoading && configs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px', color: '#718096' }}>
              Загрузка...
            </div>
          ) : configs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px', color: '#718096' }}>
              У вас нет сохранённых конфигураций
            </div>
          ) : (
            <div className="configs-list" style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {configs.map(config => (
                <div 
                  key={config.id}
                  className={`config-item ${selectedId === config.id ? 'selected' : ''}`}
                  onClick={() => setSelectedId(config.id)}
                  style={{
                    padding: '12px 16px',
                    borderRadius: '8px',
                    marginBottom: '8px',
                    background: selectedId === config.id ? 'rgba(102, 126, 234, 0.15)' : 'rgba(0, 0, 0, 0.03)',
                    border: selectedId === config.id ? '2px solid #667eea' : '2px solid transparent',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, color: '#2d3748', marginBottom: '4px' }}>
                      {config.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#718096' }}>
                      Обновлено: {formatDate(config.updated_at)}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(config.id, config.name);
                    }}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '4px',
                      border: 'none',
                      background: deleteConfirm === config.id ? '#e53e3e' : '#edf2f7',
                      color: deleteConfirm === config.id ? 'white' : '#718096',
                      cursor: 'pointer',
                      fontSize: '12px',
                    }}
                    title={deleteConfirm === config.id ? 'Нажмите ещё раз для подтверждения' : 'Удалить'}
                  >
                    {deleteConfirm === config.id ? 'Подтвердить' : 'Удалить'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="dlg-footer" style={{ padding: '16px' }}>
          <div className="dlg-footer-row" style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button 
              type="button" 
              className="dlg-btn dlg-btn-ok" 
              onClick={handleLoad}
              disabled={isLoading || !selectedId}
              style={{ minWidth: '120px' }}
            >
              {isLoading ? 'Загрузка...' : 'Загрузить'}
            </button>
            <button 
              type="button" 
              className="dlg-btn dlg-btn-cancel" 
              onClick={() => closeDialog('loadConfig')}
              disabled={isLoading}
              style={{ minWidth: '100px' }}
            >
              Отмена
            </button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default LoadConfigDialog;

