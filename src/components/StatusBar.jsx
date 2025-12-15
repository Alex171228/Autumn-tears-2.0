import React from 'react';
import { useAppState } from '../App';

function StatusBar() {
  const { state } = useAppState();

  const robotTypeLabel = () => {
    switch (state.robotType) {
      case "cartesian": return "Декартовый";
      case "cylindrical": return "Цилиндрический";
      case "scara": return "Скара";
      case "coler": return "Колер";
      default: return state.robotType;
    }
  };

  const movementTypeLabel = () => {
    switch (state.movementType) {
      case "position": return "Позиционное";
      case "contour": return "Контурное";
      default: return state.movementType;
    }
  };

  let extra = "";
  if (state.robotType === "cartesian") {
    const p = state.cartesianParams;
    extra = (p.mass1 != null)
      ? `Декарт: m1=${p.mass1}, m2=${p.mass2}, m3=${p.mass3}, J=${p.moment}`
      : "Декарт: параметры не заданы";
  } else if (state.robotType === "scara") {
    const p = state.scaraParams;
    extra = (p.moment1 != null)
      ? `Скара: M1=${p.moment1}, M2=${p.moment2}, M3=${p.moment3}`
      : "Скара: параметры не заданы";
  } else if (state.robotType === "cylindrical") {
    const p = state.cylindricalParams;
    extra = (p.moment1 != null)
      ? `Цилиндр: M1=${p.moment1}, M2=${p.moment2}, M3=${p.moment3}`
      : "Цилиндр: параметры не заданы";
  } else if (state.robotType === "coler") {
    const p = state.colerParams;
    extra = (p.moment1 != null)
      ? `Колер: M1=${p.moment1}, M2=${p.moment2}, M3=${p.moment3}`
      : "Колер: параметры не заданы";
  }

  const traj = state.trajectory;
  const trajLabel = (traj.type === "circle") ? "Окружность" : "Прямая";

  return (
    <footer id="statusBar">
      <div id="statusLeft">Готово</div>
      <div id="statusRight">
        Тип робота: {robotTypeLabel()} | Тип движения: {movementTypeLabel()} | {extra}
      </div>
    </footer>
  );
}

export default StatusBar;

