import React, { useState, useEffect, useCallback } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';
import * as adminApi from '../../services/adminApi';

function AdminPanelDialog() {
  const { dialogs, closeDialog, user, setState, setCurrentConfigId, setCurrentConfigName, addLog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.adminPanel);
  
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [configs, setConfigs] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingConfigId, setLoadingConfigId] = useState(null);

  // Загрузка данных
  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await adminApi.getAllUsers();
      setUsers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadConfigs = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await adminApi.getAllConfigs();
      setConfigs(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadUserDetails = useCallback(async (userId) => {
    setIsLoading(true);
    setError('');
    try {
      const data = await adminApi.getUser(userId);
      setSelectedUser(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Загрузка при открытии
  useEffect(() => {
    if (dialogs.adminPanel && user?.isAdmin) {
      if (activeTab === 'users') {
        loadUsers();
      } else if (activeTab === 'configs') {
        loadConfigs();
      }
    }
  }, [dialogs.adminPanel, activeTab, user?.isAdmin, loadUsers, loadConfigs]);

  // Действия
  const handleDeleteUser = async (userId, username) => {
    if (!confirm(`Удалить пользователя "${username}" и все его данные?`)) return;
    
    try {
      await adminApi.deleteUser(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
      setSelectedUser(null);
      alert('Пользователь удалён');
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    }
  };

  const handleToggleAdmin = async (userId) => {
    try {
      const result = await adminApi.toggleAdmin(userId);
      setUsers(prev => prev.map(u => 
        u.id === userId ? { ...u, is_admin: result.is_admin } : u
      ));
      alert(result.message);
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    }
  };

  const handleDeleteConfig = async (configId, configName) => {
    if (!confirm(`Удалить конфигурацию "${configName}"?`)) return;
    
    try {
      await adminApi.deleteConfig(configId);
      setConfigs(prev => prev.filter(c => c.id !== configId));
      alert('Конфигурация удалена');
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    }
  };

  const handleLoadConfig = async (configId, configName, username) => {
    setLoadingConfigId(configId);
    try {
      const config = await adminApi.getConfig(configId);
      if (config && config.config_data) {
        setState(prev => ({
          ...prev,
          ...config.config_data,
        }));
        setCurrentConfigId(null); // Не связываем с облачной конфигурацией админа
        setCurrentConfigName(`${configName} (${username})`);
        if (addLog) {
          addLog(`Загружена конфигурация "${configName}" пользователя ${username}`, 'success');
        }
        alert(`Конфигурация "${configName}" пользователя ${username} загружена`);
        closeDialog('adminPanel');
      }
    } catch (err) {
      alert(`Ошибка загрузки: ${err.message}`);
    } finally {
      setLoadingConfigId(null);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString('ru-RU');
  };

  if (!dialogs.adminPanel) return null;

  // Проверка прав
  if (!user?.isAdmin) {
    return (
      <dialog ref={dialogRef} className="dlg-admin-panel" onClick={(e) => handleBackdropClick(e, () => closeDialog('adminPanel'))}>
        <div className="dlg" style={{ width: '400px' }}>
          <div className="dlg-header" ref={dragRef}>Панель администратора</div>
          <div className="dlg-form" style={{ padding: '24px', textAlign: 'center' }}>
            <p style={{ color: '#e53e3e' }}>Доступ запрещён. Требуются права администратора.</p>
          </div>
          <div className="dlg-footer">
            <button className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('adminPanel')}>
              Закрыть
            </button>
          </div>
        </div>
      </dialog>
    );
  }

  return (
    <dialog ref={dialogRef} className="dlg-admin-panel" onClick={(e) => handleBackdropClick(e, () => closeDialog('adminPanel'))}>
      <div className="dlg" style={{ width: '900px', maxHeight: '80vh' }}>
        <div className="dlg-header" ref={dragRef}>
          Панель администратора
        </div>
        
        {/* Вкладки */}
        <div style={{ 
          display: 'flex', 
          borderBottom: '2px solid #e2e8f0',
          background: '#f7fafc',
        }}>
          <button
            onClick={() => { setActiveTab('users'); setSelectedUser(null); }}
            style={{
              flex: 1,
              padding: '12px 16px',
              border: 'none',
              background: activeTab === 'users' ? '#667eea' : 'transparent',
              color: activeTab === 'users' ? 'white' : '#4a5568',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            Пользователи ({users.length})
          </button>
          <button
            onClick={() => { setActiveTab('configs'); setSelectedUser(null); }}
            style={{
              flex: 1,
              padding: '12px 16px',
              border: 'none',
              background: activeTab === 'configs' ? '#667eea' : 'transparent',
              color: activeTab === 'configs' ? 'white' : '#4a5568',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            Конфигурации ({configs.length})
          </button>
        </div>

        <div className="dlg-form" style={{ padding: '16px', minHeight: '400px', maxHeight: '500px', overflowY: 'auto' }}>
          {error && (
            <div style={{ 
              color: '#e53e3e', 
              padding: '8px 12px', 
              background: '#fed7d7', 
              borderRadius: '6px', 
              marginBottom: '12px' 
            }}>
              {error}
            </div>
          )}

          {isLoading && (
            <div style={{ textAlign: 'center', padding: '24px', color: '#718096' }}>
              Загрузка...
            </div>
          )}

          {/* Вкладка Пользователи */}
          {activeTab === 'users' && !isLoading && (
            <div style={{ display: 'flex', gap: '16px' }}>
              {/* Список пользователей */}
              <div style={{ flex: '1', minWidth: '300px' }}>
                <h4 style={{ marginBottom: '12px', color: '#2d3748' }}>Список пользователей</h4>
                {users.length === 0 ? (
                  <p style={{ color: '#718096' }}>Нет пользователей</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {users.map(u => (
                      <div
                        key={u.id}
                        onClick={() => loadUserDetails(u.id)}
                        style={{
                          padding: '12px',
                          borderRadius: '8px',
                          background: selectedUser?.id === u.id ? 'rgba(102, 126, 234, 0.15)' : 'rgba(0,0,0,0.03)',
                          border: selectedUser?.id === u.id ? '2px solid #667eea' : '2px solid transparent',
                          cursor: 'pointer',
                          transition: 'all 0.15s',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontWeight: 600, color: '#2d3748' }}>
                            {u.username}
                          </span>
                          {u.is_admin && (
                            <span style={{ 
                              fontSize: '10px', 
                              background: '#667eea', 
                              color: 'white', 
                              padding: '2px 6px', 
                              borderRadius: '4px' 
                            }}>
                              ADMIN
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '12px', color: '#718096', marginTop: '4px' }}>
                          Конфигураций: {u.configs_count} | Создан: {formatDate(u.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Детали пользователя */}
              {selectedUser && (
                <div style={{ flex: '1', minWidth: '300px', borderLeft: '1px solid #e2e8f0', paddingLeft: '16px' }}>
                  <h4 style={{ marginBottom: '12px', color: '#2d3748' }}>
                    {selectedUser.username}
                    {selectedUser.is_admin && (
                      <span style={{ 
                        fontSize: '10px', 
                        background: '#667eea', 
                        color: 'white', 
                        padding: '2px 6px', 
                        borderRadius: '4px',
                        marginLeft: '8px',
                        verticalAlign: 'middle'
                      }}>
                        ADMIN
                      </span>
                    )}
                  </h4>
                  
                  <div style={{ marginBottom: '16px' }}>
                    <p><strong>ID:</strong> {selectedUser.id}</p>
                    <p><strong>Создан:</strong> {formatDate(selectedUser.created_at)}</p>
                    <p><strong>Администратор:</strong> {selectedUser.is_admin ? 'Да' : 'Нет'}</p>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                    <button
                      onClick={() => handleToggleAdmin(selectedUser.id)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        border: 'none',
                        background: selectedUser.is_admin ? '#ecc94b' : '#48bb78',
                        color: 'white',
                        cursor: 'pointer',
                        fontSize: '13px',
                      }}
                    >
                      {selectedUser.is_admin ? 'Снять админа' : 'Сделать админом'}
                    </button>
                    <button
                      onClick={() => handleDeleteUser(selectedUser.id, selectedUser.username)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        border: 'none',
                        background: '#e53e3e',
                        color: 'white',
                        cursor: 'pointer',
                        fontSize: '13px',
                      }}
                    >
                      Удалить
                    </button>
                  </div>

                  <h5 style={{ marginBottom: '8px', color: '#4a5568' }}>Конфигурации пользователя:</h5>
                  {selectedUser.configs?.length === 0 ? (
                    <p style={{ color: '#718096', fontSize: '13px' }}>Нет сохранённых конфигураций</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {selectedUser.configs?.map(c => (
                        <div
                          key={c.id}
                          style={{
                            padding: '8px',
                            background: 'rgba(0,0,0,0.03)',
                            borderRadius: '4px',
                            fontSize: '13px',
                          }}
                        >
                          <div style={{ fontWeight: 500 }}>{c.name}</div>
                          <div style={{ color: '#718096', fontSize: '11px' }}>
                            Обновлено: {formatDate(c.updated_at)}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Вкладка Конфигурации */}
          {activeTab === 'configs' && !isLoading && (
            <div>
              <h4 style={{ marginBottom: '12px', color: '#2d3748' }}>Все конфигурации</h4>
              {configs.length === 0 ? (
                <p style={{ color: '#718096' }}>Нет конфигураций</p>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f7fafc' }}>
                      <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #e2e8f0' }}>ID</th>
                      <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #e2e8f0' }}>Название</th>
                      <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #e2e8f0' }}>Пользователь</th>
                      <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #e2e8f0' }}>Обновлено</th>
                      <th style={{ padding: '10px', textAlign: 'center', borderBottom: '2px solid #e2e8f0' }}>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {configs.map(c => (
                      <tr key={c.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                        <td style={{ padding: '10px', color: '#718096' }}>{c.id}</td>
                        <td style={{ padding: '10px', fontWeight: 500 }}>{c.name}</td>
                        <td style={{ padding: '10px' }}>{c.username}</td>
                        <td style={{ padding: '10px', fontSize: '13px', color: '#718096' }}>
                          {formatDate(c.updated_at)}
                        </td>
                        <td style={{ padding: '10px', textAlign: 'center' }}>
                          <button
                            onClick={() => handleLoadConfig(c.id, c.name, c.username)}
                            disabled={loadingConfigId === c.id}
                            style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: 'none',
                              background: loadingConfigId === c.id ? '#a0aec0' : '#48bb78',
                              color: 'white',
                              cursor: loadingConfigId === c.id ? 'not-allowed' : 'pointer',
                              fontSize: '12px',
                              marginRight: '4px',
                            }}
                          >
                            {loadingConfigId === c.id ? '...' : 'Загрузить'}
                          </button>
                          <button
                            onClick={() => handleDeleteConfig(c.id, c.name)}
                            style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: 'none',
                              background: '#fed7d7',
                              color: '#e53e3e',
                              cursor: 'pointer',
                              fontSize: '12px',
                            }}
                          >
                            Удалить
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>

        <div className="dlg-footer" style={{ padding: '16px', borderTop: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              onClick={() => activeTab === 'users' ? loadUsers() : loadConfigs()}
              style={{
                padding: '8px 32px',
                borderRadius: '6px',
                border: '1px solid #cbd5e0',
                background: 'white',
                color: '#4a5568',
                cursor: 'pointer',
                minWidth: '140px',
              }}
            >
              Обновить
            </button>
            <button
              onClick={() => closeDialog('adminPanel')}
              style={{
                padding: '8px 32px',
                borderRadius: '6px',
                border: 'none',
                background: '#e53e3e',
                color: 'white',
                cursor: 'pointer',
                minWidth: '80px',
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

export default AdminPanelDialog;
