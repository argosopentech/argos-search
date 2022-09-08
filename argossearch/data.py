from bs4 import BeautifulSoup

import sys
from pathlib import Path

# python data.py www.argosopentech.com
assert len(sys.argv) == 2

site_path = Path(sys.argv[1])
assert site_path.is_dir()


def extract_query_data_from_html(filepath: Path):
    if filepath.suffix != ".html":
        return None
    with open(filepath) as f:
        file_content = f.read()
        soup = BeautifulSoup(file_content, "html.parser")
        title = soup.title.string
        print(filepath)
        print(title)


def process_dir(dirpath: Path):
    for path in dirpath.iterdir():
        if path.is_dir():
            process_dir(path)
        elif path.is_file():
            extract_query_data_from_html(path)


process_dir(site_path)
