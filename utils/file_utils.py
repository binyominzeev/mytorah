import os
import markdown
import re

def read_markdown_file(filepath):
    """Reads a Markdown file and converts it to HTML"""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def remove_cssclasses(md_text):
    md_text = re.sub(r"---\n.*?\n---\n", "", md_text, flags=re.DOTALL)
    return md_text

import markdown
import re

def markdown_to_html(md_text):
    """Convert Markdown text to HTML and handle both types of Obsidian-style links."""

    def replace_link(match):
        """Convert Markdown links to JavaScript-highlighted commentary links."""
        label, file = match.groups()
        file_id = file.replace(".md", "")
        return f'<a href="javascript:void(0);" onclick="highlightCommentary(\'{file_id}\')">{label}</a>'

    # Handle both styles of Obsidian links:
    # [[link|caption]]  → <a href="#link">caption</a>
    # [[link which is a caption]] → <a href="#link-which-is-a-caption">link which is a caption</a>

    # First, process links with captions: [[id|display text]]
    md_text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', 
                     lambda m: f'<a href="#{m.group(1)}" class="commentary-link" onclick="highlightCommentary(\'{m.group(1)}\')">{m.group(2)}</a>', 
                     md_text)

    # Now, process links without captions: [[some text]] → <a href="#some-text">some text</a>
    md_text = re.sub(r'\[\[([^\]]+)\]\]', 
                     lambda m: f'<a href="#{m.group(1).replace(" ", "-")}" class="commentary-link" onclick="highlightCommentary(\'{m.group(1)}\')">{m.group(1)}</a>', 
                     md_text)

    # Ensure single line breaks create new paragraphs
    md_text = md_text.replace("\n", "  \n\n")  # Add Markdown line break notation

    # Convert Markdown to HTML
    md_html = markdown.markdown(md_text)

    # Replace standard Markdown links with JavaScript-highlighted commentary links
    md_html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, md_html)

    return md_html

