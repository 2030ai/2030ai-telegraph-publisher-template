# История разработки

Правило ротации: только последние 10 записей. Старые переносить в development-history-archive.md.

---

## 2026-05-25 — Modern Claude Code skill layout

**Что сделано:**
- Добавлен canonical skill `.agents/skills/telegraph/SKILL.md`.
- Добавлены platform mirrors `.claude/skills/`, `.codex/skills/`, `.cursor/skills/`.
- Документация обновлена с uppercase `SKILL.md` и `.agents` source of truth.

**Почему:** Приведение публичного шаблона к актуальной Claude Code/Codex/Cursor skill layout.

**Обновлено:**
- [x] `.agents/skills/telegraph/SKILL.md`
- [x] README.md
- [x] AGENTS.md
- [x] agent_docs/guides/environment-setup.md

---

## 2026-03-08 — Расширение функциональности и тесты

**Что сделано:**
- Добавлены команды `list` (getPageList) и `upload` (загрузка изображений)
- Таблицы (HTML и Markdown) рендерятся как `<pre>` с box-drawing рамками
- Auto-split: контент > 64KB разбивается на связанные страницы (create + edit)
- Split крупных узлов: `<pre>` блоки > 60KB разрезаются по строкам
- Автоопределение формата по расширению файла (.md → markdown, .html → html)
- `--author-name`/`--author-url` добавлены в `edit`
- Экранирование literal HTML в Markdown (literal `<div>` → текст, не тег)
- Чтение файлов с explicit UTF-8
- Исправлен баг: `<img>` как void element (ломал стек парсера)
- 51 unit-тест покрывает конвертеры, split, навигацию, format detection
- README переписан на русский, install.sh заменён на промпт для Claude Code
- Skill обновлён: heredoc-примеры, выбор формата, typography guidelines

**Почему:** Подготовка к публикации как open-source шаблона. Закрытие всех TODO.

**Обновлено:**
- [x] publish.py
- [x] test_publish.py (новый)
- [x] SKILL.md
- [x] AGENTS.md
- [x] README.md

**Следующие шаги:** —

---

## 2026-03-08 — agent_docs и чистка

**Что сделано:**
- Создан скелет agent_docs/: architecture, adr (3 записи), development-history, guides
- AGENTS.md реструктурирован: описание проекта, протокол инициализации, чеклист
- Удалены templates/, index.md, dod.md (избыточны для маленького проекта)
- Удалён install.sh (заменён промптом в README)

**Почему:** Приведение проекта к шаблону 2030ai_project_template.

**Обновлено:**
- [x] agent_docs/ (новый)
- [x] AGENTS.md
- [x] CLAUDE.md

---

## 2026-03-08 — Начальная реализация

**Что сделано:**
- CLI-скрипт publish.py: HTML/Markdown/text → Telegraph nodes → API
- Claude Code skill с триггерами и workflow
- Команды: create, edit, get
- Markdown-конвертер: headings, bold, italic, code, lists, blockquotes, links, images
- HTML-конвертер: heading remap, passthrough tags, attribute preservation
- Автосоздание Telegraph-аккаунта при первом использовании

**Почему:** Решение проблемы шеринга контента из Claude Code.

**Обновлено:**
- [x] publish.py (новый)
- [x] SKILL.md (новый)
- [x] README.md (новый)
