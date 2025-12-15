import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function ScaraLimitsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.scaraLimits);
  const [formData, setFormData] = useState({
    q1Min: '', q1Max: '', q2Min: '', q2Max: '',
    q3Min: '', q3Max: '', zMin: '', zMax: '',
  });

  useEffect(() => {
    if (dialogs.scaraLimits) {
      const l = state.scaraLimits;
      setFormData({
        q1Min: l.q1Min ?? '', q1Max: l.q1Max ?? '',
        q2Min: l.q2Min ?? '', q2Max: l.q2Max ?? '',
        q3Min: l.q3Min ?? '', q3Max: l.q3Max ?? '',
        zMin: l.zMin ?? '', zMax: l.zMax ?? '',
      });
    }
  }, [dialogs.scaraLimits, state.scaraLimits]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const q1Min = parseField(formData.q1Min);
    const q1Max = parseField(formData.q1Max);
    const q2Min = parseField(formData.q2Min);
    const q2Max = parseField(formData.q2Max);
    const q3Min = parseField(formData.q3Min);
    const q3Max = parseField(formData.q3Max);
    const zMin = parseField(formData.zMin);
    const zMax = parseField(formData.zMax);

    if ([q1Min, q1Max, q2Min, q2Max, q3Min, q3Max, zMin, zMax].some(v => v === null)) {
      alert("Некорректные ограничения для Скара.");
      return;
    }

    updateState({
      scaraLimits: { q1Min, q1Max, q2Min, q2Max, q3Min, q3Max, zMin, zMax }
    });
    closeDialog('scaraLimits');
  };

  const handleHelp = () => {
    alert(`На обобщенные координаты робота Скара наложены следующие ограничения:

q1min - минимально возможное значение угла поворота 1 звена;
q1max - максимально возможное значение угла поворота 1 звена;
q2min - минимально возможное значение угла поворота 2 звена;
q2max - максимально возможное значение угла поворота 2 звена;
q3min - минимально возможное значение угла поворота 3 звена;
q3max - максимально возможное значение угла поворота 3 звена;
zmin - минимально возможное значение линейного перемещения 3 звена;
zmax - максимально возможное значение линейного перемещения 3 звена.`);
  };

  if (!dialogs.scaraLimits) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('scaraLimits'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Ограничения по координатам Скара</div>
        <div className="dlg-form">
          <div className="dlg-form-row">
            <label htmlFor="sc_q1min">Q1min</label>
            <input id="sc_q1min" type="number" step="0.001" value={formData.q1Min}
              onChange={(e) => setFormData({ ...formData, q1Min: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_q1max">Q1max</label>
            <input id="sc_q1max" type="number" step="0.001" value={formData.q1Max}
              onChange={(e) => setFormData({ ...formData, q1Max: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_q2min">Q2min</label>
            <input id="sc_q2min" type="number" step="0.001" value={formData.q2Min}
              onChange={(e) => setFormData({ ...formData, q2Min: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_q2max">Q2max</label>
            <input id="sc_q2max" type="number" step="0.001" value={formData.q2Max}
              onChange={(e) => setFormData({ ...formData, q2Max: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_q3min">Q3min</label>
            <input id="sc_q3min" type="number" step="0.001" value={formData.q3Min}
              onChange={(e) => setFormData({ ...formData, q3Min: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_q3max">Q3max</label>
            <input id="sc_q3max" type="number" step="0.001" value={formData.q3Max}
              onChange={(e) => setFormData({ ...formData, q3Max: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_zmin">Zmin</label>
            <input id="sc_zmin" type="number" step="0.001" value={formData.zMin}
              onChange={(e) => setFormData({ ...formData, zMin: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="sc_zmax">Zmax</label>
            <input id="sc_zmax" type="number" step="0.001" value={formData.zMax}
              onChange={(e) => setFormData({ ...formData, zMax: e.target.value })} />
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>Помощь</button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('scaraLimits')}>Отменить</button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default ScaraLimitsDialog;

