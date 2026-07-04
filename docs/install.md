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
    - linux
    - windows
  responsibilities:
    - list system requirements
    - describe GitHub, source and dependency installation
    - explain how to verify the installation
    - provide Linux and Windows setup examples
---

# Installation / Установка

## Requirements / Требования

- Python 3.9 or newer / Python 3.9 или новее
- `pip`
- `git` (for GitHub installs) / `git` (для установки из GitHub)

## Install from GitHub / Установка из GitHub

Install the latest version directly from the GitHub repository:
Установите последнюю версию напрямую из репозитория GitHub:

```bash
pip install git+https://github.com/InsonusK/ai-skill-manager.git
```

To install a specific branch, tag or commit:
Чтобы установить конкретную ветку, тег или коммит:

```bash
# Latest master / Последний master
pip install git+https://github.com/InsonusK/ai-skill-manager.git

# Specific tag / Конкретный тег
pip install git+https://github.com/InsonusK/ai-skill-manager.git@v1.1.0

# Specific branch / Конкретная ветка
pip install git+https://github.com/InsonusK/ai-skill-manager.git@feature-branch
```

This requires `git` to be installed on your system.
Для этого на системе должен быть установлен `git`.

### Upgrade / Обновление

To upgrade to the latest master:
Чтобы обновиться до последнего master:

```bash
pip install --force-reinstall git+https://github.com/InsonusK/ai-skill-manager.git
```

## Install from source (development) / Установка из исходников (для разработки)

Clone the repository and install in editable mode:
Клонируйте репозиторий и установите в редактируемом режиме:

```bash
git clone https://github.com/InsonusK/ai-skill-manager
cd ai-skill-manager
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows use PowerShell:
В Windows используйте PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

This installs the package along with its runtime dependencies (`pyyaml` and `rich`).
Это устанавливает пакет вместе с его runtime-зависимостями (`pyyaml` и `rich`).

### Possible errors
**filename too long error: cannot stat**
In case file path is too long, you can fix it by:
В случае если длинна путей слишком большая, то можно пофиксить
```shell
git config --global core.longpaths true
```

## Install dependencies only / Установка только зависимостей

If you prefer to run the code without installing the package, install the requirements file:
Если вы предпочитаете запускать код без установки пакета, установите зависимости из requirements:

```bash
pip install -r requirements.txt
```

## Basic setup / Базовая настройка

### Linux / macOS

```bash
# Create a project folder / Создайте папку проекта
mkdir my-agent-project && cd my-agent-project

# Create a virtual environment / Создайте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Install ai-skill-manager from GitHub / Установите ai-skill-manager из GitHub
pip install git+https://github.com/InsonusK/ai-skill-manager.git

# Create a skills folder and config / Создайте папку навыков и конфиг
mkdir my-skills
cat > ai-skills.yaml << 'EOF'
sources:
  - path: ./my-skills
    type: auto

settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: error
EOF

# Sync skills / Синхронизируйте навыки
ai-skill-manager sync --dry-run
ai-skill-manager sync
```

### Windows (PowerShell)

```powershell
# Create a project folder / Создайте папку проекта
mkdir my-agent-project; cd my-agent-project

# Create a virtual environment / Создайте виртуальное окружение
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install ai-skill-manager from GitHub / Установите ai-skill-manager из GitHub
pip install git+https://github.com/InsonusK/ai-skill-manager.git

# Create a skills folder and config / Создайте папку навыков и конфиг
mkdir my-skills
@'
sources:
  - path: ./my-skills
    type: auto

settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: error
'@ | Out-File -Encoding utf8 ai-skills.yaml

# Sync skills / Синхронизируйте навыки
ai-skill-manager sync --dry-run
ai-skill-manager sync
```

### Use public skills from GitHub / Использовать публичные навыки из GitHub

You can point the config directly at the public skills repository:
Можно направить конфиг напрямую на публичный репозиторий навыков:

```yaml
sources:
  - path: https://github.com/InsonusK/ai-skills.git
    type: github
    tree: master
    subpath: skills

settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: error
```

Run:
Запустите:

```bash
ai-skill-manager sync
```

More example skills are available at <https://github.com/InsonusK/ai-skills.git>.
Больше примеров навыков доступно по адресу <https://github.com/InsonusK/ai-skills.git>.

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
