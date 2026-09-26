# Практики по ROS 2

Корень репозитория — одновременно корень colcon workspace.
Каждая практика выполняется в своей ветке, следующая продолжает предыдущую:

- `pr01` — ПР01 (граф turtlesim, ROS_DOMAIN_ID), `master` указывает на тот же снимок;
- `pr02` — ПР02: пакет `turtle_bringup`, launch turtlesim, управление из CLI
  и диагностика неверного имени топика;
- `pr03` — ПР03: первая нода `patrol` — подписка на позу, таймер 10 Гц,
  публикация `Twist` в относительный `cmd_vel` и исправление через remap.

Отчёты: [evidence/pr01](evidence/pr01), [evidence/pr02](evidence/pr02),
[evidence/pr03](evidence/pr03) ([опыт и роли init/spin/callback/Ctrl+C](evidence/pr03/demo.md)).
[Декларация помощи ИИ](AI_USAGE.md), CI: [.github/workflows](.github/workflows).
Инструкции к ПР02 — в README ветки `pr02`.

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

## ПР03: устройство пакета `patrol`

- [patrol/control.py](src/patrol/patrol/control.py) — чистая функция
  `compute_command(pose)`: без позы — стоп `(0, 0)`, с позой — `(0.5, 0.3)`.
  Не зависит от ROS, поэтому проверяется обычными unit-тестами.
- [patrol/patrol.py](src/patrol/patrol/patrol.py) — нода `patrol`: подписка на
  `/turtle1/pose` (хранит последнюю позу), таймер 0,1 с, издатель `Twist`
  в **относительный** `cmd_vel`.
- [test/test_control.py](src/patrol/test/test_control.py) — тесты чистой функции:
  нет позы, обычное сообщение, независимость от значений позы.

## ПР03: сборка и тесты

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash
(cd src/patrol && python3 -m pytest test -q)
```

Тесты запускаются из каталога пакета: сгенерированные линтеры (flake8, mypy)
проверяют текущий каталог, и из корня захватывают копии в `build/`
(mypy: `Duplicate module named "setup"`).

## ПР03: опыт

- A: `ros2 launch turtle_bringup sim.launch.py`
- B: `ros2 run patrol patrol` — нода публикует в `/cmd_vel`, у которого нет
  подписчика, черепаха стоит.
- C: `ros2 topic info /cmd_vel`, `ros2 topic info /turtle1/cmd_vel`.
- B после Ctrl+C: `ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel` —
  издатель и подписчик соединились, черепаха едет по кругу.
- C: `timeout --signal=INT 12s ros2 topic hz /turtle1/cmd_vel` — частота
  команды (ожидается 10 Гц).

## Проверка

```bash
curl -fsSLo course-kit.tar.gz \
  https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w03-7fbfd3e8161a.tar.gz
printf '%s  %s\n' 7fbfd3e8161ab6c6ebefc7663efdaf77d9a7d490399743507f33dcefbd5ac522 \
  course-kit.tar.gz | sha256sum -c -
mkdir -p .course-kit && tar -xzf course-kit.tar.gz -C .course-kit
python3 .course-kit/v1/tools/check_practice.py PR03 --submission .
```

Сдача: коммит A — код, тесты, README, workflow; коммит B — только `evidence/pr03/`
и `AI_USAGE.md`. `report.commit` = SHA коммита A, сдаётся SHA коммита B.
