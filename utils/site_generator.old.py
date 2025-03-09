import os
import shutil
from utils.file_utils import read_markdown_file, markdown_to_html
from config import VAULT_PATH, OUTPUT_PATH
import re

def copy_static_files():
    """Copy static assets (CSS, JS) to the output folder"""
    static_src = os.path.join(os.path.dirname(__file__), "..", "static")  # Path to static folder
    static_dst = os.path.join(OUTPUT_PATH, "static")  # Destination in output

    if os.path.exists(static_dst):
        shutil.rmtree(static_dst)  # Remove old static files

    shutil.copytree(static_src, static_dst)  # Copy entire static directory
    print("✅ Static assets copied.")

def generate_html():
    """Generate static HTML from the Obsidian vault structure"""
    if os.path.exists(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    nav_html = "<ul>"
    
    for book in sorted(os.listdir(VAULT_PATH)):
        if book.startswith("."):
            continue

        book_path = os.path.join(VAULT_PATH, book)
        if os.path.isdir(book_path):
            nav_html += f"<li>{book}<ul>"
            for parasha in sorted(os.listdir(book_path)):
                if parasha.startswith("."):
                    continue

                parasha_path = os.path.join(book_path, parasha)
                if os.path.isdir(parasha_path):
                    nav_html += f'<li><a href="{parasha}.html">{parasha}</a></li>'
                    
                    he_text = markdown_to_html(read_markdown_file(os.path.join(parasha_path, "HE.md")))
                    hu_text = markdown_to_html(read_markdown_file(os.path.join(parasha_path, "HU.md")))
                    commentary_html = ""

                    perusim_path = os.path.join(parasha_path, "perusim")
                    if os.path.exists(perusim_path):
                        for commentary_file in os.listdir(perusim_path):
                            if commentary_file.endswith(".md"):
                                file_id = commentary_file.replace(".md", "")
                                commentary_html += f'<div id="{file_id}" class="commentary">{markdown_to_html(read_markdown_file(os.path.join(perusim_path, commentary_file)))}</div><hr>'

                    # Read parasha template
                    with open("templates/parasha.html", "r", encoding="utf-8") as f:
                        page_template = f.read()

                    page_html = page_template.format(
                        title=parasha,
                        nav_structure=nav_html,
                        hebrew=he_text,
                        hungarian=hu_text,
                        commentary=commentary_html
                    )

                    with open(os.path.join(OUTPUT_PATH, f"{parasha}.html"), "w", encoding="utf-8") as f:
                        f.write(page_html)

            nav_html += "</ul></li>"

    nav_html += "</ul>"

    # Generate index page
    with open("templates/index.html", "r", encoding="utf-8") as f:
        index_template = f.read()

    with open(os.path.join(OUTPUT_PATH, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_template.format(nav_structure=nav_html))

    copy_static_files()  # Copy CSS & JS to the output directory
    print("✅ Static site generated.")

