import os
import shutil
from utils.file_utils import read_markdown_file, markdown_to_html, remove_cssclasses
from config import VAULT_PATH, OUTPUT_PATH
import re
import unicodedata
import json

def remove_accents(text):
    """Convert accented characters to their non-accented equivalents."""
    normalized = unicodedata.normalize('NFD', text)  # Decomposes accents
    return re.sub(r'[\u0300-\u036f]', '', normalized)  # Removes diacritic marks

def copy_static_files():
    """Copy static assets (CSS, JS) to the output folder"""
    static_src = os.path.join(os.path.dirname(__file__), "..", "static")  # Path to static folder
    static_dst = os.path.join(OUTPUT_PATH, "static")  # Destination in output

    if os.path.exists(static_dst):
        shutil.rmtree(static_dst)  # Remove old static files

    shutil.copytree(static_src, static_dst)  # Copy entire static directory
    print("✅ Static assets copied.")

def load_custom_sort():
    """Load the custom sort order from bookmarks.json."""
    try:
        with open(os.path.join(VAULT_PATH, ".obsidian/bookmarks.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        
        sortspec = next((item for item in data["items"] if item.get("title") == "sortspec"), None)
        if not sortspec:
            print("⚠ Custom sort order not found, using default alphabetical order.")
            return None

        book_order = {}
        for book in sortspec["items"]:
            book_title = book["title"].replace("\\\\", "").strip()  # Remove escape sequences
            parasha_order = [p["title"] for p in book["items"]]
            book_order[book_title] = parasha_order

        return book_order

    except Exception as e:
        print(f"⚠ Error loading bookmarks.json: {e}")
        return None

def generate_nav_structure():
    """Generate the navigation HTML using the custom order where available, falling back to alphabetical otherwise."""
    custom_order = load_custom_sort()
    nav_html = "<ul>"

    # Get the actual books and parashiyot from the vault
    books_in_vault = {
        book: sorted(os.listdir(os.path.join(VAULT_PATH, book))) 
        for book in os.listdir(VAULT_PATH) if not book.startswith(".")
    }

    # Process books (custom order first, then add missing books)
    processed_books = set()
    for book, parashiyot in custom_order.items():
        if book in books_in_vault:
            nav_html += f"<li>{book}<ul>"
            processed_books.add(book)

            # Process parashiyot (custom order first, then add missing ones)
            processed_parashiyot = set()
            for parasha in parashiyot:
                if parasha in books_in_vault[book]:
                    parasha_filename = remove_accents(parasha) + ".html"
                    nav_html += f'<li><a href="{parasha_filename}">{parasha}</a></li>'
                    processed_parashiyot.add(parasha)

            # Add any missing parashiyot in alphabetical order
            for parasha in sorted(books_in_vault[book]):
                if parasha not in processed_parashiyot:
                    parasha_filename = remove_accents(parasha) + ".html"
                    nav_html += f'<li><a href="{parasha_filename}">{parasha}</a></li>'

            nav_html += "</ul></li>"

    # Add any missing books in alphabetical order
    for book in sorted(books_in_vault.keys()):
        if book not in processed_books:
            nav_html += f"<li>{book}<ul>"
            for parasha in sorted(books_in_vault[book]):
                parasha_filename = remove_accents(parasha) + ".html"
                nav_html += f'<li><a href="{parasha_filename}">{parasha}</a></li>'
            nav_html += "</ul></li>"

    nav_html += "</ul>"
    return nav_html

def generate_html():
    """Generate static HTML files from the Obsidian vault structure."""
    if os.path.exists(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    nav_html = generate_nav_structure()  # ✅ Generate nav structure once

    for book in sorted(os.listdir(VAULT_PATH)):
        if book.startswith("."):
            continue

        book_path = os.path.join(VAULT_PATH, book)
        if os.path.isdir(book_path):
            for parasha in sorted(os.listdir(book_path)):
                if parasha.startswith("."):
                    continue

                parasha_path = os.path.join(book_path, parasha)
                if os.path.isdir(parasha_path):
                    filename = remove_accents(parasha) + ".html"

                    # Read Hebrew & Hungarian Markdown
                    he_text_lines = remove_cssclasses(read_markdown_file(os.path.join(parasha_path, "HE.md"))).split("\n")
                    hu_text_lines = remove_cssclasses(read_markdown_file(os.path.join(parasha_path, "HU.md"))).split("\n")

                    # Convert Markdown to HTML and structure as a bilingual table
                    table_rows = ""
                    for he_line, hu_line in zip(he_text_lines, hu_text_lines):
                        he_html = markdown_to_html(he_line.strip()) if he_line.strip() else "&nbsp;"
                        hu_html = markdown_to_html(hu_line.strip()) if hu_line.strip() else "&nbsp;"
                        table_rows += f"<tr><td class='hebrew'>{he_html}</td><td class='hungarian'>{hu_html}</td></tr>\n"

                    bilingual_table_html = f"""
                    <table class="bilingual-table">
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                    """

                    # Process Commentaries
                    commentary_html = ""
                    perusim_path = os.path.join(parasha_path, "perusim")
                    if os.path.exists(perusim_path):
                        for commentary_file in os.listdir(perusim_path):
                            if commentary_file.endswith(".md"):
                                file_id = commentary_file.replace(".md", "")
                                commentary_html += f'<div id="{file_id}" class="commentary">{markdown_to_html(read_markdown_file(os.path.join(perusim_path, commentary_file)))}</div><hr>'

                    # Read template
                    with open("templates/parasha.html", "r", encoding="utf-8") as f:
                        page_template = f.read()

                    # Generate final HTML
                    page_html = page_template.format(
                        title=parasha,
                        nav_structure=nav_html,
                        bilingual_content=bilingual_table_html,
                        commentary=commentary_html
                    )

                    with open(os.path.join(OUTPUT_PATH, filename), "w", encoding="utf-8") as f:
                        f.write(page_html)

    # Generate Index Page
    with open("templates/index.html", "r", encoding="utf-8") as f:
        index_template = f.read()

    with open(os.path.join(OUTPUT_PATH, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_template.format(nav_structure=nav_html))

    copy_static_files()  # ✅ Copy CSS & JS
    print("✅ Static site generated.")


