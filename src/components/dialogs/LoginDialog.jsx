import React, { useState } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function LoginDialog() {
  const { dialogs, closeDialog, handleLogin } = useAppState();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.login);

  const handleSubmit = async () => {
    if (!formData.username || !formData.password) {
      alert('Пожалуйста, заполните все поля');
      return;
    }

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        console.log('Login response:', data);
        const isAdmin = data.is_admin === true;
        handleLogin(data.access_token, data.username, isAdmin);
        setFormData({ username: '', password: '' });
      } else {
        // Показываем понятное сообщение об ошибке
        let errorMessage = 'Ошибка входа. Проверьте данные.';
        if (data && typeof data === 'object') {
          if (data.detail && typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (data.message && typeof data.message === 'string') {
            errorMessage = data.message;
          } else if (typeof data === 'string') {
            errorMessage = data;
          }
        }
        alert(errorMessage);
      }
    } catch (error) {
      console.error('Login error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Ошибка соединения с сервером';
      alert(errorMessage);
    }
  };

  const handleCancel = () => {
    closeDialog('login');
    setFormData({ username: '', password: '' });
  };

  if (!dialogs.login) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('login'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Вход</div>
        <div className="dlg-form">
          <div className="dlg-form-row">
            <label htmlFor="login_username">Имя пользователя</label>
            <input
              id="login_username"
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              autoComplete="username"
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="login_password">Пароль</label>
            <input
              id="login_password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              autoComplete="current-password"
            />
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleSubmit}>
              Войти
            </button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={handleCancel}>
              Отменить
            </button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default LoginDialog;

