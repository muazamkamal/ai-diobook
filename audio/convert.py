import subprocess
from pathlib import Path
from pydub import AudioSegment
from typing import Optional, List

def convert_wav_to_mp3(wav_path: str, mp3_path: str, bitrate: str = "192k", chunks_json_path: str = "data/chunks.json") -> str:
    """
    Convert a WAV file to MP3 at the specified bitrate, with optional metadata.
    Args:
        wav_path (str): Path to the input WAV file.
        mp3_path (str): Path to the output MP3 file.
        bitrate (str): Bitrate for MP3 (default: 192k).
        chunks_json_path (str): Path to JSON file with metadata
    Returns:
        str: Path to the output MP3 file.
    """
    import json
    title = None
    author = None
    cover_path = None

    if chunks_json_path and Path(chunks_json_path).is_file():
        with open(chunks_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            title = data.get("title", "")
            author = data.get("author", "")
            cover_path = data.get("cover_file", "")

    print(f"[convert] Reading WAV file: {wav_path}")
    audio = AudioSegment.from_wav(wav_path)
    tags = {}
    if title:
        tags["title"] = title
    if author:
        tags["artist"] = author
    print(f"[convert] Exporting to MP3: {mp3_path} (bitrate={bitrate})")
    audio.export(mp3_path, format="mp3", bitrate=bitrate, tags=tags, cover=cover_path if cover_path and Path(cover_path).is_file() else None)
    print(f"[convert] Export complete.")
    return str(Path(mp3_path).resolve())

def write_ffmpeg_chapters(chapters: List[dict], chapter_file: str):
    """
    Write chapters to a ffmpeg-compatible metadata file.
    Args:
        chapters (List[dict]): List of dicts with 'start', 'end', 'title' (start/end in milliseconds)
        chapter_file (str): Path to the output chapter file.
    """
    with open(chapter_file, 'w', encoding='utf-8') as f:
        f.write(';FFMETADATA1\n')
        for i, ch in enumerate(chapters):
            f.write(f'\n[CHAPTER]\nTIMEBASE=1/1000\nSTART={ch["start"]}\nEND={ch["end"]}\ntitle={ch["title"]}\n')

def convert_wav_to_m4b(wav_path: str, m4b_path: str, bitrate: str = "128k", chunks_json_path: str = "data/chunks.json", chapters: Optional[List[dict]] = None) -> str:
    """
    Convert a WAV file to M4B (AAC in MPEG-4 container) using ffmpeg, with optional metadata and chapters.
    Args:
        wav_path (str): Path to the input WAV file.
        m4b_path (str): Path to the output M4B file.
        bitrate (str): Bitrate for M4B (default: 128k).
        chunks_json_path (str): Path to JSON file with metadata
        chapters (Optional[List[dict]]): Optional list of chapters for the M4B file.
    Returns:
        str: Path to the output M4B file.
    """
    import json
    title = None
    author = None
    cover_path = None

    if chunks_json_path and Path(chunks_json_path).is_file():
        with open(chunks_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            title = data.get("title", "")
            author = data.get("author", "")
            cover_path = data.get("cover_file", "")

    print(f"[m4b] Converting {wav_path} to {m4b_path} (bitrate={bitrate})")
    cmd = ["ffmpeg", "-y", "-i", wav_path]
    input_count = 1
    if cover_path and Path(cover_path).is_file():
        cmd += ["-i", cover_path]
        input_count += 1
    chapter_file = None
    if chapters:
        chapter_file = str(Path(m4b_path).with_suffix('.chapters.txt'))
        write_ffmpeg_chapters(chapters, chapter_file)
        cmd += ["-f", "ffmetadata", "-i", chapter_file]
        input_count += 1
    cmd += ["-c:a", "aac", "-b:a", bitrate, "-c:v", "copy", "-f", "mp4"]
    if title:
        cmd += ["-metadata", f"title={title}"]
    if author:
        cmd += ["-metadata", f"artist={author}"]
    if cover_path and Path(cover_path).is_file():
        cmd += ["-map", "0", "-map", "1", "-disposition:v:0", "attached_pic"]
    if chapters:
        # chapter_file is always the last input
        cmd += ["-map_metadata", str(input_count - 1)]
    cmd.append(m4b_path)
    print(f"Running command: \'{str(cmd)}\'")
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print(f"[m4b] ffmpeg error: {result.stderr.decode()}")
        raise RuntimeError("ffmpeg failed to create m4b file")
    if chapter_file and Path(chapter_file).exists():
        Path(chapter_file).unlink() # Clean up
    print(f"[m4b] M4B saved to: {m4b_path}")
    return str(Path(m4b_path).resolve())

def get_chapters_from_chunks_json(chunks_json_path: str) -> List[dict]:
    """
    Read chapter_markers from chunks.json and return ffmpeg-compatible chapters list.
    """
    import json
    chapters = []
    with open(chunks_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        markers = data.get("chapter_markers", {})
        for ch_num, marker in markers.items():
            title = "Introduction" if ch_num == "0" else f"Chapter {ch_num}"
            chapters.append({
                "start": marker["start_ms"],
                "end": marker["end_ms"],
                "title": title
            })
    return chapters

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert WAV to MP3 or M4B with metadata and chapters support")
    parser.add_argument("wav_path", help="Path to input WAV file")
    parser.add_argument("output_path", help="Path to output MP3 or M4B file")
    parser.add_argument("--bitrate", default="192k", help="MP3 bitrate (default: 192k)")
    parser.add_argument("--chunks_json", help="Path to chunks.json (for M4B chapters)")
    args = parser.parse_args()
    if args.output_path.endswith(".mp3"):
        out = convert_wav_to_mp3(args.wav_path, args.output_path, args.bitrate, args.chunks_json)
        print(f"MP3 saved to: {out}")
    elif args.output_path.endswith(".m4b"):
        chapters = None
        if args.chunks_json and Path(args.chunks_json).is_file():
            chapters = get_chapters_from_chunks_json(args.chunks_json)
        out = convert_wav_to_m4b(args.wav_path, args.output_path, args.bitrate, args.chunks_json, chapters)
        print(f"M4B saved to: {out}")
    else:
        print("Unsupported output file type. Please use .mp3 or .m4b extension.")
