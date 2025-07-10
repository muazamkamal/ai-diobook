from pathlib import Path
from PyPDF2 import PdfReader

def extract_text(pdf_path: str, output_txt: str = "data/input.txt"):
    try:
        reader = PdfReader(pdf_path)
        all_text = []

        for page in reader.pages:
            text = page.extract_text().strip()
            if text:  # Only add non-empty text
                all_text.append(text)

        full_text = "\n\n".join(all_text)
        Path("data").mkdir(exist_ok=True)
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(full_text)

        print(f"[extract/pdf] Extracted text to {output_txt}")
        return output_txt
    except Exception as e:
        print(f"[extract/pdf] Error: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf.py path/to/book.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    extract_text(pdf_path)
