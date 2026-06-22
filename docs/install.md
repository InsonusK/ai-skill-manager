---
name: ai-skill-manager-install
description: Installation instructions for ai-skill-manager in English and Russian.
metadata:
  domain: documentation
  tags:
    - ai-skill-manager
    - install
    - setup
    - bilingual
  responsibilities:
    - list system requirements
    - describe source and dependency installation
    - explain how to verify the installation
---

# Installation / Установка

## Requirements / Требования

- Python 3.9 or newer / Python 3.9 или новее
- `pip`

## Install from source (development) / Установка из исходников (для разработки)

Clone the repository and install in editable mode:
Клонируйте репозиторий и установите в редактируемом режиме:

```bash
git clone https://github.com/InsonusK/ai-skills-manager
cd ai-skill-manager
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

This installs the package along with its runtime dependency (`pyyaml`).
Это устанавливает пакет вместе с его runtime-зависимостью (`pyyaml`).

## Install dependencies only / Установка только зависимостей

If you prefer to run the code without installing the package, install the requirements file:
Если вы предпочитаете запускать код без установки пакета, установите зависимости из requirements:

```bash
pip install -r requirements.txt
```

## Verify installation / Проверка установки

After installation, the `ai-skill-manager` command should be available:
После установки команда `ai-skill-manager` должна быть доступна:

```bash
ai-skill-manager --help
```

The command also has a short alias:
Команда также имеет короткий псевдоним:

```bash
aism --help
```

Or run the CLI module directly:
Или запустите CLI-модуль напрямую:

```bash
python -m ai_skill_manager.cli --help
```

## Next steps / Следующие шаги

- Configure your skills in `ai-skills.yaml` (see [Configuration / Конфигурация](config.md)).
  Настройте свои навыки в `ai-skills.yaml` (см. [Configuration / Конфигурация](config.md)).
- Run the sync (see [Running / Запуск](run.md)).
  Запустите синхронизацию (см. [Running / Запуск](run.md)).
