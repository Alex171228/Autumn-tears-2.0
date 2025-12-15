import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';
import * as configsApi from '../../services/configsApi';

function SaveConfigDialog() {
  const { state, dialogs, closeDialog, user, currentConfigId, setCurrentConfigId, currentConfigName, setCurrentConfigName, addLog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.saveConfig);
  const [name, setName] = useState('');
  const [saveAsNew, setSaveAsNew] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (dialogs.saveConfig) {
      setName(currentConfigName || '');
      setSaveAsNew(!currentConfigId);
      setError('');
    }
  }, [dialogs.saveConfig, currentConfigName, currentConfigId]);

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Введите название конфигурации');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      if (currentConfigId && !saveAsNew) {
        // Обновляем существующую
        await configsApi.updateConfig(currentConfigId, name.trim(), state);
        addLog(`Конфигурация "${name}" обновлена`, 'success');
      } else {
        // Сохраняем новую
        const result = await configsApi.saveConfig(name.trim(), state);
        setCurrentConfigId(result.id);
        setCurrentConfigName(result.name);
        addLog(`Конфигурация "${name}" сохранена`, 'success');
      }
      closeDialog('saveConfig');
    } catch (err) {
      setError(err.message);
      addLog(`Ошибка сохранения: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  if (!dialogs.saveConfig) return null;

  if (!user) {
    return (
      <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('saveConfig'))}>
        <div className="dlg">
          <div className="dlg-header" ref={dragRef}>Сохранить конфигурацию</div>
          <div className="dlg-form" style={{ padding: '24px', textAlign: 'center' }}>
            <p style={{ color: '#e53e3e', marginBottom: '16px' }}>
              Для сохранения конфигурации необходимо авторизоваться
            </p>
          </div>
          <div className="dlg-footer">
            <div className="dlg-footer-row">
              <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('saveConfig')}>
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </dialog>
    );
  }

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('saveConfig'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>
          {currentConfigId && !saveAsNew ? 'Сохранить конфигурацию' : 'Сохранить как'}
        </div>
        <div className="dlg-form">
          {error && (
            <div style={{ color: '#e53e3e', padding: '8px 12px', background: '#fed7d7', borderRadius: '6px', marginBottom: '12px' }}>
              {error}
            </div>
          )}
          
          <div className="dlg-form-row">
            <label htmlFor="config_name">Название</label>
            <input
              id="config_name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Введите название конфигурации"
              maxLength={100}
              autoFocus
            />
          </div>

          {currentConfigId && (
            <div className="dlg-form-row" style={{ marginTop: '12px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={saveAsNew}
                  onChange={(e) => setSaveAsNew(e.target.checked)}
                />
                Сохранить как новую конфигурацию
              </label>
            </div>
          )}
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button 
              type="button" 
              className="dlg-btn dlg-btn-ok" 
              onClick={handleSave}
              disabled={isLoading}
            >
              {isLoading ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button 
              type="button" 
              className="dlg-btn dlg-btn-cancel" 
              onClick={() => closeDialog('saveConfig')}
              disabled={isLoading}
            >
              Отмена
            </button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default SaveConfigDialog;

