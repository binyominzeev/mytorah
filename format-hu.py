import requests
import re
from bs4 import BeautifulSoup

def get_exodus_chapter(chapter):
    url = f"https://www.sefaria.org/api/texts/Exodus.{chapter}?context=0"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("he", [])  # Fetch Hebrew text
    else:
        raise Exception(f"Failed to retrieve data from Sefaria API for Exodus {chapter}")

def clean_text(text):
    """Remove HTML tags and special characters from the text."""
    return BeautifulSoup(text, "html.parser").get_text()

def find_line_break_verses():
    break_verses = []
    
    for chapter in range(27, 31):  # Chapters 27-30
        verses = get_exodus_chapter(chapter)
        for i, verse in enumerate(verses, start=1):
            clean_verse = clean_text(verse)
            if re.search(r'[{][פס][}]', clean_verse):  # Check if verse contains {פ} or {ס} explicitly
                break_verses.append((chapter, i + 1))  # Shift paragraph break one verse later
    
    return break_verses

def process_hu_text(input_file, output_file, break_verses):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    processed_lines = []
    current_chapter = None
    paragraph = []
    
    for line in lines:
        line = line.strip()
        
        # Detect chapter headings
        chapter_match = re.match(r"(\d+)\. fejezet", line)
        if chapter_match:
            if paragraph:
                processed_lines.append(" ".join(paragraph) + "\n\n")  # Join verse lines in a paragraph
                paragraph = []
            current_chapter = int(chapter_match.group(1))
            processed_lines.append(f"# {line}\n\n")  # Add Markdown heading symbol
            continue
        
        # Skip section titles (lines with only uppercase or empty lines)
        if line.isupper() or line == "":
            continue
        
        # Detect verses
        verse_match = re.match(r"(\d+)\. (.+)", line)
        if verse_match and current_chapter:
            verse_number = int(verse_match.group(1))
            verse_text = verse_match.group(2)
            
            if (current_chapter, verse_number) in break_verses:
                if paragraph:
                    processed_lines.append(" ".join(paragraph) + "\n\n")  # Join verse lines in a paragraph
                    paragraph = []
            
            paragraph.append(f"**{verse_number}.** {verse_text}")
    
    if paragraph:
        processed_lines.append(" ".join(paragraph) + "\n\n")  # Final paragraph
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(processed_lines)

if __name__ == "__main__":
    results = find_line_break_verses()
    process_hu_text("hu.txt", "hu-2.txt", results)
    print("Processing complete. Output saved to hu-2.txt.")
