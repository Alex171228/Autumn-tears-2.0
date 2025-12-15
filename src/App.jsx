import React, { useState, useEffect, createContext, useContext, useCallback } from 'react';
import TopMenu from './components/TopMenu';
import WeatherWidget from './components/WeatherWidget';
import DateTimeWidget from './components/DateTimeWidget';
import Tabs from './components/Tabs';
import StatusBar from './components/StatusBar';
import RobotTypeDialog from './components/dialogs/RobotTypeDialog';
import MovementTypeDialog from './components/dialogs/MovementTypeDialog';
import CartesianParamsDialog from './components/dialogs/CartesianParamsDialog';
import CartesianLimitsDialog from './components/dialogs/CartesianLimitsDialog';
import ScaraParamsDialog from './components/dialogs/ScaraParamsDialog';
import ScaraLimitsDialog from './components/dialogs/ScaraLimitsDialog';
import CylindricalParamsDialog from './components/dialogs/CylindricalParamsDialog';
import CylindricalLimitsDialog from './components/dialogs/CylindricalLimitsDialog';
import ColerParamsDialog from './components/dialogs/ColerParamsDialog';
import ColerLimitsDialog from './components/dialogs/ColerLimitsDialog';
import MotorParamsDialog from './components/dialogs/MotorParamsDialog';
import RegulatorParamsDialog from './components/dialogs/RegulatorParamsDialog';
import CalculatorDialog from './components/dialogs/CalculatorDialog';
import CyclegramDialog from './components/dialogs/CyclegramDialog';
import TrajectoryTypeDialog from './components/dialogs/TrajectoryTypeDialog';
import LineParamsDialog from './components/dialogs/LineParamsDialog';
import CircleParamsDialog from './components/dialogs/CircleParamsDialog';
import GraphSettingsDialog from './components/dialogs/GraphSettingsDialog';
import CreatorsDialog from './components/dialogs/CreatorsDialog';
import LoginDialog from './components/dialogs/LoginDialog';
import RegisterDialog from './components/dialogs/RegisterDialog';
import SaveConfigDialog from './components/dialogs/SaveConfigDialog';
import LoadConfigDialog from './components/dialogs/LoadConfigDialog';
import AdminPanelDialog from './components/dialogs/AdminPanelDialog';
import ChangePasswordDialog from './components/dialogs/ChangePasswordDialog';
import SplineCyclegramDialog from './components/dialogs/SplineCyclegramDialog';
import * as robotApi from './services/robotApi';

// Create context for app state
const AppContext = createContext();

export const useAppState = () => useContext(AppContext);

function App() {
  // User authentication state
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem('auth_token');
    const username = localStorage.getItem('username');
    const isAdmin = localStorage.getItem('is_admin') === 'true';
    return token && username ? { token, username, isAdmin } : null;
  });

  // Проверка токена при загрузке приложения
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const username = localStorage.getItem('username');
    
    if (token && username) {
      // Проверяем валидность токена и получаем актуальные данные
      fetch('/api/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(async response => {
        if (!response.ok) {
          // Токен невалиден, удаляем его
          localStorage.removeItem('auth_token');
          localStorage.removeItem('username');
          localStorage.removeItem('is_admin');
          setUser(null);
          return null;
        }
        return response.json();
      })
      .then(data => {
        if (data) {
          // Обновляем данные пользователя из ответа сервера
          const isAdmin = data.is_admin === true;
          localStorage.setItem('is_admin', isAdmin ? 'true' : 'false');
          localStorage.setItem('username', data.username);
          setUser({
            token,
            username: data.username,
            isAdmin: isAdmin
          });
          console.log('User restored:', { username: data.username, isAdmin });
        }
      })
      .catch((err) => {
        console.error('Error checking token:', err);
        // Ошибка соединения, но оставляем пользователя залогиненным
        // используя данные из localStorage
      });
    }
  }, []);

  // Initial state matching the original HTML
  const [state, setState] = useState({
    robotType: "cartesian",
    movementType: "position",
    cartesianParams: {
      mass1: null,
      mass2: null,
      mass3: null,
      moment: null,
    },
    cartesianLimits: {
      Xmin: null, Xmax: null,
      Ymin: null, Ymax: null,
      Zmin: null, Zmax: null,
      Qmin: null, Qmax: null,
    },
    scaraParams: {
      moment1: null,
      moment2: null,
      moment3: null,
      length1: null,
      length2: null,
      distance: null,
      mass2: null,
      mass3: null,
    },
    scaraLimits: {
      q1Min: null, q1Max: null,
      q2Min: null, q2Max: null,
      q3Min: null, q3Max: null,
      zMin: null, zMax: null,
    },
    cylindricalParams: {
      moment1: null,
      moment2: null,
      moment3: null,
      length1: null,
      length2: null,
      distance: null,
      mass2: null,
      mass3: null,
    },
    cylindricalLimits: {
      q1Min: null, q1Max: null,
      a2Min: null, a2Max: null,
      q3Min: null, q3Max: null,
      zMin: null, zMax: null,
    },
    colerParams: {
      moment1: null,
      moment2: null,
      moment3: null,
      length1: null,
      length2: null,
      distance: null,
      mass2: null,
      mass3: null,
    },
    colerLimits: {
      a2Min: null, a2Max: null,
      q1Min: null, q1Max: null,
      q3Min: null, q3Max: null,
      zMin: null, zMax: null,
    },
    motorParams: {
      J: [null, null],
      Te: [null, null],
      Umax: [null, null],
      Fi: [null, null],
      Ce: [null, null],
      Ra: [null, null],
      Cm: [null, null],
    },
    regulatorParams: {
      Kp: [null, null, null, null],
      Ki: [null, null, null, null],
      Kd: [null, null, null, null],
    },
    calculatorValues: {
      bitDepth: null,
      exchangeCycle: null,
      controlCycle: null,
      filterConstant: null,
    },
    cyclegram: {
      t: Array(9).fill(null),
      q1: Array(9).fill(null),
      q2: Array(9).fill(null),
      q3: Array(9).fill(null),
      q4: Array(9).fill(null),
    },
    trajectory: {
      type: "line",
      line: {
        x1: null,
        x2: null,
        y1: null,
        y2: null,
        speed: null,
      },
      circle: {
        x: null,
        y: null,
        radius: null,
        speed: null,
      },
    },
    graphSettings: {
      coordType: "general",
      showSpline: false,
    },
  });

  // Dialog visibility state
  const [dialogs, setDialogs] = useState({
    robotType: false,
    movementType: false,
    cartesianParams: false,
    cartesianLimits: false,
    scaraParams: false,
    scaraLimits: false,
    cylindricalParams: false,
    cylindricalLimits: false,
    colerParams: false,
    colerLimits: false,
    motorParams: false,
    regulatorParams: false,
    calculator: false,
    cyclegram: false,
    trajectoryType: false,
    lineParams: false,
    circleParams: false,
    graphSettings: false,
    creators: false,
    login: false,
    register: false,
    saveConfig: false,
    loadConfig: false,
    adminPanel: false,
    changePassword: false,
    splineCyclegram: false,
  });

  // Текущая сохранённая конфигурация
  const [currentConfigId, setCurrentConfigId] = useState(null);
  const [currentConfigName, setCurrentConfigName] = useState('');

  // Результаты расчёта траектории
  const [calculationResult, setCalculationResult] = useState(null);
  const [isCalculating, setIsCalculating] = useState(false);
  
  // Логи
  const [logs, setLogs] = useState([]);
  
  // Добавить запись в лог
  const addLog = useCallback((message, type = 'info') => {
    setLogs(prev => [...prev, { 
      message, 
      type, 
      timestamp: new Date().toISOString() 
    }]);
  }, []);

  // Очистить логи
  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Расчёт траектории
  const calculateTrajectory = useCallback(async () => {
    setIsCalculating(true);
    addLog('Начало расчёта траектории...', 'info');
    
    try {
      // Конфигурируем робота с текущими параметрами
      addLog('Конфигурация робота...', 'info');
      await robotApi.configureRobot(state);
      addLog('Робот успешно сконфигурирован', 'success');

      // Если контурное управление - настраиваем контур
      if (state.movementType === 'contour') {
        if (state.trajectory.type === 'line') {
          const { x1, x2, y1, y2, speed } = state.trajectory.line;
          if (x1 != null && x2 != null && y1 != null && y2 != null) {
            addLog('Установка линейного контура...', 'info');
            await robotApi.setLineContour(x1, x2, y1, y2, speed || 1);
          }
        } else if (state.trajectory.type === 'circle') {
          const { x, y, radius, speed } = state.trajectory.circle;
          if (x != null && y != null && radius != null) {
            addLog('Установка кругового контура...', 'info');
            await robotApi.setCircleContour(x, y, radius, speed || 1);
          }
        }
      }
      
      // Выполняем расчёт
      addLog('Расчёт траектории...', 'info');
      const result = await robotApi.calculateTrajectory();
      
      if (result.success) {
        setCalculationResult(result);
        addLog(`Расчёт завершён успешно. Точек траектории: ${result.trajectory_length}`, 'success');
        addLog(`Тип робота: ${result.robot_type}`, 'info');
        addLog(`Тип управления: ${result.type_of_control}`, 'info');
        
        // Логируем качество регулирования
        if (result.quality_link_1) {
          addLog(`Звено 1 - Средняя ошибка: ${result.quality_link_1.avg_error?.toFixed(6)}, Время регулирования: ${result.quality_link_1.avg_reg_time?.toFixed(4)} с`, 'info');
        }
        if (result.quality_link_2) {
          addLog(`Звено 2 - Средняя ошибка: ${result.quality_link_2.avg_error?.toFixed(6)}, Время регулирования: ${result.quality_link_2.avg_reg_time?.toFixed(4)} с`, 'info');
        }
      } else {
        addLog('Ошибка при расчёте траектории', 'error');
      }
      
      return result;
    } catch (error) {
      addLog(`Ошибка: ${error.message}`, 'error');
      console.error('Calculation error:', error);
      throw error;
    } finally {
      setIsCalculating(false);
    }
  }, [state, addLog]);

  // Загрузка файла конфигурации
  const loadConfigFile = useCallback(async (file) => {
    try {
      addLog(`Загрузка файла: ${file.name}...`, 'info');
      const result = await robotApi.uploadConfigFile(file);
      
      if (result.success && result.state) {
        // Обновляем состояние данными из файла
        setState(prev => ({
          ...prev,
          ...result.state,
        }));
        // Запоминаем имя загруженного файла
        setCurrentFileName(file.name);
        addLog(`Файл "${result.filename}" успешно загружен`, 'success');
        return result;
      } else {
        throw new Error('Не удалось загрузить файл');
      }
    } catch (error) {
      addLog(`Ошибка загрузки файла: ${error.message}`, 'error');
      throw error;
    }
  }, [addLog]);

  // Текущее имя файла для "Сохранить"
  const [currentFileName, setCurrentFileName] = useState('robot_config.txt');

  // Сохранение файла конфигурации (с текущим именем)
  const saveConfigFile = useCallback(async () => {
    try {
      addLog(`Сохранение конфигурации как "${currentFileName}"...`, 'info');
      await robotApi.downloadConfigFile(state, currentFileName);
      addLog('Файл успешно сохранён', 'success');
    } catch (error) {
      addLog(`Ошибка сохранения файла: ${error.message}`, 'error');
      throw error;
    }
  }, [state, addLog, currentFileName]);

  // Сохранение файла конфигурации с выбором имени
  const saveConfigFileAs = useCallback(async () => {
    const filename = prompt('Введите имя файла:', currentFileName);
    if (!filename) {
      return; // Пользователь отменил
    }
    
    try {
      addLog(`Сохранение конфигурации как "${filename}"...`, 'info');
      const result = await robotApi.downloadConfigFile(state, filename);
      setCurrentFileName(result.filename); // Запоминаем новое имя
      addLog('Файл успешно сохранён', 'success');
    } catch (error) {
      addLog(`Ошибка сохранения файла: ${error.message}`, 'error');
      throw error;
    }
  }, [state, addLog, currentFileName]);

  const openDialog = (name) => {
    setDialogs(prev => ({ ...prev, [name]: true }));
  };

  const closeDialog = (name) => {
    setDialogs(prev => ({ ...prev, [name]: false }));
  };

  // Authentication functions
  const handleLogin = (token, username, isAdmin = false) => {
    localStorage.setItem('auth_token', token);
    localStorage.setItem('username', username);
    localStorage.setItem('is_admin', isAdmin ? 'true' : 'false');
    setUser({ token, username, isAdmin });
    closeDialog('login');
    closeDialog('register');
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('username');
    localStorage.removeItem('is_admin');
    setUser(null);
  };

  // Ref для input загрузки файла
  const fileInputRef = React.useRef(null);

  // Обработчик выбора файла
  const handleFileSelect = useCallback(async (event) => {
    const file = event.target.files?.[0];
    if (file) {
      try {
        await loadConfigFile(file);
        alert('Данные успешно загружены!');
      } catch (error) {
        alert(`Ошибка загрузки: ${error.message}`);
      }
    }
    // Сбрасываем input для возможности повторной загрузки того же файла
    event.target.value = '';
  }, [loadConfigFile]);

  // Actions object - all menu actions
  const actions = {
    show_creators_info: () => openDialog('creators'),
    show_register_dialog: () => openDialog('register'),
    show_login_dialog: () => openDialog('login'),
    logout: handleLogout,
    // Загрузить из базы данных
    load_data: () => openDialog('loadConfig'),
    // Сохранить в базу данных (если есть текущая конфигурация - обновить, иначе открыть диалог)
    save_data: () => {
      if (currentConfigId) {
        // Если есть текущая конфигурация - открываем диалог сохранения
        openDialog('saveConfig');
      } else {
        // Если нет - тоже открываем диалог для ввода имени
        openDialog('saveConfig');
      }
    },
    // Сохранить как - всегда открывает диалог для нового имени
    save_data_as: () => openDialog('saveConfig'),
    // Скачать файл на компьютер
    download_data: async () => {
      try {
        await saveConfigFileAs();
      } catch (error) {
        if (error.message) {
          alert(`Ошибка скачивания: ${error.message}`);
        }
      }
    },
    // Загрузить файл с компьютера
    upload_data: () => fileInputRef.current?.click(),
    show_robot_type_dialog: () => openDialog('robotType'),
    show_movement_type_dialog: () => openDialog('movementType'),
    show_cartesian_params_dialog: () => openDialog('cartesianParams'),
    show_cartesian_limits_dialog: () => openDialog('cartesianLimits'),
    show_scara_params_dialog: () => openDialog('scaraParams'),
    show_scara_limits_dialog: () => openDialog('scaraLimits'),
    show_cylindrical_params_dialog: () => openDialog('cylindricalParams'),
    show_cylindrical_limits_dialog: () => openDialog('cylindricalLimits'),
    show_coler_params_dialog: () => openDialog('colerParams'),
    show_coler_limits_dialog: () => openDialog('colerLimits'),
    show_motor_params_dialog: () => openDialog('motorParams'),
    show_regulator_params_dialog: () => openDialog('regulatorParams'),
    show_calculator_dialog: () => openDialog('calculator'),
    show_cyclegram_dialog: () => openDialog('cyclegram'),
    show_trajectory_type_dialog: () => openDialog('trajectoryType'),
    show_graph_settings_dialog: () => openDialog('graphSettings'),
    draw_workspace: async () => {
      try {
        await calculateTrajectory();
      } catch (error) {
        alert(`Ошибка расчёта: ${error.message}`);
      }
    },
    calculate_trajectory: async () => {
      try {
        await calculateTrajectory();
      } catch (error) {
        alert(`Ошибка расчёта: ${error.message}`);
      }
    },
    show_admin_panel: () => openDialog('adminPanel'),
    show_change_password: () => openDialog('changePassword'),
    show_spline_cyclegram: () => openDialog('splineCyclegram'),
  };

  const updateState = (updates) => {
    setState(prev => {
      const newState = { ...prev };
      Object.keys(updates).forEach(key => {
        const value = updates[key];
        if (typeof value === 'object' && value !== null && !Array.isArray(value) && !(value instanceof Date)) {
          // Deep merge for nested objects
          newState[key] = { ...prev[key], ...value };
        } else {
          newState[key] = value;
        }
      });
      return newState;
    });
  };

  return (
    <AppContext.Provider value={{ 
      state, 
      setState,
      updateState, 
      actions, 
      dialogs, 
      openDialog, 
      closeDialog, 
      user, 
      handleLogin,
      calculationResult,
      setCalculationResult,
      isCalculating,
      calculateTrajectory,
      logs,
      addLog,
      clearLogs,
      loadConfigFile,
      saveConfigFile,
      currentConfigId,
      setCurrentConfigId,
      currentConfigName,
      setCurrentConfigName,
    }}>
      {/* Скрытый input для загрузки файлов */}
      <input
        type="file"
        ref={fileInputRef}
        accept=".txt"
        style={{ display: 'none' }}
        onChange={handleFileSelect}
      />
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <TopMenu />
        <div id="mainWrapper">
          <div id="centralArea">
            <aside id="leftDock">
              <DateTimeWidget />
              <WeatherWidget />
            </aside>
            <main id="centerContent">
              <Tabs />
            </main>
          </div>
          <StatusBar />
        </div>

        {/* All dialogs */}
        <RobotTypeDialog />
        <MovementTypeDialog />
        <CartesianParamsDialog />
        <CartesianLimitsDialog />
        <ScaraParamsDialog />
        <ScaraLimitsDialog />
        <CylindricalParamsDialog />
        <CylindricalLimitsDialog />
        <ColerParamsDialog />
        <ColerLimitsDialog />
        <MotorParamsDialog />
        <RegulatorParamsDialog />
        <CalculatorDialog />
        <CyclegramDialog />
        <TrajectoryTypeDialog />
        <LineParamsDialog />
        <CircleParamsDialog />
        <GraphSettingsDialog />
        <CreatorsDialog />
        <LoginDialog />
        <RegisterDialog />
        <SaveConfigDialog />
        <LoadConfigDialog />
        <AdminPanelDialog />
        <ChangePasswordDialog />
        <SplineCyclegramDialog />
      </div>
    </AppContext.Provider>
  );
}

export default App;

