import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function ScaraParamsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.scaraParams);
  const [formData, setFormData] = useState({
    moment1: '', moment2: '', moment3: '',
    length1: '', length2: '', distance: '',
    mass2: '', mass3: '',
  });

  useEffect(() => {
    if (dialogs.scaraParams) {
      const p = state.scaraParams;
      setFormData({
        moment1: p.moment1 ?? '', moment2: p.moment2 ?? '', moment3: p.moment3 ?? '',
        length1: p.length1 ?? '', length2: p.length2 ?? '', distance: p.distance ?? '',
        mass2: p.mass2 ?? '', mass3: p.mass3 ?? '',
      });
    }
  }, [dialogs.scaraParams, state.scaraParams]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const moment1 = parseField(formData.moment1);
    const moment2 = parseField(formData.moment2);
    const moment3 = parseField(formData.moment3);
    const length1 = parseField(formData.length1);
    const length2 = parseField(formData.length2);
    const distance = parseField(formData.distance);
    const mass2 = parseField(formData.mass2);
    const mass3 = parseField(formData.mass3);

    if ([moment1, moment2, moment3, length1, length2, distance, mass2, mass3].some(v => v === null)) {
      alert("Некорректные конструктивные параметры Скара.");
      return;
    }

    updateState({
      scaraParams: { moment1, moment2, moment3, length1, length2, distance, mass2, mass3 }
    });
    closeDialog('scaraParams');
  };

  const handleHelp = () => {
    alert(`Конструктивные параметры робота СКАРА:

J01 - момент инерции 1 звена относительно шарнира O1 при вращении в горизонтальной плоскости;
Jc2 - момент инерции 2 звена относительно центра инерции 2 звена;
Jc3 - момент инерции 3 звена относительно центра инерции 3 звена;
a1 - длина 1 звена;
a2 - длина 2 звена;
r2 - расстояние от начала 2 звена до его центра инерции;
m2 - масса 2 звена;
m3 - масса 3 звена.`);
  };

  if (!dialogs.scaraParams) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('scaraParams'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Конструктивные параметры Скара</div>
        <div className="dlg-form">
          <div className="dlg-form-row">
            <label htmlFor="sc_moment1">Момент 1-го звена</label>
            <input id="sc_moment1" type="number" step="0.001" value={formData.moment1}
              onChange={(e) => setFormData({ ...formData, moment1: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_moment2">Момент 2-го звена</label>
            <input id="sc_moment2" type="number" step="0.001" value={formData.moment2}
              onChange={(e) => setFormData({ ...formData, moment2: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_moment3">Момент 3-го звена</label>
            <input id="sc_moment3" type="number" step="0.001" value={formData.moment3}
              onChange={(e) => setFormData({ ...formData, moment3: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_length1">Длина 1-го звена</label>
            <input id="sc_length1" type="number" step="0.001" value={formData.length1}
              onChange={(e) => setFormData({ ...formData, length1: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_length2">Длина 2-го звена</label>
            <input id="sc_length2" type="number" step="0.001" value={formData.length2}
              onChange={(e) => setFormData({ ...formData, length2: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_distance">Расстояние</label>
            <input id="sc_distance" type="number" step="0.001" value={formData.distance}
              onChange={(e) => setFormData({ ...formData, distance: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_mass2">Масса 2-го звена</label>
            <input id="sc_mass2" type="number" step="0.001" value={formData.mass2}
              onChange={(e) => setFormData({ ...formData, mass2: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_mass3">Масса 3-го звена</label>
            <input id="sc_mass3" type="number" step="0.001" value={formData.mass3}
              onChange={(e) => setFormData({ ...formData, mass3: e.target.value })} />
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>Помощь</button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('scaraParams')}>Отменить</button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default ScaraParamsDialog;

