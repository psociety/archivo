import sqlite3
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os

class SiteGenerator:
    def __init__(self, db_path="archivo.db", output_dir="output"):
        self.db_path = db_path
        self.output_dir = output_dir
        self.override_all = os.getenv("OVERRIDE_ALL")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup Jinja2 environment
        self.env = Environment(loader=FileSystemLoader("."))
        self.env.filters["format_date"] = self.format_date

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def format_date(value, fmt="%Y-%m-%d"):
        if not value: return ""
        try:
            # Check if value is timestamp (int/float)
            if isinstance(value, (int, float)):
                 return datetime.fromtimestamp(value).strftime(fmt)
            return str(value)
        except:
            return str(value)

    def generate_documents(self):
        print("Generating documents...")
        conn = self.get_connection()
        try:
            rows = conn.execute("SELECT * FROM documents").fetchall()
        finally:
            conn.close()

        template = self.env.get_template("templates/document.html")
        
        doc_dir = os.path.join(self.output_dir, "document")
        os.makedirs(doc_dir, exist_ok=True)

        for doc in rows:
            output_path = os.path.join(doc_dir, f"{doc['id']}.html")

            # Skip if file exists and OVERRIDE_ALL is not set
            if not self.override_all and os.path.exists(output_path):
                # print(f"Skipping {output_path} (already exists)")
                continue

            html = template.render(document=doc)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"Rendered {output_path}")

    def generate_index(self):
        print("Generating index...")
        conn = self.get_connection()
        try:
            # Get latest 10 documents
            rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC LIMIT 10").fetchall()
        finally:
            conn.close()

        template = self.env.get_template("templates/index.html")
        html = template.render(documents=rows)

        output_path = os.path.join(self.output_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Rendered {output_path}")

    def run(self):
        self.generate_documents()
        self.generate_index()

if __name__ == "__main__":
    generator = SiteGenerator()
    generator.run()
