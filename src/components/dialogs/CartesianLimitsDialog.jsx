import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function CartesianLimitsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.cartesianLimits);
  const [formData, setFormData] = useState({
    Xmin: '', Xmax: '',
    Ymin: '', Ymax: '',
    Zmin: '', Zmax: '',
    Qmin: '', Qmax: '',
  });

  useEffect(() => {
    if (dialogs.cartesianLimits) {
      const l = state.cartesianLimits;
      setFormData({
        Xmin: l.Xmin ?? '', Xmax: l.Xmax ?? '',
        Ymin: l.Ymin ?? '', Ymax: l.Ymax ?? '',
        Zmin: l.Zmin ?? '', Zmax: l.Zmax ?? '',
        Qmin: l.Qmin ?? '', Qmax: l.Qmax ?? '',
      });
    }
  }, [dialogs.cartesianLimits, state.cartesianLimits]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const Xmin = parseField(formData.Xmin);
    const Xmax = parseField(formData.Xmax);
    const Ymin = parseField(formData.Ymin);
    const Ymax = parseField(formData.Ymax);
    const Zmin = parseField(formData.Zmin);
    const Zmax = parseField(formData.Zmax);
    const Qmin = parseField(formData.Qmin);
    const Qmax = parseField(formData.Qmax);

    if ([Xmin, Xmax, Ymin, Ymax, Zmin, Zmax, Qmin, Qmax].some(v => v === null)) {
      alert("Некорректные ограничения по координатам.");
      return;
    }

    updateState({
      cartesianLimits: { Xmin, Xmax, Ymin, Ymax, Zmin, Zmax, Qmin, Qmax }
    });
    closeDialog('cartesianLimits');
  };

  const handleHelp = () => {
    alert(`На обобщенные координаты робота Декарт наложены следующие ограничения:

xmin - минимально возможное значение линейного перемещения 1 звена;
xmax - максимально возможное значение линейного перемещения 1 звена;
ymin - минимально возможное значение линейного перемещения 2 звена;
ymax - максимально возможное значение линейного перемещения 2 звена;
q3min - минимально возможное значение угла поворота 3 звена;
q3max - максимально возможное значение угла поворота 3 звена;
zmin - минимально возможное значение линейного перемещения 3 звена;
zmax - максимально возможное значение линейного перемещения 3 звена.`);
  };

  if (!dialogs.cartesianLimits) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('cartesianLimits'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Ограничения по координатам</div>
        <div className="dlg-form">
          <div className="dlg-form-row">
            <label htmlFor="limXmin">X Мин:</label>
            <input
              id="limXmin"
              type="number"
              step="0.001"
              value={formData.Xmin}
              onChange={(e) => setFormData({ ...formData, Xmin: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="limXmax">X Макс:</label>
            <input
              id="limXmax"
              type="number"
              step="0.001"
              value={formData.Xmax}
              onChange={(e) => setFormData({ ...formData, Xmax: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="limYmin">Y Мин:</label>
            <input
              id="limYmin"
              type="number"
              step="0.001"
              value={formData.Ymin}
              onChange={(e) => setFormData({ ...formData, Ymin: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="limYmax">Y Макс:</label>
            <input
              id="limYmax"
              type="number"
              step="0.001"
              value={formData.Ymax}
              onChange={(e) => setFormData({ ...formData, Ymax: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="limZmin">Z Мин:</label>
            <input
              id="limZmin"
              type="number"
              step="0.001"
              value={formData.Zmin}
              onChange={(e) => setFormData({ ...formData, Zmin: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="limZmax">Z Макс:</label>
            <input
              id="limZmax"
              type="number"
              step="0.001"
              value={formData.Zmax}
              onChange={(e) => setFormData({ ...formData, Zmax: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="limQmin">Q Мин:</label>
            <input
              id="limQmin"
              type="number"
              step="0.001"
              value={formData.Qmin}
              onChange={(e) => setFormData({ ...formData, Qmin: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="limQmax">Q Макс:</label>
            <input
              id="limQmax"
              type="number"
              step="0.001"
              value={formData.Qmax}
              onChange={(e) => setFormData({ ...formData, Qmax: e.target.value })}
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
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('cartesianLimits')}>
              Отменить
            </button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default CartesianLimitsDialog;

