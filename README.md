# MyTorah

Publish and sync Torah chidushim online using Obsidian.

That's how it looks like now:

![Screenshot from 2025-03-09 17-58-54](https://github.com/user-attachments/assets/7b8bcf96-fe3c-4e2a-a341-720d7735cc94)

This is the Obsidian vault for editing it:

![Screenshot from 2025-03-06 22-51-48](https://github.com/user-attachments/assets/39a42336-28c5-493e-9386-c090e730cb9e)

It can:

- Take original Torah sources and format them into the vault
- Take the commentaries and implement them into the text
- Get them together in a comment sidebar and clickable inner link

## Local development

Copy `.env.local.example` to `.env.local` and point `CONTENT_PATH` at the vault (or a synced
copy of it). Then run:

```bash
npm install
npm run dev
```

Open http://localhost:3000. Deep verse links like `/Softim/17/14` and chapter links like
`/Softim/17` won't resolve to a distinct route in dev mode (there's only one page per parasha,
`/Softim`) — use `npm run build` + a static server with the nginx rewrite (see below) to test
those, or just open `/Softim` and click a verse.

## Build

```bash
npm run build
```

With `output: 'export'` in `next.config.js`, this produces a static `out/` folder with exactly
**one page per parasha** (`out/Softim.html`) — not one per verse. `/Softim/17/14` is still a real,
bookmarkable, shareable permalink: nginx's `location ~ ^/([^/]+)/\d+(/\d+)?/?$` rule (see
`deploy/nginx.conf.sample`) serves `Softim.html` for it without a redirect, and client-side JS
(`components/ParashaView.tsx`) reads the URL on load to scroll to and highlight the right verse.
This trades "highlighted even with JavaScript disabled" for a build that's two orders of magnitude
smaller (~54 pages instead of thousands) — small text edits no longer touch a big fan-out of files.

## Deploy

Two independent things need to reach the server:

1. **Vault content** (Markdown notes) — synced over FTP, separate from the code:

   ```bash
   python3 content-sync/sync_content.py
   ```

   This uploads only changed `*.md` files (and `.obsidian/bookmarks.json`) to `CONTENT_FTP_DIR`
   (configured in `config.py`, excluded from Git). Use `--dry-run` to preview changes.

2. **Code** — deployed via git, built in place on the server:

   ```bash
   ssh your-server
   cd /path/to/mytorah
   git pull
   npm install
   npm run build
   ```

   nginx serves the `out/` folder directly (see `deploy/nginx.conf.sample`); there's no separate
   upload step and no server restart — the new static files are live as soon as the build finishes.

It is written together with ChatGPT:

https://chatgpt.com/share/67ca0b33-bbc0-8002-9da7-a5df08bc731c

