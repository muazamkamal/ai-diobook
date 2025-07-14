from ebooklib import epub, ITEM_DOCUMENT, ITEM_NAVIGATION
from bs4 import BeautifulSoup
from pathlib import Path
import sys
import json

def extract_text(epub_path: str, output_json: str = "data/chunks.json", output_txt: str = "data/extracted.txt"):
    try:
        book = epub.read_epub(epub_path)
        all_text = []
        # Extract metadata
        title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "Unknown Title"
        author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown Author"

        # Extract cover
        cover = book.get_item_with_id('cover-image')

        # Extract chapters
        for item in book.get_items_of_type(ITEM_DOCUMENT):
            if 'chapter' in item.get_name():
                soup = BeautifulSoup(item.get_body_content(), "html.parser")
                text = ' '.join(para.get_text() for para in soup.find_all('p'))
                if text:
                    all_text.append(text)

        chapter_count = len(all_text)
        Path("data").mkdir(exist_ok=True)

        # Save metadata to JSON
        chunk_data = {
            "title": title,
            "author": author,
            "chapter_count": chapter_count
        }

        # Save cover to disk, and add to the metadata json
        cover_path = None
        if cover:
            cover_name = "cover.jpg"
            cover_path = Path(f"data/{cover_name}")
            with open(cover_path, "wb") as f:
                f.write(cover.get_content())

            chunk_data["cover_file"] = str(cover_path)
            print(f"Cover saved as {cover_name}")
        else:
            print("Cover image not found")

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)
        # Save extracted lines to txt
        with open(output_txt, "w", encoding="utf-8") as f:
            for line in all_text:
                f.write(line + "\n")
        print(f"[extract/epub] Extracted metadata to {output_json} and text to {output_txt}")
        return output_json, output_txt
    except Exception as e:
        print(f"[extract/epub] Error: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python epub.py path/to/book.epub")
        sys.exit(1)
    epub_path = sys.argv[1]
    extract_text(epub_path)