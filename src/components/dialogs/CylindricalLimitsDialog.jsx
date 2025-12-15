import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function CylindricalLimitsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.cylindricalLimits);
  const [formData, setFormData] = useState({
    q1Min: '', q1Max: '', a2Min: '', a2Max: '',
    q3Min: '', q3Max: '', zMin: '', zMax: '',
  });

  useEffect(() => {
    if (dialogs.cylindricalLimits) {
      const l = state.cylindricalLimits;
      setFormData({
        q1Min: l.q1Min ?? '', q1Max: l.q1Max ?? '',
        a2Min: l.a2Min ?? '', a2Max: l.a2Max ?? '',
        q3Min: l.q3Min ?? '', q3Max: l.q3Max ?? '',
        zMin: l.zMin ?? '', zMax: l.zMax ?? '',
      });
    }
  }, [dialogs.cylindricalLimits, state.cylindricalLimits]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const q1Min = parseField(formData.q1Min);
    const q1Max = parseField(formData.q1Max);
    const a2Min = parseField(formData.a2Min);
    const a2Max = parseField(formData.a2Max);
    const q3Min = parseField(formData.q3Min);
    const q3Max = parseField(formData.q3Max);
    const zMin = parseField(formData.zMin);
    const zMax = parseField(formData.zMax);

    if ([q1Min, q1Max, a2Min, a2Max, q3Min, q3Max, zMin, zMax].some(v => v === null)) {
      alert("Некорректные ограничения по координатам для Цилиндр.");
      return;
    }

    updateState({
      cylindricalLimits: { q1Min, q1Max, a2Min, a2Max, q3Min, q3Max, zMin, zMax }
    });
    closeDialog('cylindricalLimits');
  };

  const handleHelp = () => {
    alert(`На обобщенные координаты робота Цилиндр наложены следующие ограничения:

q1min - минимально возможное значение угла поворота 1 звена;
q1max - максимально возможное значение угла поворота 1 звена;
a2min - минимально возможное значение линейного перемещения 2 звена;
a2max - максимальное возможное значение линейного перемещения 2 звена;
q3min - минимальное возможное значение угла поворота 3 звена;
q3max - максимальное возможное значение угла поворота 3 звена;
zmin - минимальное возможное значение линейного перемещения 3 звена;
zmax - максимально возможное значение линейного перемещения 3 звена.`);
  };

  if (!dialogs.cylindricalLimits) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('cylindricalLimits'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Ограничения по координатам Цилиндр</div>
        <div className="dlg-form">
          <div className="dlg-form-row">
            <label htmlFor="cyl_q1min">Q1min</label>
            <input id="cyl_q1min" type="number" step="0.001" value={formData.q1Min}
              onChange={(e) => setFormData({ ...formData, q1Min: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="cyl_q1max">Q1max</label>
            <input id="cyl_q1max" type="number" step="0.001" value={formData.q1Max}
              onChange={(e) => setFormData({ ...formData, q1Max: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="cyl_a2min">A2min</label>
            <input id="cyl_a2min" type="number" step="0.001" value={formData.a2Min}
              onChange={(e) => setFormData({ ...formData, a2Min: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="cyl_a2max">A2max</label>
            <input id="cyl_a2max" type="number" step="0.001" value={formData.a2Max}
              onChange={(e) => setFormData({ ...formData, a2Max: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="cyl_q3min">Q3min</label>
            <input id="cyl_q3min" type="number" step="0.001" value={formData.q3Min}
              onChange={(e) => setFormData({ ...formData, q3Min: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="cyl_q3max">Q3max</label>
            <input id="cyl_q3max" type="number" step="0.001" value={formData.q3Max}
              onChange={(e) => setFormData({ ...formData, q3Max: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="cyl_zmin">Zmin</label>
            <input id="cyl_zmin" type="number" step="0.001" value={formData.zMin}
              onChange={(e) => setFormData({ ...formData, zMin: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="cyl_zmax">Zmax</label>
            <input id="cyl_zmax" type="number" step="0.001" value={formData.zMax}
              onChange={(e) => setFormData({ ...formData, zMax: e.target.value })} />
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>Помощь</button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('cylindricalLimits')}>Отменить</button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default CylindricalLimitsDialog;

