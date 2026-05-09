"""
Pydantic модели для API запросов и ответов.
"""

from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional, Dict, Any
from enum import Enum


class RobotType(str, Enum):
    CARTESIAN = "Декартовый"
    SCARA = "Скара"
    CYLINDRICAL = "Цилиндрический"
    COLER = "Колер"


class ControlType(str, Enum):
    POSITIONAL = "Позиционное"
    CONTOUR = "Контурное"


class PlotType(str, Enum):
    DECART_PLANE = "decart_plane"
    OBOBSHENNIE_COORDINATES = "obobshennie_coordinates"
    DECART_COORDINATES = "decart_coordinates"
    VOLTAGE = "voltage"
    VOLTAGE_STAR = "voltage_star"
    CURRENT = "current"
    MOTOR_MOMENT = "motor_moment"
    LOAD_MOMENT = "load_moment"
    MOMENT_STAR = "moment_star"
    SPEED = "speed"
    ACCELERATION = "acceleration"


# === Модели для настройки робота ===

class RobotTypeRequest(BaseModel):
    """Запрос на установку типа робота"""
    robot_type: RobotType


class CyclogramRequest(BaseModel):
    """Запрос на установку циклограммы"""
    t: List[float]
    q1: List[float]
    q2: List[float]
    q3: List[float] = []
    q4: List[float] = []
    type_of_control: ControlType = ControlType.POSITIONAL
    
    @model_validator(mode='after')
    def check_length(self):
        if len(self.q1) != len(self.t) or len(self.q2) != len(self.t):
            raise ValueError('Все массивы должны быть одинаковой длины')
        return self


class PIDRequest(BaseModel):
    """Запрос на установку параметров ПИД-регулятора"""
    Kp: List[float]  # [Kp1, Kp2, Kp3, Kp4]
    Ki: List[float]  # [Ki1, Ki2, Ki3, Ki4]
    Kd: List[float]  # [Kd1, Kd2, Kd3, Kd4]
    
    @field_validator('Kp', 'Ki', 'Kd')
    @classmethod
    def check_length(cls, v):
        if len(v) < 2:
            raise ValueError('Массив должен содержать минимум 2 элемента')
        return v


class MotorParamsRequest(BaseModel):
    """Запрос на установку параметров двигателей"""
    J: List[float]     # Моменты инерции
    T_e: List[float]   # Электрические постоянные
    Umax: List[float]  # Максимальные напряжения
    Fi: List[float]    # Потоки
    Ce: List[float]    # Коэффициенты ЭДС
    Ra: List[float]    # Сопротивления
    Cm: List[float]    # Коэффициенты момента


class CartesianLimitsRequest(BaseModel):
    """Ограничения координат декартового робота"""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float = 0
    z_max: float = 0
    q_min: float = 0
    q_max: float = 0


class CartesianParamsRequest(BaseModel):
    """Параметры декартового робота"""
    massd_1: float
    massd_2: float
    massd_3: float = 0
    momentd_1: float


class ScaraLimitsRequest(BaseModel):
    """Ограничения координат SCARA робота"""
    q1s_min: float
    q1s_max: float
    q2s_min: float
    q2s_max: float
    q3s_min: float = 0
    q3s_max: float = 0
    zs_min: float = 0
    zs_max: float = 0


class ScaraParamsRequest(BaseModel):
    """Параметры SCARA робота"""
    moment_1: float
    moment_2: float
    moment_3: float = 0
    length_1: float
    length_2: float
    distance: float = 0
    masss_2: float
    masss_3: float = 0


class CylindricalLimitsRequest(BaseModel):
    """Ограничения координат цилиндрического робота"""
    q1c_min: float
    q1c_max: float
    a2c_min: float
    a2c_max: float
    q3c_min: float = 0
    q3c_max: float = 0
    zc_min: float = 0
    zc_max: float = 0


class CylindricalParamsRequest(BaseModel):
    """Параметры цилиндрического робота"""
    momentc_1: float
    momentc_2: float
    momentc_3: float = 0
    lengthc_1: float
    lengthc_2: float
    distancec: float = 0
    massc_2: float
    massc_3: float = 0


class ColerLimitsRequest(BaseModel):
    """Ограничения координат робота Колер"""
    q1col_min: float
    q1col_max: float
    a2col_min: float
    a2col_max: float
    q3col_min: float = 0
    q3col_max: float = 0
    zcol_min: float = 0
    zcol_max: float = 0


class ColerParamsRequest(BaseModel):
    """Параметры робота Колер"""
    momentcol_1: float
    momentcol_2: float
    momentcol_3: float = 0
    lengthcol_1: float
    lengthcol_2: float
    distancecol: float = 0
    masscol_2: float
    masscol_3: float = 0


class LineContourRequest(BaseModel):
    """Параметры линейного контура"""
    x1: float
    x2: float
    y1: float
    y2: float
    speed: float = 1.0


class CircleContourRequest(BaseModel):
    """Параметры кругового контура"""
    x: float
    y: float
    radius: float
    speed: float = 1.0


class SplineRequest(BaseModel):
    """Настройки сплайна"""
    enabled: bool
    num_dots: int = 100


# === Полная конфигурация робота ===

class FullRobotConfig(BaseModel):
    """Полная конфигурация робота"""
    robot_type: RobotType
    type_of_control: ControlType = ControlType.POSITIONAL
    spline: bool = False
    num_splain_dots: int = 100
    
    # ПИД
    Kp: List[float] = [1.0, 1.0, 0, 0]
    Ki: List[float] = [0.0, 0.0, 0, 0]
    Kd: List[float] = [0.0, 0.0, 0, 0]
    
    # Циклограмма
    t: List[float] = []
    q1: List[float] = []
    q2: List[float] = []
    q3: List[float] = []
    q4: List[float] = []
    
    # Параметры двигателей
    J: List[float] = [1.0, 1.0]
    T_e: List[float] = [0.002, 0.002]
    Umax: List[float] = [24.0, 24.0]
    Fi: List[float] = [1.0, 1.0]
    Ce: List[float] = [1.0, 1.0]
    Ra: List[float] = [1.0, 1.0]
    Cm: List[float] = [1.0, 1.0]
    
    # Декартовый робот
    x_min: float = 0
    x_max: float = 1
    y_min: float = 0
    y_max: float = 1
    z_min: float = 0
    z_max: float = 0
    massd_1: float = 1
    massd_2: float = 1
    massd_3: float = 0
    momentd_1: float = 0.1
    
    # SCARA
    q1s_min: float = -1.57
    q1s_max: float = 1.57
    q2s_min: float = -2.0
    q2s_max: float = 2.0
    q3s_min: float = 0
    q3s_max: float = 0
    zs_min: float = 0
    zs_max: float = 0
    moment_1: float = 0.1
    moment_2: float = 0.1
    moment_3: float = 0
    length_1: float = 0.5
    length_2: float = 0.5
    distance: float = 0
    masss_2: float = 1
    masss_3: float = 0
    
    # Цилиндрический
    q1c_min: float = -1.57
    q1c_max: float = 1.57
    a2c_min: float = 0
    a2c_max: float = 0.5
    q3c_min: float = 0
    q3c_max: float = 0
    zc_min: float = 0
    zc_max: float = 0
    momentc_1: float = 0.1
    momentc_2: float = 0.1
    momentc_3: float = 0
    lengthc_1: float = 0.5
    lengthc_2: float = 0.3
    distancec: float = 0
    massc_2: float = 1
    massc_3: float = 0
    
    # Колер
    q1col_min: float = -1.57
    q1col_max: float = 1.57
    a2col_min: float = 0
    a2col_max: float = 0.5
    q3col_min: float = 0
    q3col_max: float = 0
    zcol_min: float = 0
    zcol_max: float = 0
    momentcol_1: float = 0.1
    momentcol_2: float = 0.1
    momentcol_3: float = 0
    lengthcol_1: float = 0.5
    lengthcol_2: float = 0.3
    distancecol: float = 0
    masscol_2: float = 1
    masscol_3: float = 0
    
    # Контурное управление
    line_x1: float = 0
    line_x2: float = 0
    line_y1: float = 0
    line_y2: float = 0
    circle_x: float = 0
    circle_y: float = 0
    circle_radius: float = 0


# === Модели ответов ===

class QualityMetrics(BaseModel):
    """Метрики качества регулирования для одного звена"""
    errors: List[float]
    avg_error: float
    median_error: float
    regulation_times: List[float]
    avg_reg_time: float
    median_reg_time: float


class TrajectoryResult(BaseModel):
    """Результат расчёта траектории"""
    success: bool
    robot_type: str
    type_of_control: str
    spline: bool
    trajectory_length: int
    quality_link_1: QualityMetrics
    quality_link_2: QualityMetrics
    
    # Данные траектории (опционально, если не слишком большие)
    output_time_array: Optional[List[float]] = None
    trajectory_q_1: Optional[List[float]] = None
    trajectory_q_2: Optional[List[float]] = None
    real_trajectory_x: Optional[List[float]] = None
    real_trajectory_y: Optional[List[float]] = None


class PlotResponse(BaseModel):
    """Ответ с графиком"""
    success: bool
    plot_type: str
    image_base64: str  # data:image/png;base64,...


class WorkspaceResponse(BaseModel):
    """Ответ с рабочей областью"""
    success: bool
    robot_type: str
    image_base64: str


class StatusResponse(BaseModel):
    """Общий ответ о статусе"""
    success: bool
    message: str


class RobotStateResponse(BaseModel):
    """Текущее состояние робота"""
    robot_type: str
    type_of_control: str
    spline: bool
    has_cyclogram: bool
    cyclogram_points: int
    pid_configured: bool
    motors_configured: bool


# === Данные для графиков (JSON вместо изображений) ===

class TrajectoryData(BaseModel):
    """Данные траектории для построения графиков на фронтенде"""
    time: List[float]
    q1: List[float]
    q2: List[float]
    real_x: List[float]
    real_y: List[float]
    cyclogram_x: List[float]
    cyclogram_y: List[float]
    cyclogram_t: List[float]
    cyclogram_q1: List[float]
    cyclogram_q2: List[float]


class ElectricalData(BaseModel):
    """Электрические параметры для построения графиков"""
    time: List[float]
    U_1: List[float]
    U_2: List[float]
    Ustar_1: List[float]
    Ustar_2: List[float]
    I_1: List[float]
    I_2: List[float]


class MechanicalData(BaseModel):
    """Механические параметры для построения графиков"""
    time: List[float]
    M_ed_1: List[float]
    M_ed_2: List[float]
    M_load_1: List[float]
    M_load_2: List[float]
    M_corrected_1: List[float]
    M_corrected_2: List[float]
    speed_1: List[float]
    speed_2: List[float]
    acceleration_1: List[float]
    acceleration_2: List[float]


class AllDataResponse(BaseModel):
    """Все данные расчёта"""
    success: bool
    trajectory: TrajectoryData
    electrical: ElectricalData
    mechanical: MechanicalData
    quality_link_1: QualityMetrics
    quality_link_2: QualityMetrics

