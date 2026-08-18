from utils.site_generator import generate_html
from utils.ftp_upload import upload_to_ftp
import sys

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv[1:]
    generate_html()
    upload_to_ftp(dry_run=dry_run)

