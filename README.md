---
name: ai-skill-manager-readme
description: Project overview and quick start guide for ai-skill-manager in English and Russian.
metadata:
  domain: documentation
  tags:
    - ai-skill-manager
    - readme
    - quickstart
    - bilingual
    - install
    - setup
  responsibilities:
    - introduce the project
    - provide installation and setup instructions
    - link to detailed documentation and example skills
---

# AI Skills Manager / Менеджер навыков ИИ

Sync AI agent skills into `.agents/skills/` from local directories or GitHub repositories.
Синхронизирует навыки AI-агентов в `.agents/skills/` из локальных директорий или репозиториев GitHub.

## Installation / Установка

```bash
pip install git+https://github.com/InsonusK/ai-skill-manager.git
```

For detailed installation options (source install, upgrade, Windows, requirements.txt) see [docs/install.md](docs/install.md).
Подробные варианты установки (из исходников, обновление, Windows, requirements.txt) см. в [docs/install.md](docs/install.md).

## Quick start / Быстрый старт

Create an `ai-skills.yaml` config in your project root:
Создайте конфиг `ai-skills.yaml` в корне проекта:

```yaml
sources:
  - path: ./my-skills
    type: auto

settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: error
```

Run the sync:
Запустите синхронизацию:

```bash
ai-skill-manager sync
# or use the short alias / или используйте короткий псевдоним
aism sync
```

## What it does / Что делает утилита

- Discovers skills from local directories or GitHub repositories.
  Обнаруживает навыки в локальных директориях или репозиториях GitHub.
- Copies them to a target directory (default: `.agents/skills`).
  Копирует их в целевую директорию (по умолчанию: `.agents/skills`).
- Removes orphan skills that are no longer in the config (optional).
  Удаляет осиротевшие навыки, которых больше нет в конфиге (опционально).
- Updates internal links so they point to the correct target paths.
  Обновляет внутренние ссылки, чтобы они указывали на правильные целевые пути.
- Supports dry-run mode to preview changes safely.
  Поддерживает режим сухого прогона для безопасного предпросмотра изменений.

## Documentation / Документация

- [Installation / Установка](docs/install.md)
- [Running / Запуск](docs/run.md)
- [Configuration / Конфигурация](docs/config.md)
- [Discovery architecture / Архитектура обнаружения](docs/discovery.md)

A public collection of ready-to-use skills is maintained at
<https://github.com/InsonusK/ai-skills.git>.
Там же поддерживается публичная коллекция готовых к использованию навыков:
<https://github.com/InsonusK/ai-skills.git>.
