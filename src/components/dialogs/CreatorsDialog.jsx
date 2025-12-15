import React from 'react';
import { useAppState } from '../../App';
import { useDraggableDialog } from '../../hooks/useDraggableDialog';

function CreatorsDialog() {
  const { dialogs, closeDialog } = useAppState();
  const { dialogRef, dragRef, handleBackdropClick } = useDraggableDialog(dialogs.creators);

  if (!dialogs.creators) return null;

  return (
    <dialog ref={dialogRef} className="dlg-creators" onClick={(e) => handleBackdropClick(e, () => closeDialog('creators'))}>
      <div className="dlg">
        <div className="dlg-header" ref={dragRef}>Создатели</div>
        <div className="dlg-form" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '22px', fontWeight: 'bold', marginBottom: '10px' }}>
            Создатели
          </div>
          <div style={{ fontSize: '18px', marginBottom: '10px' }}>
            Руководитель проекта: Шишков А.Д.
          </div>
          <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '10px' }}>
            Бюджет разработки
          </div>
          <img
            src="/static/ohota.jpg"
            alt="Создатели"
            style={{ maxWidth: '90%', borderRadius: '8px', marginTop: '10px' }}
          />
        </div>
        <div className="dlg-footer">
          <div className="dlg-footer-row">
            <button type="button" className="dlg-btn dlg-btn-ok" onClick={() => closeDialog('creators')}>
              OK
            </button>
          </div>
        </div>
      </div>
    </dialog>
  );
}

export default CreatorsDialog;

