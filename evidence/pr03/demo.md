# ПР03. Первая нода: поза и команда

Среда: Windows 10 + WSL 2 (Ubuntu 24.04), контейнер
`osrf/ros:lyrical-desktop-full` (ROS 2 Lyrical), репозиторий смонтирован
в `/work`, окно turtlesim через WSLg. Во всех терминалах `ROS_DOMAIN_ID=16`.
Опыт: 2026-09-26, 15:56:53–15:59:01 UTC ([started-utc.txt](started-utc.txt),
[finished-utc.txt](finished-utc.txt)). Терминалы: A — сборка и
`ros2 launch turtle_bringup sim.launch.py`, B — нода `patrol`,
C — диагностика.

## Как устроена нода

```text
                 /turtle1/pose (≈62 Гц)                cmd_vel → /cmd_vel
turtlesim ───────────────────────────▶ _on_pose ──▶ self._pose
                                                        │
                   таймер 0,1 с ──▶ _on_timer ──▶ compute_command(self._pose) ──▶ publish(Twist)
```

- [control.py](../../src/patrol/patrol/control.py): чистая функция
  `compute_command(pose)` — без позы `(0.0, 0.0)`, с позой `(0.5, 0.3)`.
- [patrol.py](../../src/patrol/patrol/patrol.py): подписка на `/turtle1/pose`,
  таймер 0,1 с, издатель `Twist` в **относительное** имя `cmd_vel`.

## Роли init, spin, callback и Ctrl+C

- **`rclpy.init(args=...)`** — создаёт контекст ROS 2 и разбирает аргументы
  после `--ros-args`. Именно здесь применяется remap
  `-r cmd_vel:=/turtle1/cmd_vel`: правило запоминается в контексте, и при
  создании издателя имя `cmd_vel` разрешается уже в `/turtle1/cmd_vel`.
  Без `init` нельзя создать ни ноду, ни подписку.
- **`Patrol()`** (конструктор ноды) — регистрирует ноду `/patrol`, подписку,
  издателя и таймер. С этого момента они видны в графе
  ([node-info-broken.txt](node-info-broken.txt)), но код ещё ничего не делает.
- **`rclpy.spin(node)`** — цикл исполнителя (executor): ждёт событий
  (пришло сообщение, истёк таймер) и вызывает соответствующие callback.
  Без `spin` сообщения копились бы в очереди, а таймер не срабатывал.
  Исполнитель однопоточный: callback вызываются по очереди, поэтому
  `self._pose` без блокировок читается в таймере и пишется в подписке.
- **Callback.**
  - `_on_pose` — вызывается на каждую позу (≈62 Гц), только сохраняет
    последнее сообщение; при первом пишет в лог `first pose`.
  - `_on_timer` — вызывается каждые 0,1 с независимо от частоты позы,
    считает команду чистой функцией и публикует `Twist`. Частота команды
    задаётся таймером, а не потоком позы.
- **Ctrl+C** — терминал посылает SIGINT. В ноде обработчик SIGINT rclpy
  отключён (`SignalHandlerOptions.NO`), и Python поднимает `KeyboardInterrupt`
  внутри `spin`. Он перехватывается, в `finally` выполняются
  `node.destroy_node()` (издатель, подписка и нода удаляются из графа)
  и `rclpy.try_shutdown()` (закрывается контекст). Результат — `exit=0`
  без трейсбека ([patrol-broken.txt](patrol-broken.txt),
  [patrol-fixed.txt](patrol-fixed.txt)), а в графе остаётся только
  `/turtlesim` ([nodes-after-patrol-stop.txt](nodes-after-patrol-stop.txt)).
  Со штатным обработчиком rclpy контекст закрывался прямо во время ожидания
  в `spin`, и нода падала с `RCLError: the given context is not valid`
  и кодом 1 — поэтому обработка перенесена в Python.

## Сборка и тесты

`colcon build --symlink-install --packages-select turtle_bringup patrol` —
2 пакета собраны ([build.txt](build.txt)).
`(cd src/patrol && python3 -m pytest test -v)` — **7 passed, 1 skipped**
([tests.txt](tests.txt)): три теста чистой функции (нет позы → стоп;
обычная поза → 0.5/0.3; результат не зависит от значений позы), flake8,
pep257, mypy, xmllint; copyright пропущен генератором ROS. Тесты запускаются
из каталога пакета: из корня workspace линтеры захватывают копии в `build/`.

## 1. До позы — команда нулевая

B: `ros2 run patrol patrol` при остановленном симуляторе. Лог:
`publishing to /cmd_vel, waiting for /turtle1/pose`.
C: `ros2 topic echo /cmd_vel --once` → `linear.x: 0.0`, `angular.z: 0.0`
([cmd-before-pose.txt](cmd-before-pose.txt)). Не зная позы, нода командует стоп.

## 2. Сбой: относительный `cmd_vel` не соединён с turtlesim

A: `ros2 launch turtle_bringup sim.launch.py`. В B появилось
`first pose: x=5.544 y=5.544 theta=0.000` — подписка работает.

- `/cmd_vel` теперь несёт рабочую команду `linear.x: 0.5`, `angular.z: 0.3`
  ([cmd-after-pose-broken.txt](cmd-after-pose-broken.txt)).
- `ros2 node info /patrol`: подписчик `/turtle1/pose`, издатель **`/cmd_vel`**
  ([node-info-broken.txt](node-info-broken.txt)).
- `ros2 topic info /cmd_vel --verbose`: **Publisher count: 1** (`patrol`),
  **Subscription count: 0** ([info-cmd_vel-broken.txt](info-cmd_vel-broken.txt)).
- `ros2 topic info /turtle1/cmd_vel --verbose`: Publisher count: 0,
  Subscription count: 1 (`turtlesim`)
  ([info-turtle1-cmd_vel-broken.txt](info-turtle1-cmd_vel-broken.txt)).
- Поза с интервалом 3 с не изменилась: x=5.544445, y=5.544445, theta=0.0,
  скорости 0 ([pose-broken-1.txt](pose-broken-1.txt),
  [pose-broken-2.txt](pose-broken-2.txt)). Черепаха стоит.

**Причина.** Имя `cmd_vel` относительное: к нему приписывается пространство
имён ноды. Нода запущена в корневом `/`, поэтому издатель получился в
`/cmd_vel`. turtlesim слушает `/turtle1/cmd_vel` — это другой топик.
Логика ноды верна (команда 0.5/0.3 считается и публикуется), тип `Twist`
и домен совпадают, но пары издатель–подписчик нет: топик обнаружен
в графе, а сообщения никому не доставляются.

## 3. Исправление: remap при запуске, код не меняется

B: `ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel`. Лог:
`publishing to /turtle1/cmd_vel`, через 0,1 с — `first pose`.

- `ros2 topic info /turtle1/cmd_vel --verbose`: **Publisher count: 1**
  (`patrol`), **Subscription count: 1** (`turtlesim`)
  ([info-turtle1-cmd_vel-fixed.txt](info-turtle1-cmd_vel-fixed.txt)).
- `/cmd_vel` исчез из графа: `Unknown topic '/cmd_vel'`
  ([info-cmd_vel-fixed.txt](info-cmd_vel-fixed.txt)).
- В `/turtle1/cmd_vel` идёт 0.5/0.3 ([cmd-fixed.txt](cmd-fixed.txt)).
- Поза меняется, черепаха едет по кругу радиусом v/ω ≈ 1.67:

| | x | y | theta | linear_velocity | angular_velocity |
|---|---|---|---|---|---|
| [pose-fixed-1.txt](pose-fixed-1.txt) | 3.923948 | 7.616968 | −1.819 | 0.5 | 0.3 |
| [pose-fixed-2.txt](pose-fixed-2.txt), через 3 с | 4.636032 | 5.811172 | −0.576 | 0.5 | 0.3 |

Угол вырос на 1.243 рад за ≈4 с (между концом первого и второго `echo`),
что согласуется с ω = 0.3 рад/с.

Remap — правильное исправление: имя топика — это настройка запуска,
а не кода. Та же нода без изменений может управлять `/turtle2`
(`-r cmd_vel:=/turtle2/cmd_vel`) или реальным роботом.

## 4. Частота команды

`timeout --signal=INT 12s ros2 topic hz /turtle1/cmd_vel` ([hz.txt](hz.txt)):
последний отчёт — **average rate: 10.000**, min 0.099 s, max 0.101 s,
std dev 0.00042 s, **window: 110** — 110 интервалов ≈ 11 с непрерывного
потока (≥ 10 с). Все промежуточные отчёты 9.999–10.000 Гц. `exit=124` —
команду остановил `timeout`, это ожидаемо. Частота совпадает с периодом
таймера 0,1 с и не зависит от частоты позы (≈62 Гц).

## 5. Остановка

Ctrl+C в B → `[ros2run]: Received signal: Interrupt`, `exit=0`, без
трейсбека. `ros2 node list` → только `/turtlesim`
([nodes-after-patrol-stop.txt](nodes-after-patrol-stop.txt)): нода и её
издатель удалены из графа, черепаха останавливается (turtlesim сам гасит
скорость через ≈1 с без новых команд). Затем Ctrl+C в A остановил симулятор.
