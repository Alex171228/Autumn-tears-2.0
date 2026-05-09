from python_microservices.trajectory_calculator import TrajectoryCalculator, WorkspaceCalculator
from python_microservices import redis_client


def get_calculator(session_id: str = "default") -> TrajectoryCalculator:
    calc = redis_client.load_calculator(session_id)
    if calc is None:
        calc = TrajectoryCalculator()
        redis_client.save_calculator(session_id, calc)
    return calc


def save_calculator(session_id: str, calc: TrajectoryCalculator) -> None:
    redis_client.save_calculator(session_id, calc)


__all__ = ["TrajectoryCalculator", "WorkspaceCalculator", "get_calculator", "save_calculator"]
