import json
from pathlib import Path
import torch
from tqdm import tqdm
import subprocess
from typing import Optional

class TTSBackend:
    def __init__(self, backend: str = "coqui", model_name: Optional[str] = None, device: Optional[str] = None, speaker: Optional[str] = None, piper_voice: Optional[str] = None, piper_exe: str = "piper", reference_audio: str = "data/reference.wav"):
        self.backend = backend
        self.model_name = model_name
        self.device = device
        self.speaker = speaker
        self.piper_voice = piper_voice
        self.piper_exe = piper_exe
        self.reference_audio = reference_audio
        if backend == "coqui":
            from TTS.api import TTS
            self.tts = TTS(model_name).to(device)
        elif backend == "piper":
            if not piper_voice:
                raise ValueError("piper_voice must be specified for Piper backend")
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def tts_to_file(self, text: str, file_path: str, language: Optional[str] = None):
        if self.backend == "coqui":
            kwargs = dict(text=text, language=language, file_path=file_path)
            # Only use speaker_wav if reference_audio is set and file exists
            if self.reference_audio and Path(self.reference_audio).is_file():
                kwargs["speaker_wav"] = self.reference_audio
            else:
                kwargs["speaker"] = self.speaker

            self.tts.tts_to_file(**kwargs)
        elif self.backend == "piper":
            # Piper CLI expects: echo "text" | piper --model <voice> --output_file <file>
            cmd = [self.piper_exe, "--model", self.piper_voice, "--output_file", file_path]
            proc = subprocess.run(cmd, input=text, text=True, capture_output=True)
            if proc.returncode != 0:
                print(f"[piper] Error: {proc.stderr}")
                raise RuntimeError(f"Piper failed: {proc.stderr}")
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

def generate_audio(
    chunks_json: str = "data/chunks.json",
    output_dir: str = "data/audio",
    speaker: str = "Gitta Nikolina",
    language: str = "en",
    model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
    backend: str = "coqui",
    piper_voice: Optional[str] = None,
    piper_exe: str = "piper",
    reference_audio: str = "data/reference.wav"
) -> str:
    """
    Generate audio files from text chunks using Coqui TTS or Piper TTS
    
    Args:
        chunks_json (str): Path to JSON file containing text chunks
        output_dir (str): Directory to save audio files
        speaker (str): Speaker to use for TTS
        language (str): Language to use for TTS
        model_name (str): Model name to use for TTS
        backend (str): TTS backend to use ("coqui" or "piper")
        piper_voice (Optional[str]): Path to Piper voice model (.onnx or .pth)
        piper_exe (str): Path to Piper executable
        reference_audio (Optional[str]): Path to reference audio for voice cloning defaits (`data/reference.wav`)
        
    Returns:
        str: Path to the output directory containing generated audio files
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    with open(chunks_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        chunks_by_chapter = data["chunks"]
        title = data.get("title", "")
        author = data.get("author", "")
        chapter_count = data.get("chapter_count", None)
    tts_backend = TTSBackend(
        backend=backend,
        model_name=model_name,
        device=device,
        speaker=speaker,
        piper_voice=piper_voice,
        piper_exe=piper_exe,
        reference_audio=reference_audio
    )
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate title audio
    title_file = output_path / "title.wav"
    if title and not title_file.exists():
        tts_backend.tts_to_file(text=f"Title: {title}", file_path=str(title_file), language=language)
        print(f"[tts] Generated {title_file}")
    # Generate author audio
    author_file = output_path / "author.wav"
    if author and not author_file.exists():
        tts_backend.tts_to_file(text=f"Author: {author}", file_path=str(author_file), language=language)
        print(f"[tts] Generated {author_file}")
    # Generate chapter count audio
    if chapter_count is not None:
        chapter_count_file = output_path / "chapter_count.wav"
        if not chapter_count_file.exists():
            tts_backend.tts_to_file(text=f"Total chapters: {chapter_count}", file_path=str(chapter_count_file), language=language)
            print(f"[tts] Generated {chapter_count_file}")
        # Generate 'Chapter X' audios
        for i in range(1, chapter_count + 1):
            chapter_file = output_path / f"chapter_{i}.wav"
            if not chapter_file.exists():
                tts_backend.tts_to_file(text=f"Chapter {i}", file_path=str(chapter_file), language=language)
                print(f"[tts] Generated {chapter_file}")

    # Generate audio for each chunk in each chapter
    for chapter_str, chunk_list in tqdm(chunks_by_chapter.items(), desc="Chapters"):
        chapter_num = int(chapter_str)
        for chunk_idx, chunk in enumerate(chunk_list):
            output_file = output_path / f"chunk_{chapter_num:02d}_{chunk_idx:04d}.wav"
            if output_file.exists():
                print(f"[tts] Skipping existing file: {output_file}")
                continue
            tts_backend.tts_to_file(text=chunk, file_path=str(output_file), language=language)
            print(f"[tts] Generated {output_file}")

    return str(output_path)

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser(description="Generate audiobook audio using TTS.")
    parser.add_argument("--chunks_json", default="data/chunks.json")
    parser.add_argument("--output_dir", default="data/audio")
    parser.add_argument("--speaker", default="Gitta Nikolina")
    parser.add_argument("--language", default="en")
    parser.add_argument("--model_name", default="tts_models/multilingual/multi-dataset/xtts_v2")
    parser.add_argument("--backend", default="coqui", choices=["coqui", "piper"])
    parser.add_argument("--piper_voice", default="data/models/en_US-hfc_female-medium.onnx", help="Path to Piper voice model (.onnx or .pth)")
    parser.add_argument("--piper_exe", default="piper", help="Path to Piper executable")
    parser.add_argument("--reference_audio", default="data/reference.wav", help="Path to reference audio for voice cloning (Coqui only)")
    args = parser.parse_args()
    generate_audio(
        chunks_json=args.chunks_json,
        output_dir=args.output_dir,
        speaker=args.speaker,
        language=args.language,
        model_name=args.model_name,
        backend=args.backend,
        piper_voice=args.piper_voice,
        piper_exe=args.piper_exe,
        reference_audio=args.reference_audio
    )
