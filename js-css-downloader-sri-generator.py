import os
import re
import requests
import hashlib
import shutil
from urllib.parse import urlparse
from pathlib import Path

BASE_DIR = Path('assets')
JS_DIR = BASE_DIR / 'js'
CSS_DIR = BASE_DIR / 'css'

JS_DIR.mkdir(parents=True, exist_ok=True)
CSS_DIR.mkdir(parents=True, exist_ok=True)

html_string = """
    <script src="https://code.jquery.com/jquery-3.7.1.js"></script>
    <script src="https://cdn.datatables.net/2.1.2/js/dataTables.js"></script>
    <script src="https://cdn.datatables.net/2.1.2/js/dataTables.bootstrap5.js"></script>
    <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.1.0/js/dataTables.buttons.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.1.0/js/buttons.flash.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.1.0/js/buttons.html5.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.1.0/js/buttons.print.min.js"></script>
    <script src="https://cdn.datatables.net/searchpanes/2.3.1/js/dataTables.searchPanes.min.js"></script>
    <script src="https://cdn.datatables.net/searchpanes/2.3.1/js/searchPanes.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/responsive/2.2.9/js/dataTables.responsive.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/2.9.2/umd/popper.min.js"></script>
    <script src="https://cdn.datatables.net/select/2.0.3/js/dataTables.select.min.js"></script>

    <link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css">
    <link rel="stylesheet" href="https://cdn.datatables.net/buttons/2.1.0/css/buttons.dataTables.min.css">
    <link rel="stylesheet" href="https://cdn.datatables.net/searchpanes/1.4.0/css/searchPanes.dataTables.min.css">
    <link rel="stylesheet" href="https://cdn.datatables.net/responsive/2.2.9/css/responsive.dataTables.min.css">
    <link href="https://cdn.datatables.net/1.10.24/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet"> 
"""

script_re = re.compile(r'<script\s+src="([^"]+)"></script>', re.IGNORECASE)
link_re = re.compile(r'<link\s+(?:rel="stylesheet"\s+)?href="([^"]+)"(?:\s+rel="stylesheet")?>', re.IGNORECASE)

def calculate_sri_hash(file_path):
    h = hashlib.sha512()
    with open(file_path, 'rb') as f:
        while (chunk := f.read(8192)):
            h.update(chunk)
    return f'sha512-{h.hexdigest()}'

def download_file(url, save_dir):
    if url.startswith(('http://', 'https://')):
        try:
            local_path = os.path.join(save_dir, os.path.basename(urlparse(url).path))
            response = requests.get(url)
            response.raise_for_status()
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return local_path, calculate_sri_hash(local_path)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None, None
    else:
        # Handle local file paths
        src_path = Path(url).resolve()
        if src_path.exists():
            dest_path = BASE_DIR / src_path.relative_to(Path.cwd())
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_path, dest_path)
            return str(dest_path), calculate_sri_hash(dest_path)
        else:
            print(f"Local file not found: {url}")
            return None, None

def process_html(html):
    def replace_script_tag(m):
        url = m.group(1)
        path, sri_hash = download_file(url, JS_DIR)
        if path:
            return f'<script src="assets\{os.path.relpath(path, BASE_DIR)}" integrity="{sri_hash}" crossorigin="anonymous"></script>'
        return m.group(0)
    
    def replace_link_tag(m):
        url = m.group(1)
        path, sri_hash = download_file(url, CSS_DIR)
        if path:
            return f'<link rel="stylesheet" href="assets\{os.path.relpath(path, BASE_DIR)}" integrity="{sri_hash}" crossorigin="anonymous">'
        return m.group(0)

    html = script_re.sub(replace_script_tag, html)
    html = link_re.sub(replace_link_tag, html)
    return html

print(process_html(html_string))
