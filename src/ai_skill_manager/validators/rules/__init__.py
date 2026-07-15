"""Link exclusion rule builder.

Structural checks (name format, duplicate names) now live on ``Skill`` and
``SkillDictBuilder`` directly instead of a separate validation rule engine -
this package only still holds the link-exclude rules ``LinkDiscovery``
reuses (inline-code/web/skip-folder).

Построитель правил исключения ссылок.

Структурные проверки (формат имени, дубликаты имён) теперь находятся прямо
в ``Skill`` и ``SkillDictBuilder``, а не в отдельном движке правил
валидации - этот пакет всё ещё содержит только правила исключения ссылок,
переиспользуемые ``LinkDiscovery`` (инлайн-код/веб-ссылка/пропускаемая
директория).
"""

from .link import build_link_exclude_rules

__all__ = [
    "build_link_exclude_rules",
]
