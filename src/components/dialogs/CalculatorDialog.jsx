import React, { useState, useEffect } from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function CalculatorDialog() {
  const { state, updateState, dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.calculator);
  const [formData, setFormData] = useState({
    bitDepth: '',
    exchangeCycle: '',
    controlCycle: '',
    filterConstant: '',
  });

  useEffect(() => {
    if (dialogs.calculator) {
      const c = state.calculatorValues;
      setFormData({
        bitDepth: c.bitDepth ?? '',
        exchangeCycle: c.exchangeCycle ?? '',
        controlCycle: c.controlCycle ?? '',
        filterConstant: c.filterConstant ?? '',
      });
    }
  }, [dialogs.calculator, state.calculatorValues]);

  const parseField = (value) => {
    const v = parseFloat(String(value).replace(",", "."));
    return Number.isNaN(v) ? null : v;
  };

  const handleOk = () => {
    const bitDepth = parseField(formData.bitDepth);
    const exchangeCycle = parseField(formData.exchangeCycle);
    const controlCycle = parseField(formData.controlCycle);
    const filterConstant = parseField(formData.filterConstant);

    if ([bitDepth, exchangeCycle, controlCycle, filterConstant].some(v => v === null)) {
      alert("Некорректные значения вычислителя. Проверьте введённые данные.");
      return;
    }

    updateState({
      calculatorValues: {
        bitDepth,
        exchangeCycle,
        controlCycle,
        filterConstant,
      }
    });
    closeDialog('calculator');
  };

  const handleHelp = () => {
    alert(`В рамках данного пакета прикладных программ имитируется работа вычислительных устройств, управляющих работой робота.

За основу принята двухуровневая иерархическая схема, при которой центральное вычислительное устройство (ЦВУ) решает задачи координации работы вычислительных устройств (ВУ), решает траекторные задачи и выдает уставки на ВУ. ВУ, в свою очередь, осуществляет управление приводами робота.

К параметрам ЦВУ и ВУ относятся:
- p - разрядность ЭВМ (определяет точность решения траектории);
- tоб - цикл обмена ЦВУ и ВУ (такт выдачи установок на ВУ);
- tупр - цикл управления (такт выдачи управляющих сигналов);
- tф - постоянная экспоненциального фильтра.`);
  };

  if (!dialogs.calculator) return null;

  return (
    <dialog ref={dialogRef} className="dlg" onClick={(e) => handleBackdropClick(e, () => closeDialog('calculator'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Вычислитель</div>
        <div className="dlg-form">
          <div className="dlg-form-row">
            <label htmlFor="calc_bitDepth">Разрядность</label>
            <input
              id="calc_bitDepth"
              type="number"
              step="1"
              value={formData.bitDepth}
              onChange={(e) => setFormData({ ...formData, bitDepth: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="calc_exchangeCycle">Такт обмена</label>
            <input
              id="calc_exchangeCycle"
              type="number"
              step="0.001"
              value={formData.exchangeCycle}
              onChange={(e) => setFormData({ ...formData, exchangeCycle: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="calc_controlCycle">Такт управления</label>
            <input
              id="calc_controlCycle"
              type="number"
              step="0.001"
              value={formData.controlCycle}
              onChange={(e) => setFormData({ ...formData, controlCycle: e.target.value })}
            />
          </div>
          <div className="dlg-form-row">
            <label htmlFor="calc_filterConstant">Постоянная фильтра</label>
            <input
              id="calc_filterConstant"
              type="number"
              step="0.001"
              value={formData.filterConstant}
              onChange={(e) => setFormData({ ...formData, filterConstant: e.target.value })}
            />
          </div>
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={handleOk}>ОК</button>
            <button type="button" className="dlg-btn dlg-btn-help" onClick={handleHelp}>Помощь</button>
            <button type="button" className="dlg-btn dlg-btn-cancel" onClick={() => closeDialog('calculator')}>Отменить</button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default CalculatorDialog;

