import json
from pathlib import Path
from typing import List, Dict

def chunk_text(input_txt: str = "data/extracted.txt", output_json: str = "data/chunks.json", max_chunk_size: int = 250) -> str:
    """
    Each line in the input file is a chapter. Each chapter is chunked into max_chunk_size chunks.
    """
    try:
        # Read input text, each line is a chapter
        with open(input_txt, 'r', encoding='utf-8') as f:
            chapter_lines = [line.strip() for line in f if line.strip()]

        chunks_by_chapter = {}
        for idx, chapter_text in enumerate(chapter_lines, 1):
            # Split chapter into sentences
            sentences = []
            for line in chapter_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                parts = line.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|')
                for part in parts:
                    if part:
                        sentences.append(part.strip())
            # Create chunks for this chapter
            chapter_chunks = []
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                    chapter_chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    if current_chunk:
                        current_chunk += " "
                    current_chunk += sentence
            if current_chunk:
                chapter_chunks.append(current_chunk.strip())
            chunks_by_chapter[str(idx)] = chapter_chunks

        # Load existing JSON and update chunks
        if Path(output_json).exists():
            with open(output_json, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
            chunk_data['chunks'] = chunks_by_chapter
        else:
            chunk_data = {"chunks": chunks_by_chapter}
        Path("data").mkdir(exist_ok=True)
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)

        print(f"[chunk] Created chunks for {len(chunks_by_chapter)} chapters in {output_json}")
        return output_json

    except Exception as e:
        print(f"[chunk] Error: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        chunk_text(input_txt=sys.argv[1])
    else:
        chunk_text()
