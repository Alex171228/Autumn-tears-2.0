import { useEffect, useRef } from 'react';

export function useDraggableDialog(isOpen) {
  const dialogRef = useRef(null);
  const dragRef = useRef(null);
  const isDraggingRef = useRef(false);
  const startXRef = useRef(0);
  const startYRef = useRef(0);
  const startLeftRef = useRef(0);
  const startTopRef = useRef(0);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      dialog.showModal();
      // Центрируем при открытии
      const centerX = window.innerWidth / 2;
      const centerY = window.innerHeight / 2;
      dialog.style.left = `${centerX}px`;
      dialog.style.top = `${centerY}px`;
      dialog.style.transform = 'translate(-50%, -50%)';
    } else {
      dialog.close();
    }
  }, [isOpen]);

  useEffect(() => {
    const dialog = dialogRef.current;
    const dragHandle = dragRef.current;
    if (!dialog || !dragHandle || !isOpen) return;

    const handleMouseDown = (e) => {
      isDraggingRef.current = true;
      const rect = dialog.getBoundingClientRect();
      startXRef.current = e.clientX;
      startYRef.current = e.clientY;
      startLeftRef.current = rect.left;
      startTopRef.current = rect.top;
      dialog.style.cursor = 'grabbing';
      e.preventDefault();
      e.stopPropagation();
    };

    const handleMouseMove = (e) => {
      if (!isDraggingRef.current) return;
      
      const deltaX = e.clientX - startXRef.current;
      const deltaY = e.clientY - startYRef.current;
      
      const newLeft = startLeftRef.current + deltaX;
      const newTop = startTopRef.current + deltaY;
      
      dialog.style.left = `${newLeft}px`;
      dialog.style.top = `${newTop}px`;
      dialog.style.transform = 'none';
    };

    const handleMouseUp = () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        if (dialogRef.current) {
          dialogRef.current.style.cursor = '';
        }
      }
    };

    dragHandle.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      dragHandle.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isOpen]);

  const handleBackdropClick = (e, onClose) => {
    if (e.target === dialogRef.current && !isDraggingRef.current) {
      if (onClose) {
        onClose();
      } else if (dialogRef.current) {
        dialogRef.current.close();
      }
    }
  };

  return { dialogRef, dragRef, handleBackdropClick };
}
