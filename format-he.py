import re

# Define replacements
maqaf = "־"  # Hebrew maqqaf

# Read input file
with open("he.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Replace simple dashes with maqqaf
text = text.replace("-", maqaf)

# Replace paragraph signs with line breaks
text = text.replace("(ס)", "\n").replace("(פ)", "\n")

# Bold the pasuk numbers using **bold** notation
text = re.sub(r"\{(.*?)\}", lambda m: "**{" + m.group(1) + "}**", text)

# Replace "שמות פרק-<number>" or "שמות פרק <number>" with a header
text = re.sub(r"(.*?) פרק[\־ ](\S+)", r"# \2", text)

# Remove leading spaces from each line
text = "\n".join(line.lstrip() for line in text.splitlines())

# Save to output file
with open("he-2.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("Formatting completed and saved to he-2.txt")

