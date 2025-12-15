import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function LineParamsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.lineParams);
  const [formData, setFormData] = useState({
    x1: '', x2: '', y1: '', y2: '', speed: '',
  });

  useEffect(() => {
    if (dialogs.lineParams) {
      const p = state.trajectory.line;
      setFormData({
        x1: p.x1 ?? '', x2: p.x2 ?? '',
        y1: p.y1 ?? '', y2: p.y2 ?? '',
        speed: p.speed ?? '',
      });
    }
  }, [dialogs.lineParams, state.trajectory.line]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const x1 = parseField(formData.x1);
    const x2 = parseField(formData.x2);
    const y1 = parseField(formData.y1);
    const y2 = parseField(formData.y2);
    const speed = parseField(formData.speed);

    if ([x1, x2, y1, y2, speed].some(v => v === null)) {
      alert("Некорректные параметры прямой. Проверьте значения.");
      return;
    }

    updateState({
      trajectory: {
        ...state.trajectory,
        line: { x1, x2, y1, y2, speed }
      }
    });
    closeDialog('lineParams');
  };

  const handleShow = () => {
    const p = state.trajectory.line;
    alert("Параметры прямой:\n" +
      "x1 = " + (p.x1 ?? formData.x1) + "\n" +
      "x2 = " + (p.x2 ?? formData.x2) + "\n" +
      "y1 = " + (p.y1 ?? formData.y1) + "\n" +
      "y2 = " + (p.y2 ?? formData.y2) + "\n" +
      "Скорость = " + (p.speed ?? formData.speed));
  };

  if (!dialogs.lineParams) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('lineParams'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Параметры прямой</div>
        <div className="dlg-form">
          <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px' }}>
            Параметры прямой
          </div>
          <div className="dlg-form-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0,1fr))', gap: '10px' }}>
            <div>
              <label htmlFor="line_x1">x1</label><br />
              <input
                id="line_x1"
                type="number"
                step="0.001"
                value={formData.x1}
                onChange={(e) => setFormData({ ...formData, x1: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="line_y1">y1</label><br />
              <input
                id="line_y1"
                type="number"
                step="0.001"
                value={formData.y1}
                onChange={(e) => setFormData({ ...formData, y1: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="line_x2">x2</label><br />
              <input
                id="line_x2"
                type="number"
                step="0.001"
                value={formData.x2}
                onChange={(e) => setFormData({ ...formData, x2: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="line_y2">y2</label><br />
              <input
                id="line_y2"
                type="number"
                step="0.001"
                value={formData.y2}
                onChange={(e) => setFormData({ ...formData, y2: e.target.value })}
              />
            </div>
            <div style={{ gridColumn: '1 / span 2' }}>
              <label htmlFor="line_speed">Скорость</label><br />
              <input
                id="line_speed"
                type="number"
                step="0.001"
                value={formData.speed}
                onChange={(e) => setFormData({ ...formData, speed: e.target.value })}
              />
            </div>
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" style={{ background: 'yellow' }} onClick={handleShow}>
              Показать
            </button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default LineParamsDialog;

