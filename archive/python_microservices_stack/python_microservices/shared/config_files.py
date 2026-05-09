from fastapi import UploadFile


ROBOT_TYPE_MAP = {
    "cartesian": "Декартовый",
    "scara": "Скара",
    "cylindrical": "Цилиндрический",
    "coler": "Колер",
    "Декартовый": "cartesian",
    "Скара": "scara",
    "Цилиндрический": "cylindrical",
    "Колер": "coler",
}


def parse_config_file(content: str) -> dict:
    lines = content.strip().split("\n")

    def safe_float(value):
        try:
            return float(value.strip())
        except Exception:
            return 0.0

    def safe_float_list(value):
        try:
            return [float(item.strip()) for item in value.strip().split(",")]
        except Exception:
            return [0.0, 0.0]

    config = {}
    robot_type_raw = lines[0].strip()
    config["robot_type"] = ROBOT_TYPE_MAP.get(robot_type_raw, robot_type_raw)

    scalar_keys = [
        ("massd_1", 1), ("massd_2", 2), ("massd_3", 3), ("momentd_1", 4),
        ("x_min", 5), ("y_min", 6), ("q_min", 7), ("z_min", 8),
        ("x_max", 9), ("y_max", 10), ("q_max", 11), ("z_max", 12),
        ("moment_1", 13), ("moment_2", 14), ("moment_3", 15), ("length_1", 16),
        ("length_2", 17), ("distance", 18), ("masss_2", 19), ("masss_3", 20),
        ("q1s_min", 21), ("q1s_max", 22), ("q2s_min", 23), ("q2s_max", 24),
        ("q3s_min", 25), ("q3s_max", 26), ("zs_min", 27), ("zs_max", 28),
        ("momentc_1", 29), ("momentc_2", 30), ("momentc_3", 31), ("lengthc_1", 32),
        ("lengthc_2", 33), ("distancec", 34), ("massc_2", 35), ("massc_3", 36),
        ("q1c_min", 37), ("q1c_max", 38), ("a2c_min", 39), ("a2c_max", 40),
        ("q3c_min", 41), ("q3c_max", 42), ("zc_min", 43), ("zc_max", 44),
        ("momentcol_1", 45), ("momentcol_2", 46), ("momentcol_3", 47), ("lengthcol_1", 48),
        ("lengthcol_2", 49), ("distancecol", 50), ("masscol_2", 51), ("masscol_3", 52),
        ("q1col_min", 53), ("q1col_max", 54), ("a2col_min", 55), ("a2col_max", 56),
        ("q3col_min", 57), ("q3col_max", 58), ("zcol_min", 59), ("zcol_max", 60),
    ]
    for key, index in scalar_keys:
        config[key] = safe_float(lines[index])

    list_keys = [("J", 61), ("T_e", 62), ("Umax", 63), ("Fi", 64), ("Ce", 65), ("Ra", 66), ("Cm", 67), ("Kp", 68), ("Ki", 69), ("Kd", 70), ("t", 71), ("q1", 72), ("q2", 73), ("q3", 74), ("q4", 75)]
    for key, index in list_keys:
        config[key] = safe_float_list(lines[index])

    if len(lines) > 76:
        config["trajectory_type"] = lines[76].strip()
    if len(lines) > 77:
        config["line_params"] = safe_float_list(lines[77])
    if len(lines) > 78:
        config["circle_params"] = safe_float_list(lines[78])
    return config


def generate_config_file(state: dict) -> str:
    lines = []

    def get(key, default=0):
        return state.get(key, default) if state.get(key) is not None else default

    def get_list(key, default=None):
        value = state.get(key, default or [0, 0])
        return value if value else default or [0, 0]

    robot_type = state.get("robotType", "cartesian")
    lines.append(ROBOT_TYPE_MAP.get(robot_type, robot_type))

    cart = state.get("cartesianParams", {})
    cart_lim = state.get("cartesianLimits", {})
    scara = state.get("scaraParams", {})
    scara_lim = state.get("scaraLimits", {})
    cyl = state.get("cylindricalParams", {})
    cyl_lim = state.get("cylindricalLimits", {})
    col = state.get("colerParams", {})
    col_lim = state.get("colerLimits", {})
    motor = state.get("motorParams", {})
    reg = state.get("regulatorParams", {})
    cycl = state.get("cyclegram", {})
    traj = state.get("trajectory", {})
    line = traj.get("line", {})
    circle = traj.get("circle", {})

    scalar_values = [
        get("massd_1", cart.get("mass1", 0)), get("massd_2", cart.get("mass2", 0)), get("massd_3", cart.get("mass3", 0)), get("momentd_1", cart.get("moment", 0)),
        get("x_min", cart_lim.get("Xmin", 0)), get("y_min", cart_lim.get("Ymin", 0)), get("q_min", cart_lim.get("Qmin", 0)), get("z_min", cart_lim.get("Zmin", 0)),
        get("x_max", cart_lim.get("Xmax", 0)), get("y_max", cart_lim.get("Ymax", 0)), get("q_max", cart_lim.get("Qmax", 0)), get("z_max", cart_lim.get("Zmax", 0)),
        get("moment_1", scara.get("moment1", 0)), get("moment_2", scara.get("moment2", 0)), get("moment_3", scara.get("moment3", 0)), get("length_1", scara.get("length1", 0)),
        get("length_2", scara.get("length2", 0)), get("distance", scara.get("distance", 0)), get("masss_2", scara.get("mass2", 0)), get("masss_3", scara.get("mass3", 0)),
        get("q1s_min", scara_lim.get("q1Min", 0)), get("q1s_max", scara_lim.get("q1Max", 0)), get("q2s_min", scara_lim.get("q2Min", 0)), get("q2s_max", scara_lim.get("q2Max", 0)),
        get("q3s_min", scara_lim.get("q3Min", 0)), get("q3s_max", scara_lim.get("q3Max", 0)), get("zs_min", scara_lim.get("zMin", 0)), get("zs_max", scara_lim.get("zMax", 0)),
        get("momentc_1", cyl.get("moment1", 0)), get("momentc_2", cyl.get("moment2", 0)), get("momentc_3", cyl.get("moment3", 0)), get("lengthc_1", cyl.get("length1", 0)),
        get("lengthc_2", cyl.get("length2", 0)), get("distancec", cyl.get("distance", 0)), get("massc_2", cyl.get("mass2", 0)), get("massc_3", cyl.get("mass3", 0)),
        get("q1c_min", cyl_lim.get("q1Min", 0)), get("q1c_max", cyl_lim.get("q1Max", 0)), get("a2c_min", cyl_lim.get("a2Min", 0)), get("a2c_max", cyl_lim.get("a2Max", 0)),
        get("q3c_min", cyl_lim.get("q3Min", 0)), get("q3c_max", cyl_lim.get("q3Max", 0)), get("zc_min", cyl_lim.get("zMin", 0)), get("zc_max", cyl_lim.get("zMax", 0)),
        get("momentcol_1", col.get("moment1", 0)), get("momentcol_2", col.get("moment2", 0)), get("momentcol_3", col.get("moment3", 0)), get("lengthcol_1", col.get("length1", 0)),
        get("lengthcol_2", col.get("length2", 0)), get("distancecol", col.get("distance", 0)), get("masscol_2", col.get("mass2", 0)), get("masscol_3", col.get("mass3", 0)),
        get("q1col_min", col_lim.get("q1Min", 0)), get("q1col_max", col_lim.get("q1Max", 0)), get("a2col_min", col_lim.get("a2Min", 0)), get("a2col_max", col_lim.get("a2Max", 0)),
        get("q3col_min", col_lim.get("q3Min", 0)), get("q3col_max", col_lim.get("q3Max", 0)), get("zcol_min", col_lim.get("zMin", 0)), get("zcol_max", col_lim.get("zMax", 0)),
    ]
    lines.extend(str(value) for value in scalar_values)

    list_values = [
        get_list("J", motor.get("J", [0, 0])),
        get_list("T_e", motor.get("Te", [0, 0])),
        get_list("Umax", motor.get("Umax", [0, 0])),
        get_list("Fi", motor.get("Fi", [0, 0])),
        get_list("Ce", motor.get("Ce", [0, 0])),
        get_list("Ra", motor.get("Ra", [0, 0])),
        get_list("Cm", motor.get("Cm", [0, 0])),
        get_list("Kp", reg.get("Kp", [0, 0, 0, 0])),
        get_list("Ki", reg.get("Ki", [0, 0, 0, 0])),
        get_list("Kd", reg.get("Kd", [0, 0, 0, 0])),
        get_list("t", cycl.get("t", [0] * 9)),
        get_list("q1", cycl.get("q1", [0] * 9)),
        get_list("q2", cycl.get("q2", [0] * 9)),
        get_list("q3", cycl.get("q3", [0] * 9)),
        get_list("q4", cycl.get("q4", [0] * 9)),
    ]
    lines.extend(",".join(map(str, value)) for value in list_values)

    lines.append(traj.get("type", "line"))
    lines.append(",".join(map(str, [line.get("x1", 0) or 0, line.get("x2", 0) or 0, line.get("y1", 0) or 0, line.get("y2", 0) or 0, line.get("speed", 0) or 0])))
    lines.append(",".join(map(str, [circle.get("x", 0) or 0, circle.get("y", 0) or 0, circle.get("radius", 0) or 0, circle.get("speed", 0) or 0])))
    return "\n".join(lines)


def config_to_frontend_state(config: dict) -> dict:
    robot_type = config.get("robot_type", "cartesian")
    if robot_type in ["Декартовый", "Скара", "Цилиндрический", "Колер"]:
        robot_type = ROBOT_TYPE_MAP.get(robot_type, "cartesian")

    return {
        "robotType": robot_type,
        "cartesianParams": {"mass1": config.get("massd_1", 0), "mass2": config.get("massd_2", 0), "mass3": config.get("massd_3", 0), "moment": config.get("momentd_1", 0)},
        "cartesianLimits": {"Xmin": config.get("x_min", 0), "Xmax": config.get("x_max", 0), "Ymin": config.get("y_min", 0), "Ymax": config.get("y_max", 0), "Zmin": config.get("z_min", 0), "Zmax": config.get("z_max", 0), "Qmin": config.get("q_min", 0), "Qmax": config.get("q_max", 0)},
        "scaraParams": {"moment1": config.get("moment_1", 0), "moment2": config.get("moment_2", 0), "moment3": config.get("moment_3", 0), "length1": config.get("length_1", 0), "length2": config.get("length_2", 0), "distance": config.get("distance", 0), "mass2": config.get("masss_2", 0), "mass3": config.get("masss_3", 0)},
        "scaraLimits": {"q1Min": config.get("q1s_min", 0), "q1Max": config.get("q1s_max", 0), "q2Min": config.get("q2s_min", 0), "q2Max": config.get("q2s_max", 0), "q3Min": config.get("q3s_min", 0), "q3Max": config.get("q3s_max", 0), "zMin": config.get("zs_min", 0), "zMax": config.get("zs_max", 0)},
        "cylindricalParams": {"moment1": config.get("momentc_1", 0), "moment2": config.get("momentc_2", 0), "moment3": config.get("momentc_3", 0), "length1": config.get("lengthc_1", 0), "length2": config.get("lengthc_2", 0), "distance": config.get("distancec", 0), "mass2": config.get("massc_2", 0), "mass3": config.get("massc_3", 0)},
        "cylindricalLimits": {"q1Min": config.get("q1c_min", 0), "q1Max": config.get("q1c_max", 0), "a2Min": config.get("a2c_min", 0), "a2Max": config.get("a2c_max", 0), "q3Min": config.get("q3c_min", 0), "q3Max": config.get("q3c_max", 0), "zMin": config.get("zc_min", 0), "zMax": config.get("zc_max", 0)},
        "colerParams": {"moment1": config.get("momentcol_1", 0), "moment2": config.get("momentcol_2", 0), "moment3": config.get("momentcol_3", 0), "length1": config.get("lengthcol_1", 0), "length2": config.get("lengthcol_2", 0), "distance": config.get("distancecol", 0), "mass2": config.get("masscol_2", 0), "mass3": config.get("masscol_3", 0)},
        "colerLimits": {"q1Min": config.get("q1col_min", 0), "q1Max": config.get("q1col_max", 0), "a2Min": config.get("a2col_min", 0), "a2Max": config.get("a2col_max", 0), "q3Min": config.get("q3col_min", 0), "q3Max": config.get("q3col_max", 0), "zMin": config.get("zcol_min", 0), "zMax": config.get("zcol_max", 0)},
        "motorParams": {"J": config.get("J", [0, 0]), "Te": config.get("T_e", [0, 0]), "Umax": config.get("Umax", [0, 0]), "Fi": config.get("Fi", [0, 0]), "Ce": config.get("Ce", [0, 0]), "Ra": config.get("Ra", [0, 0]), "Cm": config.get("Cm", [0, 0])},
        "regulatorParams": {"Kp": config.get("Kp", [0, 0, 0, 0]), "Ki": config.get("Ki", [0, 0, 0, 0]), "Kd": config.get("Kd", [0, 0, 0, 0])},
        "cyclegram": {"t": config.get("t", [0] * 9), "q1": config.get("q1", [0] * 9), "q2": config.get("q2", [0] * 9), "q3": config.get("q3", [0] * 9), "q4": config.get("q4", [0] * 9)},
        "trajectory": {
            "type": config.get("trajectory_type", "line"),
            "line": {
                "x1": config.get("line_params", [0, 0, 0, 0, 0])[0] if config.get("line_params") else 0,
                "x2": config.get("line_params", [0, 0, 0, 0, 0])[1] if config.get("line_params") else 0,
                "y1": config.get("line_params", [0, 0, 0, 0, 0])[2] if config.get("line_params") else 0,
                "y2": config.get("line_params", [0, 0, 0, 0, 0])[3] if config.get("line_params") else 0,
                "speed": config.get("line_params", [0, 0, 0, 0, 0])[4] if len(config.get("line_params", [])) > 4 else 0,
            },
            "circle": {
                "x": config.get("circle_params", [0, 0, 0, 0])[0] if config.get("circle_params") else 0,
                "y": config.get("circle_params", [0, 0, 0, 0])[1] if config.get("circle_params") else 0,
                "radius": config.get("circle_params", [0, 0, 0, 0])[2] if config.get("circle_params") else 0,
                "speed": config.get("circle_params", [0, 0, 0, 0])[3] if len(config.get("circle_params", [])) > 3 else 0,
            },
        },
    }


async def decode_upload_file(file: UploadFile) -> str:
    content = await file.read()
    encodings = ["utf-8", "cp1251", "windows-1251", "latin-1"]
    for encoding in encodings:
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError("Не удалось определить кодировку файла")
