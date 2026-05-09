import asyncio

from python_microservices.shared.config_files import ROBOT_TYPE_MAP, config_to_frontend_state, decode_upload_file, generate_config_file, parse_config_file


class FakeUploadFile:
    def __init__(self, content: bytes):
        self._content = content

    async def read(self) -> bytes:
        return self._content


def make_state():
    return {
        "robotType": "scara",
        "cartesianParams": {"mass1": 1, "mass2": 2, "mass3": 3, "moment": 4},
        "cartesianLimits": {"Xmin": 5, "Xmax": 6, "Ymin": 7, "Ymax": 8, "Zmin": 9, "Zmax": 10, "Qmin": 11, "Qmax": 12},
        "scaraParams": {"moment1": 13, "moment2": 14, "moment3": 15, "length1": 16, "length2": 17, "distance": 18, "mass2": 19, "mass3": 20},
        "scaraLimits": {"q1Min": 21, "q1Max": 22, "q2Min": 23, "q2Max": 24, "q3Min": 25, "q3Max": 26, "zMin": 27, "zMax": 28},
        "cylindricalParams": {"moment1": 29, "moment2": 30, "moment3": 31, "length1": 32, "length2": 33, "distance": 34, "mass2": 35, "mass3": 36},
        "cylindricalLimits": {"q1Min": 37, "q1Max": 38, "a2Min": 39, "a2Max": 40, "q3Min": 41, "q3Max": 42, "zMin": 43, "zMax": 44},
        "colerParams": {"moment1": 45, "moment2": 46, "moment3": 47, "length1": 48, "length2": 49, "distance": 50, "mass2": 51, "mass3": 52},
        "colerLimits": {"q1Min": 53, "q1Max": 54, "a2Min": 55, "a2Max": 56, "q3Min": 57, "q3Max": 58, "zMin": 59, "zMax": 60},
        "motorParams": {"J": [61, 62], "Te": [63, 64], "Umax": [65, 66], "Fi": [67, 68], "Ce": [69, 70], "Ra": [71, 72], "Cm": [73, 74]},
        "regulatorParams": {"Kp": [75, 76, 77, 78], "Ki": [79, 80, 81, 82], "Kd": [83, 84, 85, 86]},
        "cyclegram": {"t": [87] * 9, "q1": [88] * 9, "q2": [89] * 9, "q3": [90] * 9, "q4": [91] * 9},
        "trajectory": {
            "type": "circle",
            "line": {"x1": 92, "x2": 93, "y1": 94, "y2": 95, "speed": 96},
            "circle": {"x": 97, "y": 98, "radius": 99, "speed": 100},
        },
    }


def test_generate_and_parse_config_round_trip_preserves_key_fields():
    state = make_state()

    generated = generate_config_file(state)
    parsed = parse_config_file(generated)

    assert parsed["robot_type"] == "scara"
    assert parsed["massd_1"] == 1
    assert parsed["q1s_min"] == 21
    assert parsed["momentcol_3"] == 47
    assert parsed["T_e"] == [63.0, 64.0]
    assert parsed["trajectory_type"] == "circle"
    assert parsed["circle_params"] == [97.0, 98.0, 99.0, 100.0]


def test_config_to_frontend_state_maps_nested_values():
    config = {
        "robot_type": ROBOT_TYPE_MAP["scara"],
        "massd_1": 1,
        "q1s_min": 2,
        "moment_1": 3,
        "T_e": [4, 5],
        "Kp": [6, 7, 8, 9],
        "trajectory_type": "line",
        "line_params": [10, 11, 12, 13, 14],
        "circle_params": [15, 16, 17, 18],
    }

    state = config_to_frontend_state(config)

    assert state["robotType"] == "scara"
    assert state["cartesianParams"]["mass1"] == 1
    assert state["scaraLimits"]["q1Min"] == 2
    assert state["scaraParams"]["moment1"] == 3
    assert state["motorParams"]["Te"] == [4, 5]
    assert state["regulatorParams"]["Kp"] == [6, 7, 8, 9]
    assert state["trajectory"]["line"]["speed"] == 14
    assert state["trajectory"]["circle"]["radius"] == 17


def test_decode_upload_file_falls_back_to_cp1251():
    text = "\u041f\u0440\u0438\u0432\u0435\u0442, \u043c\u0438\u0440!"
    upload = FakeUploadFile(b"\xcf\xf0\xe8\xe2\xe5\xf2, \xec\xe8\xf0!")

    decoded = asyncio.run(decode_upload_file(upload))

    assert decoded == text
