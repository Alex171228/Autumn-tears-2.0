import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function ColerLimitsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.colerLimits);
  const [formData, setFormData] = useState({
    a2Min: '', a2Max: '', q1Min: '', q1Max: '',
    q3Min: '', q3Max: '', zMin: '', zMax: '',
  });

  useEffect(() => {
    if (dialogs.colerLimits) {
      const l = state.colerLimits;
      setFormData({
        a2Min: l.a2Min ?? '', a2Max: l.a2Max ?? '',
        q1Min: l.q1Min ?? '', q1Max: l.q1Max ?? '',
        q3Min: l.q3Min ?? '', q3Max: l.q3Max ?? '',
        zMin: l.zMin ?? '', zMax: l.zMax ?? '',
      });
    }
  }, [dialogs.colerLimits, state.colerLimits]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const a2Min = parseField(formData.a2Min);
    const a2Max = parseField(formData.a2Max);
    const q1Min = parseField(formData.q1Min);
    const q1Max = parseField(formData.q1Max);
    const q3Min = parseField(formData.q3Min);
    const q3Max = parseField(formData.q3Max);
    const zMin = parseField(formData.zMin);
    const zMax = parseField(formData.zMax);

    if ([a2Min, a2Max, q1Min, q1Max, q3Min, q3Max, zMin, zMax].some(v => v === null)) {
      alert("Некорректные ограничения по координатам для Колер.");
      return;
    }

    updateState({
      colerLimits: { a2Min, a2Max, q1Min, q1Max, q3Min, q3Max, zMin, zMax }
    });
    closeDialog('colerLimits');
  };

  const handleHelp = () => {
    alert(`На обобщенные координаты робота Колер наложены следующие ограничения:

q1min - минимально возможное значение угла поворота 1 звена;
q1max - максимально возможное значение угла поворота 1 звена;
a2min - минимально возможное значение линейного перемещения 2 звена;
a2max - максимальное возможное значение линейного перемещения 2 звена;
q3min - минимальное возможное значение угла поворота 3 звена;
q3max - максимальное возможное значение угла поворота 3 звена;
zmin - минимальное возможное значение линейного перемещения 3 звена;
zmax - максимально возможное значение линейного перемещения 3 звена.`);
  };

  if (!dialogs.colerLimits) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('colerLimits'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Ограничения по координатам Колер</div>
        <div className="dlg-form">
          <div className="dlg-form-row">
            <label htmlFor="col_a2min">A1min</label>
            <input id="col_a2min" type="number" step="0.001" value={formData.a2Min}
              onChange={(e) => setFormData({ ...formData, a2Min: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="col_a2max">A2max</label>
            <input id="col_a2max" type="number" step="0.001" value={formData.a2Max}
              onChange={(e) => setFormData({ ...formData, a2Max: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="col_q1min">Q1min</label>
            <input id="col_q1min" type="number" step="0.001" value={formData.q1Min}
              onChange={(e) => setFormData({ ...formData, q1Min: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="col_q1max">Q1max</label>
            <input id="col_q1max" type="number" step="0.001" value={formData.q1Max}
              onChange={(e) => setFormData({ ...formData, q1Max: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="col_q3min">Q3min</label>
            <input id="col_q3min" type="number" step="0.001" value={formData.q3Min}
              onChange={(e) => setFormData({ ...formData, q3Min: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="col_q3max">Q3max</label>
            <input id="col_q3max" type="number" step="0.001" value={formData.q3Max}
              onChange={(e) => setFormData({ ...formData, q3Max: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="col_zmin">Zmin</label>
            <input id="col_zmin" type="number" step="0.001" value={formData.zMin}
              onChange={(e) => setFormData({ ...formData, zMin: e.target.value })} />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="col_zmax">Zmax</label>
            <input id="col_zmax" type="number" step="0.001" value={formData.zMax}
              onChange={(e) => setFormData({ ...formData, zMax: e.target.value })} />
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>Помощь</button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('colerLimits')}>Отменить</button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default ColerLimitsDialog;

