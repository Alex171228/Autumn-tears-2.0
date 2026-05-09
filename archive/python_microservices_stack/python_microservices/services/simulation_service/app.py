import datetime as dt

from fastapi import HTTPException

from python_microservices.models import (
    AllDataResponse,
    CartesianLimitsRequest,
    CartesianParamsRequest,
    CircleContourRequest,
    ColerLimitsRequest,
    ColerParamsRequest,
    CylindricalLimitsRequest,
    CylindricalParamsRequest,
    CyclogramRequest,
    FullRobotConfig,
    LineContourRequest,
    MotorParamsRequest,
    PIDRequest,
    PlotResponse,
    PlotType,
    RobotStateResponse,
    RobotType,
    ScaraLimitsRequest,
    ScaraParamsRequest,
    SplineRequest,
    StatusResponse,
    WorkspaceResponse,
)
from python_microservices import redis_client
from python_microservices.shared.app_factory import create_service_app
from python_microservices.shared.simulation_core import WorkspaceCalculator, get_calculator, save_calculator


app = create_service_app("Simulation Service")


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "simulation", "time": dt.datetime.utcnow().isoformat()}


@app.post("/api/robot/configure", response_model=StatusResponse)
def configure_robot(config: FullRobotConfig, session_id: str = "default"):
    try:
        calc = get_calculator(session_id)
        state = calc.state
        state.robot_type = config.robot_type.value
        state.type_of_control = config.type_of_control.value
        state.spline = config.spline
        state.num_splain_dots = config.num_splain_dots
        state.Kp = config.Kp
        state.Ki = config.Ki
        state.Kd = config.Kd
        if config.t:
            state.t = config.t
            state.q1 = config.q1
            state.q2 = config.q2
            state.q3 = config.q3 or [0] * len(config.t)
            state.q4 = config.q4 or [0] * len(config.t)
        for field in [
            "J", "T_e", "Umax", "Fi", "Ce", "Ra", "Cm",
            "x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "massd_1", "massd_2", "massd_3", "momentd_1",
            "q1s_min", "q1s_max", "q2s_min", "q2s_max", "q3s_min", "q3s_max", "zs_min", "zs_max", "moment_1", "moment_2", "moment_3", "length_1", "length_2", "distance", "masss_2", "masss_3",
            "q1c_min", "q1c_max", "a2c_min", "a2c_max", "q3c_min", "q3c_max", "zc_min", "zc_max", "momentc_1", "momentc_2", "momentc_3", "lengthc_1", "lengthc_2", "distancec", "massc_2", "massc_3",
            "q1col_min", "q1col_max", "a2col_min", "a2col_max", "q3col_min", "q3col_max", "zcol_min", "zcol_max", "momentcol_1", "momentcol_2", "momentcol_3", "lengthcol_1", "lengthcol_2", "distancecol", "masscol_2", "masscol_3",
        ]:
            setattr(state, field, getattr(config, field))
        save_calculator(session_id, calc)
        return {"success": True, "message": "Робот успешно сконфигурирован"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _update_state(session_id: str, mutator):
    calc = get_calculator(session_id)
    mutator(calc)
    save_calculator(session_id, calc)
    return calc


@app.post("/api/robot/type", response_model=StatusResponse)
def set_robot_type(robot_type: RobotType, session_id: str = "default"):
    _update_state(session_id, lambda calc: setattr(calc.state, "robot_type", robot_type.value))
    return {"success": True, "message": f"Тип робота установлен: {robot_type.value}"}


@app.post("/api/robot/cyclogram", response_model=StatusResponse)
def set_cyclogram(data: CyclogramRequest, session_id: str = "default"):
    def mutator(calc):
        calc.state.t = data.t
        calc.state.q1 = data.q1
        calc.state.q2 = data.q2
        calc.state.q3 = data.q3 or [0] * len(data.t)
        calc.state.q4 = data.q4 or [0] * len(data.t)
        calc.state.type_of_control = data.type_of_control.value
    _update_state(session_id, mutator)
    return {"success": True, "message": f"Циклограмма установлена ({len(data.t)} точек)"}


@app.post("/api/robot/pid", response_model=StatusResponse)
def set_pid(data: PIDRequest, session_id: str = "default"):
    _update_state(session_id, lambda calc: [setattr(calc.state, key, getattr(data, key)) for key in ("Kp", "Ki", "Kd")])
    return {"success": True, "message": "Параметры ПИД установлены"}


@app.post("/api/robot/motors", response_model=StatusResponse)
def set_motor_params(data: MotorParamsRequest, session_id: str = "default"):
    def mutator(calc):
        calc.state.J = data.J
        calc.state.T_e = data.T_e
        calc.state.Umax = data.Umax
        calc.state.Fi = data.Fi
        calc.state.Ce = data.Ce
        calc.state.Ra = data.Ra
        calc.state.Cm = data.Cm
    _update_state(session_id, mutator)
    return {"success": True, "message": "Параметры двигателей установлены"}


def _generic_update(session_id: str, data, fields: list[str], message: str):
    def mutator(calc):
        for field in fields:
            setattr(calc.state, field, getattr(data, field))
    _update_state(session_id, mutator)
    return {"success": True, "message": message}


@app.post("/api/robot/cartesian/limits", response_model=StatusResponse)
def set_cartesian_limits(data: CartesianLimitsRequest, session_id: str = "default"):
    return _generic_update(session_id, data, ["x_min", "x_max", "y_min", "y_max", "z_min", "z_max", "q_min", "q_max"], "Ограничения декартового робота установлены")


@app.post("/api/robot/cartesian/params", response_model=StatusResponse)
def set_cartesian_params(data: CartesianParamsRequest, session_id: str = "default"):
    return _generic_update(session_id, data, ["massd_1", "massd_2", "massd_3", "momentd_1"], "Параметры декартового робота установлены")


@app.post("/api/robot/scara/limits", response_model=StatusResponse)
def set_scara_limits(data: ScaraLimitsRequest, session_id: str = "default"):
    return _generic_update(session_id, data, ["q1s_min", "q1s_max", "q2s_min", "q2s_max", "q3s_min", "q3s_max", "zs_min", "zs_max"], "Ограничения SCARA робота установлены")


@app.post("/api/robot/scara/params", response_model=StatusResponse)
def set_scara_params(data: ScaraParamsRequest, session_id: str = "default"):
    return _generic_update(session_id, data, ["moment_1", "moment_2", "moment_3", "length_1", "length_2", "distance", "masss_2", "masss_3"], "Параметры SCARA робота установлены")


@app.post("/api/robot/cylindrical/limits", response_model=StatusResponse)
def set_cylindrical_limits(data: CylindricalLimitsRequest, session_id: str = "default"):
    return _generic_update(session_id, data, ["q1c_min", "q1c_max", "a2c_min", "a2c_max", "q3c_min", "q3c_max", "zc_min", "zc_max"], "Ограничения цилиндрического робота установлены")


@app.post("/api/robot/cylindrical/params", response_model=StatusResponse)
def set_cylindrical_params(data: CylindricalParamsRequest, session_id: str = "default"):
    return _generic_update(session_id, data, ["momentc_1", "momentc_2", "momentc_3", "lengthc_1", "lengthc_2", "distancec", "massc_2", "massc_3"], "Параметры цилиндрического робота установлены")


@app.post("/api/robot/coler/limits", response_model=StatusResponse)
def set_coler_limits(data: ColerLimitsRequest, session_id: str = "default"):
    return _generic_update(session_id, data, ["q1col_min", "q1col_max", "a2col_min", "a2col_max", "q3col_min", "q3col_max", "zcol_min", "zcol_max"], "Ограничения робота Колер установлены")


@app.post("/api/robot/coler/params", response_model=StatusResponse)
def set_coler_params(data: ColerParamsRequest, session_id: str = "default"):
    return _generic_update(session_id, data, ["momentcol_1", "momentcol_2", "momentcol_3", "lengthcol_1", "lengthcol_2", "distancecol", "masscol_2", "masscol_3"], "Параметры робота Колер установлены")


@app.post("/api/robot/contour/line", response_model=StatusResponse)
def set_line_contour(data: LineContourRequest, session_id: str = "default"):
    def mutator(calc):
        calc.state.type_of_control = "Контурное"
        calc.state.line_x1 = data.x1
        calc.state.line_x2 = data.x2
        calc.state.line_y1 = data.y1
        calc.state.line_y2 = data.y2
        calc.state.line_speed = data.speed
        calc.create_contour_line(data.x1, data.x2, data.y1, data.y2)
        calc.reverse_coordinate_transform()
    _update_state(session_id, mutator)
    return {"success": True, "message": "Линейный контур установлен"}


@app.post("/api/robot/contour/circle", response_model=StatusResponse)
def set_circle_contour(data: CircleContourRequest, session_id: str = "default"):
    def mutator(calc):
        calc.state.type_of_control = "Контурное"
        calc.state.circle_x = data.x
        calc.state.circle_y = data.y
        calc.state.circle_radius = data.radius
        calc.state.circle_speed = data.speed
        calc.create_contour_circle(data.x, data.y, data.radius)
        calc.reverse_coordinate_transform()
    _update_state(session_id, mutator)
    return {"success": True, "message": "Круговой контур установлен"}


@app.post("/api/robot/spline", response_model=StatusResponse)
def set_spline(data: SplineRequest, session_id: str = "default"):
    def mutator(calc):
        calc.state.spline = data.enabled
        calc.state.num_splain_dots = data.num_dots
    _update_state(session_id, mutator)
    return {"success": True, "message": f"Сплайн {'включен' if data.enabled else 'выключен'}"}


@app.get("/api/robot/state", response_model=RobotStateResponse)
def get_robot_state(session_id: str = "default"):
    calc = get_calculator(session_id)
    s = calc.state
    return {
        "robot_type": s.robot_type,
        "type_of_control": s.type_of_control,
        "spline": s.spline,
        "has_cyclogram": len(s.t) > 0 and any(t > 0 for t in s.t),
        "cyclogram_points": len(s.t),
        "pid_configured": any(k > 0 for k in s.Kp + s.Ki + s.Kd),
        "motors_configured": any(j > 0 for j in s.J),
    }


@app.post("/api/robot/calculate")
def calculate_trajectory(session_id: str = "default"):
    calc = get_calculator(session_id)
    calc.calculate_trajectory()
    calc.coordinate_transform()
    summary = calc.get_results_summary()
    save_calculator(session_id, calc)
    return {
        "success": True,
        "robot_type": summary["robot_type"],
        "type_of_control": summary["type_of_control"],
        "spline": summary["spline"],
        "trajectory_length": summary["trajectory_length"],
        "quality_link_1": summary["quality"]["link_1"],
        "quality_link_2": summary["quality"]["link_2"],
    }


@app.get("/api/robot/plot/{plot_type}", response_model=PlotResponse)
def get_plot(plot_type: PlotType, session_id: str = "default"):
    calc = get_calculator(session_id)
    if not calc.output_time_array:
        calc.calculate_trajectory()
        calc.coordinate_transform()
        save_calculator(session_id, calc)
    image_base64 = calc.generate_plot(plot_type.value)
    if not image_base64:
        raise HTTPException(status_code=400, detail="Не удалось создать график")
    return {"success": True, "plot_type": plot_type.value, "image_base64": image_base64}


@app.get("/api/robot/workspace", response_model=WorkspaceResponse)
def get_workspace(session_id: str = "default"):
    calc = get_calculator(session_id)
    workspace_calc = WorkspaceCalculator(calc.state)
    return {"success": True, "robot_type": calc.state.robot_type, "image_base64": workspace_calc.generate_workspace_plot()}


@app.get("/api/robot/spline-cyclegram")
def get_spline_cyclegram(session_id: str = "default"):
    calc = get_calculator(session_id)
    t_list = list(getattr(calc, "t_spline", []))
    q1_list = list(getattr(calc, "q_1_spline", []))
    q2_list = list(getattr(calc, "q_2_spline", []))
    return {"success": True, "data": {"t": t_list, "q1": q1_list, "q2": q2_list}, "length": max(len(t_list), len(q1_list), len(q2_list)), "spline_enabled": calc.state.spline}


@app.get("/api/robot/data/all", response_model=AllDataResponse)
def get_all_data(session_id: str = "default"):
    calc = get_calculator(session_id)
    if not calc.output_time_array:
        calc.calculate_trajectory()
        calc.coordinate_transform()
        save_calculator(session_id, calc)

    s = calc.state
    max_points = 10000
    step = max(1, len(calc.output_time_array) // max_points)
    time = calc.output_time_array[::step]
    return {
        "success": True,
        "trajectory": {
            "time": time,
            "q1": calc.trajectory_q_1[::step],
            "q2": calc.trajectory_q_2[::step],
            "real_x": calc.real_trajectory_x[::step] if calc.real_trajectory_x else [],
            "real_y": calc.real_trajectory_y[::step] if calc.real_trajectory_y else [],
            "cyclogram_x": calc.cyclogram_real_x,
            "cyclogram_y": calc.cyclogram_real_y,
            "cyclogram_t": s.t,
            "cyclogram_q1": s.q1,
            "cyclogram_q2": s.q2,
        },
        "electrical": {
            "time": time,
            "U_1": calc.U_array_1[::step],
            "U_2": calc.U_array_2[::step],
            "Ustar_1": calc.Ustar_array_1[::step],
            "Ustar_2": calc.Ustar_array_2[::step],
            "I_1": calc.I_array_1[::step],
            "I_2": calc.I_array_2[::step],
        },
        "mechanical": {
            "time": time,
            "M_ed_1": calc.M_ed_array_1[::step],
            "M_ed_2": calc.M_ed_array_2[::step],
            "M_load_1": calc.M1_array[::step],
            "M_load_2": calc.M2_array[::step],
            "M_corrected_1": calc.M_ed_corrected_array_1[::step],
            "M_corrected_2": calc.M_ed_corrected_array_2[::step],
            "speed_1": calc.speed_array_1[::step],
            "speed_2": calc.speed_array_2[::step],
            "acceleration_1": calc.acceleration_array_1[::step],
            "acceleration_2": calc.acceleration_array_2[::step],
        },
        "quality_link_1": {
            "errors": calc.error_1,
            "avg_error": calc.avg_error_1,
            "median_error": calc.median_error_1,
            "regulation_times": calc.reg_time_1,
            "avg_reg_time": calc.avg_reg_time_1,
            "median_reg_time": calc.median_reg_time_1,
        },
        "quality_link_2": {
            "errors": calc.error_2,
            "avg_error": calc.avg_error_2,
            "median_error": calc.median_error_2,
            "regulation_times": calc.reg_time_2,
            "avg_reg_time": calc.avg_reg_time_2,
            "median_reg_time": calc.median_reg_time_2,
        },
    }


@app.delete("/api/robot/session/{session_id}")
def delete_session(session_id: str):
    deleted = redis_client.delete_calculator(session_id)
    return {"success": deleted, "message": "Сессия удалена" if deleted else "Сессия не найдена"}
