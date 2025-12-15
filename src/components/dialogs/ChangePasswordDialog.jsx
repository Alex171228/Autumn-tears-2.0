import React, { useState } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function ChangePasswordDialog() {
  const { dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.changePassword);
  
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    setError('');
    
    // Валидация
    if (!formData.currentPassword || !formData.newPassword || !formData.confirmPassword) {
      setError('Заполните все поля');
      return;
    }
    
    if (formData.newPassword.length < 6) {
      setError('Новый пароль должен содержать минимум 6 символов');
      return;
    }
    
    if (formData.newPassword !== formData.confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }
    
    if (formData.currentPassword === formData.newPassword) {
      setError('Новый пароль должен отличаться от текущего');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: formData.currentPassword,
          new_password: formData.newPassword,
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        alert('Пароль успешно изменён');
        handleClose();
      } else {
        setError(data.detail || 'Ошибка смены пароля');
      }
    } catch (err) {
      setError('Ошибка соединения с сервером');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    setError('');
    closeDialog('changePassword');
  };

  if (!dialogs.changePassword) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, handleClose)}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Смена пароля</div>
        <div className="dlg-form">
          {error && (
            <div style={{
              color: '#e53e3e',
              background: '#fed7d7',
              padding: '8px 12px',
              borderRadius: '6px',
              marginBottom: '12px',
              fontSize: '14px',
            }}>
              {error}
            </div>
          )}
          
          <div className="dlg-form-row">
            <label htmlFor="current_password">Текущий пароль</label>
            <input
              id="current_password"
              type="password"
              value={formData.currentPassword}
              onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
              autoComplete="current-password"
            />
          </div>
          
          <div className="dlg-form-row">
            <label htmlFor="new_password">Новый пароль</label>
            <input
              id="new_password"
              type="password"
              value={formData.newPassword}
              onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
              autoComplete="new-password"
            />
          </div>
          
          <div className="dlg-form-row">
            <label htmlFor="confirm_password">Подтвердите пароль</label>
            <input
              id="confirm_password"
              type="password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              autoComplete="new-password"
            />
          </div>
        </div>
        
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button
              type="button"
              className="dlg-btn dlg-btn-ok"
              onClick={handleSubmit}
              disabled={isLoading}
            >
              {isLoading ? 'Сохранение...' : 'Сменить пароль'}
            </button>
            <button
              type="button"
              className="dlg-btn dlg-btn-cancel"
              onClick={handleClose}
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

export default ChangePasswordDialog;

