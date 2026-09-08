# config.py

VAULT_PATH = "/home/user/Documents/MyTorah"
FTP_HOST = ""
FTP_USER = ""
FTP_PASS = ""
# Directory on the FTP server where content-sync/sync_content.py uploads the vault
# Markdown notes. Must be outside the nginx web root (which serves the Next.js
# `out/` build via git pull + npm run build), e.g. a sibling folder to public_html.
CONTENT_FTP_DIR = "/mytorah-content"
FTP_TIMEOUT = 30
