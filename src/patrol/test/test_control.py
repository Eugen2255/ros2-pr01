from patrol.control import ANGULAR_SPEED, compute_command, LINEAR_SPEED, STOP
from turtlesim_msgs.msg import Pose


def test_no_pose_gives_stop():
    assert compute_command(None) == STOP
    assert compute_command(None).linear_x == 0.0
    assert compute_command(None).angular_z == 0.0


def test_pose_gives_patrol_command():
    pose = Pose(x=5.544445, y=5.544445, theta=0.0)
    command = compute_command(pose)
    assert command.linear_x == LINEAR_SPEED == 0.5
    assert command.angular_z == ANGULAR_SPEED == 0.3


def test_command_does_not_depend_on_pose_values():
    first = compute_command(Pose(x=1.0, y=1.0, theta=0.0))
    second = compute_command(Pose(x=10.0, y=2.0, theta=3.0))
    assert first == second
