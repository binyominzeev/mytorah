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

## Local test server

The generated site (`site/`) uses absolute paths like `/static/styles.css`, so it must be served
from its own folder as the web root, not just opened as a `file://` page (otherwise the CSS/JS
won't load). Run this from the project root:

```bash
python3 -m http.server 8000 --directory site
```

Then open http://localhost:8000/index.html (or http://localhost:8000/hu/index.html for the
Hungarian version) in a browser. Use your browser's device toolbar (responsive mode) to test the
mobile/tablet layout.

## Deploy

Run the generator and FTP synchronisation from the project root:

```bash
python3 upload.py
```

The synchronisation uses plain FTP and stores a `.mytorah-manifest.json` file in the
configured remote directory. After the first full upload, only files whose SHA-256 hash
changed are uploaded. Remote files that no longer exist locally are not deleted.

To inspect the planned changes without uploading files:

```bash
python3 upload.py --dry-run
```

FTP credentials are read from the local `config.py`, which is excluded from Git. Do not
commit that file or share its contents. Because plain FTP is unencrypted, use it only when
the hosting environment requires it and rotate the password if it has been exposed.

It is written together with ChatGPT:

https://chatgpt.com/share/67ca0b33-bbc0-8002-9da7-a5df08bc731c

