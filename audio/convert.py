from pydub import AudioSegment
from pathlib import Path

def convert_wav_to_mp3(wav_path: str, mp3_path: str, bitrate: str = "192k") -> str:
    """
    Convert a WAV file to MP3 at the specified bitrate.
    Args:
        wav_path (str): Path to the input WAV file.
        mp3_path (str): Path to the output MP3 file.
        bitrate (str): Bitrate for MP3 (default: 192k).
    Returns:
        str: Path to the output MP3 file.
    """
    print(f"[convert] Reading WAV file: {wav_path}")
    audio = AudioSegment.from_wav(wav_path)
    print(f"[convert] Exporting to MP3: {mp3_path} (bitrate={bitrate})")
    audio.export(mp3_path, format="mp3", bitrate=bitrate)
    print(f"[convert] Export complete.")
    return str(Path(mp3_path).resolve())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert WAV to MP3 at high quality (192k)")
    parser.add_argument("wav_path", help="Path to input WAV file")
    parser.add_argument("mp3_path", help="Path to output MP3 file")
    parser.add_argument("--bitrate", default="192k", help="MP3 bitrate (default: 192k)")
    args = parser.parse_args()
    out = convert_wav_to_mp3(args.wav_path, args.mp3_path, args.bitrate)
    print(f"MP3 saved to: {out}")
