import os
import shutil
from utils.file_utils import read_markdown_file, markdown_to_html, remove_cssclasses
from config import VAULT_PATH, OUTPUT_PATH
import re
import unicodedata
import json
from collections import OrderedDict

SEFARIA_BOOK_MAP = {
    "1 Berésit": "Genesis",
    "2 Smot": "Exodus",
    "3 Vájikrá": "Leviticus",
    "4 Bámidbár": "Numbers",
    "5 Devárim": "Deuteronomy"
}

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

def extract_chapter_verse_en(line, current_chapter, current_verse):
    """Extracts chapter and verse numbers from a line in HU.md"""
    chapter_match = re.match(r"# Chapter (\d+)", line)
    verse_match = re.match(r"\*\*(\d+)\.\*\*", line)

    if chapter_match:
        return int(chapter_match.group(1)), 0  # Reset verse when chapter changes
    elif verse_match:
        return current_chapter, int(verse_match.group(1))
    
    return current_chapter, current_verse  # Keep last known values

def extract_chapter_verse_hu(line, current_chapter, current_verse):
    """Extracts chapter and verse numbers from a line in HU.md"""
    chapter_match = re.match(r"# (\d+)\. fejezet", line)
    verse_match = re.match(r"\*\*(\d+)\.\*\*", line)

    if chapter_match:
        return int(chapter_match.group(1)), 0  # Reset verse when chapter changes
    elif verse_match:
        return current_chapter, int(verse_match.group(1))
    
    return current_chapter, current_verse  # Keep last known values

def generate_bilingual_html(lang1, lang2, output_subdir=""):
    """Generate bilingual HTML pages for two languages and save them under the specified subdirectory."""
    out_path = os.path.join(OUTPUT_PATH, output_subdir)
    os.makedirs(out_path, exist_ok=True)

    nav_html = generate_nav_structure()

    for book in sorted(os.listdir(VAULT_PATH)):
        if book.startswith("."):
            continue

        book_path = os.path.join(VAULT_PATH, book)
        if not os.path.isdir(book_path):
            continue

        for parasha in sorted(os.listdir(book_path)):
            if parasha.startswith("."):
                continue

            parasha_path = os.path.join(book_path, parasha)
            if not os.path.isdir(parasha_path):
                continue

            file1 = os.path.join(parasha_path, f"{lang1}.md")
            file2 = os.path.join(parasha_path, f"{lang2}.md")
            if not (os.path.exists(file1) and os.path.exists(file2)):
                continue

            lang1_lines = remove_cssclasses(read_markdown_file(file1)).split("\n")
            lang2_lines = remove_cssclasses(read_markdown_file(file2)).split("\n")

            filename = remove_accents(parasha) + ".html"
            table_rows = ""
            chapter = verse = 0
            commentaries = OrderedDict()
            
            for l1_line, l2_line in zip(lang1_lines, lang2_lines):
                if lang2 == "HU":
                    chapter, verse = extract_chapter_verse_hu(l2_line, chapter, verse)

                if lang2 == "EN":
                    chapter, verse = extract_chapter_verse_en(l2_line, chapter, verse)

                l1_html = markdown_to_html(l1_line.strip()) if l1_line.strip() else "&nbsp;"
                l2_html = markdown_to_html(l2_line.strip()) if l2_line.strip() else "&nbsp;"

                current_verse = verse  # Save a local verse counter

                # Define a replacement function that updates the verse each time
                def replace_strong_with_link(match):
                    nonlocal current_verse
                    verse_id = f"ch{chapter}-vrs{current_verse}"
                    text_inside = match.group(1)
                    sefaria_book = SEFARIA_BOOK_MAP.get(book, None)
                    if sefaria_book:
                        #sefaria_link = f"https://www.sefaria.org/{sefaria_book}.{chapter}.{current_verse}?lang=bi&with=all&lang2=en"
                        result = (
                            f"<a id='{verse_id}' href='#{verse_id}' onclick=\"showSefariaLink({chapter}, {current_verse}, '{sefaria_book}')\">"
                            f"<strong>{text_inside}</strong></a>"
                        )
                    else:
                        result=f"<a id='{verse_id}' href='#{verse_id}'\"><strong>{text_inside}</strong></a>"
                    current_verse += 1  # Increment after each replacement
                    return result

                # Apply replacement for l1 and l2
                l1_html = re.sub(r"<strong>\{(.*?)\}</strong>", replace_strong_with_link, l1_html)
                l2_html = re.sub(r"<strong>\{(.*?)\}</strong>", replace_strong_with_link, l2_html)

                # Commentary links should be collected from lang2 (e.g., HU or EN)
                for match in re.findall(r"highlightCommentary\('([^\']+)'\)", l2_html):
                    if match not in commentaries:
                        comment_path = os.path.join(parasha_path, "perusim", f"{match}.md")
                        if os.path.exists(comment_path):
                            comment_text = markdown_to_html(read_markdown_file(comment_path))
                            prefix = f"<a href='#ch{chapter}-vrs{current_verse}'><strong>{chapter}:{current_verse}</strong></a> "
                            commentaries[match] = prefix + comment_text

                table_rows += f"<tr><td class='{lang1.lower()}'>{l1_html}</td><td class='{lang2.lower()} chapter-heading'>{l2_html}</td></tr>\n"

            bilingual_table_html = f"""
            <table class="bilingual-table">
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            """

            commentary_html = "".join(
                f'<div id="{cid}" class="commentary">{text}</div><hr>' for cid, text in commentaries.items()
            )

            with open("templates/parasha.html", "r", encoding="utf-8") as f:
                page_template = f.read()

            page_html = page_template.format(
                title=parasha,
                nav_structure=nav_html,
                bilingual_content=bilingual_table_html,
                commentary=commentary_html
            )

            with open(os.path.join(out_path, filename), "w", encoding="utf-8") as f:
                f.write(page_html)

    # Index page
    with open("templates/index.html", "r", encoding="utf-8") as f:
        index_template = f.read()
    with open(os.path.join(out_path, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_template.format(nav_structure=nav_html))


def generate_html():
    """Generate Hebrew-English (root) and Hebrew-Hungarian (hu/) HTML sites."""
    if os.path.exists(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)

    generate_bilingual_html("HE", "EN", "")
    generate_bilingual_html("HE", "HU", "hu")
    copy_static_files()
    print("✅ Bilingual sites generated.")



