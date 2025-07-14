from pathlib import Path
from pydub import AudioSegment
import glob
import json

def stitch_audio(
    input_dir: str = "data/audio",
    output_file: str = "data/output.wav",
    fade_duration: int = 100,  # milliseconds
    chunks_json: str = "data/chunks.json"
) -> str:
    """
    Stitch title, author, chapter count, chapter announcements, and chunk WAV files together with crossfading
    
    Args:
        input_dir (str): Directory containing WAV files
        output_file (str): Path to output WAV file
        fade_duration (int): Duration of crossfade in milliseconds
        chunks_json (str): Path to JSON file with chapter metadata
        
    Returns:
        str: Path to the output file
    """
    try:
        # Load metadata
        with open(chunks_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chapter_count = data.get("chapter_count", 0)

        # Prepare list of files in order
        files_to_stitch = []
        # Prepare a short silence segment (e.g., 1000ms)
        pause = AudioSegment.silent(duration=1000)
        # Add title, author, chapter count (no pauses between them)
        for meta in ["title", "author", "chapter_count"]:
            meta_file = Path(input_dir) / f"{meta}.wav"
            if meta_file.exists():
                files_to_stitch.append(str(meta_file))
        # For each chapter: add chapter announcement, then its chunks, with pause before each chapter
        for chapter_num in range(1, chapter_count + 1):
            chapter_announce = Path(input_dir) / f"chapter_{chapter_num}.wav"
            if chapter_announce.exists():
                files_to_stitch.append("__PAUSE__")
                files_to_stitch.append(str(chapter_announce))
                files_to_stitch.append("__PAUSE__")  # Add pause after chapter announcement
            # Add all chunks for this chapter, in order
            chapter_chunks = sorted(glob.glob(str(Path(input_dir) / f"chunk_{chapter_num:02d}_*.wav")))
            files_to_stitch.extend(chapter_chunks)
        # Remove trailing pause if present
        while files_to_stitch and files_to_stitch[-1] == "__PAUSE__":
            files_to_stitch.pop()

        if not files_to_stitch:
            raise ValueError(f"No audio files found to stitch in {input_dir}")

        # Load first file
        if files_to_stitch[0] == "__PAUSE__":
            combined = pause
            start_idx = 1
        else:
            combined = AudioSegment.from_wav(files_to_stitch[0])
            start_idx = 1
        print(f"[audio] Processing {len(files_to_stitch)} files...")

        # Track chapter start/end times in ms
        chapter_markers = {}
        current_ms = 0
        chapter_idx = 0 # Chapter 0 is intro
        last_chapter_idx = None

        # If the first audio is a chapter announcement, then skip chapter marker 0/intro
        if "chapter_1.wav" in files_to_stitch[0]:
            chapter_idx = 1

        chapter_markers[str(chapter_idx)] = {"start_ms": current_ms}

        # Add subsequent files with crossfading or pause
        for idx, wav_file in enumerate(files_to_stitch[start_idx:]):
            # Check if processing next chapter, then mark current chapter end and increment the chapter id and mark start time
            if (f"chapter_{chapter_idx + 1}.wav" in wav_file):
                chapter_markers[str(chapter_idx)]["end_ms"] = max(current_ms - len(pause), 0)
                chapter_idx += 1
                chapter_markers[str(chapter_idx)] = { "start_ms": max(current_ms - len(pause), 0)}

            if wav_file == "__PAUSE__":
                combined = combined.append(pause, crossfade=0)
            else:
                next_segment = AudioSegment.from_wav(wav_file)
                combined = combined.append(next_segment, crossfade=fade_duration)

            current_ms = len(combined)

            # If the file processed was the last file, mark end for the chapter
            if idx+2 == len(files_to_stitch) and str(chapter_idx) in chapter_markers:
                chapter_markers[str(chapter_idx)]["end_ms"] = current_ms

        # Create output directory if needed
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        # Export final audio
        combined.export(output_file, format="wav")
        print(f"[audio] Exported stitched audio to {output_file}")

        # Save chapter markers to chunks.json
        with open(chunks_json, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data["chapter_markers"] = chapter_markers
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        return output_file

    except Exception as e:
        print(f"[audio] Error: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stitch audiobook WAV files with chapter markers.")
    parser.add_argument("--input_dir", default="data/audio", help="Directory containing WAV files")
    parser.add_argument("--output_file", default="data/output.wav", help="Path to output WAV file")
    parser.add_argument("--fade_duration", type=int, default=100, help="Crossfade duration in ms")
    parser.add_argument("--chunks_json", default="data/chunks.json", help="Path to chunks.json")
    args = parser.parse_args()
    stitch_audio(
        input_dir=args.input_dir,
        output_file=args.output_file,
        fade_duration=args.fade_duration,
        chunks_json=args.chunks_json
    )
