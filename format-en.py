import requests
import os
import re

# Map Parasha to its Torah portion (you can expand this dictionary)
PARASHA_TO_REF = {
    "Yitro": "Exodus 18-20",
    "Naso": "Numbers 4:21-7:89",
    "Slach": "Numbers 25-30",
    # Add more as needed
}

OUTPUT_DIR = "."

def clean_text(raw):
    """Remove HTML tags and footnote markers from Sefaria text."""
    raw = re.sub(r'<i class="footnote">.*?</i>', '', raw, flags=re.DOTALL)
    # Remove any other HTML tags
    raw = re.sub(r'<[^>]+>', '', raw)
    # Remove stray symbols like asterisks
    raw = re.sub(r"[*]", "", raw)
    raw = re.sub(r"יהוה", "Hashem", raw)
    return raw.strip()

def format_verse(chapter, verse_num, text):
    cleaned = clean_text(text)
    return f"**{verse_num}.** {cleaned}"

def download_parasha_english(parasha_name):
    ref = PARASHA_TO_REF.get(parasha_name)
    if not ref:
        print(f"⚠️ No Sefaria reference found for parasha '{parasha_name}'")
        return

    url = f"https://www.sefaria.org/api/texts/{ref}?lang=en&commentary=0&context=0&vside=0&version=The_Contemporary_Torah,_Jewish_Publication_Society,_2006"
    response = requests.get(url)

    if not response.ok:
        print(f"❌ Failed to fetch text for {ref}")
        return

    data = response.json()

    # Sefaria may return a list of chapters, or one chapter
    text_data = data.get("text", [])
    if not isinstance(text_data[0], list):  # If it's a flat list (single chapter)
        text_data = [text_data]

    output = ""
    start_chapter = int(re.search(r"(\d+)", ref).group(1))

    for i, chapter in enumerate(text_data):
        chapter_num = start_chapter + i
        output += f"# Chapter {chapter_num}\n"
        for verse_num, verse in enumerate(chapter, start=1):
            output += format_verse(chapter_num, verse_num, verse)+" "
        output += "\n"

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(OUTPUT_DIR, f"{parasha_name}_EN.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output.strip())

    print(f"✅ English translation for '{parasha_name}' saved to {filename}")

# Example usage:
download_parasha_english("Slach")

