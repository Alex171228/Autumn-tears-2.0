/**
 * API сервис для работы с сохранёнными конфигурациями
 */

/**
 * Получить токен авторизации
 */
function getAuthHeader() {
  const token = localStorage.getItem('auth_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

/**
 * Получить список сохранённых конфигураций
 */
export async function getConfigs() {
  const response = await fetch('/api/configs', {
    headers: {
      ...getAuthHeader(),
    },
  });
  
  if (response.status === 401) {
    throw new Error('Необходима авторизация');
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка загрузки' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Получить конфигурацию по ID
 */
export async function getConfig(configId) {
  const response = await fetch(`/api/configs/${configId}`, {
    headers: {
      ...getAuthHeader(),
    },
  });
  
  if (response.status === 401) {
    throw new Error('Необходима авторизация');
  }
  
  if (response.status === 404) {
    throw new Error('Конфигурация не найдена');
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка загрузки' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Сохранить новую конфигурацию
 */
export async function saveConfig(name, configData) {
  const response = await fetch('/api/configs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify({ name, config_data: configData }),
  });
  
  if (response.status === 401) {
    throw new Error('Необходима авторизация');
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка сохранения' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Обновить существующую конфигурацию
 */
export async function updateConfig(configId, name, configData) {
  const body = {};
  if (name !== undefined) body.name = name;
  if (configData !== undefined) body.config_data = configData;
  
  const response = await fetch(`/api/configs/${configId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(body),
  });
  
  if (response.status === 401) {
    throw new Error('Необходима авторизация');
  }
  
  if (response.status === 404) {
    throw new Error('Конфигурация не найдена');
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка обновления' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Удалить конфигурацию
 */
export async function deleteConfig(configId) {
  const response = await fetch(`/api/configs/${configId}`, {
    method: 'DELETE',
    headers: {
      ...getAuthHeader(),
    },
  });
  
  if (response.status === 401) {
    throw new Error('Необходима авторизация');
  }
  
  if (response.status === 404) {
    throw new Error('Конфигурация не найдена');
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка удаления' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

export default {
  getConfigs,
  getConfig,
  saveConfig,
  updateConfig,
  deleteConfig,
};

