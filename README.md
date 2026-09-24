# Практики по ROS 2

Корень репозитория — одновременно корень colcon workspace.
Каждая практика выполняется в своей ветке, следующая продолжает предыдущую:

- `pr01` — ПР01 (граф turtlesim, ROS_DOMAIN_ID), `master` указывает на тот же снимок;
- `pr02` — ПР02: пакет `turtle_bringup`, launch turtlesim, управление из CLI
  и диагностика неверного имени топика.

Отчёты: [evidence/pr01](evidence/pr01), [evidence/pr02](evidence/pr02)
([команды и объяснение сбоя](evidence/pr02/commands.md),
[типы сообщений](evidence/pr02/types.md)).
[Декларация помощи ИИ](AI_USAGE.md), CI: [.github/workflows](.github/workflows).

## Среда

Windows 10 + WSL 2 (Ubuntu 24.04) и контейнер `osrf/ros:lyrical-desktop-full`
(ROS 2 Lyrical). Окно turtlesim выводится через WSLg. Домен — `ROS_DOMAIN_ID=16`
во всех терминалах.

```bash
docker run -d --name pr01-student-demo \
  -e DISPLAY -e WAYLAND_DISPLAY -e XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir \
  -v /tmp/.X11-unix:/tmp/.X11-unix -v /mnt/wslg:/mnt/wslg \
  -v "$PWD":/work -w /work \
  osrf/ros:lyrical-desktop-full sleep infinity
docker exec -it pr01-student-demo bash
```

## ПР02: сборка и запуск

Из корня workspace в свежем терминале:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
set -o pipefail
colcon build --symlink-install --packages-select turtle_bringup
source install/setup.bash
test -f "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch/sim.launch.py"
ros2 launch turtle_bringup sim.launch.py
```

Пакет уже создан — не запускайте `ros2 pkg create` поверх него. Launch-файл
устанавливается через `data_files` в `setup.py`.

## ПР02: эксперимент

Во втором терминале (тот же `source` и домен 16):

```bash
ros2 topic echo /turtle1/pose --once
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
ros2 topic echo /turtle1/pose --once
```

Сбой — та же команда в неверное имя:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

В третьем терминале `ros2 topic info /cmd_vel --verbose` и
`ros2 topic info /turtle1/cmd_vel --verbose`: у `/cmd_vel` есть издатель,
но нет подписчика, черепаха стоит. После замены **только имени** на
`/turtle1/cmd_vel` у топика один издатель и один подписчик, поза меняется.

## Проверка

```bash
python3 -m py_compile src/turtle_bringup/launch/sim.launch.py
(cd src/turtle_bringup && python3 -m pytest test -q)
curl -fsSLo course-kit.tar.gz \
  https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w02-5d210c431e32.tar.gz
printf '%s  %s\n' 5d210c431e32418f45e2cffa9dd2028116c7a9520a36f3c7079c778cd73437a8 \
  course-kit.tar.gz | sha256sum -c -
mkdir -p .course-kit && tar -xzf course-kit.tar.gz -C .course-kit
python3 .course-kit/v1/tools/check_practice.py PR02 --submission .
```

Сдача: коммит A — пакет, README, workflow; коммит B — только `evidence/pr02/`
и `AI_USAGE.md`. `report.commit` = SHA коммита A, сдаётся SHA коммита B.
