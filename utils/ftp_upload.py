from ftplib import FTP
from io import BytesIO
import hashlib
import json
import os

from config import FTP_DIR, FTP_HOST, FTP_PASS, FTP_USER, OUTPUT_PATH

FTP_TIMEOUT = 30
MANIFEST_NAME = ".mytorah-manifest.json"


def build_manifest(local_root):
    """Return SHA-256 hashes for every file below local_root."""
    manifest = {}
    for root, directories, filenames in os.walk(local_root):
        directories.sort()
        for filename in sorted(filenames):
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_root).replace(os.sep, "/")
            digest = hashlib.sha256()
            with open(local_path, "rb") as file_handle:
                for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            manifest[relative_path] = digest.hexdigest()
    return manifest


def read_remote_manifest(ftp):
    """Read the previous manifest once; a missing manifest means full sync."""
    contents = BytesIO()
    try:
        ftp.retrbinary(f"RETR {MANIFEST_NAME}", contents.write)
    except Exception:
        return {}

    try:
        data = json.loads(contents.getvalue().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def ensure_remote_directory(ftp, remote_path):
    try:
        ftp.mkd(remote_path)
    except Exception:
        pass


def upload_file(ftp, local_root, relative_path):
    local_path = os.path.join(local_root, *relative_path.split("/"))
    remote_directory, filename = os.path.split(relative_path)
    if remote_directory:
        for directory in remote_directory.split("/"):
            ensure_remote_directory(ftp, directory)
            ftp.cwd(directory)

    try:
        with open(local_path, "rb") as file_handle:
            ftp.storbinary(f"STOR {filename}", file_handle)
    finally:
        if remote_directory:
            ftp.cwd("/" + FTP_DIR.strip("/"))


def upload_to_ftp(dry_run=False):
    """Upload only changed files over plain FTP and fail on any upload error."""
    print("🚀 Starting FTP upload...")
    local_manifest = build_manifest(OUTPUT_PATH)
    ftp = FTP(timeout=FTP_TIMEOUT)
    uploaded = 0
    skipped = 0

    try:
        ftp.connect(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        print(f"✅ Logged in to FTP: {FTP_HOST}")
        ftp.cwd(FTP_DIR)
        remote_manifest = read_remote_manifest(ftp)

        changed_files = [
            path for path, digest in local_manifest.items()
            if remote_manifest.get(path) != digest
        ]
        skipped = len(local_manifest) - len(changed_files)

        for relative_path in changed_files:
            if dry_run:
                print(f"🔎 Would upload: {relative_path}")
                continue
            upload_file(ftp, OUTPUT_PATH, relative_path)
            uploaded += 1
            print(f"📄 Uploaded: {relative_path}")

        if not dry_run:
            manifest_data = json.dumps(local_manifest, ensure_ascii=True, sort_keys=True).encode("utf-8")
            ftp.storbinary(f"STOR {MANIFEST_NAME}", BytesIO(manifest_data))
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()

    action = "would upload" if dry_run else "uploaded"
    print(f"✅ FTP sync complete: {action} {uploaded}, skipped {skipped}.")


