import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function CircleParamsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.circleParams);
  const [formData, setFormData] = useState({
    x: '', y: '', radius: '', speed: '',
  });

  useEffect(() => {
    if (dialogs.circleParams) {
      const p = state.trajectory.circle;
      setFormData({
        x: p.x ?? '', y: p.y ?? '',
        radius: p.radius ?? '', speed: p.speed ?? '',
      });
    }
  }, [dialogs.circleParams, state.trajectory.circle]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const x = parseField(formData.x);
    const y = parseField(formData.y);
    const radius = parseField(formData.radius);
    const speed = parseField(formData.speed);

    if ([x, y, radius, speed].some(v => v === null)) {
      alert("Некорректные параметры окружности. Проверьте значения.");
      return;
    }

    updateState({
      trajectory: {
        ...state.trajectory,
        circle: { x, y, radius, speed }
      }
    });
    closeDialog('circleParams');
  };

  const handleShow = () => {
    const p = state.trajectory.circle;
    alert("Параметры окружности:\n" +
      "x = " + (p.x ?? formData.x) + "\n" +
      "y = " + (p.y ?? formData.y) + "\n" +
      "Радиус = " + (p.radius ?? formData.radius) + "\n" +
      "Скорость = " + (p.speed ?? formData.speed));
  };

  if (!dialogs.circleParams) return null;

  return (
    <dialog ref={dialogRef} className="dlg-circle-wide" onClick={(e) => handleBackdropClick(e, () => closeDialog('circleParams'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Параметры окружности</div>
        <div className="dlg-form">
          <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '8px' }}>
            Параметры окружности
          </div>
          <div className="dlg-form-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0,1fr))', gap: '10px' }}>
            <div>
              <label htmlFor="circle_x">x</label><br />
              <input
                id="circle_x"
                type="number"
                step="0.001"
                value={formData.x}
                onChange={(e) => setFormData({ ...formData, x: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="circle_y">y</label><br />
              <input
                id="circle_y"
                type="number"
                step="0.001"
                value={formData.y}
                onChange={(e) => setFormData({ ...formData, y: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="circle_radius">Радиус</label><br />
              <input
                id="circle_radius"
                type="number"
                step="0.001"
                value={formData.radius}
                onChange={(e) => setFormData({ ...formData, radius: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="circle_speed">Скорость</label><br />
              <input
                id="circle_speed"
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

export default CircleParamsDialog;

