# ПР02. Команды, наблюдения и объяснение сбоя

Среда: Windows 10 + WSL 2 (Ubuntu 24.04), контейнер
`osrf/ros:lyrical-desktop-full` (ROS 2 Lyrical), репозиторий смонтирован
в `/work`, окно turtlesim выводится через WSLg (`DISPLAY=:0`).
Во всех терминалах `ROS_DOMAIN_ID=16`. Опыт: 2026-09-24,
16:31:12–16:37:12 UTC ([started-utc.txt](started-utc.txt),
[finished-utc.txt](finished-utc.txt)).

## Три команды Linux

| Команда | Зачем | Результат |
|---|---|---|
| `mkdir -p src evidence/pr02` | создать каталоги workspace и отчёта; `-p` создаёт промежуточные и не падает, если каталог уже есть | появились `src/` и `evidence/pr02/` |
| `colcon build ... 2>&1 \| tee evidence/pr02/build.txt` | `2>&1` перенаправляет stderr в stdout, `tee` одновременно показывает вывод на экране и пишет его в файл | лог сборки сохранён в [build.txt](build.txt), `set -o pipefail` сохраняет код ошибки colcon, а не `tee` |
| `test -f "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch/sim.launch.py"` | проверить, что launch-файл действительно **установлен** в `install/`, а не только лежит в `src/`; `$(...)` подставляет вывод команды | код 0: файл на месте (symlink из-за `--symlink-install`) |

Эксперимент вёлся в трёх терминалах: A — `ros2 launch`, B — издатель
`ros2 topic pub`, C — диагностика `ros2 topic info` и `ros2 topic echo`.
Издатель с `--rate 1` останавливался через Ctrl+C (SIGINT).

### `>` и `|`

- `>` перенаправляет stdout **в файл** (перезаписывая его):
  `ros2 topic echo /turtle1/pose --once > pose-fixed-before.txt`.
  Вывод на экран не попадает.
- `|` (конвейер) передаёт stdout одной программы **на stdin другой**,
  обе работают одновременно: `ros2 node list | tee nodes.txt`.
  Файл создаёт не `|`, а вторая программа (`tee`).

### `source` и запуск программы

- `source /opt/ros/lyrical/setup.bash` выполняет скрипт **в текущей
  оболочке**: изменения `PATH`, `AMENT_PREFIX_PATH`, `PYTHONPATH` и т. п.
  остаются в этом терминале и наследуются всеми программами, запущенными
  из него потом. Поэтому после сборки нужен `source install/setup.bash`,
  иначе `ros2 launch` не найдёт `turtle_bringup`.
- `bash script.sh` или `ros2 launch ...` запускают **новый дочерний процесс**.
  Он получает копию окружения, а его собственные изменения переменных
  пропадают при завершении и не влияют на родительский терминал.
  По той же причине `export ROS_DOMAIN_ID=...` не меняет уже работающую ноду.

## Пакет и сборка

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=16
cd src && ros2 pkg create --build-type ament_python --license Apache-2.0 \
  turtle_bringup --dependencies launch launch_ros turtlesim && cd ..
colcon build --symlink-install --packages-select turtle_bringup 2>&1 | tee evidence/pr02/build-empty.txt
source install/setup.bash && ros2 pkg prefix turtle_bringup   # /work/install/turtle_bringup
```

После добавления `launch/sim.launch.py` и строки
`('share/' + package_name + '/launch', glob('launch/*.launch.py'))`
в `data_files` пакет пересобран ([build.txt](build.txt)). Проверки:
`test -f` установленного launch — успешно, `python3 -m py_compile` — успешно,
`python3 -m pytest test -q` в каталоге пакета — `4 passed, 1 skipped`
(copyright пропущен генератором ROS).

## Граф после `ros2 launch turtle_bringup sim.launch.py`

- `ros2 node list` → `/turtlesim` ([nodes.txt](nodes.txt)).
- `ros2 topic list -t` → `/turtle1/cmd_vel [geometry_msgs/msg/Twist]`,
  `/turtle1/pose [turtlesim_msgs/msg/Pose]` и др. ([topics.txt](topics.txt)).
- После Ctrl+C (SIGINT) launch завершил turtlesim (`process has finished
  cleanly`), и `ros2 node list` вернул пустой список
  ([nodes-after-stop.txt](nodes-after-stop.txt) пуст).

## 1. Команда доходит

```bash
ros2 topic echo /turtle1/pose --once
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
ros2 topic echo /turtle1/pose --once
```

| | x | y | theta |
|---|---|---|---|
| до ([pose-before.txt](pose-before.txt)) | 5.544445 | 5.544445 | 0.000 |
| после ([pose-after-once.txt](pose-after-once.txt)) | 6.509309 | 5.796991 | 0.504 |

Черепаха проехала дугу и остановилась (скорости снова 0.0).

## 2. Сбой: та же команда в неверное имя

```bash
# терминал B:
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'
# терминал C, пока издатель работает:
ros2 topic info /cmd_vel --verbose
ros2 topic info /turtle1/cmd_vel --verbose
ros2 topic echo /turtle1/pose --once
```

- `/cmd_vel`: **Publisher count: 1** (`_ros2cli_1396`), **Subscription count: 0**
  ([info-cmd_vel-broken.txt](info-cmd_vel-broken.txt)).
- `/turtle1/cmd_vel`: Publisher count: 0, Subscription count: 1 (`turtlesim`)
  ([info-turtle1-cmd_vel-broken.txt](info-turtle1-cmd_vel-broken.txt)).
- Издатель отправил 49 сообщений ([pub-broken.txt](pub-broken.txt)), но поза
  не изменилась: 6.509309 / 5.796991 / 0.504 до и во время публикации
  ([pose-broken-before.txt](pose-broken-before.txt),
  [pose-broken-after.txt](pose-broken-after.txt)).

## 3. Исправлено только имя

Та же команда, тот же тип, те же данные и частота; изменено только имя
топика на `/turtle1/cmd_vel`.

- `/turtle1/cmd_vel`: **Publisher count: 1** (`_ros2cli_1636`),
  **Subscription count: 1** (`turtlesim`)
  ([info-turtle1-cmd_vel-fixed.txt](info-turtle1-cmd_vel-fixed.txt)).
- Поза: было 6.509 / 5.797 / 0.504, во время публикации
  x=7.341527, y=6.683215, theta=1.122, linear_velocity=1.0,
  angular_velocity=0.5 ([pose-fixed-before.txt](pose-fixed-before.txt),
  [pose-fixed-after.txt](pose-fixed-after.txt)). Черепаха едет по кругу;
  издатель отправил 27 сообщений ([pub-fixed.txt](pub-fixed.txt)).

## Почему так: обнаружение ≠ доставка

`--wait-matching-subscriptions 0` отключает ожидание подписчика, поэтому
`ros2 topic pub` честно пишет `publishing #N` — это лишь значит, что
сообщение **отправлено** издателем. Доставка происходит, только если DDS
сопоставил издателя и подписчика: совпадают **имя топика**, тип и
совместимые QoS, и оба в одном домене. Тип `Twist` у обоих совпадал,
домен тоже, но turtlesim подписан на `/turtle1/cmd_vel`, а `/cmd_vel` —
это другой топик, у которого нет ни одного подписчика. Граф это
показывает: топик **обнаружен** (виден в `topic list`/`topic info`, у него
есть издатель), но **Subscription count: 0**, значит, сообщения никому
не доставляются и просто отбрасываются. После исправления имени у топика
появилась пара издатель–подписчик, и поза начала меняться.
