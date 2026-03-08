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

## Установка как Claude Code skill

Вставить промпт в Claude Code:

> Скачай два файла из репозитория github.com/2030ai/2030ai-telegraph-publisher-template: файл `publish.py` сохрани в `~/.claude/telegraph/publish.py`, а файл `.claude/skills/telegraph/skill.md` сохрани в `~/.claude/skills/telegraph/skill.md`. Создай директории, если их нет.

## Запуск тестов

```bash
python3 -m unittest test_publish -v
```

## Правила для .env

В этом проекте .env не используется. Токен Telegraph хранится в `~/.claude/telegraph/token.txt` (вне репозитория).
