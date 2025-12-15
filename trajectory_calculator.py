"""
Модуль расчёта траекторий роботов.
Адаптировано для веб-приложения на FastAPI.
"""

import numpy as np
import scipy as sp
from scipy import interpolate
import matplotlib
matplotlib.use('Agg')  # Не показывать окна
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Wedge
import io
import base64
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RobotState:
    """Состояние робота и все параметры"""
    # Тип робота
    robot_type: str = "Декартовый"
    spline: bool = False
    type_of_control: str = "Позиционное"
    
    # Коэффициенты ПИД-регулятора
    Kp: List[float] = field(default_factory=lambda: [0, 0, 0, 0])
    Ki: List[float] = field(default_factory=lambda: [0, 0, 0, 0])
    Kd: List[float] = field(default_factory=lambda: [0, 0, 0, 0])
    
    # Циклограмма
    t: List[float] = field(default_factory=lambda: [0, 0, 0, 0, 0, 0, 0, 0, 0])
    q1: List[float] = field(default_factory=lambda: [0, 0, 0, 0, 0, 0, 0, 0, 0])
    q2: List[float] = field(default_factory=lambda: [0, 0, 0, 0, 0, 0, 0, 0, 0])
    q3: List[float] = field(default_factory=lambda: [0, 0, 0, 0, 0, 0, 0, 0, 0])
    q4: List[float] = field(default_factory=lambda: [0, 0, 0, 0, 0, 0, 0, 0, 0])
    
    # Параметры двигателей
    J: List[float] = field(default_factory=lambda: [0, 0])
    Umax: List[float] = field(default_factory=lambda: [0, 0])
    T_e: List[float] = field(default_factory=lambda: [0, 0])
    Fi: List[float] = field(default_factory=lambda: [0, 0])
    Ce: List[float] = field(default_factory=lambda: [0, 0])
    Ra: List[float] = field(default_factory=lambda: [0, 0])
    Cm: List[float] = field(default_factory=lambda: [0, 0])
    
    # Моменты инерции звеньев
    I_1: float = 0.0
    I_2: float = 0.0
    
    # Параметры Декартового робота
    x_min: float = 0
    x_max: float = 0
    y_min: float = 0
    y_max: float = 0
    z_min: float = 0
    z_max: float = 0
    q_min: float = 0
    q_max: float = 0
    massd_1: float = 0
    massd_2: float = 0
    massd_3: float = 0
    momentd_1: float = 0
    
    # Параметры SCARA
    q1s_min: float = 0
    q1s_max: float = 0
    q2s_min: float = 0
    q2s_max: float = 0
    q3s_min: float = 0
    q3s_max: float = 0
    zs_min: float = 0
    zs_max: float = 0
    moment_1: float = 0
    moment_2: float = 0
    moment_3: float = 0
    length_1: float = 0
    length_2: float = 0
    distance: float = 0
    masss_2: float = 0
    masss_3: float = 0
    
    # Параметры Цилиндрического робота
    q1c_min: float = 0
    q1c_max: float = 0
    a2c_min: float = 0
    a2c_max: float = 0
    q3c_min: float = 0
    q3c_max: float = 0
    zc_min: float = 0
    zc_max: float = 0
    momentc_1: float = 0
    momentc_2: float = 0
    momentc_3: float = 0
    lengthc_1: float = 0
    lengthc_2: float = 0
    distancec: float = 0
    massc_2: float = 0
    massc_3: float = 0
    
    # Параметры Колер
    q1col_min: float = 0
    q1col_max: float = 0
    a2col_min: float = 0
    a2col_max: float = 0
    q3col_min: float = 0
    q3col_max: float = 0
    zcol_min: float = 0
    zcol_max: float = 0
    momentcol_1: float = 0
    momentcol_2: float = 0
    momentcol_3: float = 0
    lengthcol_1: float = 0
    lengthcol_2: float = 0
    distancecol: float = 0
    masscol_2: float = 0
    masscol_3: float = 0
    
    # Контурное управление
    line_x1: float = 0
    line_x2: float = 0
    line_y1: float = 0
    line_y2: float = 0
    line_speed: float = 0
    circle_x: float = 0
    circle_y: float = 0
    circle_radius: float = 0
    circle_speed: float = 0
    
    # Сплайн
    num_splain_dots: int = 100


class TrajectoryCalculator:
    """Класс для расчёта траекторий роботов"""
    
    def __init__(self, state: Optional[RobotState] = None):
        self.state = state or RobotState()
        
        # Результаты расчётов
        self.output_time_array = []
        self.trajectory_q_1 = []
        self.trajectory_q_2 = []
        self.real_trajectory_x = []
        self.real_trajectory_y = []
        self.cyclogram_real_x = [0] * 9
        self.cyclogram_real_y = [0] * 9
        
        # Массивы для графиков
        self.q_error_array_1 = []
        self.SAU_SUM_array_1 = []
        self.U_array_1 = []
        self.Ustar_array_1 = []
        self.I_array_1 = []
        self.M_ed_array_1 = []
        self.M1_array = []
        self.M_ed_corrected_array_1 = []
        self.acceleration_array_1 = []
        self.speed_array_1 = []
        
        self.q_error_array_2 = []
        self.SAU_SUM_array_2 = []
        self.U_array_2 = []
        self.Ustar_array_2 = []
        self.I_array_2 = []
        self.M_ed_array_2 = []
        self.M2_array = []
        self.M_ed_corrected_array_2 = []
        self.acceleration_array_2 = []
        self.speed_array_2 = []
        
        # Контурное управление
        self.t_contur = []
        self.x_contur = []
        self.y_contur = []
        self.t_contur_control = []
        self.q1_contur_control = []
        self.q2_contur_control = []
        
        # Сплайн
        self.q_1_spline = []
        self.q_2_spline = []
        self.t_spline = []
        
        # Данные об ошибках
        self.error_1 = []
        self.avg_error_1 = 0
        self.median_error_1 = 0
        self.reg_time_1 = []
        self.avg_reg_time_1 = 0
        self.median_reg_time_1 = 0
        
        self.error_2 = []
        self.avg_error_2 = 0
        self.median_error_2 = 0
        self.reg_time_2 = []
        self.avg_reg_time_2 = 0
        self.median_reg_time_2 = 0
    
    def update_state(self, **kwargs):
        """Обновить состояние робота"""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
    
    def _clear_arrays(self):
        """Очистить все массивы результатов"""
        self.output_time_array.clear()
        self.trajectory_q_1.clear()
        self.trajectory_q_2.clear()
        self.real_trajectory_x.clear()
        self.real_trajectory_y.clear()
        
        self.q_error_array_1.clear()
        self.SAU_SUM_array_1.clear()
        self.U_array_1.clear()
        self.Ustar_array_1.clear()
        self.I_array_1.clear()
        self.M_ed_array_1.clear()
        self.M1_array.clear()
        self.M_ed_corrected_array_1.clear()
        self.acceleration_array_1.clear()
        self.speed_array_1.clear()
        
        self.q_error_array_2.clear()
        self.SAU_SUM_array_2.clear()
        self.U_array_2.clear()
        self.Ustar_array_2.clear()
        self.I_array_2.clear()
        self.M_ed_array_2.clear()
        self.M2_array.clear()
        self.M_ed_corrected_array_2.clear()
        self.acceleration_array_2.clear()
        self.speed_array_2.clear()
    
    def get_true_I(self) -> Tuple[float, float]:
        """Получить моменты инерции в зависимости от типа робота"""
        s = self.state
        if s.robot_type == "Декартовый":
            return s.momentd_1, s.momentd_1
        elif s.robot_type == "Скара":
            return s.moment_1, s.moment_2
        elif s.robot_type == "Цилиндрический":
            return s.momentc_1, s.momentc_2
        elif s.robot_type == "Колер":
            return s.momentcol_1, s.momentcol_2
        return 0, 0
    
    def get_true_q_min_max(self, num_zvena: int) -> Tuple[float, float]:
        """Получить границы координат для звена"""
        s = self.state
        if num_zvena == 1:
            if s.robot_type == "Декартовый":
                return s.x_min, s.x_max
            elif s.robot_type == "Скара":
                return s.q1s_min, s.q1s_max
            elif s.robot_type == "Цилиндрический":
                return s.q1c_min, s.q1c_max
            elif s.robot_type == "Колер":
                return s.a2col_min, s.a2col_max
        elif num_zvena == 2:
            if s.robot_type == "Декартовый":
                return s.y_min, s.y_max
            elif s.robot_type == "Скара":
                return s.q2s_min, s.q2s_max
            elif s.robot_type == "Цилиндрический":
                return s.a2c_min, s.a2c_max
            elif s.robot_type == "Колер":
                return s.q1col_min, s.q1col_max
        return 0, 0
    
    def get_true_a1_a2(self) -> Tuple[float, float]:
        """Получить длины звеньев"""
        s = self.state
        if s.robot_type == "Декартовый":
            return s.x_max, s.y_max
        elif s.robot_type == "Скара":
            return s.length_1, s.length_2
        elif s.robot_type == "Цилиндрический":
            return s.lengthc_1, s.lengthc_2
        elif s.robot_type == "Колер":
            return s.lengthcol_1, s.lengthcol_2
        return 0, 0
    
    def create_contour_line(self, x1: float, x2: float, y1: float, y2: float):
        """Создать линейный контур"""
        t_linspace = np.linspace(10, 110, 1000)
        x_contur = []
        y_contur = []
        dx = (x2 - x1) / 1000
        dy = (y2 - y1) / 1000
        for i in range(1000):
            x_contur.append(x1 + dx * i)
            y_contur.append(y1 + dy * i)
        self.t_contur = list(t_linspace)
        self.x_contur = x_contur
        self.y_contur = y_contur
    
    def create_contour_circle(self, x: float, y: float, radius: float):
        """Создать круговой контур"""
        t_linspace = np.linspace(10, 110, 1000)
        fi_linspace = np.linspace(0, 2 * np.pi, 1000)
        x_contur = []
        y_contur = []
        for i in range(len(fi_linspace)):
            x_contur.append(x + radius * np.cos(fi_linspace[i]))
            y_contur.append(y + radius * np.sin(fi_linspace[i]))
        self.t_contur = list(t_linspace)
        self.x_contur = x_contur
        self.y_contur = y_contur
    
    def reverse_coordinate_transform(self):
        """Обратное преобразование координат для контурного управления"""
        self.t_contur_control = []
        self.q1_contur_control = []
        self.q2_contur_control = []
        a_1, a_2 = self.get_true_a1_a2()
        s = self.state
        
        if s.robot_type == "Декартовый":
            self.t_contur_control = self.t_contur.copy()
            self.q1_contur_control = self.x_contur.copy()
            self.q2_contur_control = self.y_contur.copy()
        
        elif s.robot_type == "Цилиндрический":
            self.t_contur_control = self.t_contur.copy()
            for i in range(len(self.t_contur)):
                if self.y_contur[i] == 0:
                    a = 0.25 * np.pi if self.x_contur[i] == 0 else np.pi / 2
                else:
                    a = np.arctan2(self.x_contur[i], self.y_contur[i])
                q1 = -1 * a
                q1 = 0 if np.isnan(q1) else q1
                q2 = np.sqrt(self.x_contur[i]**2 + self.y_contur[i]**2) - a_1
                self.q1_contur_control.append(q1)
                self.q2_contur_control.append(q2)
        
        elif s.robot_type == "Скара":
            self.t_contur_control = self.t_contur.copy()
            for i in range(len(self.t_contur)):
                if self.x_contur[i] == 0:
                    a = 0.25 * np.pi if self.y_contur[i] == 0 else np.pi / 2
                else:
                    a = np.arctan2(self.y_contur[i], self.x_contur[i])
                a = 0 if np.isnan(a) else a
                r = np.sqrt(self.x_contur[i]**2 + self.y_contur[i]**2)
                g1 = np.arccos(((a_1**2) - (a_2**2) + (r**2)) / (2 * a_1 * r))
                g1 = 0 if np.isnan(g1) else g1
                g2 = np.arcsin((a_1 / a_2) * np.sin(g1))
                g2 = 0 if np.isnan(g2) else g2
                ARM = -1
                q1 = -np.pi / 2 + a - g1 * np.sign(ARM)
                q2 = (g1 + g2) * np.sign(ARM)
                self.q1_contur_control.append(q1)
                self.q2_contur_control.append(q2)
        
        elif s.robot_type == "Колер":
            self.t_contur_control = self.t_contur.copy()
            for i in range(len(self.t_contur)):
                square = 1 - (self.x_contur[i] / a_2)**2
                square = max(0, square)
                q1 = self.y_contur[i] - a_2 * np.sqrt(square)
                q2 = -np.arcsin(self.x_contur[i] / a_2)
                q2 = 0 if np.isnan(q2) else q2
                self.q1_contur_control.append(q1)
                self.q2_contur_control.append(q2)
    
    def spline_creation(self, q1: List[float], q2: List[float], t: List[float]):
        """Создание сплайн-траектории"""
        num_splain_dots = self.state.num_splain_dots
        q1_spline = sp.interpolate.CubicSpline(t, q1, bc_type=((2, 0), (2, 0)))
        q2_spline = sp.interpolate.CubicSpline(t, q2, bc_type=((2, 0), (2, 0)))
        t_spline = np.arange(t[0], t[-1] + 1 / num_splain_dots, 1 / num_splain_dots)
        self.q_1_spline = list(q1_spline(t_spline))
        self.q_2_spline = list(q2_spline(t_spline))
        self.t_spline = list(t_spline)
        return self.q_1_spline, self.q_2_spline, self.t_spline
    
    def excess_fluctuation_filter(self, Med_1: float, Med_2: float, M1: float, M2: float) -> Tuple[float, float]:
        """Фильтр избыточных колебаний"""
        s = self.state
        if s.robot_type == "Скара":
            if np.sign(Med_1) != np.sign(M1):
                M1 = 0.5 * Med_1
            if np.sign(Med_2) != np.sign(M2):
                M2 = 0.5 * Med_2
            if Med_1 != 0:
                M1 = Med_1 * ((2 * M1 / Med_1) / (1 + (2 * M1 / Med_1)))
            if Med_2 != 0:
                M2 = Med_2 * ((2 * M2 / Med_2) / (1 + (2 * M2 / Med_2)))
        
        # Фильтрация для звена 1
        if np.sign(Med_1) == np.sign(M1):
            if M1 >= 0:
                if M1 > 0.5 * Med_1 and Med_1 != 0:
                    M1 = Med_1 * ((2 * M1 / Med_1) / (1 + (2 * M1 / Med_1)))
            else:
                if M1 < 0.5 * Med_1 and Med_1 != 0:
                    M1 = Med_1 * ((2 * M1 / Med_1) / (1 + (2 * M1 / Med_1)))
        
        # Фильтрация для звена 2
        if np.sign(Med_2) == np.sign(M2):
            if M2 >= 0:
                if M2 > 0.5 * Med_2 and Med_2 != 0:
                    M2 = Med_2 * ((2 * M2 / Med_2) / (1 + (2 * M2 / Med_2)))
            else:
                if M2 < 0.5 * Med_2 and Med_2 != 0:
                    M2 = Med_2 * ((2 * M2 / Med_2) / (1 + (2 * M2 / Med_2)))
        
        return M1, M2
    
    def robot_function(self, q1: List[float], q2: List[float], t: List[float]) -> Dict[str, List[float]]:
        """Основная функция расчёта динамики робота"""
        s = self.state
        accuracy = 1e-3
        K_U = 1
        T_U = 0.07
        
        Kp = s.Kp
        Ki = s.Ki
        Kd = s.Kd
        J = s.J
        Umax = s.Umax
        T_I = s.T_e
        Fi = s.Fi
        Ce = s.Ce
        Ra = s.Ra
        Cm = s.Cm
        
        I_1, I_2 = self.get_true_I()
        q_min_1, q_max_1 = self.get_true_q_min_max(1)
        q_min_2, q_max_2 = self.get_true_q_min_max(2)
        
        # Инициализация переменных
        q_output_1, q_output_2 = 0, 0
        U_1, U_2 = 0, 0
        I_a_1, I_a_2 = 0, 0
        a_w_1, a_w_2 = 0, 0
        W_1, W_2 = 0, 0
        q_error_prev_1, q_error_prev_2 = 0, 0
        Integral_channel_1, Integral_channel_2 = 0, 0
        
        # Выходные массивы
        output_time_array = []
        q_error_array_1, SAU_SUM_array_1, U_array_1, Ustar_array_1 = [], [], [], []
        I_array_1, M_ed_array_1, M1_array, M_ed_corrected_array_1 = [], [], [], []
        acceleration_array_1, speed_array_1, output_q_array_1 = [], [], []
        
        q_error_array_2, SAU_SUM_array_2, U_array_2, Ustar_array_2 = [], [], [], []
        I_array_2, M_ed_array_2, M2_array, M_ed_corrected_array_2 = [], [], [], []
        acceleration_array_2, speed_array_2, output_q_array_2 = [], [], []
        
        flag_1 = True
        
        for i in range(len(t)):
            if flag_1:
                time_start = 0
                time_stop = t[0]
                flag_1 = False
            else:
                time_start = t[i - 1]
                time_stop = t[i]
            
            steps = []
            time_now = time_start
            while time_now <= time_stop:
                steps.append(time_now)
                time_now += accuracy
            
            q_input_1 = q1[i]
            q_input_2 = q2[i]
            
            for time in steps:
                q_error_1 = q_input_1 - q_output_1
                q_error_2 = q_input_2 - q_output_2
                
                # ПИД для звена 1
                Proportional_channel_1 = Kp[0] * q_error_1
                Integral_channel_1 += Ki[0] * q_error_1 * accuracy
                Differential_channel_1 = Kd[0] * ((q_error_1 - q_error_prev_1) / accuracy)
                Differential_channel_1 = max(-10, min(10, Differential_channel_1))
                SAU_SUM_1 = Proportional_channel_1 + Integral_channel_1 + Differential_channel_1
                q_error_prev_1 = q_error_1
                
                # ПИД для звена 2
                Proportional_channel_2 = Kp[1] * q_error_2
                Integral_channel_2 += Ki[1] * q_error_2 * accuracy
                Differential_channel_2 = Kd[1] * ((q_error_2 - q_error_prev_2) / accuracy)
                Differential_channel_2 = max(-10, min(10, Differential_channel_2))
                SAU_SUM_2 = Proportional_channel_2 + Integral_channel_2 + Differential_channel_2
                q_error_prev_2 = q_error_2
                
                # Расчёт напряжения
                U_need_1 = min(SAU_SUM_1 * K_U, Umax[0])
                U_1 += (U_need_1 * (1 / T_U) - U_1 * (1 / T_U)) * accuracy
                U_changed_1 = U_1 - W_1 * Ce[0] * Fi[0]
                
                U_need_2 = min(SAU_SUM_2 * K_U, Umax[1])
                U_2 += (U_need_2 * (1 / T_U) - U_2 * (1 / T_U)) * accuracy
                U_changed_2 = U_2 - W_2 * Ce[1] * Fi[1]
                
                # Расчёт тока
                nI_Ra_1 = U_changed_1 / Ra[0] if Ra[0] != 0 else 0
                I_a_1 += (nI_Ra_1 * (1 / T_I[0]) - I_a_1 * (1 / T_I[0])) * accuracy if T_I[0] != 0 else 0
                I_a__Cm_1 = I_a_1 * Cm[0]
                
                nI_Ra_2 = U_changed_2 / Ra[1] if Ra[1] != 0 else 0
                I_a_2 += (nI_Ra_2 * (1 / T_I[1]) - I_a_2 * (1 / T_I[1])) * accuracy if T_I[1] != 0 else 0
                I_a__Cm_2 = I_a_2 * Cm[1]
                
                # Расчёт момента двигателя
                M_ed_1 = I_a__Cm_1 * Fi[0]
                M_ed_2 = I_a__Cm_2 * Fi[1]
                
                # Расчёт моментов звеньев
                if s.robot_type == "Декартовый":
                    d1 = (s.massd_1 + s.massd_2) / 2
                    d3 = s.massd_2 / 2
                    M1 = 2 * d1 * a_w_1
                    M2 = 2 * d3 * a_w_2
                elif s.robot_type == "Скара":
                    d1 = (s.moment_1 + s.masss_2 * s.length_1**2 + 
                          2 * s.masss_2 * s.length_2**2 * s.length_1 * np.cos(q_output_1) + 
                          s.masss_2 * s.length_2**2 + s.moment_2 / 2) / 2
                    d2 = (2 * s.masss_2 * s.length_2**2 * s.length_1 + 
                          s.masss_2 * s.length_2**2 + s.moment_2 / 2) / 2
                    d3 = (s.masss_2 * s.length_2**2 + s.moment_2 / 2) / 2
                    M1 = (2 * d1 * a_w_1 + 2 * d2 * a_w_2 - 
                          2 * s.masss_2 * s.length_2 * s.length_1 * np.sin(q_output_2) * W_1 * W_2 - 
                          s.masss_2 * s.length_2 * s.length_1 * np.sin(q_output_2) * W_2**2)
                    M2 = (2 * d1 * a_w_1 + 2 * d3 * a_w_2 + 
                          s.masss_2 * s.length_2 * s.length_1 * np.sin(q_output_2) * W_1**2)
                elif s.robot_type == "Цилиндрический":
                    d1 = 0.5 * (s.momentc_1 + (s.momentc_2 / 2 + 
                               s.massc_2 * (s.lengthc_1 - 0.5 * s.lengthc_2 + q_output_2)**2))
                    d3 = s.massc_2 / 2
                    M1 = (2 * d1 * a_w_1 + 
                          2 * s.massc_2 * (s.lengthc_1 - 0.5 * s.lengthc_2 + q_output_2) * W_1 * W_2)
                    M2 = (2 * d3 * a_w_1 - 
                          s.massc_2 * (s.lengthc_1 - 0.5 * s.lengthc_2 + q_output_2) * W_1**2)
                elif s.robot_type == "Колер":
                    d1 = (1 + s.masscol_2) / 2
                    d2 = s.masscol_2 * s.lengthcol_2 * np.sin(q_output_2) / 2
                    d3 = (s.momentcol_2 + s.masscol_2 * s.lengthcol_2**2) / 2
                    M1 = 2 * d1 * a_w_1 + 2 * d1 * a_w_1 + s.masscol_2 * s.lengthcol_2 * np.cos(q_output_2) * W_2**2
                    M2 = 2 * d2 * a_w_1 + 2 * d3 * a_w_1
                else:
                    M1, M2 = 0, 0
                
                M1, M2 = self.excess_fluctuation_filter(M_ed_1, M_ed_2, M1, M2)
                
                M_ed_corrected_1 = M_ed_1 - M1
                M_ed_corrected_2 = M_ed_2 - M2
                
                # Расчёт ускорения
                a_w_1 = M_ed_corrected_1 / J[0] if J[0] != 0 else 0
                a_w_2 = M_ed_corrected_2 / J[1] if J[1] != 0 else 0
                
                # Расчёт скорости
                W_1 += a_w_1 * accuracy
                W_2 += a_w_2 * accuracy
                
                # Расчёт координаты
                q_output_1 += W_1 * accuracy
                q_output_2 += W_2 * accuracy
                
                # Проверка границ
                if q_output_1 < q_min_1:
                    q_output_1 = q_min_1
                    a_w_1, W_1 = 0, 0
                if q_output_1 > q_max_1:
                    q_output_1 = q_max_1
                    a_w_1, W_1 = 0, 0
                if q_output_2 < q_min_2:
                    q_output_2 = q_min_2
                    a_w_2, W_2 = 0, 0
                if q_output_2 > q_max_2:
                    q_output_2 = q_max_2
                    a_w_2, W_2 = 0, 0
                
                # Сохранение результатов
                output_time_array.append(time)
                q_error_array_1.append(q_error_1)
                SAU_SUM_array_1.append(SAU_SUM_1)
                U_array_1.append(U_1)
                Ustar_array_1.append(U_changed_1)
                I_array_1.append(I_a_1)
                M_ed_array_1.append(M_ed_1)
                M1_array.append(M1)
                M_ed_corrected_array_1.append(M_ed_corrected_1)
                acceleration_array_1.append(a_w_1)
                speed_array_1.append(W_1)
                output_q_array_1.append(q_output_1)
                
                q_error_array_2.append(q_error_2)
                SAU_SUM_array_2.append(SAU_SUM_2)
                U_array_2.append(U_2)
                Ustar_array_2.append(U_changed_2)
                I_array_2.append(I_a_2)
                M_ed_array_2.append(M_ed_2)
                M2_array.append(M2)
                M_ed_corrected_array_2.append(M_ed_corrected_2)
                acceleration_array_2.append(a_w_2)
                speed_array_2.append(W_2)
                output_q_array_2.append(q_output_2)
        
        return {
            'output_time_array': output_time_array,
            'q_error_array_1': q_error_array_1,
            'SAU_SUM_array_1': SAU_SUM_array_1,
            'U_array_1': U_array_1,
            'Ustar_array_1': Ustar_array_1,
            'I_array_1': I_array_1,
            'M_ed_array_1': M_ed_array_1,
            'M1_array': M1_array,
            'M_ed_corrected_array_1': M_ed_corrected_array_1,
            'acceleration_array_1': acceleration_array_1,
            'speed_array_1': speed_array_1,
            'trajectory_q_1': output_q_array_1,
            'q_error_array_2': q_error_array_2,
            'SAU_SUM_array_2': SAU_SUM_array_2,
            'U_array_2': U_array_2,
            'Ustar_array_2': Ustar_array_2,
            'I_array_2': I_array_2,
            'M_ed_array_2': M_ed_array_2,
            'M2_array': M2_array,
            'M_ed_corrected_array_2': M_ed_corrected_array_2,
            'acceleration_array_2': acceleration_array_2,
            'speed_array_2': speed_array_2,
            'trajectory_q_2': output_q_array_2,
        }
    
    def quality_of_regulation(self, q: List[float], t: List[float], 
                              trajectory_q: List[float], output_time_array: List[float]) -> Tuple[List[float], List[float]]:
        """Оценка качества регулирования"""
        j = 0
        dist_prev = 3600
        real_time_array = []
        erorr_stable_array = []
        regulation_time_array = []
        
        for i in range(len(output_time_array)):
            dist = abs(output_time_array[i] - t[j])
            if dist < dist_prev:
                dist_prev = dist
            else:
                dist_prev = 3600
                real_time_array.append(i - 1)
                j += 1
            if j == len(t) - 1 and i == len(output_time_array) - 1:
                real_time_array.append(i)
        
        for i in range(len(real_time_array)):
            if i < len(q) and real_time_array[i] < len(trajectory_q):
                erorr_stable_array.append(abs(q[i] - trajectory_q[real_time_array[i]]))
        
        flag_point_notfound = True
        point_number = 0
        t_now = 0
        
        for i in range(len(output_time_array)):
            if point_number < len(t) and output_time_array[i] >= t[point_number]:
                point_number += 1
                flag_point_notfound = True
                t_now = output_time_array[i]
            
            if (flag_point_notfound and point_number < len(real_time_array) and 
                real_time_array[point_number] < len(trajectory_q) and
                abs(trajectory_q[i] - trajectory_q[real_time_array[point_number]]) <= 
                0.05 * abs(trajectory_q[real_time_array[point_number]]) if trajectory_q[real_time_array[point_number]] != 0 else True):
                t_reg = output_time_array[i] - t_now
                regulation_time_array.append(t_reg)
                flag_point_notfound = False
            
            if (not flag_point_notfound and point_number < len(real_time_array) and 
                real_time_array[point_number] < len(trajectory_q) and
                abs(trajectory_q[i] - trajectory_q[real_time_array[point_number]]) > 
                0.05 * abs(trajectory_q[real_time_array[point_number]]) if trajectory_q[real_time_array[point_number]] != 0 else False):
                flag_point_notfound = True
                if regulation_time_array:
                    del regulation_time_array[-1]
        
        return erorr_stable_array, regulation_time_array
    
    def calculate_trajectory(self) -> Dict[str, Any]:
        """Основной метод расчёта траектории"""
        self._clear_arrays()
        s = self.state
        
        if s.type_of_control == "Позиционное":
            if not s.spline:
                result = self.robot_function(s.q1, s.q2, s.t)
            else:
                q_1_spline, q_2_spline, t_spline = self.spline_creation(s.q1, s.q2, s.t)
                result = self.robot_function(q_1_spline, q_2_spline, t_spline)
        elif s.type_of_control == "Контурное":
            result = self.robot_function(self.q1_contur_control, self.q2_contur_control, self.t_contur_control)
        else:
            result = {}
        
        # Сохраняем результаты
        self.output_time_array = result.get('output_time_array', [])
        self.trajectory_q_1 = result.get('trajectory_q_1', [])
        self.trajectory_q_2 = result.get('trajectory_q_2', [])
        
        self.q_error_array_1 = result.get('q_error_array_1', [])
        self.SAU_SUM_array_1 = result.get('SAU_SUM_array_1', [])
        self.U_array_1 = result.get('U_array_1', [])
        self.Ustar_array_1 = result.get('Ustar_array_1', [])
        self.I_array_1 = result.get('I_array_1', [])
        self.M_ed_array_1 = result.get('M_ed_array_1', [])
        self.M1_array = result.get('M1_array', [])
        self.M_ed_corrected_array_1 = result.get('M_ed_corrected_array_1', [])
        self.acceleration_array_1 = result.get('acceleration_array_1', [])
        self.speed_array_1 = result.get('speed_array_1', [])
        
        self.q_error_array_2 = result.get('q_error_array_2', [])
        self.SAU_SUM_array_2 = result.get('SAU_SUM_array_2', [])
        self.U_array_2 = result.get('U_array_2', [])
        self.Ustar_array_2 = result.get('Ustar_array_2', [])
        self.I_array_2 = result.get('I_array_2', [])
        self.M_ed_array_2 = result.get('M_ed_array_2', [])
        self.M2_array = result.get('M2_array', [])
        self.M_ed_corrected_array_2 = result.get('M_ed_corrected_array_2', [])
        self.acceleration_array_2 = result.get('acceleration_array_2', [])
        self.speed_array_2 = result.get('speed_array_2', [])
        
        # Оценка качества регулирования
        if s.type_of_control == "Позиционное":
            error_1, reg_time_1 = self.quality_of_regulation(s.q1, s.t, self.trajectory_q_1, self.output_time_array)
            error_2, reg_time_2 = self.quality_of_regulation(s.q2, s.t, self.trajectory_q_2, self.output_time_array)
        else:
            error_1, reg_time_1 = self.quality_of_regulation(
                self.q1_contur_control, self.t_contur_control, 
                self.trajectory_q_1, self.output_time_array)
            error_2, reg_time_2 = self.quality_of_regulation(
                self.q2_contur_control, self.t_contur_control, 
                self.trajectory_q_2, self.output_time_array)
        
        self.error_1 = error_1
        self.avg_error_1 = float(np.mean(error_1)) if error_1 else 0
        self.median_error_1 = float(np.median(error_1)) if error_1 else 0
        self.reg_time_1 = reg_time_1
        self.avg_reg_time_1 = float(np.mean(reg_time_1)) if reg_time_1 else 0
        self.median_reg_time_1 = float(np.median(reg_time_1)) if reg_time_1 else 0
        
        self.error_2 = error_2
        self.avg_error_2 = float(np.mean(error_2)) if error_2 else 0
        self.median_error_2 = float(np.median(error_2)) if error_2 else 0
        self.reg_time_2 = reg_time_2
        self.avg_reg_time_2 = float(np.mean(reg_time_2)) if reg_time_2 else 0
        self.median_reg_time_2 = float(np.median(reg_time_2)) if reg_time_2 else 0
        
        return result
    
    def coordinate_transform(self) -> Dict[str, List[float]]:
        """Преобразование обобщённых координат в декартовы"""
        s = self.state
        a_1, a_2 = self.get_true_a1_a2()
        
        real_x = []
        real_y = []
        cyclogram_x = list(self.cyclogram_real_x)
        cyclogram_y = list(self.cyclogram_real_y)
        
        if s.type_of_control == "Позиционное":
            trajectory_q_1 = self.trajectory_q_1
            trajectory_q_2 = self.trajectory_q_2
            cyclogramm_q_1 = s.q1
            cyclogramm_q_2 = s.q2
        else:
            trajectory_q_1 = self.trajectory_q_1
            trajectory_q_2 = self.trajectory_q_2
            cyclogramm_q_1 = []
            cyclogramm_q_2 = []
        
        if s.robot_type == "Декартовый":
            real_x = list(trajectory_q_1)
            real_y = list(trajectory_q_2)
            cyclogram_x = list(cyclogramm_q_1) if cyclogramm_q_1 else cyclogram_x
            cyclogram_y = list(cyclogramm_q_2) if cyclogramm_q_2 else cyclogram_y
        
        elif s.robot_type == "Цилиндрический":
            for i in range(len(trajectory_q_1)):
                real_x.append(-(a_1 + trajectory_q_2[i]) * np.sin(trajectory_q_1[i]))
                real_y.append((a_1 + trajectory_q_2[i]) * np.cos(trajectory_q_1[i]))
            for i in range(len(cyclogramm_q_1)):
                if i < len(cyclogram_x):
                    cyclogram_x[i] = -(a_1 + cyclogramm_q_2[i]) * np.sin(cyclogramm_q_1[i])
                    cyclogram_y[i] = (a_1 + cyclogramm_q_2[i]) * np.cos(cyclogramm_q_1[i])
        
        elif s.robot_type == "Скара":
            for i in range(len(trajectory_q_1)):
                real_x.append(-a_1 * np.sin(trajectory_q_1[i]) - a_2 * np.sin(trajectory_q_1[i] + trajectory_q_2[i]))
                real_y.append(a_1 * np.cos(trajectory_q_1[i]) + a_2 * np.cos(trajectory_q_1[i] + trajectory_q_2[i]))
            for i in range(len(cyclogramm_q_1)):
                if i < len(cyclogram_x):
                    cyclogram_x[i] = -a_1 * np.sin(cyclogramm_q_1[i]) - a_2 * np.sin(cyclogramm_q_1[i] + cyclogramm_q_2[i])
                    cyclogram_y[i] = a_1 * np.cos(cyclogramm_q_1[i]) + a_2 * np.cos(cyclogramm_q_1[i] + cyclogramm_q_2[i])
        
        elif s.robot_type == "Колер":
            for i in range(len(trajectory_q_1)):
                real_x.append(-a_2 * np.sin(trajectory_q_2[i]))
                real_y.append(trajectory_q_1[i] + a_2 * np.cos(trajectory_q_2[i]))
            for i in range(len(cyclogramm_q_1)):
                if i < len(cyclogram_x):
                    cyclogram_x[i] = -a_2 * np.sin(cyclogramm_q_2[i])
                    cyclogram_y[i] = cyclogramm_q_1[i] + a_2 * np.cos(cyclogramm_q_2[i])
        
        self.real_trajectory_x = real_x
        self.real_trajectory_y = real_y
        self.cyclogram_real_x = cyclogram_x
        self.cyclogram_real_y = cyclogram_y
        
        return {
            'real_trajectory_x': real_x,
            'real_trajectory_y': real_y,
            'cyclogram_real_x': cyclogram_x,
            'cyclogram_real_y': cyclogram_y,
        }
    
    def generate_plot(self, plot_type: str) -> str:
        """Генерация графика и возврат как base64 PNG"""
        fig = plt.figure(figsize=(11, 11))
        ax = fig.add_subplot()
        s = self.state
        
        if plot_type == "decart_plane":
            self._draw_decart_plane(ax)
        elif plot_type == "obobshennie_coordinates":
            self._draw_obobshennie_coordinates(ax)
        elif plot_type == "decart_coordinates":
            self._draw_decart_coordinates(ax)
        elif plot_type == "voltage":
            self._draw_voltage(ax)
        elif plot_type == "voltage_star":
            self._draw_voltage_star(ax)
        elif plot_type == "current":
            self._draw_current(ax)
        elif plot_type == "motor_moment":
            self._draw_motor_moment(ax)
        elif plot_type == "load_moment":
            self._draw_load_moment(ax)
        elif plot_type == "moment_star":
            self._draw_moment_star(ax)
        elif plot_type == "speed":
            self._draw_speed(ax)
        elif plot_type == "acceleration":
            self._draw_acceleration(ax)
        else:
            plt.close(fig)
            return ""
        
        # Конвертация в base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f"data:image/png;base64,{img_base64}"
    
    def _draw_workspace_area(self, ax):
        """Нарисовать рабочую область на графике"""
        s = self.state
        a_1, a_2 = self.get_true_a1_a2()
        
        if s.robot_type == "Декартовый":
            rect = Rectangle((0, 0), a_1, a_2, linewidth=1, facecolor="palegreen", alpha=0.4, label='Рабочая область')
            plt.gca().set_aspect('equal', adjustable='box')
            ax.add_patch(rect)
            ax.set_facecolor('azure')
        
        elif s.robot_type == "Цилиндрический":
            rad_min = s.lengthc_1 + s.a2c_min
            rad_max = s.lengthc_1 + s.a2c_max
            small = Wedge((0, 0), rad_min, np.rad2deg(s.q1c_min) + 90, np.rad2deg(s.q1c_max) + 90, color="white", alpha=1)
            big = Wedge((0, 0), rad_max, np.rad2deg(s.q1c_min) + 90, np.rad2deg(s.q1c_max) + 90, color="darkgreen", alpha=0.5, label='Рабочая область')
            plt.gca().set_aspect('equal', adjustable='box')
            ax.add_artist(big)
            ax.add_artist(small)
        
        elif s.robot_type == "Скара":
            rad_min = a_1 - a_2
            rad_max = a_1 + a_2
            helping = (rad_max - rad_min) / 2
            hypotenuse = helping + rad_min
            
            small = Wedge((0, 0), rad_min, np.rad2deg(s.q1s_min) + 90, np.rad2deg(s.q1s_max) + 90, color="white", alpha=1)
            big = Wedge((0, 0), rad_max, np.rad2deg(s.q1s_min) + 90, np.rad2deg(s.q1s_max) + 90, color="darkgreen", alpha=0.5, label='Рабочая область')
            right = Wedge((hypotenuse * np.cos(s.q1s_max + np.pi / 2), hypotenuse * np.sin(s.q1s_max + np.pi / 2)), 
                         helping, np.rad2deg(s.q1s_max) + 90, np.rad2deg(s.q1s_max) + 270, color="darkgreen", alpha=0.5)
            left = Wedge((hypotenuse * np.cos(s.q1s_min + np.pi / 2), hypotenuse * np.sin(s.q1s_min + np.pi / 2)), 
                        helping, np.rad2deg(s.q1s_min) + 270, np.rad2deg(s.q1s_min) + 90, color="darkgreen", alpha=0.5)
            
            plt.gca().set_aspect('equal', adjustable='box')
            ax.add_artist(big)
            ax.add_artist(small)
            ax.add_artist(right)
            ax.add_artist(left)
        
        elif s.robot_type == "Колер":
            q1_linspace = np.linspace(s.q1col_min, s.q1col_max, 100)
            a1_linspace = np.linspace(s.a2col_min, s.a2col_max, 50)
            x_linspace, y_linspace = [], []
            for i in range(len(a1_linspace)):
                for j in range(len(q1_linspace)):
                    y_linspace.append(a1_linspace[i] + a_2 * np.cos(q1_linspace[j]))
                    x_linspace.append(-1 * a_2 * np.sin(q1_linspace[j]))
            plt.scatter(x_linspace, y_linspace, c="palegreen", s=80, alpha=0.5, label='Рабочая область')
    
    def _draw_decart_plane(self, ax):
        """Рисование траектории на декартовой плоскости"""
        s = self.state
        self._draw_workspace_area(ax)
        
        if s.type_of_control == "Позиционное":
            plt.plot(self.real_trajectory_x, self.real_trajectory_y, color='red', 
                    label='Траектория по сплайну' if s.spline else 'Траектория')
            plt.scatter(self.cyclogram_real_x, self.cyclogram_real_y, c="blue",
                       linewidths=1, marker="^", edgecolor="black", s=50, alpha=0.6, 
                       label='Заданные циклограммой точки')
        elif s.type_of_control == "Контурное":
            plt.plot(self.real_trajectory_x, self.real_trajectory_y, color='red', label='Траектория')
            plt.scatter(self.x_contur, self.y_contur, s=5, color='midnightblue', label='Контур')
        
        plt.grid(True)
        plt.xlim([-1.1, 1.1])
        plt.ylim([-1.1, 1.1])
        plt.legend()
        plt.axhline(y=0, color='steelblue', lw=1)
        plt.axvline(x=0, color='steelblue', lw=1)
        plt.grid(True, color='lightskyblue')
        
        titles = {
            "Декартовый": "Траектория робота Декарта",
            "Цилиндрический": "Траектория робота Цилиндр",
            "Скара": "Траектория робота Скара",
            "Колер": "Траектория робота Колер"
        }
        plt.title(titles.get(s.robot_type, 'Траектория движения робота'))
    
    def _draw_obobshennie_coordinates(self, ax):
        """Рисование обобщённых координат от времени"""
        s = self.state
        
        if s.type_of_control == "Позиционное":
            color1 = 'maroon' if s.spline else 'red'
            color2 = 'cyan' if s.spline else 'blue'
            label1 = 'Обобщённые координаты первого звена - сплайн' if s.spline else 'Обобщённые координаты первого звена'
            label2 = 'Обобщённые координаты второго звена - сплайн' if s.spline else 'Обобщённые координаты второго звена'
            
            plt.plot(self.output_time_array, self.trajectory_q_1, color=color1, label=label1)
            plt.plot(self.output_time_array, self.trajectory_q_2, color=color2, label=label2)
            plt.scatter(s.t, s.q1, c="red", linewidths=1, marker="s", edgecolor="black", s=50, alpha=0.5, 
                       label='Циклограмма координат первого звена')
            plt.scatter(s.t, s.q2, c="blue", linewidths=1, marker="^", edgecolor="black", s=50, alpha=0.5, 
                       label='Циклограмма координат второго звена')
        elif s.type_of_control == "Контурное":
            plt.plot(self.output_time_array, self.trajectory_q_1, color='red', label='Обобщённые координаты первого звена')
            plt.plot(self.output_time_array, self.trajectory_q_2, color='blue', label='Обобщённые координаты второго звена')
            plt.scatter(self.t_contur_control, self.q1_contur_control, c="darkorange", label='Контур движения первого звена')
            plt.scatter(self.t_contur_control, self.q2_contur_control, c="darkgreen", label='Контур движения второго звена')
        
        plt.grid(True)
        plt.legend(bbox_to_anchor=[1, 1], loc='lower center')
        plt.axhline(y=0, color='steelblue', lw=1)
        plt.axvline(x=0, color='steelblue', lw=1)
        plt.grid(True, color='lightskyblue')
        
        titles = {
            "Декартовый": "Обобщённые координаты робота Декарта",
            "Цилиндрический": "Обобщённые координаты робота Цилиндр",
            "Скара": "Обобщённые координаты робота Скара",
            "Колер": "Обобщённые координаты робота Колер"
        }
        plt.title(titles.get(s.robot_type, 'Обобщённые координаты'))
    
    def _draw_decart_coordinates(self, ax):
        """Рисование декартовых координат от времени"""
        s = self.state
        
        if s.type_of_control == "Позиционное":
            color1 = 'maroon' if s.spline else 'red'
            color2 = 'cyan' if s.spline else 'blue'
            plt.plot(self.output_time_array, self.real_trajectory_x, color=color1, label='Декартовы координаты X')
            plt.plot(self.output_time_array, self.real_trajectory_y, color=color2, label='Декартовы координаты Y')
            plt.scatter(s.t, self.cyclogram_real_x, c="red", linewidths=1, marker="s", edgecolor="black", s=50, alpha=0.5, 
                       label='Циклограмма X')
            plt.scatter(s.t, self.cyclogram_real_y, c="blue", linewidths=1, marker="^", edgecolor="black", s=50, alpha=0.5, 
                       label='Циклограмма Y')
        elif s.type_of_control == "Контурное":
            plt.plot(self.output_time_array, self.real_trajectory_x, color='red', label='Декартовы координаты X')
            plt.plot(self.output_time_array, self.real_trajectory_y, color='blue', label='Декартовы координаты Y')
            plt.scatter(self.t_contur_control, self.x_contur, c="darkorange", label='Контур X')
            plt.scatter(self.t_contur_control, self.y_contur, c="darkgreen", label='Контур Y')
        
        plt.grid(True)
        plt.legend(bbox_to_anchor=[1, 1], loc='lower center')
        plt.axhline(y=0, color='steelblue', lw=1)
        plt.axvline(x=0, color='steelblue', lw=1)
        plt.grid(True, color='lightskyblue')
        plt.title(f'Декартовы координаты робота {s.robot_type}')
    
    def _draw_voltage(self, ax):
        """Рисование напряжения от времени"""
        s = self.state
        color1 = 'maroon' if s.spline else 'red'
        color2 = 'cyan' if s.spline else 'blue'
        
        plt.plot(self.output_time_array, self.U_array_1, color=color1, label='Напряжение — первое звено')
        plt.plot(self.output_time_array, self.U_array_2, color=color2, label='Напряжение — второе звено')
        plt.grid(True)
        plt.legend(bbox_to_anchor=[1, 1], loc='lower center')
        plt.axhline(y=0, color='steelblue', lw=1)
        plt.axvline(x=0, color='steelblue', lw=1)
        plt.title(f'Напряжения робот {s.robot_type}')
    
    def _draw_voltage_star(self, ax):
        """Рисование напряжения* (U - ЭДС) от времени"""
        s = self.state
        color1 = 'maroon' if s.spline else 'red'
        color2 = 'cyan' if s.spline else 'blue'
        
        plt.plot(self.output_time_array, self.Ustar_array_1, color=color1, label='U* первое звено')
        plt.plot(self.output_time_array, self.Ustar_array_2, color=color2, label='U* второе звено')
        plt.grid(True)
        plt.legend(bbox_to_anchor=[1, 1], loc='lower center')
        plt.title(f'Напряжение* (U - ЭДС) робот {s.robot_type}')
    
    def _draw_current(self, ax):
        """Рисование тока от времени"""
        s = self.state
        color1 = 'maroon' if s.spline else 'red'
        color2 = 'cyan' if s.spline else 'blue'
        
        plt.plot(self.output_time_array, self.I_array_1, color=color1, label='Ток первое звено')
        plt.plot(self.output_time_array, self.I_array_2, color=color2, label='Ток второе звено')
        plt.grid(True)
        plt.legend(bbox_to_anchor=[1, 1], loc='lower center')
        plt.title(f'Ток робот {s.robot_type}')
    
    def _draw_motor_moment(self, ax):
        """Рисование момента двигателя от времени"""
        s = self.state
        color1 = 'maroon' if s.spline else 'red'
        color2 = 'cyan' if s.spline else 'blue'
        
        plt.plot(self.output_time_array, self.M_ed_array_1, color=color1, label='Момент ЭД первое звено')
        plt.plot(self.output_time_array, self.M_ed_array_2, color=color2, label='Момент ЭД второе звено')
        plt.grid(True)
        plt.legend(bbox_to_anchor=[1, 1], loc='lower center')
        plt.title(f'Момент электродвигателя робот {s.robot_type}')
    
    def _draw_load_moment(self, ax):
        """Рисование момента нагрузки от времени"""
        s = self.state
        color1 = 'maroon' if s.spline else 'red'
        color2 = 'cyan' if s.spline else 'blue'
        
        plt.plot(self.output_time_array, self.M1_array, color=color1, label='Момент нагрузки первое звено')
        plt.plot(self.output_time_array, self.M2_array, color=color2, label='Момент нагрузки второе звено')
        plt.grid(True)
        plt.legend(bbox_to_anchor=[1, 1], loc='lower center')
        plt.title(f'Момент нагрузки робот {s.robot_type}')
    
    def _draw_moment_star(self, ax):
        """Рисование момента* (МЭД - М нагрузки) от времени"""
        s = self.state
        color1 = 'maroon' if s.spline else 'red'
        color2 = 'cyan' if s.spline else 'blue'
        
        plt.plot(self.output_time_array, self.M_ed_corrected_array_1, color=color1, label='М* первое звено')
        plt.plot(self.output_time_array, self.M_ed_corrected_array_2, color=color2, label='М* второе звено')
        plt.grid(True)
        plt.legend(bbox_to_anchor=[1, 1], loc='lower center')
        plt.title(f'Момент* (МЭД - М нагрузки) робот {s.robot_type}')
    
    def _draw_speed(self, ax):
        """Рисование скорости от времени"""
        s = self.state
        color1 = 'maroon' if s.spline else 'red'
        color2 = 'cyan' if s.spline else 'blue'
        
        plt.plot(self.output_time_array, self.speed_array_1, color=color1, label='Скорость первое звено')
        plt.plot(self.output_time_array, self.speed_array_2, color=color2, label='Скорость второе звено')
        plt.grid(True)
        plt.legend(bbox_to_anchor=[1, 1], loc='lower center')
        plt.title(f'Обобщённые скорости робот {s.robot_type}')
    
    def _draw_acceleration(self, ax):
        """Рисование ускорения от времени"""
        s = self.state
        color1 = 'maroon' if s.spline else 'red'
        color2 = 'cyan' if s.spline else 'blue'
        
        plt.plot(self.output_time_array, self.acceleration_array_1, color=color1, label='Ускорение первое звено')
        plt.plot(self.output_time_array, self.acceleration_array_2, color=color2, label='Ускорение второе звено')
        plt.grid(True)
        plt.legend(bbox_to_anchor=[1, 1], loc='lower center')
        plt.title(f'Обобщённые ускорения робот {s.robot_type}')
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Получить сводку результатов расчёта"""
        return {
            'robot_type': self.state.robot_type,
            'type_of_control': self.state.type_of_control,
            'spline': self.state.spline,
            'quality': {
                'link_1': {
                    'errors': self.error_1,
                    'avg_error': self.avg_error_1,
                    'median_error': self.median_error_1,
                    'regulation_times': self.reg_time_1,
                    'avg_reg_time': self.avg_reg_time_1,
                    'median_reg_time': self.median_reg_time_1,
                },
                'link_2': {
                    'errors': self.error_2,
                    'avg_error': self.avg_error_2,
                    'median_error': self.median_error_2,
                    'regulation_times': self.reg_time_2,
                    'avg_reg_time': self.avg_reg_time_2,
                    'median_reg_time': self.median_reg_time_2,
                }
            },
            'trajectory_length': len(self.output_time_array),
        }


class WorkspaceCalculator:
    """Класс для расчёта и отображения рабочей области робота"""
    
    def __init__(self, state: RobotState):
        self.state = state
    
    def generate_workspace_plot(self) -> str:
        """Генерация изображения рабочей области"""
        s = self.state
        fig = plt.figure(figsize=(7, 7))
        fig.patch.set_facecolor('#00f0d4')
        ax = fig.add_subplot()
        
        if s.robot_type == "Декартовый":
            self._draw_cartesian_workspace(ax)
        elif s.robot_type == "Скара":
            self._draw_scara_workspace(ax)
        elif s.robot_type == "Цилиндрический":
            self._draw_cylindrical_workspace(ax)
        elif s.robot_type == "Колер":
            self._draw_coler_workspace(ax)
        
        # Конвертация в base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f"data:image/png;base64,{img_base64}"
    
    def _draw_cartesian_workspace(self, ax):
        """Рисование рабочей области для декартового робота"""
        s = self.state
        rect = Rectangle((0, 0), s.x_max, s.y_max, linewidth=1, facecolor="palegreen")
        plt.gca().set_aspect('equal', adjustable='box')
        ax.add_patch(rect)
        ax.set_facecolor('azure')
        plt.xlim([-0.3, s.x_max + 0.3])
        plt.ylim([-0.3, s.y_max + 0.3])
        plt.axhline(y=0, color='steelblue', lw=1)
        plt.axvline(x=0, color='steelblue', lw=1)
        plt.grid(True, color='lightskyblue')
        plt.title('Рабочая область робота Декарта')
    
    def _draw_scara_workspace(self, ax):
        """Рисование рабочей области для SCARA робота"""
        s = self.state
        a_1 = s.length_1
        a_2 = s.length_2
        rad_min = a_1 - a_2
        rad_max = a_1 + a_2
        
        helping = (rad_max - rad_min) / 2
        hypotenuse = helping + rad_min
        
        small = Wedge((0, 0), rad_min, np.rad2deg(s.q1s_min) + 90, np.rad2deg(s.q1s_max) + 90, color="white", alpha=1)
        big = Wedge((0, 0), rad_max, np.rad2deg(s.q1s_min) + 90, np.rad2deg(s.q1s_max) + 90, color="darkgreen", alpha=0.5)
        right = Wedge((hypotenuse * np.cos(s.q1s_max + np.pi/2), hypotenuse * np.sin(s.q1s_max + np.pi/2)), 
                     helping, np.rad2deg(s.q1s_max) + 90, np.rad2deg(s.q1s_max) + 270, color="darkgreen", alpha=0.5)
        left = Wedge((hypotenuse * np.cos(s.q1s_min + np.pi/2), hypotenuse * np.sin(s.q1s_min + np.pi/2)), 
                    helping, np.rad2deg(s.q1s_min) + 270, np.rad2deg(s.q1s_min) + 90, color="darkgreen", alpha=0.5)
        
        plt.gca().set_aspect('equal', adjustable='box')
        ax.add_artist(big)
        ax.add_artist(small)
        ax.add_artist(right)
        ax.add_artist(left)
        plt.grid(True)
        plt.xlim([-2, 2])
        plt.ylim([-2, 2])
        plt.title('Рабочая область робота Скара')
        plt.axhline(y=0, color='steelblue', lw=1)
        plt.axvline(x=0, color='steelblue', lw=1)
        plt.grid(True, color='lightskyblue')
    
    def _draw_cylindrical_workspace(self, ax):
        """Рисование рабочей области для цилиндрического робота"""
        s = self.state
        rad_min = s.lengthc_1 + s.a2c_min
        rad_max = s.lengthc_1 + s.a2c_max
        
        small = Wedge((0, 0), rad_min, np.rad2deg(s.q1c_min) + 90, np.rad2deg(s.q1c_max) + 90, color="white", alpha=1)
        big = Wedge((0, 0), rad_max, np.rad2deg(s.q1c_min) + 90, np.rad2deg(s.q1c_max) + 90, color="darkgreen", alpha=0.5)
        
        plt.gca().set_aspect('equal', adjustable='box')
        ax.add_artist(big)
        ax.add_artist(small)
        plt.grid(True)
        plt.xlim([-1.5, 1.5])
        plt.ylim([-1.5, 1.5])
        plt.title('Рабочая область робота Цилиндра')
        plt.axhline(y=0, color='steelblue', lw=1)
        plt.axvline(x=0, color='steelblue', lw=1)
        plt.grid(True, color='lightskyblue')
    
    def _draw_coler_workspace(self, ax):
        """Рисование рабочей области для робота Колер"""
        s = self.state
        a2 = s.lengthcol_2
        
        q1_linspace = np.linspace(s.q1col_min, s.q1col_max, 100)
        a1_linspace = np.linspace(s.a2col_min, s.a2col_max, 50)
        x_linspace, y_linspace = [], []
        
        for i in range(len(a1_linspace)):
            for j in range(len(q1_linspace)):
                y_linspace.append(a1_linspace[i] + a2 * np.cos(q1_linspace[j]))
                x_linspace.append(-1 * a2 * np.sin(q1_linspace[j]))
        
        plt.scatter(x_linspace, y_linspace, c="palegreen", s=80, alpha=0.5)
        plt.grid(True)
        plt.xlim([-1.5, 1.5])
        plt.ylim([-1.5, 1.5])
        plt.title('Рабочая область робота Колер')
        plt.axhline(y=0, color='steelblue', lw=1)
        plt.axvline(x=0, color='steelblue', lw=1)
        plt.grid(True, color='lightskyblue')

