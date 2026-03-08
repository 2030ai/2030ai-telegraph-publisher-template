# Telegraph Publisher — Agent Rules

## Описание проекта

CLI-инструмент + Claude Code skill для публикации контента на telegra.ph.
Один Python-файл (`publish.py`), stdlib only, zero external dependencies.

**Цель:** Позволить агенту Claude Code публиковать сгенерированный контент (анализ, отчёт, таблицу) на telegra.ph одной командой и возвращать ссылку пользователю.

**Контекст:** Пользователи Claude Code генерируют длинные артефакты, но не могут удобно поделиться ими. Скилл решает проблему: одна фраза → ссылка telegra.ph.

**Ограничения:** Только stdlib Python 3.10+, никаких pip-зависимостей.

## Назначение и границы

AGENTS.md содержит универсальные правила. Специфические инструкции — в agent_docs/.

## Инициализация задачи

Перед началом работы агент должен:
1. Прочитать описание проекта выше
2. Прочитать последние 10 записей в [agent_docs/development-history.md](agent_docs/development-history.md)
3. Прочитать релевантные документы из agent_docs/

## Ключевые файлы

- `publish.py` — main CLI script (HTML/Markdown/text → Telegraph nodes → API)
- `test_publish.py` — unit tests (51 тест)
- `.claude/skills/telegraph/skill.md` — Claude Code skill с триггерами и workflow

## Conventions

- No external dependencies — stdlib only (`urllib.request`, `html.parser`, `json`, `argparse`)
- JSON output on stdout, diagnostics on stderr
- Token auto-created on first use, stored in `~/.claude/telegraph/token.txt`
- Pipe-friendly: content via stdin or `--file`
- Format auto-detected from file extension (`.md` → markdown, `.html` → html, `.txt` → text)
- HTML `<table>` and Markdown pipe tables → monospace `<pre>` with box-drawing borders
- Content > 64KB auto-split into linked multi-part pages
- Image upload via `upload` command (Telegraph file hosting, no token required)

## Универсальные правила

- Следуй существующим паттернам в коде
- Держи документацию краткой: не копируй код, ссылайся на файлы
- Перед крупными изменениями — координируй (ADR если значительно)

## Чеклист перед завершением

- [ ] Требования выполнены
- [ ] Тесты проходят (`python3 -m unittest test_publish -v`)
- [ ] Документация обновлена
- [ ] Запись добавлена в development-history.md
- [ ] Проверены conventions выше
