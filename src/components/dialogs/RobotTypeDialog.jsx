import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function RobotTypeDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const [selectedType, setSelectedType] = useState(state.robotType);
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.robotType);

  useEffect(() => {
    if (dialogs.robotType) {
      setSelectedType(state.robotType);
    }
  }, [dialogs.robotType, state.robotType]);

  const handleOk = () => {
    updateState({ robotType: selectedType });
    closeDialog('robotType');
  };

  const handleHelp = () => {
    alert(`Выберите тип робота, с которым вы будете работать в дальнейшем:

ДЕКАРТ - робот имеет 4 степени подвижности, 3 степени обеспечивают перемещение по осям X, Y, Z, четвертая выполняет вращение рабочего органа.

СКАРА - робот имеет 4 степени подвижности. 1 и 2 звенья перемещаются в горизонтальной плоскости, 3 звено может вращаться и перемещаться вертикально.

ЦИЛИНДР - робот имеет 4 степени подвижности. 1 звено вращается в горизонтальной плоскости, 2 звено совершает поступательное перемещение, 3 звено перемещается вертикально и вращается.

КОЛЕР - аналогичен цилиндрическому роботу.`);
  };

  if (!dialogs.robotType) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('robotType'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Тип робота</div>
        <div className="dlg-group">
          <div className="dlg-radio">
            <label>
              <input
                type="radio"
                name="robotType"
                value="cartesian"
                checked={selectedType === "cartesian"}
                onChange={(e) => setSelectedType(e.target.value)}
              />
              Декартовый
            </label>
          </div>
          <div className="dlg-radio">
            <label>
              <input
                type="radio"
                name="robotType"
                value="cylindrical"
                checked={selectedType === "cylindrical"}
                onChange={(e) => setSelectedType(e.target.value)}
              />
              Цилиндрический
            </label>
          </div>
          <div className="dlg-radio">
            <label>
              <input
                type="radio"
                name="robotType"
                value="scara"
                checked={selectedType === "scara"}
                onChange={(e) => setSelectedType(e.target.value)}
              />
              Скара
            </label>
          </div>
          <div className="dlg-radio">
            <label>
              <input
                type="radio"
                name="robotType"
                value="coler"
                checked={selectedType === "coler"}
                onChange={(e) => setSelectedType(e.target.value)}
              />
              Колер
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

export default RobotTypeDialog;

