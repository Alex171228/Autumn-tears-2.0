import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function MovementTypeDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const [selectedType, setSelectedType] = useState(state.movementType);
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.movementType);

  useEffect(() => {
    if (dialogs.movementType) {
      setSelectedType(state.movementType);
    }
  }, [dialogs.movementType, state.movementType]);

  const handleOk = () => {
    updateState({ movementType: selectedType });
    closeDialog('movementType');
  };

  const handleHelp = () => {
    alert(`Выберите тип движения: Позиционное или Контурное.

ПОЗИЦИОННОЕ УПРАВЛЕНИЕ:
Циклограмма представляет собой прямоугольную матрицу, в которой заданы последовательность моментов времени и соответствующие значения обобщенных координат. При задании циклограммы следует задавать значения моментов времени в возрастающем порядке.

КОНТУРНОЕ УПРАВЛЕНИЕ:
Контурное управление предполагает задание траектории движения рабочего органа робота и его скорости. Траектории движения рабочего органа могут быть двух видов - прямая линия и окружность. При задании параметров траектории следует учитывать, что эта траектория должна целиком лежать в пределах рабочей зоны робота.`);
  };

  if (!dialogs.movementType) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('movementType'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Тип движения</div>
        <div className="dlg-group">
          <div className="dlg-radio">
            <label>
              <input
                type="radio"
                name="movementType"
                value="position"
                checked={selectedType === "position"}
                onChange={(e) => setSelectedType(e.target.value)}
              />
              Позиционное
            </label>
          </div>
          <div className="dlg-radio">
            <label>
              <input
                type="radio"
                name="movementType"
                value="contour"
                checked={selectedType === "contour"}
                onChange={(e) => setSelectedType(e.target.value)}
              />
              Контурное
            </label>
          </div>
        </div>
        <div className="dlg-footer">
          <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>
            Помощь
          </button>
          <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>
            OK
          </button>
        </div>
      </div>
    </dialog>
  );
}

export default MovementTypeDialog;

