# ПР02. Топики и типы сообщений

ROS 2 Lyrical, `ROS_DOMAIN_ID=16`. Типы получены командами
`ros2 topic list -t` ([topics.txt](topics.txt)) и `ros2 topic type /turtle1/pose`
([pose-type.txt](pose-type.txt)), поля — `ros2 interface show`
([twist-interface.txt](twist-interface.txt)).

| Топик | Тип | Кто публикует | Кто подписан |
|---|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | CLI `ros2 topic pub` (или teleop) | `/turtlesim` |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | `/turtlesim` | CLI `ros2 topic echo` |

В Lyrical (как и в Jazzy) сообщения turtlesim вынесены в пакет
`turtlesim_msgs`, поэтому тип позы — `turtlesim_msgs/msg/Pose`,
а не старый `turtlesim/msg/Pose`.

## Поля Twist

`Twist` — скорость в свободном пространстве, два вектора `Vector3`
(`float64 x, y, z`):

- `linear` — линейная скорость, м/с в системе координат робота.
  Для turtlesim используется только `linear.x` (вперёд/назад по курсу черепахи);
  `linear.y` тоже учитывается turtlesim (движение вбок), `linear.z` игнорируется.
- `angular` — угловая скорость, рад/с вокруг осей. Черепаха на плоскости
  поворачивается только вокруг вертикали, поэтому значим `angular.z`
  (положительное — против часовой стрелки); `angular.x`, `angular.y` игнорируются.

Команда `{linear: {x: 1.0}, angular: {z: 0.5}}` задаёт движение вперёд
со скоростью 1 и поворот 0.5 рад/с — дугу окружности радиусом
`v/ω = 2`. turtlesim применяет последнюю команду около 1 секунды, затем
останавливается: после `pub --once` угол вырос ровно на 0.504 рад,
а скорости в позе снова 0.0 ([pose-after-once.txt](pose-after-once.txt)).

## Поля Pose

`turtlesim_msgs/msg/Pose`: `x`, `y` — положение в окне (0…≈11),
`theta` — курс в радианах, `linear_velocity`, `angular_velocity` — текущие
скорости черепахи.
