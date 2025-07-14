from pathlib import Path
from typing import Optional
from extract.epub import extract_text as extract_epub
from extract.pdf import extract_text as extract_pdf
from textchunk.chunker import chunk_text
from tts.generate import generate_audio
from audio.stitch import stitch_audio
from audio.convert import convert_wav_to_mp3, convert_wav_to_m4b

def process_book(
    input_file: str,
    output_file: Optional[str] = None,
    chunk_size: int = 250,
    speaker: str = "Gitta Nikolina",
    language: str = "en",
    model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
    backend: str = "coqui",
    piper_voice: Optional[str] = None,
    piper_exe: str = "piper"
) -> str:
    """
    Process a book file (PDF or EPUB) into an audiobook
    
    Args:
        input_file (str): Path to input book file (PDF or EPUB)
        output_file (str): Path to output WAV file (optional)
        chunk_size (int): Maximum size of text chunks
        speaker (str): Speaker to use for TTS
        language (str): Language for TTS
        model_name (str): Model name for TTS
        backend (str): Backend to use for TTS
        piper_voice (Optional[str]): Path to Piper voice model (if using Piper backend)
        piper_exe (str): Path to Piper executable (if using Piper backend)
        
    Returns:
        str: Path to the output audio file
    """
    try:
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Determine file type and extract text
        if input_path.suffix.lower() == '.pdf':
            text_file = extract_pdf(input_file)
        elif input_path.suffix.lower() == '.epub':
            json_file, text_file = extract_epub(input_file)
        else:
            raise ValueError(f"Unsupported file type: {input_path.suffix}")

        # Chunk the text (each line = chapter)
        chunks_file = chunk_text(text_file, max_chunk_size=chunk_size)
        # Generate audio files
        audio_dir = generate_audio(
            chunks_json=chunks_file,
            output_dir="data/audio",
            speaker=speaker,
            language=language,
            model_name=model_name,
            backend=backend,
            piper_voice=piper_voice,
            piper_exe=piper_exe
        )
        # Set default output file if none provided
        if output_file is None:
            output_file = f"data/{input_path.stem}_audio.wav"
        # Stitch audio files
        final_audio = stitch_audio(audio_dir, output_file)
        # Convert to MP3 after stitching
        mp3_output = str(Path(output_file).with_suffix('.mp3'))
        convert_wav_to_mp3(final_audio, mp3_output, bitrate="192k", chunks_json_path=chunks_file)
        print(f"MP3 saved to: {mp3_output}")
        # Convert to M4B after stitching
        m4b_output = str(Path(output_file).with_suffix('.m4b'))
        convert_wav_to_m4b(final_audio, m4b_output, bitrate="128k", chunks_json_path=chunks_file, chapters=None)
        print(f"M4B saved to: {m4b_output}")
        return final_audio
    except Exception as e:
        print(f"[main] Error: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser(description="Convert a book (PDF/EPUB) to an audiobook.")
    parser.add_argument("input_file", help="Path to input book file (.pdf or .epub)")
    parser.add_argument("output_file", nargs="?", default=None, help="Path to output WAV file")
    parser.add_argument("--chunk_size", type=int, default=250, help="Max chunk size in characters")
    parser.add_argument("--speaker", default="Gitta Nikolina", help="TTS speaker name")
    parser.add_argument("--language", default="en", help="TTS language")
    parser.add_argument("--model_name", default="tts_models/multilingual/multi-dataset/xtts_v2", help="Coqui TTS model name")
    parser.add_argument("--backend", default="coqui", choices=["coqui", "piper"], help="TTS backend")
    parser.add_argument("--piper_voice", default=None, help="Path to Piper voice model (.onnx or .pth)")
    parser.add_argument("--piper_exe", default="piper", help="Path to Piper executable")
    args = parser.parse_args()
    process_book(
        input_file=args.input_file,
        output_file=args.output_file,
        chunk_size=args.chunk_size,
        speaker=args.speaker,
        language=args.language,
        model_name=args.model_name,
        backend=args.backend,
        piper_voice=args.piper_voice,
        piper_exe=args.piper_exe
    )
