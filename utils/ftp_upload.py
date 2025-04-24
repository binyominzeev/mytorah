from ftplib import FTP
import os
from config import FTP_HOST, FTP_USER, FTP_PASS, FTP_DIR, OUTPUT_PATH

def upload_directory(ftp, local_path, remote_path, level=0):
    """Recursively upload a directory and its contents to the FTP server, with verbose logging."""
    indent = "  " * level  # Indentation for readability

    if not os.path.isdir(local_path):
        print(f"{indent}❌ Skipping non-directory: {local_path}")
        return

    try:
        ftp.mkd(remote_path)
        print(f"{indent}📁 Created remote directory: {remote_path}")
    except Exception as e:
        print(f"{indent}📁 Remote directory exists: {remote_path}")

    ftp.cwd(remote_path)

    for item in os.listdir(local_path):
        local_item = os.path.join(local_path, item)
        remote_item = f"{remote_path}/{item}"

        if os.path.isdir(local_item):
            upload_directory(ftp, local_item, remote_item, level + 1)
        else:
            try:
                with open(local_item, "rb") as f:
                    ftp.storbinary(f"STOR {item}", f)
                filesize = os.path.getsize(local_item)
                print(f"{indent}📄 Uploaded {item} → {remote_item} ({filesize} bytes)")
            except Exception as e:
                print(f"{indent}❌ Failed to upload {item} → {remote_item}: {e}")

    ftp.cwd("..")


def upload_to_ftp():
    """Uploads generated HTML files and static assets to FTP server."""
    print("🚀 Starting FTP upload...")
    ftp = FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    print(f"✅ Logged in to FTP: {FTP_HOST}")
    ftp.cwd(FTP_DIR)

    upload_directory(ftp, OUTPUT_PATH, FTP_DIR)

    ftp.quit()
    print("✅ Site uploaded to FTP (including static assets).")


