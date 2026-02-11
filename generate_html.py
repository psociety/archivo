import sqlite3
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os

# Ensure output directory exists
os.makedirs("output", exist_ok=True)

# Check override flag
OVERRIDE_ALL = os.getenv("OVERRIDE_ALL")

# Connect and return rows as dict-like objects
conn = sqlite3.connect("archivo.db")
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT * FROM documents").fetchall()

# Create a Jinja2 environment (loads templates from current directory)
env = Environment(loader=FileSystemLoader("."))

# Custom filter to format timestamps
def format_date(value, fmt="%Y-%m-%d"):
    return datetime.fromtimestamp(value).strftime(fmt)

env.filters["format_date"] = format_date

# Load your template
template = env.get_template("templates/document.html")

# Render one HTML file per row
for doc in rows:
    output_path = f"output/document/{doc['id']}.html"

    # Skip if file exists and OVERRIDE_ALL is not set
    if not OVERRIDE_ALL and os.path.exists(output_path):
        print(f"Skipping {output_path} (already exists)")
        continue

    html = template.render(document=doc)

    with open(output_path, "w") as f:
        f.write(html)

    print(f"Rendered {output_path}")
