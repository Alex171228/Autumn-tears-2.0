import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function RegulatorParamsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.regulatorParams);
  const [formData, setFormData] = useState({
    Kp1: '', Kp2: '', Kp3: '', Kp4: '',
    Ki1: '', Ki2: '', Ki3: '', Ki4: '',
    Kd1: '', Kd2: '', Kd3: '', Kd4: '',
  });

  useEffect(() => {
    if (dialogs.regulatorParams) {
      const r = state.regulatorParams;
      setFormData({
        Kp1: r.Kp[0] ?? '', Kp2: r.Kp[1] ?? '', Kp3: r.Kp[2] ?? '', Kp4: r.Kp[3] ?? '',
        Ki1: r.Ki[0] ?? '', Ki2: r.Ki[1] ?? '', Ki3: r.Ki[2] ?? '', Ki4: r.Ki[3] ?? '',
        Kd1: r.Kd[0] ?? '', Kd2: r.Kd[1] ?? '', Kd3: r.Kd[2] ?? '', Kd4: r.Kd[3] ?? '',
      });
    }
  }, [dialogs.regulatorParams, state.regulatorParams]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const Kp1 = parseField(formData.Kp1);
    const Kp2 = parseField(formData.Kp2);
    const Kp3 = parseField(formData.Kp3);
    const Kp4 = parseField(formData.Kp4);
    const Ki1 = parseField(formData.Ki1);
    const Ki2 = parseField(formData.Ki2);
    const Ki3 = parseField(formData.Ki3);
    const Ki4 = parseField(formData.Ki4);
    const Kd1 = parseField(formData.Kd1);
    const Kd2 = parseField(formData.Kd2);
    const Kd3 = parseField(formData.Kd3);
    const Kd4 = parseField(formData.Kd4);

    if ([Kp1, Kp2, Kp3, Kp4, Ki1, Ki2, Ki3, Ki4, Kd1, Kd2, Kd3, Kd4].some(v => v === null)) {
      alert("Некорректные параметры регуляторов. Проверьте введённые значения.");
      return;
    }

    updateState({
      regulatorParams: {
        Kp: [Kp1, Kp2, Kp3, Kp4],
        Ki: [Ki1, Ki2, Ki3, Ki4],
        Kd: [Kd1, Kd2, Kd3, Kd4],
      }
    });
    closeDialog('regulatorParams');
  };

  const handleHelp = () => {
    alert(`Параметры ПИД-регуляторов:

Кп - пропорциональный коэффициент;
Ки - интегральный коэффициент;
Кд - дифференциальный коэффициент.

Коэффициенты задаются для каждой из 4 степеней подвижности робота.`);
  };

  if (!dialogs.regulatorParams) return null;

  return (
    <dialog ref={dialogRef} className="dlg-wide dlg-wide-big" onClick={(e) => handleBackdropClick(e, () => closeDialog('regulatorParams'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Параметры регуляторов</div>
        <div className="dlg-form">
          <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, fontSize: '14px' }}>
            <tbody>
              <tr>
                <td>Kп1</td><td><input type="number" step="0.001" value={formData.Kp1}
                  onChange={(e) => setFormData({ ...formData, Kp1: e.target.value })} /></td>
                <td>Kп2</td><td><input type="number" step="0.001" value={formData.Kp2}
                  onChange={(e) => setFormData({ ...formData, Kp2: e.target.value })} /></td>
                <td>Kп3</td><td><input type="number" step="0.001" value={formData.Kp3}
                  onChange={(e) => setFormData({ ...formData, Kp3: e.target.value })} /></td>
                <td>Kп4</td><td><input type="number" step="0.001" value={formData.Kp4}
                  onChange={(e) => setFormData({ ...formData, Kp4: e.target.value })} /></td>
              </tr>
              <tr>
                <td>Kи1</td><td><input type="number" step="0.001" value={formData.Ki1}
                  onChange={(e) => setFormData({ ...formData, Ki1: e.target.value })} /></td>
                <td>Kи2</td><td><input type="number" step="0.001" value={formData.Ki2}
                  onChange={(e) => setFormData({ ...formData, Ki2: e.target.value })} /></td>
                <td>Kи3</td><td><input type="number" step="0.001" value={formData.Ki3}
                  onChange={(e) => setFormData({ ...formData, Ki3: e.target.value })} /></td>
                <td>Kи4</td><td><input type="number" step="0.001" value={formData.Ki4}
                  onChange={(e) => setFormData({ ...formData, Ki4: e.target.value })} /></td>
              </tr>
              <tr>
                <td>Kд1</td><td><input type="number" step="0.001" value={formData.Kd1}
                  onChange={(e) => setFormData({ ...formData, Kd1: e.target.value })} /></td>
                <td>Kд2</td><td><input type="number" step="0.001" value={formData.Kd2}
                  onChange={(e) => setFormData({ ...formData, Kd2: e.target.value })} /></td>
                <td>Kд3</td><td><input type="number" step="0.001" value={formData.Kd3}
                  onChange={(e) => setFormData({ ...formData, Kd3: e.target.value })} /></td>
                <td>Kд4</td><td><input type="number" step="0.001" value={formData.Kd4}
                  onChange={(e) => setFormData({ ...formData, Kd4: e.target.value })} /></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>Помощь</button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('regulatorParams')}>Отменить</button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default RegulatorParamsDialog;

