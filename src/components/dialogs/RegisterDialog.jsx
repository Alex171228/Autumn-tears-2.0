import React, { useState } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function RegisterDialog() {
  const { dialogs, closeDialog, handleLogin } = useAppState();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
  });
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.register);

  const handleSubmit = async () => {
    if (!formData.username || !formData.password || !formData.confirmPassword) {
      alert('Пожалуйста, заполните все обязательные поля');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      alert('Пароли не совпадают');
      return;
    }

    if (formData.password.length < 6) {
      alert('Пароль должен содержать не менее 6 символов');
      return;
    }

    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username.trim(),
          password: formData.password,
        }),
      });

      let data;
      try {
        data = await response.json();
      } catch (e) {
        // Если ответ не JSON, читаем как текст
        const text = await response.text();
        alert(`Ошибка регистрации: ${text || 'Неизвестная ошибка'}`);
        return;
      }

      if (response.ok) {
        // Успешная регистрация - автоматический вход
        handleLogin(data.access_token, data.username, data.is_admin || false);
        setFormData({ username: '', password: '', confirmPassword: '' });
      } else {
        // Показываем понятное сообщение об ошибке
        let errorMessage = 'Ошибка регистрации. Попробуйте другое имя пользователя.';
        if (data && typeof data === 'object') {
          // Обработка массива ошибок валидации FastAPI
          if (Array.isArray(data.detail)) {
            const errors = data.detail.map(err => {
              if (typeof err === 'object' && err.msg) {
                return `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`;
              }
              return String(err);
            }).join('\n');
            errorMessage = errors || errorMessage;
          } else if (data.detail && typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (data.message && typeof data.message === 'string') {
            errorMessage = data.message;
          } else if (typeof data === 'string') {
            errorMessage = data;
          }
        }
        console.error('Registration error:', data);
        alert(errorMessage);
      }
    } catch (error) {
      console.error('Register error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Ошибка соединения с сервером';
      alert(errorMessage);
    }
  };

  const handleCancel = () => {
    closeDialog('register');
    setFormData({ username: '', password: '', confirmPassword: '' });
  };

  if (!dialogs.register) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('register'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Регистрация</div>
        <div className="dlg-form">
          <div className="dlg-form-row">
            <label htmlFor="register_username">Имя пользователя</label>
            <input
              id="register_username"
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              autoComplete="username"
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="register_password">Пароль</label>
            <input
              id="register_password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              autoComplete="new-password"
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="register_confirm_password">Подтвердите пароль</label>
            <input
              id="register_confirm_password"
              type="password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              autoComplete="new-password"
            />
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleSubmit}>
              Зарегистрироваться
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

export default RegisterDialog;

