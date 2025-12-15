/**
 * API для администратора
 */

const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

/**
 * Получить список всех пользователей
 */
export async function getAllUsers() {
  const response = await fetch('/api/admin/users', {
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
    throw new Error(error.detail || 'Ошибка получения пользователей');
  }
  
  return response.json();
}

/**
 * Получить информацию о пользователе
 */
export async function getUser(userId) {
  const response = await fetch(`/api/admin/users/${userId}`, {
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
    throw new Error(error.detail || 'Ошибка получения пользователя');
  }
  
  return response.json();
}

/**
 * Удалить пользователя
 */
export async function deleteUser(userId) {
  const response = await fetch(`/api/admin/users/${userId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
    throw new Error(error.detail || 'Ошибка удаления пользователя');
  }
  
  return response.json();
}

/**
 * Переключить права администратора
 */
export async function toggleAdmin(userId) {
  const response = await fetch(`/api/admin/users/${userId}/toggle-admin`, {
    method: 'PUT',
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
    throw new Error(error.detail || 'Ошибка изменения прав');
  }
  
  return response.json();
}

/**
 * Получить все конфигурации всех пользователей
 */
export async function getAllConfigs() {
  const response = await fetch('/api/admin/configs', {
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
    throw new Error(error.detail || 'Ошибка получения конфигураций');
  }
  
  return response.json();
}

/**
 * Получить конфигурацию по ID
 */
export async function getConfig(configId) {
  const response = await fetch(`/api/admin/configs/${configId}`, {
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
    throw new Error(error.detail || 'Ошибка получения конфигурации');
  }
  
  return response.json();
}

/**
 * Удалить конфигурацию
 */
export async function deleteConfig(configId) {
  const response = await fetch(`/api/admin/configs/${configId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
    throw new Error(error.detail || 'Ошибка удаления конфигурации');
  }
  
  return response.json();
}

