import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function MotorParamsDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.motorParams);
  const [formData, setFormData] = useState({
    J1: '', J2: '', Te1: '', Te2: '',
    Umax1: '', Umax2: '', Fi1: '', Fi2: '',
    Ce1: '', Ce2: '', Ra1: '', Ra2: '',
    Cm1: '', Cm2: '',
  });

  useEffect(() => {
    if (dialogs.motorParams) {
      const m = state.motorParams;
      setFormData({
        J1: m.J[0] ?? '', J2: m.J[1] ?? '',
        Te1: m.Te[0] ?? '', Te2: m.Te[1] ?? '',
        Umax1: m.Umax[0] ?? '', Umax2: m.Umax[1] ?? '',
        Fi1: m.Fi[0] ?? '', Fi2: m.Fi[1] ?? '',
        Ce1: m.Ce[0] ?? '', Ce2: m.Ce[1] ?? '',
        Ra1: m.Ra[0] ?? '', Ra2: m.Ra[1] ?? '',
        Cm1: m.Cm[0] ?? '', Cm2: m.Cm[1] ?? '',
      });
    }
  }, [dialogs.motorParams, state.motorParams]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const J1 = parseField(formData.J1);
    const J2 = parseField(formData.J2);
    const Te1 = parseField(formData.Te1);
    const Te2 = parseField(formData.Te2);
    const Umax1 = parseField(formData.Umax1);
    const Umax2 = parseField(formData.Umax2);
    const Fi1 = parseField(formData.Fi1);
    const Fi2 = parseField(formData.Fi2);
    const Ce1 = parseField(formData.Ce1);
    const Ce2 = parseField(formData.Ce2);
    const Ra1 = parseField(formData.Ra1);
    const Ra2 = parseField(formData.Ra2);
    const Cm1 = parseField(formData.Cm1);
    const Cm2 = parseField(formData.Cm2);

    if ([J1, J2, Te1, Te2, Umax1, Umax2, Fi1, Fi2, Ce1, Ce2, Ra1, Ra2, Cm1, Cm2].some(v => v === null)) {
      alert("Некорректные параметры двигателей. Проверьте введённые значения.");
      return;
    }

    updateState({
      motorParams: {
        J: [J1, J2],
        Te: [Te1, Te2],
        Umax: [Umax1, Umax2],
        Fi: [Fi1, Fi2],
        Ce: [Ce1, Ce2],
        Ra: [Ra1, Ra2],
        Cm: [Cm1, Cm2],
      }
    });
    closeDialog('motorParams');
  };

  const handleHelp = () => {
    alert(`К числу параметров двигателя относятся:

J — момент инерции ротора;
T_e — электрическая постоянная;
Umax — максимальное напряжение двигателя;
Fi — магнитный поток;
Ce — коэффициент электрический;
Ra — сопротивление якоря;
Cм — коэффициент магнитный.

Обратите внимание, что значения должны быть числами.

Для базового варианта исходных данных для управления 1 и 2 степенями подвижности робота используется двигатель ДР-72-Н2-02, а для управления 3 и 4 степенями - двигатель ДПМ-30-Н2-04.`);
  };

  if (!dialogs.motorParams) return null;

  return (
    <dialog ref={dialogRef} className="dlg-wide" onClick={(e) => handleBackdropClick(e, () => closeDialog('motorParams'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Параметры двигателей</div>
        <div className="dlg-form">
          <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, fontSize: '14px' }}>
            <tbody>
              <tr>
                <td>J1</td>
                <td><input type="number" step="0.001" value={formData.J1}
                  onChange={(e) => setFormData({ ...formData, J1: e.target.value })} /></td>
                <td>J2</td>
                <td><input type="number" step="0.001" value={formData.J2}
                  onChange={(e) => setFormData({ ...formData, J2: e.target.value })} /></td>
              </tr>
              <tr>
                <td>T_e1</td>
                <td><input type="number" step="0.001" value={formData.Te1}
                  onChange={(e) => setFormData({ ...formData, Te1: e.target.value })} /></td>
                <td>T_e2</td>
                <td><input type="number" step="0.001" value={formData.Te2}
                  onChange={(e) => setFormData({ ...formData, Te2: e.target.value })} /></td>
              </tr>
              <tr>
                <td>Umax1</td>
                <td><input type="number" step="0.001" value={formData.Umax1}
                  onChange={(e) => setFormData({ ...formData, Umax1: e.target.value })} /></td>
                <td>Umax2</td>
                <td><input type="number" step="0.001" value={formData.Umax2}
                  onChange={(e) => setFormData({ ...formData, Umax2: e.target.value })} /></td>
              </tr>
              <tr>
                <td>Fi1</td>
                <td><input type="number" step="0.001" value={formData.Fi1}
                  onChange={(e) => setFormData({ ...formData, Fi1: e.target.value })} /></td>
                <td>Fi2</td>
                <td><input type="number" step="0.001" value={formData.Fi2}
                  onChange={(e) => setFormData({ ...formData, Fi2: e.target.value })} /></td>
              </tr>
              <tr>
                <td>Ce1</td>
                <td><input type="number" step="0.001" value={formData.Ce1}
                  onChange={(e) => setFormData({ ...formData, Ce1: e.target.value })} /></td>
                <td>Ce2</td>
                <td><input type="number" step="0.001" value={formData.Ce2}
                  onChange={(e) => setFormData({ ...formData, Ce2: e.target.value })} /></td>
              </tr>
              <tr>
                <td>Ra1</td>
                <td><input type="number" step="0.001" value={formData.Ra1}
                  onChange={(e) => setFormData({ ...formData, Ra1: e.target.value })} /></td>
                <td>Ra2</td>
                <td><input type="number" step="0.001" value={formData.Ra2}
                  onChange={(e) => setFormData({ ...formData, Ra2: e.target.value })} /></td>
              </tr>
              <tr>
                <td>Cm1</td>
                <td><input type="number" step="0.001" value={formData.Cm1}
                  onChange={(e) => setFormData({ ...formData, Cm1: e.target.value })} /></td>
                <td>Cm2</td>
                <td><input type="number" step="0.001" value={formData.Cm2}
                  onChange={(e) => setFormData({ ...formData, Cm2: e.target.value })} /></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>Помощь</button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('motorParams')}>Отменить</button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default MotorParamsDialog;

