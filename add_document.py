
import argparse
import hashlib
import os
import sqlite3
import datetime
import re

def parse_details_md(file_path):
    """Parses a details.md file and returns a dictionary of metadata."""
    metadata = {}
    current_key = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Regex for key-value pairs like "**Key:** Value"
    key_value_pattern = re.compile(r'\*\*(.+?):\*\*\s*(.*)')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = key_value_pattern.match(line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            current_key = key
            metadata[key] = value
        elif line.startswith('- ') and current_key == 'Tags':
            # Handle list items for Tags
            tag = line[2:].strip()
            # If Tags was previously a string, convert to list
            if 'Tags' in metadata:
                if isinstance(metadata['Tags'], str):
                     metadata['Tags'] = [metadata['Tags'], tag] if metadata['Tags'] else [tag]
                elif isinstance(metadata['Tags'], list):
                    metadata['Tags'].append(tag)
            else:
                metadata['Tags'] = [tag]

    # Convert Tags list to comma-separated string
    if 'Tags' in metadata and isinstance(metadata['Tags'], list):
        metadata['Tags'] = ','.join(metadata['Tags'])
        
    return metadata

def get_document_slug(file_path):
    """Generates the ID based on the directory slug."""
    # The slug is the name of the parent directory
    return os.path.basename(os.path.dirname(os.path.abspath(file_path)))

def update_database(db_path, file_path, metadata):
    """Updates the database with the parsed metadata."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Map metadata keys to database columns
    # DB Schema: id, name, type, files, created_irl_at, language, source, country, tags, uploader, created_at
    
    doc_id = get_document_slug(file_path)
    name = metadata.get('Nombre', '')
    doc_type = metadata.get('Tipo', '').lower()
    if doc_type == 'imagen':
        doc_type = 'image'
    files = metadata.get('Ficheros', '')
    
    # Parse date
    date_str = metadata.get('Fecha', '')
    created_irl_at = 0
    if date_str:
        try:
            dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            created_irl_at = int(dt.timestamp())
        except ValueError:
            print(f"Warning: Invalid date format '{date_str}' in {file_path}")

    language = metadata.get('Idioma', '')
    source = metadata.get('Fuente', '')
    country = metadata.get('País', '')
    tags = metadata.get('Tags', '')
    uploader = metadata.get('Autor', 'Unknown') 
    
    created_at = int(datetime.datetime.now().timestamp())
    
    cursor.execute("SELECT id FROM documents WHERE id = ?", (doc_id,))
    exists = cursor.fetchone()

    if exists:
        sql = """
            UPDATE documents SET
                name = ?,
                type = ?,
                files = ?,
                created_irl_at = ?,
                language = ?,
                source = ?,
                country = ?,
                tags = ?,
                uploader = ?
            WHERE id = ?
        """
        cursor.execute(sql, (name, doc_type, files, created_irl_at, language, source, country, tags, uploader, doc_id))
    else:
        sql = """
            INSERT INTO documents (id, name, type, files, created_irl_at, language, source, country, tags, uploader, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (doc_id, name, doc_type, files, created_irl_at, language, source, country, tags, uploader, created_at))

    conn.commit()
    conn.close()
    print(f"Successfully processed {file_path}")

def main():
    parser = argparse.ArgumentParser(description='Update archivo.db from details.md')
    parser.add_argument('file_path', help='Path to the details.md file')
    parser.add_argument('--db', default='archivo.db', help='Path to the database file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} not found.")
        return

    metadata = parse_details_md(args.file_path)
    # Relative path from project root is better for unique ID generation across machines?
    # Or just use the absolute path provided? 
    # The get_file_hash_id uses the path as is. 
    # If run in CI, the path might be relative. 
    # Github Action will likely pass relative paths or absolute paths. 
    # To be consistent, let's normalize to relative path if possible, or just rely on the input being consistent.
    # The user example path is `./documents/rumasa/details.md`.
    
    try:
        update_database(args.db, args.file_path, metadata)
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == '__main__':
    main()
