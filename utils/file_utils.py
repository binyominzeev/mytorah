import os
import markdown
import re

def read_markdown_file(filepath):
    """Reads a Markdown file and converts it to HTML"""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def markdown_to_html(md_text):
    """Convert Markdown text to HTML and handle commentary links"""
    def replace_link(match):
        label, file = match.groups()
        file_id = file.replace(".md", "")
        return f'<a href="javascript:void(0);" onclick="highlightCommentary(\'{file_id}\')">{label}</a>'
    
    md_html = markdown.markdown(md_text)
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, md_html)

