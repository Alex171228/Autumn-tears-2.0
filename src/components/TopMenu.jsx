import React, { useState } from 'react';
import { useAppState } from '../App';

function TopMenu() {
  const { actions, user, isCalculating } = useAppState();
  const [hoveredMenu, setHoveredMenu] = useState(null);

  const handleAction = (actionName) => {
    if (actions[actionName]) {
      actions[actionName]();
    }
  };

  return (
    <div id="menuBar">
      <div className="menu-root">
        <button className="menu-button" onClick={() => handleAction('show_creators_info')}>
          ≡
        </button>
      </div>

      {/* Меню "Авторизация" или имя пользователя */}
      {user ? (
        <div
          className="menu-root menu-item"
          onMouseEnter={() => setHoveredMenu('user')}
          onMouseLeave={() => setHoveredMenu(null)}
        >
          <div className="menu-label">{user.username}</div>
          <div className="submenu" onMouseEnter={() => setHoveredMenu('user')} onMouseLeave={() => setHoveredMenu(null)}>
            <button onClick={() => handleAction('show_change_password')}>Сменить пароль</button>
            <button onClick={() => handleAction('logout')}>Выйти</button>
          </div>
        </div>
      ) : (
        <div
          className="menu-root menu-item"
          onMouseEnter={() => setHoveredMenu('auth')}
          onMouseLeave={() => setHoveredMenu(null)}
        >
          <div className="menu-label">Авторизация</div>
          <div className="submenu" onMouseEnter={() => setHoveredMenu('auth')} onMouseLeave={() => setHoveredMenu(null)}>
            <button onClick={() => handleAction('show_register_dialog')}>Регистрация</button>
            <button onClick={() => handleAction('show_login_dialog')}>Войти</button>
          </div>
        </div>
      )}

      {/* Меню "Данные" */}
      <div
        className="menu-root menu-item"
        onMouseEnter={() => setHoveredMenu('data')}
        onMouseLeave={() => setHoveredMenu(null)}
      >
        <div className="menu-label">Данные</div>
        <div className="submenu" onMouseEnter={() => setHoveredMenu('data')} onMouseLeave={() => setHoveredMenu(null)}>
          <div style={{ padding: '4px 12px', fontSize: '11px', color: '#718096', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Облако
          </div>
          <button onClick={() => handleAction('load_data')}>Мои конфигурации</button>
          <button onClick={() => handleAction('save_data')}>Сохранить</button>
          <button onClick={() => handleAction('save_data_as')}>Сохранить как</button>
          <div style={{ height: '1px', background: '#e2e8f0', margin: '8px 0' }}></div>
          <div style={{ padding: '4px 12px', fontSize: '11px', color: '#718096', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Файл
          </div>
          <button onClick={() => handleAction('upload_data')}>Загрузить из файла</button>
          <button onClick={() => handleAction('download_data')}>Скачать в файл</button>
        </div>
      </div>

      {/* Меню "Режим работы" */}
      <div
        className="menu-root menu-item"
        onMouseEnter={() => setHoveredMenu('mode')}
        onMouseLeave={() => setHoveredMenu(null)}
      >
        <div className="menu-label">Режим работы</div>
        <div className="submenu" onMouseEnter={() => setHoveredMenu('mode')} onMouseLeave={() => setHoveredMenu(null)}>
          <button onClick={() => handleAction('show_robot_type_dialog')}>Тип робота</button>
          <button onClick={() => handleAction('show_movement_type_dialog')}>Тип движения</button>
        </div>
      </div>

      {/* Меню "Параметры" */}
      <div
        className="menu-root menu-item"
        onMouseEnter={() => setHoveredMenu('params')}
        onMouseLeave={() => setHoveredMenu(null)}
      >
        <div className="menu-label">Параметры</div>
        <div className="submenu" onMouseEnter={() => setHoveredMenu('params')} onMouseLeave={() => setHoveredMenu(null)}>
          {/* Робот */}
          <div
            className="submenu-item"
            onMouseEnter={() => setHoveredMenu('robot')}
            onMouseLeave={() => setHoveredMenu('params')}
          >
            <div className="submenu-label">Робот</div>
            <div className="submenu-level2" onMouseEnter={() => setHoveredMenu('robot')} onMouseLeave={() => setHoveredMenu('params')}>
              {/* Декартовый */}
              <div
                className="submenu-item"
                onMouseEnter={() => setHoveredMenu('cartesian')}
                onMouseLeave={() => setHoveredMenu('robot')}
              >
                <div className="submenu-label">Декартовый</div>
                <div className="submenu-level2" onMouseEnter={() => setHoveredMenu('cartesian')} onMouseLeave={() => setHoveredMenu('robot')}>
                  <button onClick={() => handleAction('show_cartesian_params_dialog')}>
                    Конструктивные параметры
                  </button>
                  <button onClick={() => handleAction('show_cartesian_limits_dialog')}>
                    Ограничения по координатам
                  </button>
                </div>
              </div>
              {/* Цилиндрический */}
              <div
                className="submenu-item"
                onMouseEnter={() => setHoveredMenu('cylindrical')}
                onMouseLeave={() => setHoveredMenu('robot')}
              >
                <div className="submenu-label">Цилиндрический</div>
                <div className="submenu-level2" onMouseEnter={() => setHoveredMenu('cylindrical')} onMouseLeave={() => setHoveredMenu('robot')}>
                  <button onClick={() => handleAction('show_cylindrical_params_dialog')}>
                    Конструктивные параметры
                  </button>
                  <button onClick={() => handleAction('show_cylindrical_limits_dialog')}>
                    Ограничения по координатам
                  </button>
                </div>
              </div>
              {/* Скара */}
              <div
                className="submenu-item"
                onMouseEnter={() => setHoveredMenu('scara')}
                onMouseLeave={() => setHoveredMenu('robot')}
              >
                <div className="submenu-label">Скара</div>
                <div className="submenu-level2" onMouseEnter={() => setHoveredMenu('scara')} onMouseLeave={() => setHoveredMenu('robot')}>
                  <button onClick={() => handleAction('show_scara_params_dialog')}>
                    Конструктивные параметры
                  </button>
                  <button onClick={() => handleAction('show_scara_limits_dialog')}>
                    Ограничения по координатам
                  </button>
                </div>
              </div>
              {/* Колер */}
              <div
                className="submenu-item"
                onMouseEnter={() => setHoveredMenu('coler')}
                onMouseLeave={() => setHoveredMenu('robot')}
              >
                <div className="submenu-label">Колер</div>
                <div className="submenu-level2" onMouseEnter={() => setHoveredMenu('coler')} onMouseLeave={() => setHoveredMenu('robot')}>
                  <button onClick={() => handleAction('show_coler_params_dialog')}>
                    Конструктивные параметры
                  </button>
                  <button onClick={() => handleAction('show_coler_limits_dialog')}>
                    Ограничения по координатам
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Система управления */}
          <div
            className="submenu-item"
            onMouseEnter={() => setHoveredMenu('control')}
            onMouseLeave={() => setHoveredMenu('params')}
          >
            <div className="submenu-label">Система управления</div>
            <div className="submenu-level2" onMouseEnter={() => setHoveredMenu('control')} onMouseLeave={() => setHoveredMenu('params')}>
              <button onClick={() => handleAction('show_motor_params_dialog')}>
                Параметры двигателей
              </button>
              <button onClick={() => handleAction('show_regulator_params_dialog')}>
                Параметры регуляторов
              </button>
            </div>
          </div>

          {/* Вычислитель */}
          <button onClick={() => handleAction('show_calculator_dialog')}>Вычислитель</button>

          {/* Движение */}
          <div
            className="submenu-item"
            onMouseEnter={() => setHoveredMenu('movement')}
            onMouseLeave={() => setHoveredMenu('params')}
          >
            <div className="submenu-label">Движение</div>
            <div className="submenu-level2" onMouseEnter={() => setHoveredMenu('movement')} onMouseLeave={() => setHoveredMenu('params')}>
              <button onClick={() => handleAction('show_cyclegram_dialog')}>Позиционное</button>
              <button onClick={() => handleAction('show_trajectory_type_dialog')}>Контурное</button>
            </div>
          </div>
        </div>
      </div>

      {/* Меню "Расчет" */}
      <div
        className="menu-root menu-item"
        onMouseEnter={() => setHoveredMenu('calc')}
        onMouseLeave={() => setHoveredMenu(null)}
      >
        <div className="menu-label">Расчет</div>
        <div className="submenu" onMouseEnter={() => setHoveredMenu('calc')} onMouseLeave={() => setHoveredMenu(null)}>
          <button onClick={() => handleAction('show_graph_settings_dialog')}>Настройки графика</button>
          <button 
            onClick={() => handleAction('calculate_trajectory')}
            disabled={isCalculating}
            style={{ fontWeight: 'bold' }}
          >
            {isCalculating ? 'Расчёт...' : 'Рассчитать траекторию'}
          </button>
          <button onClick={() => handleAction('draw_workspace')}>Рабочая область</button>
        </div>
      </div>

      {/* Меню "Админ" - только для администраторов */}
      {user?.isAdmin && (
        <div
          className="menu-root menu-item"
          onMouseEnter={() => setHoveredMenu('admin')}
          onMouseLeave={() => setHoveredMenu(null)}
        >
          <div className="menu-label" style={{ color: '#667eea', fontWeight: 600 }}>Админ</div>
          <div className="submenu" onMouseEnter={() => setHoveredMenu('admin')} onMouseLeave={() => setHoveredMenu(null)}>
            <button onClick={() => handleAction('show_admin_panel')}>
              Управление пользователями
            </button>
            <button onClick={() => handleAction('show_admin_panel')}>
              Все конфигурации
            </button>
          </div>
        </div>
      )}

      <div className="menu-spacer"></div>
    </div>
  );
}

export default TopMenu;

