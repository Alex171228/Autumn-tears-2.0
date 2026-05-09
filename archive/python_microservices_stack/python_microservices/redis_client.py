"""
Модуль для работы с Redis — хранение состояний калькуляторов по сессиям.
Замена in-memory dict robot_calculators.
"""

import os
import json
import logging
from dataclasses import asdict
from typing import Optional

import redis

from python_microservices.trajectory_calculator import TrajectoryCalculator, RobotState

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CALCULATOR_TTL = 60 * 60 * 24  # 24 часа

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """Получить клиент Redis (lazy singleton)"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def _calculator_key(session_id: str) -> str:
    """Ключ для хранения калькулятора в Redis"""
    return f"calculator:{session_id}"


def _serialize_calculator(calc: TrajectoryCalculator) -> str:
    """Сериализовать состояние калькулятора в JSON"""
    data = {
        # Состояние робота (dataclass -> dict)
        "state": asdict(calc.state),

        # Результаты расчётов
        "output_time_array": calc.output_time_array,
        "trajectory_q_1": calc.trajectory_q_1,
        "trajectory_q_2": calc.trajectory_q_2,
        "real_trajectory_x": calc.real_trajectory_x,
        "real_trajectory_y": calc.real_trajectory_y,
        "cyclogram_real_x": calc.cyclogram_real_x,
        "cyclogram_real_y": calc.cyclogram_real_y,

        # Массивы звена 1
        "q_error_array_1": calc.q_error_array_1,
        "SAU_SUM_array_1": calc.SAU_SUM_array_1,
        "U_array_1": calc.U_array_1,
        "Ustar_array_1": calc.Ustar_array_1,
        "I_array_1": calc.I_array_1,
        "M_ed_array_1": calc.M_ed_array_1,
        "M1_array": calc.M1_array,
        "M_ed_corrected_array_1": calc.M_ed_corrected_array_1,
        "acceleration_array_1": calc.acceleration_array_1,
        "speed_array_1": calc.speed_array_1,

        # Массивы звена 2
        "q_error_array_2": calc.q_error_array_2,
        "SAU_SUM_array_2": calc.SAU_SUM_array_2,
        "U_array_2": calc.U_array_2,
        "Ustar_array_2": calc.Ustar_array_2,
        "I_array_2": calc.I_array_2,
        "M_ed_array_2": calc.M_ed_array_2,
        "M2_array": calc.M2_array,
        "M_ed_corrected_array_2": calc.M_ed_corrected_array_2,
        "acceleration_array_2": calc.acceleration_array_2,
        "speed_array_2": calc.speed_array_2,

        # Контурное управление
        "t_contur": calc.t_contur,
        "x_contur": calc.x_contur,
        "y_contur": calc.y_contur,
        "t_contur_control": calc.t_contur_control,
        "q1_contur_control": calc.q1_contur_control,
        "q2_contur_control": calc.q2_contur_control,

        # Сплайн
        "q_1_spline": calc.q_1_spline,
        "q_2_spline": calc.q_2_spline,
        "t_spline": calc.t_spline,

        # Качество регулирования
        "error_1": calc.error_1,
        "avg_error_1": calc.avg_error_1,
        "median_error_1": calc.median_error_1,
        "reg_time_1": calc.reg_time_1,
        "avg_reg_time_1": calc.avg_reg_time_1,
        "median_reg_time_1": calc.median_reg_time_1,

        "error_2": calc.error_2,
        "avg_error_2": calc.avg_error_2,
        "median_error_2": calc.median_error_2,
        "reg_time_2": calc.reg_time_2,
        "avg_reg_time_2": calc.avg_reg_time_2,
        "median_reg_time_2": calc.median_reg_time_2,
    }
    return json.dumps(data)


def _deserialize_calculator(json_str: str) -> TrajectoryCalculator:
    """Десериализовать калькулятор из JSON"""
    data = json.loads(json_str)

    # Восстанавливаем RobotState
    state_dict = data.get("state", {})
    state = RobotState(**state_dict)

    calc = TrajectoryCalculator(state=state)

    # Восстанавливаем результаты расчётов
    calc.output_time_array = data.get("output_time_array", [])
    calc.trajectory_q_1 = data.get("trajectory_q_1", [])
    calc.trajectory_q_2 = data.get("trajectory_q_2", [])
    calc.real_trajectory_x = data.get("real_trajectory_x", [])
    calc.real_trajectory_y = data.get("real_trajectory_y", [])
    calc.cyclogram_real_x = data.get("cyclogram_real_x", [0] * 9)
    calc.cyclogram_real_y = data.get("cyclogram_real_y", [0] * 9)

    # Массивы звена 1
    calc.q_error_array_1 = data.get("q_error_array_1", [])
    calc.SAU_SUM_array_1 = data.get("SAU_SUM_array_1", [])
    calc.U_array_1 = data.get("U_array_1", [])
    calc.Ustar_array_1 = data.get("Ustar_array_1", [])
    calc.I_array_1 = data.get("I_array_1", [])
    calc.M_ed_array_1 = data.get("M_ed_array_1", [])
    calc.M1_array = data.get("M1_array", [])
    calc.M_ed_corrected_array_1 = data.get("M_ed_corrected_array_1", [])
    calc.acceleration_array_1 = data.get("acceleration_array_1", [])
    calc.speed_array_1 = data.get("speed_array_1", [])

    # Массивы звена 2
    calc.q_error_array_2 = data.get("q_error_array_2", [])
    calc.SAU_SUM_array_2 = data.get("SAU_SUM_array_2", [])
    calc.U_array_2 = data.get("U_array_2", [])
    calc.Ustar_array_2 = data.get("Ustar_array_2", [])
    calc.I_array_2 = data.get("I_array_2", [])
    calc.M_ed_array_2 = data.get("M_ed_array_2", [])
    calc.M2_array = data.get("M2_array", [])
    calc.M_ed_corrected_array_2 = data.get("M_ed_corrected_array_2", [])
    calc.acceleration_array_2 = data.get("acceleration_array_2", [])
    calc.speed_array_2 = data.get("speed_array_2", [])

    # Контурное управление
    calc.t_contur = data.get("t_contur", [])
    calc.x_contur = data.get("x_contur", [])
    calc.y_contur = data.get("y_contur", [])
    calc.t_contur_control = data.get("t_contur_control", [])
    calc.q1_contur_control = data.get("q1_contur_control", [])
    calc.q2_contur_control = data.get("q2_contur_control", [])

    # Сплайн
    calc.q_1_spline = data.get("q_1_spline", [])
    calc.q_2_spline = data.get("q_2_spline", [])
    calc.t_spline = data.get("t_spline", [])

    # Качество регулирования
    calc.error_1 = data.get("error_1", [])
    calc.avg_error_1 = data.get("avg_error_1", 0)
    calc.median_error_1 = data.get("median_error_1", 0)
    calc.reg_time_1 = data.get("reg_time_1", [])
    calc.avg_reg_time_1 = data.get("avg_reg_time_1", 0)
    calc.median_reg_time_1 = data.get("median_reg_time_1", 0)

    calc.error_2 = data.get("error_2", [])
    calc.avg_error_2 = data.get("avg_error_2", 0)
    calc.median_error_2 = data.get("median_error_2", 0)
    calc.reg_time_2 = data.get("reg_time_2", [])
    calc.avg_reg_time_2 = data.get("avg_reg_time_2", 0)
    calc.median_reg_time_2 = data.get("median_reg_time_2", 0)

    return calc


def save_calculator(session_id: str, calc: TrajectoryCalculator) -> None:
    """Сохранить калькулятор в Redis с TTL"""
    try:
        r = get_redis()
        key = _calculator_key(session_id)
        json_str = _serialize_calculator(calc)
        r.setex(key, CALCULATOR_TTL, json_str)
    except Exception as e:
        logger.error(f"Ошибка сохранения калькулятора в Redis: {e}")
        raise


def load_calculator(session_id: str) -> Optional[TrajectoryCalculator]:
    """Загрузить калькулятор из Redis. Возвращает None если не найден."""
    try:
        r = get_redis()
        key = _calculator_key(session_id)
        json_str = r.get(key)
        if json_str is None:
            return None
        return _deserialize_calculator(json_str)
    except Exception as e:
        logger.error(f"Ошибка загрузки калькулятора из Redis: {e}")
        return None


def delete_calculator(session_id: str) -> bool:
    """Удалить калькулятор из Redis. Возвращает True если удалён."""
    try:
        r = get_redis()
        key = _calculator_key(session_id)
        deleted = r.delete(key)
        return deleted > 0
    except Exception as e:
        logger.error(f"Ошибка удаления калькулятора из Redis: {e}")
        return False
