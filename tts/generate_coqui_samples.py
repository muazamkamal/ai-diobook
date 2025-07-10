import os
import torch
from TTS.api import TTS
from pathlib import Path
import re

# List of Coqui speakers
SPEAKERS = [
    'Aaron Dreschner',
    'Abrahan Mack',
    'Adde Michal',
    'Alexandra Hisakawa',
    'Alison Dietlinde',
    'Alma María',
    'Ana Florence',
    'Andrew Chipper',
    'Annmarie Nele',
    'Asya Anara',
    'Badr Odhiambo',
    'Baldur Sanjin',
    'Barbora MacLean',
    'Brenda Stern',
    'Camilla Holmström',
    'Chandra MacFarland',
    'Claribel Dervla',
    'Craig Gutsy',
    'Daisy Studious',
    'Damien Black',
    'Damjan Chapman',
    'Dionisio Schuyler',
    'Eugenio Mataracı',
    'Ferran Simen',
    'Filip Traverse',
    'Gilberto Mathias',
    'Gitta Nikolina',
    'Gracie Wise',
    'Henriette Usha',
    'Ige Behringer',
    'Ilkin Urbano',
    'Kazuhiko Atallah',
    'Kumar Dahl',
    'Lidiya Szekeres',
    'Lilya Stainthorpe',
    'Ludvig Milivoj',
    'Luis Moray',
    'Maja Ruoho',
    'Marcos Rudaski'
    'Narelle Moon',
    'Nova Hogarth',
    'Rosemary Okafor',
    'Royston Min',
    'Sofia Hellen',
    'Suad Qasim',
    'Szofi Granger',
    'Tammie Ema',
    'Tammy Grit',
    'Tanja Adelina',
    'Torcull Diarmuid',
    'Uta Obando',
    'Viktor Eka',
    'Viktor Menelaos',
    'Vjollca Johnnie',
    'Wulf Carlevaro',
    'Xavier Hayasaka',
    'Zacharie Aimilios',
    'Zofija Kendrick',
]

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
SAMPLES_DIR = Path("samples")
SAMPLES_DIR.mkdir(exist_ok=True)

def safe_filename(name):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS(MODEL_NAME).to(device)
    for speaker in SPEAKERS:
        filename = SAMPLES_DIR / f"{safe_filename(speaker)}.wav"
        if filename.exists():
            print(f"[skip] {filename} exists")
            continue
        text = f"This is a sample of {speaker}. A few years back I was running out of money so I volunteered for a research study at the University of Pennsylvania. The directions brought me to the campus medical center in West Philly and a large auditorium filled with women, all between eighteen and thirty-five years old. There weren’t enough chairs and I was among the last to arrive so I had to sit shivering on the floor."
        try:
            tts.tts_to_file(text=text, speaker=speaker, language="en", file_path=str(filename))
            print(f"[ok] Generated {filename}")
        except Exception as e:
            print(f"[error] Failed for {speaker}: {e}")

if __name__ == "__main__":
    main()
