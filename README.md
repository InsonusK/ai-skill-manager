# AI SKILL MANAGER

Update skills in .agets/skills from source

```yaml
# ai-skills.yaml
sources:
  - path: ./my-skills       # auto-detect по умолчанию
    type: auto              # auto, flat, dir

settings:
    target: .agents/skills  # куда копировать
    remove_orphans: true    # удалять skills, пропавшие из конфига
    on_conflict: error      # error | last_wins
    dry_run: false          # можно включить глобально
```

## Install
```bash
# Из PyPI (когда опубликуешь)
pip install ai-skills-sync

# Из wheel файла
pip install ai_skills_sync-1.0.0-py3-none-any.whl

# Из source (development mode)
git clone <repo>
cd ai-skills-sync
pip install -e .
```

## Run
```bash
# Стандартный запуск (ищет ai-skills.yaml в текущей директории)
python ai-skills-sync.py

# Кастомный конфиг
python ai-skills-sync.py -c ./config/my-skills.yaml

# Проверка без изменений
python ai-skills-sync.py --dry-run

# Базовый запуск (ищет ai-skills.yaml в текущей директории)
ai-skills-sync

# С кастомным конфигом
ai-skills-sync -c ./config/skills.yaml

# Dry-run для проверки
ai-skills-sync --dry-run

# Переопределение target
ai-skills-sync --target ./my-skills

# Управление orphans
ai-skills-sync --remove-orphans      # удалить лишнее
ai-skills-sync --keep-orphans        # оставить лишнее

# Полная справка
ai-skills-sync -h
```

## Types
### flat
```
- directory
  - skill_1.md      -> ${settings.target}/skill_1/SKILL.md
  - skill_2.md      -> ${settings.target}/skill_2/SKILL.md
```

### dir
```
- directory
  - skill_1
    - any_dir       -> ${settings.target}/skill_1/any_dir
    - any_files     -> ${settings.target}/skill_1/any_files
    - SKILL.md      -> ${settings.target}/skill_1/SKILL.md
  - skill_2
    - any_dir       -> ${settings.target}/skill_2/any_dir
    - any_files     -> ${settings.target}/skill_2/any_files
    - SKILL.md      -> ${settings.target}/skill_2/SKILL.md
```

### auto
1. SKILL.MD существует в директории
    1. Есть - работаем в режиме dir
    2. Нет - работаем как с flat, все директории проверяем повторно