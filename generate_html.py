import sqlite3
from jinja2 import Template
import os

# Ensure output directory exists
os.makedirs("output", exist_ok=True)

# Connect and return rows as dict-like objects
conn = sqlite3.connect("archivo.db")
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT * FROM documents").fetchall()

# Load your template
with open("template.html") as f:
    template = Template(f.read())

# Render one HTML file per row
for doc in rows:
    html = template.render(document=doc)
    output_path = f"output/{doc['id']}.html"
    with open(output_path, "w") as f:
        f.write(html)
