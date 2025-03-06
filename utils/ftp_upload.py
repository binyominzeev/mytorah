from ftplib import FTP
import os
from config import FTP_HOST, FTP_USER, FTP_PASS, FTP_DIR, OUTPUT_PATH

def upload_directory(ftp, local_path, remote_path):
    """Recursively upload a directory and its contents to the FTP server."""
    if not os.path.isdir(local_path):
        return
    
    try:
        ftp.mkd(remote_path)  # Create remote directory if not exists
    except:
        pass  # Ignore if the directory already exists

    ftp.cwd(remote_path)

    for item in os.listdir(local_path):
        local_item = os.path.join(local_path, item)
        remote_item = f"{remote_path}/{item}"

        if os.path.isdir(local_item):
            upload_directory(ftp, local_item, remote_item)  # Recursively upload subdirectory
        else:
            with open(local_item, "rb") as f:
                ftp.storbinary(f"STOR {item}", f)  # Upload file

    ftp.cwd("..")  # Move back to parent directory

def upload_to_ftp():
    """Uploads generated HTML files and static assets to FTP server"""
    ftp = FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.cwd(FTP_DIR)

    # Upload all HTML files and static assets
    upload_directory(ftp, OUTPUT_PATH, FTP_DIR)

    ftp.quit()
    print("✅ Site uploaded to FTP (including static assets).")

