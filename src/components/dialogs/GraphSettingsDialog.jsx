import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function GraphSettingsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.graphSettings);
  const [coordType, setCoordType] = useState(state.graphSettings.coordType);
  const [showSpline, setShowSpline] = useState(state.graphSettings.showSpline);

  useEffect(() => {
    if (dialogs.graphSettings) {
      setCoordType(state.graphSettings.coordType);
      setShowSpline(state.graphSettings.showSpline);
    }
  }, [dialogs.graphSettings, state.graphSettings]);

  const handleOk = () => {
    updateState({
      graphSettings: {
        coordType,
        showSpline,
      }
    });
    closeDialog('graphSettings');
  };

  const handleHelp = () => {
    alert(`В данном режиме необходимо выбрать тип и количество выводимых переменных и запустить расчёт.

Типы графиков:
• Обобщённые координаты - зависимость обобщённых координат от времени
• Декартовы (плоскость) - траектория в декартовых координатах
• Декартовы (время) - зависимость декартовых координат от времени
• Скорости - зависимость скоростей от времени
• Ускорения - зависимость ускорений от времени
• Напряжение - зависимость напряжения от времени
• Ток - зависимость тока от времени
• Моменты - зависимость моментов от времени

Чекбокс "Показать сплайн" включает сглаживание траектории сплайном.`);
  };

  if (!dialogs.graphSettings) return null;

  return (
    <dialog ref={dialogRef} className="dlg-graph" onClick={(e) => handleBackdropClick(e, () => closeDialog('graphSettings'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Настройки графика</div>
        <div className="dlg-form">
          <fieldset className="group-box">
            <legend>Тип координат</legend>
            <div className="graph-section">
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="general"
                  checked={coordType === "general"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Обобщённые от времени
              </label>
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="plane"
                  checked={coordType === "plane"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Декартовы на плоскости
              </label>
            </div>
            <div className="graph-subtitle">Дополнительные</div>
            <div className="graph-section">
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="time"
                  checked={coordType === "time"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Декартовы от времени
              </label>
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="speed"
                  checked={coordType === "speed"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Обобщённые скорости
              </label>
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="accel"
                  checked={coordType === "accel"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Обобщённые ускорения
              </label>
            </div>
            <div className="graph-subtitle">Внутренние</div>
            <div className="graph-section">
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="voltage"
                  checked={coordType === "voltage"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Напряжение
              </label>
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="voltage_star"
                  checked={coordType === "voltage_star"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Напряжение* (Напряжение - ЭДС)
              </label>
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="current"
                  checked={coordType === "current"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Ток
              </label>
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="motor_moment"
                  checked={coordType === "motor_moment"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Момент электродвижущий
              </label>
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="load_moment"
                  checked={coordType === "load_moment"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Момент нагрузки
              </label>
              <label className="graph-radio">
                <input
                  type="radio"
                  name="graphCoordType"
                  value="moment_star"
                  checked={coordType === "moment_star"}
                  onChange={(e) => setCoordType(e.target.value)}
                />
                Момент* (МЭ - М нагрузки)
              </label>
            </div>
          </fieldset>
          <fieldset className="group-box">
            <legend>Отображение сплайна</legend>
            <label className="graph-radio">
              <input
                type="checkbox"
                checked={showSpline}
                onChange={(e) => setShowSpline(e.target.checked)}
              />
              Показать сплайн
            </label>
          </fieldset>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>Помощь</button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('graphSettings')}>Отмена</button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default GraphSettingsDialog;

