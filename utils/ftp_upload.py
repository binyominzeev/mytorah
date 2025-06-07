from ftplib import FTP, error_perm
import os
from config import FTP_HOST, FTP_USER, FTP_PASS, FTP_DIR, OUTPUT_PATH

def remote_file_size(ftp, filename):
    """Return the size of a remote file, or None if it doesn't exist."""
    try:
        return ftp.size(filename)
    except Exception:
        return None

def upload_directory(ftp, local_path, remote_path, level=0):
    """Recursively upload only new or changed files to the FTP server."""
    indent = "  " * level  # Indentation for readability

    if not os.path.isdir(local_path):
        print(f"{indent}❌ Skipping non-directory: {local_path}")
        return

    # Try to create remote directory if it doesn't exist
    try:
        ftp.mkd(remote_path)
        print(f"{indent}📁 Created remote directory: {remote_path}")
    except Exception:
        print(f"{indent}📁 Remote directory exists: {remote_path}")

    ftp.cwd(remote_path)

    remote_files = []
    try:
        remote_files = ftp.nlst()
    except Exception:
        pass

    for item in os.listdir(local_path):
        local_item = os.path.join(local_path, item)
        remote_item = f"{remote_path}/{item}"

        if os.path.isdir(local_item):
            upload_directory(ftp, local_item, remote_item, level + 1)
        else:
            upload = False
            local_size = os.path.getsize(local_item)
            remote_size = None
            if item in remote_files:
                remote_size = remote_file_size(ftp, item)
                if remote_size != local_size:
                    upload = True
            else:
                upload = True

            if upload:
                try:
                    with open(local_item, "rb") as f:
                        ftp.storbinary(f"STOR {item}", f)
                    print(f"{indent}📄 Uploaded {item} → {remote_item} ({local_size} bytes)")
                except Exception as e:
                    print(f"{indent}❌ Failed to upload {item} → {remote_item}: {e}")
            else:
                print(f"{indent}✅ Skipped (unchanged): {item}")

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


