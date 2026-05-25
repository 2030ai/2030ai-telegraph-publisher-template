# Настройка окружения

Применяется при создании нового проекта из шаблона.

## Требования

- Python 3.10+
- Git

## Установка для разработки

```bash
git clone https://github.com/2030ai/2030ai-telegraph-publisher-template.git
cd 2030ai-telegraph-publisher-template
```

Зависимости не нужны — скрипт использует только stdlib.

## Установка как project-local skill

Вставить промпт в Claude Code / Codex:

> Скачай файлы из репозитория github.com/2030ai/2030ai-telegraph-publisher-template: файл `publish.py` сохрани в `~/.claude/telegraph/publish.py`, а skill manifest `.agents/skills/telegraph/SKILL.md` сохрани как canonical source в `.agents/skills/telegraph/SKILL.md` текущего проекта. Создай symlink mirrors: `.claude/skills/telegraph`, `.codex/skills/telegraph`, `.cursor/skills/telegraph` → `../../.agents/skills/telegraph`.

## Запуск тестов

```bash
python3 -m unittest test_publish -v
```

## Правила для .env

В этом проекте .env не используется. Токен Telegraph хранится в `~/.claude/telegraph/token.txt` (вне репозитория).
