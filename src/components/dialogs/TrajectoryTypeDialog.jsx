import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function TrajectoryTypeDialog() {
  const { state, updateState, dialogs, closeDialog, openDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.trajectoryType);
  const [selectedType, setSelectedType] = useState(state.trajectory.type);

  useEffect(() => {
    if (dialogs.trajectoryType) {
      setSelectedType(state.trajectory.type);
    }
  }, [dialogs.trajectoryType, state.trajectory.type]);

  const handleOk = () => {
    updateState({
      trajectory: { ...state.trajectory, type: selectedType }
    });
    closeDialog('trajectoryType');
    
    // After selecting type, open the corresponding params dialog
    if (selectedType === "line") {
      openDialog('lineParams');
    } else {
      openDialog('circleParams');
    }
  };

  const handleHelp = () => {
    alert(`Контурное управление предполагает задание траектории движения рабочего органа робота и его скорости.

Траектории движения рабочего органа могут быть двух видов:
• ПРЯМАЯ ЛИНИЯ - движение по прямой между двумя точками
• ОКРУЖНОСТЬ - движение по окружности с заданным центром и радиусом

При задании параметров траектории следует учитывать, что эта траектория должна целиком лежать в пределах рабочей зоны робота.`);
  };

  if (!dialogs.trajectoryType) return null;

  return (
    <dialog ref={dialogRef} className="dlg-trajectory" onClick={(e) => handleBackdropClick(e, () => closeDialog('trajectoryType'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Выбор типа траектории</div>
        <div className="dlg-form">
          <div style={{ fontSize: '25px', fontWeight: 'bold', marginBottom: '10px' }}>
            Тип траектории
          </div>
          <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
            <label style={{ fontSize: '25px' }}>
              <input
                type="radio"
                name="trajectoryType"
                value="line"
                checked={selectedType === "line"}
                onChange={(e) => setSelectedType(e.target.value)}
              />
              Прямая
            </label>
            <label style={{ fontSize: '25px' }}>
              <input
                type="radio"
                name="trajectoryType"
                value="circle"
                checked={selectedType === "circle"}
                onChange={(e) => setSelectedType(e.target.value)}
              />
              Окружность
            </label>
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>Помощь</button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('trajectoryType')}>Отменить</button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default TrajectoryTypeDialog;

