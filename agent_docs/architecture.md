# Архитектура

## Обзор

CLI-инструмент + Claude Code skill для публикации контента на telegra.ph. Один Python-файл, stdlib only, zero dependencies.

## Контекст

Пользователь работает в Claude Code. Агент генерирует контент (анализ, отчёт, таблицу) — и хочет поделиться ссылкой. Скилл позволяет опубликовать контент одной командой и получить URL.

## Ключевые компоненты

```
publish.py (единственный файл)
├── Конвертеры
│   ├── html_to_nodes()    — HTML → Telegraph Node[]
│   ├── markdown_to_nodes() — Markdown → HTML → Telegraph Node[]
│   └── text_to_nodes()    — Plain text → Telegraph Node[]
├── Таблицы
│   ├── _format_table_mono() — таблица → моноширинный <pre> с рамками
│   └── _NodeBuilder (table buffering) — HTML <table> → <pre>
├── Auto-split
│   ├── _split_nodes()      — разбиение на чанки ≤ 60KB
│   ├── _split_large_node() — разрезание крупного <pre> по строкам
│   └── _add_nav_links()    — навигация между частями
├── API
│   ├── api_call()     — вызов Telegraph API
│   ├── ensure_token() — загрузка/создание токена
│   └── upload_image() — загрузка файла на Telegraph CDN
└── CLI (argparse)
    ├── create  — создание страницы
    ├── edit    — редактирование страницы
    ├── get     — информация о странице
    ├── list    — список созданных страниц
    └── upload  — загрузка изображения
```

## Потоки данных

```
Контент (HTML/MD/text)
  → Конвертер (html.parser / regex)
    → Telegraph Node[] (JSON)
      → _split_nodes() если > 60KB
        → POST api.telegra.ph/createPage
          → {"ok": true, "url": "https://telegra.ph/..."}
```

## Технологии и зависимости

- Python 3.10+ (только stdlib)
- `urllib.request` — HTTP-запросы к Telegraph API
- `html.parser.HTMLParser` — парсинг HTML
- `argparse` — CLI
- `json` — сериализация Telegraph nodes

## Ограничения

- Telegraph API: максимум 64KB контента на страницу
- Поддерживаемые теги: a, aside, b, blockquote, br, code, em, figcaption, figure, h3, h4, hr, i, img, li, ol, p, pre, s, strong, u, ul
- Страницы нельзя удалить, только редактировать
- `<table>` не поддерживается — рендерим как `<pre>` с box-drawing

## Roadmap

- [ ] Поддержка вложенных списков в Markdown
- [ ] Команда `auth` для настройки аккаунта с кастомным именем
- [ ] Поддержка Markdown footnotes
