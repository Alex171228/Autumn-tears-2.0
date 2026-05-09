import importlib
from types import SimpleNamespace

from fastapi.testclient import TestClient

simulation_app_module = importlib.import_module("python_simulation_engine.services.simulation_service.app")


class FakeCalc:
    def __init__(self):
        self.state = SimpleNamespace(
            robot_type="start",
            type_of_control="Позиционное",
            spline=False,
            t=[0] * 9,
            Kp=[0, 0],
            Ki=[0, 0],
            Kd=[0, 0],
            J=[0, 0],
        )
        self.output_time_array = []
        self.trajectory_q_1 = []
        self.trajectory_q_2 = []
        self.real_trajectory_x = []
        self.real_trajectory_y = []
        self.cyclogram_real_x = []
        self.cyclogram_real_y = []
        self.U_array_1 = []
        self.U_array_2 = []
        self.Ustar_array_1 = []
        self.Ustar_array_2 = []
        self.I_array_1 = []
        self.I_array_2 = []
        self.M_ed_array_1 = []
        self.M_ed_array_2 = []
        self.M1_array = []
        self.M2_array = []
        self.M_ed_corrected_array_1 = []
        self.M_ed_corrected_array_2 = []
        self.speed_array_1 = []
        self.speed_array_2 = []
        self.acceleration_array_1 = []
        self.acceleration_array_2 = []
        self.error_1 = []
        self.error_2 = []
        self.avg_error_1 = 0
        self.avg_error_2 = 0
        self.median_error_1 = 0
        self.median_error_2 = 0
        self.reg_time_1 = []
        self.reg_time_2 = []
        self.avg_reg_time_1 = 0
        self.avg_reg_time_2 = 0
        self.median_reg_time_1 = 0
        self.median_reg_time_2 = 0

    def calculate_trajectory(self):
        self.output_time_array = [0.0, 1.0]

    def coordinate_transform(self):
        return None

    def generate_plot(self, plot_type):
        return f"plot:{plot_type}"

    def get_results_summary(self):
        return {
            "robot_type": self.state.robot_type,
            "type_of_control": self.state.type_of_control,
            "spline": self.state.spline,
            "trajectory_length": len(self.output_time_array),
            "quality": {
                "link_1": {"avg_error": 0, "median_error": 0, "avg_reg_time": 0, "median_reg_time": 0, "errors": [], "regulation_times": []},
                "link_2": {"avg_error": 0, "median_error": 0, "avg_reg_time": 0, "median_reg_time": 0, "errors": [], "regulation_times": []},
            },
        }


def make_client(calc):
    simulation_app_module.get_calculator = lambda session_id="default": calc
    simulation_app_module.save_calculator = lambda session_id, calc_obj: None
    return TestClient(simulation_app_module.app)


def test_set_robot_type_updates_calculator_state():
    calc = FakeCalc()
    client = make_client(calc)

    response = client.post("/api/robot/type?robot_type=Декартовый")

    assert response.status_code == 200
    assert calc.state.robot_type == "Декартовый"


def test_calculate_returns_summary():
    calc = FakeCalc()
    calc.state.robot_type = "Декартовый"
    client = make_client(calc)

    response = client.post("/api/robot/calculate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["robot_type"] == "Декартовый"
    assert payload["trajectory_length"] == 2


def test_robot_state_reflects_existing_configuration():
    calc = FakeCalc()
    calc.state.Kp = [1, 0]
    calc.state.J = [0.1, 0.2]
    calc.state.t = [0, 1, 2]
    client = make_client(calc)

    response = client.get("/api/robot/state")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cyclogram_points"] == 3
    assert payload["pid_configured"] is True
    assert payload["motors_configured"] is True


def test_plot_endpoint_returns_generated_image():
    calc = FakeCalc()
    calc.output_time_array = [0.0]
    client = make_client(calc)

    response = client.get("/api/robot/plot/speed")

    assert response.status_code == 200
    payload = response.json()
    assert payload["plot_type"] == "speed"
    assert payload["image_base64"] == "plot:speed"
