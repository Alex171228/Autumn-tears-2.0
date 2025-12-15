import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function CyclegramDialog() {
  const { state, updateState, dialogs, closeDialog, openDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.cyclegram);
  const cycleKeys = ["t", "q1", "q2", "q3", "q4"];
  const [formData, setFormData] = useState(() => {
    const data = {};
    cycleKeys.forEach(key => {
      data[key] = Array(9).fill('');
    });
    return data;
  });

  useEffect(() => {
    if (dialogs.cyclegram) {
      const c = state.cyclegram;
      const newData = {};
      cycleKeys.forEach(key => {
        newData[key] = c[key].map(v => v != null ? String(v) : '');
      });
      setFormData(newData);
    }
  }, [dialogs.cyclegram, state.cyclegram]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const c = {};
    for (const key of cycleKeys) {
      c[key] = [];
      for (let i = 0; i < 9; i++) {
        const v = parseField(formData[key][i]);
        if (v === null) {
          alert("Некорректные значения циклограммы в строке " + key + ", столбец " + (i + 1));
          return;
        }
        c[key][i] = v;
      }
    }

    updateState({ cyclegram: c });
    closeDialog('cyclegram');
  };

  const handleHelp = () => {
    alert(`Задайте циклограмму движения.

В первой строке задаются моменты времени (в порядке возрастания), в остальных - программные значения обобщенных координат.

Циклограмма представляет собой прямоугольную матрицу, в которой заданы последовательность моментов времени и соответствующие значения обобщенных координат.`);
  };

  const handleSpline = () => {
    openDialog('splineCyclegram');
  };

  if (!dialogs.cyclegram) return null;

  return (
    <dialog ref={dialogRef} className="dlg-cycle" onClick={(e) => handleBackdropClick(e, () => closeDialog('cyclegram'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Циклограмма</div>
        <div className="dlg-form">
          <div id="cyclegramGrid">
            <table style={{ borderCollapse: 'separate', borderSpacing: 0, fontSize: '14px', width: '100%' }}>
              <thead>
                <tr>
                  <th style={{ padding: '2px 4px' }}></th>
                  {Array.from({ length: 9 }, (_, i) => (
                    <th key={i} style={{ padding: '2px 4px' }}>{i + 1}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cycleKeys.map(key => (
                  <tr key={key}>
                    <td style={{ padding: '2px 4px' }}>{key}</td>
                    {Array.from({ length: 9 }, (_, i) => (
                      <td key={i} style={{ padding: '2px 4px' }}>
                        <input
                          type="number"
                          step="0.001"
                          style={{ fontSize: '14px' }}
                          value={formData[key][i]}
                          onChange={(e) => {
                            const newRow = [...formData[key]];
                            newRow[i] = e.target.value;
                            setFormData({ ...formData, [key]: newRow });
                          }}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>Помощь</button>
            <button type="button" className="dlg-btn dlg-btn-help" style={{ background: 'steelblue' }} onClick={handleSpline}>
              Циклограмма сплайна
            </button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('cyclegram')}>Отменить</button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default CyclegramDialog;

