# Использование ИИ

- ИИ (Qwen) использовался для:
  - адаптации команды `docker run` под WSL 2 с WSLg;
  - объяснения причины сбоя discovery в DDS при разных ROS_DOMAIN_ID.
  - Заполнение environment-sources.txt
  - настройка автотестов
- Все команды ROS и интерпретация результатов выполнены автором работы самостоятельно.
## PR02

- Использован ИИ: да
- Модель и версия: Claude Opus 5.5 (Anthropic)
- Среда или интерфейс агента: Claude Code (CLI) на Windows с доступом к WSL 2
  и Docker-контейнеру osrf/ros:lyrical-desktop-full
- Затронутые компоненты: пакет src/turtle_bringup (launch-файл, data_files
  в setup.py), README, .gitignore, workflow .github/workflows/pr02.yml,
  evidence/pr02 (commands.md, types.md, report.json), перевод репозитория
  на схему «ветка на практику» (pr01, pr02).
- Характер помощи: разбор задания и эталонного примера; подготовка пакета,
  launch-файла, README и CI; черновики commands.md и types.md и их
  оформление по фактическим выводам CLI.
- Как результат был проверен независимо: команды сборки и эксперимента
  выполнены автором в контейнере ROS 2 Lyrical, окно turtlesim наблюдалось
  через WSLg; таблицы и выводы в commands.md сверены с сохранёнными
  выводами ros2 CLI. Сборка, установка launch, py_compile, тесты пакета
  и check_practice.py PR02 выполнены локально.

Переписка и промпты не приложены.
