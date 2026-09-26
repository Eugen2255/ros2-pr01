"""Логика команды патрулирования без зависимостей от ROS."""

from typing import NamedTuple, Optional

LINEAR_SPEED = 0.5
ANGULAR_SPEED = 0.3


class Command(NamedTuple):
    """Скорости, которые нода кладёт в Twist."""

    linear_x: float
    angular_z: float


STOP = Command(0.0, 0.0)


def compute_command(pose: Optional[object]) -> Command:
    """
    Вернуть команду по последней известной позе.

    Пока поза не получена, робот стоит: нельзя ехать, не зная, где он.
    После первой позы — движение по дуге с постоянными скоростями.
    """
    if pose is None:
        return STOP
    return Command(LINEAR_SPEED, ANGULAR_SPEED)
