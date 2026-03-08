# История разработки

Правило ротации: только последние 10 записей. Старые переносить в development-history-archive.md.

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
- [x] skill.md
- [x] AGENTS.md
- [x] README.md

**Следующие шаги:** Создание agent_docs скелета, публикация.

---

## 2026-03-08 — Начальная реализация

**Что сделано:**
- CLI-скрипт publish.py: HTML/Markdown/text → Telegraph nodes → API
- Claude Code skill с триггерами и workflow
- Команды: create, edit, get
- Markdown-конвертер: headings, bold, italic, code, lists, blockquotes, links, images
- HTML-конвертер: heading remap, passthrough tags, attribute preservation
- Автосоздание Telegraph-аккаунта при первом использовании
- install.sh для установки в ~/.claude/

**Почему:** Решение проблемы шеринга контента из Claude Code.

**Обновлено:**
- [x] publish.py (новый)
- [x] skill.md (новый)
- [x] install.sh (новый)
- [x] README.md (новый)
