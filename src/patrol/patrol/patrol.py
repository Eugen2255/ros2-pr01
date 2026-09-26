"""Нода patrol: хранит последнюю позу черепахи и по таймеру публикует Twist."""

import signal
from typing import Optional

from geometry_msgs.msg import Twist
from patrol.control import compute_command
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from turtlesim_msgs.msg import Pose

TIMER_PERIOD_S = 0.1


class Patrol(Node):
    """Подписка на /turtle1/pose, таймер 10 Гц и издатель в относительный cmd_vel."""

    def __init__(self) -> None:
        super().__init__('patrol')
        self._pose: Optional[Pose] = None
        # Относительное имя: без remap это /cmd_vel, а не /turtle1/cmd_vel.
        self._publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_subscription(Pose, '/turtle1/pose', self._on_pose, 10)
        self.create_timer(TIMER_PERIOD_S, self._on_timer)
        self.get_logger().info(
            f'publishing to {self._publisher.topic_name}, waiting for /turtle1/pose')

    def _on_pose(self, msg: Pose) -> None:
        if self._pose is None:
            self.get_logger().info(
                f'first pose: x={msg.x:.3f} y={msg.y:.3f} theta={msg.theta:.3f}')
        self._pose = msg

    def _on_timer(self) -> None:
        command = compute_command(self._pose)
        msg = Twist()
        msg.linear.x = command.linear_x
        msg.angular.z = command.angular_z
        self._publisher.publish(msg)


def main(args: Optional[list[str]] = None) -> None:
    # Ctrl+C обрабатывает Python (KeyboardInterrupt из spin), а не обработчик rclpy:
    # иначе контекст гасится во время ожидания и spin падает с RCLError.
    # Обработчик ставится явно: у фонового процесса SIGINT может быть унаследован
    # как игнорируемый, и тогда Python сам KeyboardInterrupt не включает.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = Patrol()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
