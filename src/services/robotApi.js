/**
 * API сервис для работы с бэкендом расчёта траекторий роботов
 */

const API_BASE = '/api/robot';

// Маппинг типов роботов
const ROBOT_TYPE_MAP = {
  cartesian: 'Декартовый',
  scara: 'Скара',
  cylindrical: 'Цилиндрический',
  coler: 'Колер',
};

const ROBOT_TYPE_REVERSE_MAP = {
  'Декартовый': 'cartesian',
  'Скара': 'scara',
  'Цилиндрический': 'cylindrical',
  'Колер': 'coler',
};

const CONTROL_TYPE_MAP = {
  position: 'Позиционное',
  contour: 'Контурное',
};

/**
 * Базовый метод для API запросов
 */
async function apiRequest(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, options);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Конвертировать состояние фронтенда в формат API
 */
export function stateToApiConfig(state) {
  const robotType = ROBOT_TYPE_MAP[state.robotType] || 'Декартовый';
  const controlType = state.movementType === 'contour' ? 'Контурное' : 'Позиционное';
  
  // Фильтруем null значения и заменяем на 0
  const filterNulls = (arr, defaultVal = 0) => {
    if (!Array.isArray(arr)) return [defaultVal, defaultVal];
    return arr.map(v => v ?? defaultVal);
  };

  const filterNull = (v, defaultVal = 0) => v ?? defaultVal;

  return {
    robot_type: robotType,
    type_of_control: controlType,
    spline: state.graphSettings?.showSpline || false,
    
    // ПИД-регулятор
    Kp: filterNulls(state.regulatorParams?.Kp, 1),
    Ki: filterNulls(state.regulatorParams?.Ki, 0),
    Kd: filterNulls(state.regulatorParams?.Kd, 0),
    
    // Циклограмма
    t: filterNulls(state.cyclegram?.t, 0),
    q1: filterNulls(state.cyclegram?.q1, 0),
    q2: filterNulls(state.cyclegram?.q2, 0),
    q3: filterNulls(state.cyclegram?.q3, 0),
    q4: filterNulls(state.cyclegram?.q4, 0),
    
    // Параметры двигателей
    J: filterNulls(state.motorParams?.J, 1),
    T_e: filterNulls(state.motorParams?.Te, 0.002),
    Umax: filterNulls(state.motorParams?.Umax, 24),
    Fi: filterNulls(state.motorParams?.Fi, 1),
    Ce: filterNulls(state.motorParams?.Ce, 1),
    Ra: filterNulls(state.motorParams?.Ra, 1),
    Cm: filterNulls(state.motorParams?.Cm, 1),
    
    // Декартовый робот
    x_min: filterNull(state.cartesianLimits?.Xmin, 0),
    x_max: filterNull(state.cartesianLimits?.Xmax, 1),
    y_min: filterNull(state.cartesianLimits?.Ymin, 0),
    y_max: filterNull(state.cartesianLimits?.Ymax, 1),
    z_min: filterNull(state.cartesianLimits?.Zmin, 0),
    z_max: filterNull(state.cartesianLimits?.Zmax, 0),
    massd_1: filterNull(state.cartesianParams?.mass1, 1),
    massd_2: filterNull(state.cartesianParams?.mass2, 1),
    massd_3: filterNull(state.cartesianParams?.mass3, 0),
    momentd_1: filterNull(state.cartesianParams?.moment, 0.1),
    
    // SCARA
    q1s_min: filterNull(state.scaraLimits?.q1Min, -1.57),
    q1s_max: filterNull(state.scaraLimits?.q1Max, 1.57),
    q2s_min: filterNull(state.scaraLimits?.q2Min, -2),
    q2s_max: filterNull(state.scaraLimits?.q2Max, 2),
    q3s_min: filterNull(state.scaraLimits?.q3Min, 0),
    q3s_max: filterNull(state.scaraLimits?.q3Max, 0),
    zs_min: filterNull(state.scaraLimits?.zMin, 0),
    zs_max: filterNull(state.scaraLimits?.zMax, 0),
    moment_1: filterNull(state.scaraParams?.moment1, 0.1),
    moment_2: filterNull(state.scaraParams?.moment2, 0.1),
    moment_3: filterNull(state.scaraParams?.moment3, 0),
    length_1: filterNull(state.scaraParams?.length1, 0.5),
    length_2: filterNull(state.scaraParams?.length2, 0.5),
    distance: filterNull(state.scaraParams?.distance, 0),
    masss_2: filterNull(state.scaraParams?.mass2, 1),
    masss_3: filterNull(state.scaraParams?.mass3, 0),
    
    // Цилиндрический
    q1c_min: filterNull(state.cylindricalLimits?.q1Min, -1.57),
    q1c_max: filterNull(state.cylindricalLimits?.q1Max, 1.57),
    a2c_min: filterNull(state.cylindricalLimits?.a2Min, 0),
    a2c_max: filterNull(state.cylindricalLimits?.a2Max, 0.5),
    q3c_min: filterNull(state.cylindricalLimits?.q3Min, 0),
    q3c_max: filterNull(state.cylindricalLimits?.q3Max, 0),
    zc_min: filterNull(state.cylindricalLimits?.zMin, 0),
    zc_max: filterNull(state.cylindricalLimits?.zMax, 0),
    momentc_1: filterNull(state.cylindricalParams?.moment1, 0.1),
    momentc_2: filterNull(state.cylindricalParams?.moment2, 0.1),
    momentc_3: filterNull(state.cylindricalParams?.moment3, 0),
    lengthc_1: filterNull(state.cylindricalParams?.length1, 0.5),
    lengthc_2: filterNull(state.cylindricalParams?.length2, 0.3),
    distancec: filterNull(state.cylindricalParams?.distance, 0),
    massc_2: filterNull(state.cylindricalParams?.mass2, 1),
    massc_3: filterNull(state.cylindricalParams?.mass3, 0),
    
    // Колер
    q1col_min: filterNull(state.colerLimits?.q1Min, -1.57),
    q1col_max: filterNull(state.colerLimits?.q1Max, 1.57),
    a2col_min: filterNull(state.colerLimits?.a2Min, 0),
    a2col_max: filterNull(state.colerLimits?.a2Max, 0.5),
    q3col_min: filterNull(state.colerLimits?.q3Min, 0),
    q3col_max: filterNull(state.colerLimits?.q3Max, 0),
    zcol_min: filterNull(state.colerLimits?.zMin, 0),
    zcol_max: filterNull(state.colerLimits?.zMax, 0),
    momentcol_1: filterNull(state.colerParams?.moment1, 0.1),
    momentcol_2: filterNull(state.colerParams?.moment2, 0.1),
    momentcol_3: filterNull(state.colerParams?.moment3, 0),
    lengthcol_1: filterNull(state.colerParams?.length1, 0.5),
    lengthcol_2: filterNull(state.colerParams?.length2, 0.3),
    distancecol: filterNull(state.colerParams?.distance, 0),
    masscol_2: filterNull(state.colerParams?.mass2, 1),
    masscol_3: filterNull(state.colerParams?.mass3, 0),
    
    // Контурное управление
    line_x1: filterNull(state.trajectory?.line?.x1, 0),
    line_x2: filterNull(state.trajectory?.line?.x2, 0),
    line_y1: filterNull(state.trajectory?.line?.y1, 0),
    line_y2: filterNull(state.trajectory?.line?.y2, 0),
    circle_x: filterNull(state.trajectory?.circle?.x, 0),
    circle_y: filterNull(state.trajectory?.circle?.y, 0),
    circle_radius: filterNull(state.trajectory?.circle?.radius, 0),
  };
}

// === API методы ===

/**
 * Полная конфигурация робота
 */
export async function configureRobot(state) {
  const config = stateToApiConfig(state);
  return apiRequest('/configure', 'POST', config);
}

/**
 * Установить тип робота
 */
export async function setRobotType(type) {
  const robotType = ROBOT_TYPE_MAP[type] || type;
  return apiRequest(`/type?robot_type=${encodeURIComponent(robotType)}`, 'POST');
}

/**
 * Установить циклограмму
 */
export async function setCyclogram(cyclegram, controlType = 'Позиционное') {
  return apiRequest('/cyclogram', 'POST', {
    t: cyclegram.t,
    q1: cyclegram.q1,
    q2: cyclegram.q2,
    q3: cyclegram.q3 || [],
    q4: cyclegram.q4 || [],
    type_of_control: controlType,
  });
}

/**
 * Установить параметры ПИД-регулятора
 */
export async function setPID(Kp, Ki, Kd) {
  return apiRequest('/pid', 'POST', { Kp, Ki, Kd });
}

/**
 * Установить параметры двигателей
 */
export async function setMotorParams(params) {
  return apiRequest('/motors', 'POST', {
    J: params.J,
    T_e: params.Te,
    Umax: params.Umax,
    Fi: params.Fi,
    Ce: params.Ce,
    Ra: params.Ra,
    Cm: params.Cm,
  });
}

/**
 * Установить линейный контур
 */
export async function setLineContour(x1, x2, y1, y2, speed = 1) {
  return apiRequest('/contour/line', 'POST', { x1, x2, y1, y2, speed });
}

/**
 * Установить круговой контур
 */
export async function setCircleContour(x, y, radius, speed = 1) {
  return apiRequest('/contour/circle', 'POST', { x, y, radius, speed });
}

/**
 * Включить/выключить сплайн
 */
export async function setSpline(enabled, numDots = 100) {
  return apiRequest('/spline', 'POST', { enabled, num_dots: numDots });
}

/**
 * Получить текущее состояние робота
 */
export async function getRobotState() {
  return apiRequest('/state');
}

/**
 * Рассчитать траекторию
 */
export async function calculateTrajectory() {
  return apiRequest('/calculate', 'POST');
}

/**
 * Получить график в виде base64 изображения
 * @param {string} plotType - Тип графика
 */
export async function getPlot(plotType) {
  return apiRequest(`/plot/${plotType}`);
}

/**
 * Получить изображение рабочей области
 */
export async function getWorkspace() {
  return apiRequest('/workspace');
}

/**
 * Получить все данные расчёта
 */
export async function getAllData() {
  return apiRequest('/data/all');
}

/**
 * Удалить сессию
 */
export async function deleteSession(sessionId = 'default') {
  return apiRequest(`/session/${sessionId}`, 'DELETE');
}

// Типы графиков - соответствуют настройкам графика (GraphSettingsDialog)
// Ключ = значение из state.graphSettings.coordType
// Значение = ID для API бэкенда
export const GRAPH_TYPE_TO_API = {
  general: 'obobshennie_coordinates',    // Обобщённые от времени
  plane: 'decart_plane',                 // Декартовы на плоскости
  time: 'decart_coordinates',            // Декартовы от времени
  speed: 'speed',                        // Обобщённые скорости
  accel: 'acceleration',                 // Обобщённые ускорения
  voltage: 'voltage',                    // Напряжение
  voltage_star: 'voltage_star',          // Напряжение* (U - ЭДС)
  current: 'current',                    // Ток
  motor_moment: 'motor_moment',          // Момент электродвижущий
  load_moment: 'load_moment',            // Момент нагрузки
  moment_star: 'moment_star',            // Момент* (МЭ - М нагрузки)
};

// Названия типов графиков на русском
export const GRAPH_TYPE_LABELS = {
  general: 'Обобщённые от времени',
  plane: 'Декартовы на плоскости',
  time: 'Декартовы от времени',
  speed: 'Обобщённые скорости',
  accel: 'Обобщённые ускорения',
  voltage: 'Напряжение',
  voltage_star: 'Напряжение* (U - ЭДС)',
  current: 'Ток',
  motor_moment: 'Момент электродвижущий',
  load_moment: 'Момент нагрузки',
  moment_star: 'Момент* (МЭ - М нагрузки)',
};

// Группы типов графиков для UI
export const GRAPH_TYPE_GROUPS = {
  basic: {
    label: 'Основные',
    types: ['general', 'plane'],
  },
  additional: {
    label: 'Дополнительные',
    types: ['time', 'speed', 'accel'],
  },
  internal: {
    label: 'Внутренние',
    types: ['voltage', 'voltage_star', 'current', 'motor_moment', 'load_moment', 'moment_star'],
  },
};

// Старые константы для совместимости
export const PLOT_TYPES = GRAPH_TYPE_TO_API;
export const PLOT_TYPE_LABELS = GRAPH_TYPE_LABELS;

/**
 * Загрузить файл конфигурации
 * @param {File} file - файл для загрузки
 */
export async function uploadConfigFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/data/upload', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка загрузки файла' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Скачать файл конфигурации
 * @param {Object} state - состояние приложения
 * @param {string} filename - имя файла (опционально)
 */
export async function downloadConfigFile(state, filename = 'robot_config.txt') {
  const response = await fetch('/api/data/download', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(state),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Ошибка скачивания файла' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  // Получаем blob и создаём ссылку для скачивания
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  // Добавляем расширение .txt если его нет
  const finalFilename = filename.endsWith('.txt') ? filename : `${filename}.txt`;
  a.download = finalFilename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
  
  return { success: true, filename: finalFilename };
}

export default {
  configureRobot,
  setRobotType,
  setCyclogram,
  setPID,
  setMotorParams,
  setLineContour,
  setCircleContour,
  setSpline,
  getRobotState,
  calculateTrajectory,
  getPlot,
  getWorkspace,
  getAllData,
  deleteSession,
  stateToApiConfig,
  uploadConfigFile,
  downloadConfigFile,
  PLOT_TYPES,
  PLOT_TYPE_LABELS,
};

