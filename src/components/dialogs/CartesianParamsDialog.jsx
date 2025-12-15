import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function CartesianParamsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const [formData, setFormData] = useState({
    mass1: '',
    mass2: '',
    mass3: '',
    moment: '',
  });
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.cartesianParams);

  useEffect(() => {
    if (dialogs.cartesianParams) {
      const p = state.cartesianParams;
      setFormData({
        mass1: p.mass1 ?? '',
        mass2: p.mass2 ?? '',
        mass3: p.mass3 ?? '',
        moment: p.moment ?? '',
      });
    }
  }, [dialogs.cartesianParams, state.cartesianParams]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const m1 = parseField(formData.mass1);
    const m2 = parseField(formData.mass2);
    const m3 = parseField(formData.mass3);
    const mo = parseField(formData.moment);

    if ([m1, m2, m3, mo].some(v => v === null)) {
      alert("Некорректные значения масс/момента инерции.");
      return;
    }

    updateState({
      cartesianParams: { mass1: m1, mass2: m2, mass3: m3, moment: mo }
    });
    closeDialog('cartesianParams');
  };

  const handleHelp = () => {
    alert(`Конструктивные параметры робота ДЕКАРТ:

m1 - масса 1 звена;
m2 - масса 2 звена;
m3 - масса 3 звена;
Jc3 - момент инерции 3 звена относительно центра инерции 3 звена.

Декартовый робот имеет 4 степени подвижности, причем 3 степени обеспечивают перемещение рабочего органа по трем взаимноперпендикулярным осям X, Y, Z, а четвертая выполняет операцию вращения (ориентации) рабочего органа.`);
  };

  if (!dialogs.cartesianParams) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('cartesianParams'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Конструктивные параметры Декартового робота</div>
        <div className="dlg-form">
          <div className="dlg-form-row">
            <label htmlFor="mass1">Масса 1-го звена</label>
            <input
              id="mass1"
              type="number"
              step="0.001"
              value={formData.mass1}
              onChange={(e) => setFormData({ ...formData, mass1: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="mass2">Масса 2-го звена</label>
            <input
              id="mass2"
              type="number"
              step="0.001"
              value={formData.mass2}
              onChange={(e) => setFormData({ ...formData, mass2: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="mass3">Масса 3-го звена</label>
            <input
              id="mass3"
              type="number"
              step="0.001"
              value={formData.mass3}
              onChange={(e) => setFormData({ ...formData, mass3: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="moment">Момент инерции</label>
            <input
              id="moment"
              type="number"
              step="0.001"
              value={formData.moment}
              onChange={(e) => setFormData({ ...formData, moment: e.target.value })}
            />
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>
              ОК
            </button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>
              Помощь
            </button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('cartesianParams')}>
              Отменить
            </button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default CartesianParamsDialog;

