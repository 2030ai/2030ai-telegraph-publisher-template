---
name: telegraph
description: "Publish Markdown, HTML, plain text, and images to telegra.ph through the local publish.py helper. Use when the user asks to publish content on Telegraph, create a telegra.ph link, update an existing Telegraph page, list Telegraph pages, or upload an image to Telegraph CDN."
when_to_use: "Use when the user asks: опубликуй на телеграф, publish to telegraph, сделай ссылку на telegra.ph, update a Telegraph page, list my Telegraph pages, or upload an image to Telegraph."
argument-hint: "[create|edit|get|list|upload] [title/path/file]"
disable-model-invocation: true
---

# Telegraph Publisher

Publish user-approved content to telegra.ph with the repository helper `publish.py`.

## Safety

Telegraph publishing is an external side effect. Before creating or editing a page, confirm what content will be published unless the user has already explicitly requested publication of the current artifact or a named file.

Never publish secrets, private medical/financial/legal data, access tokens, `.env` files, or private chat/email content unless the user explicitly confirms that exact content can be public.

## Helper Resolution

Use the first existing helper path:

1. `./publish.py` from the current repository.
2. `~/.claude/telegraph/publish.py` for a global install.
3. A user-provided path.

Run `python3 <helper> --help` if command details are unclear.

## Common Commands

Create a page from stdin:

```bash
printf '%s' "$CONTENT" | python3 publish.py create --title "Title"
```

Create a page from a file:

```bash
python3 publish.py create --title "Title" --file report.md
```

Edit an existing page:

```bash
python3 publish.py edit --path "Page-Path-01-01" --title "Updated title" --file report.md
```

Read or list pages:

```bash
python3 publish.py get --path "Page-Path-01-01"
python3 publish.py list
```

Upload an image:

```bash
python3 publish.py upload --file screenshot.png
```

## Output

Return the Telegraph URL and a short note about what was published. If the helper returns JSON, parse it and report only the useful fields.
