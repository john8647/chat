import os
import subprocess
from pathlib import Path


def fix_metadata_file(csv_path=r"G:/text ts/metadata.csv"):
    path = Path(csv_path)

    if not path.exists():
        print(f"File not found: {csv_path}")
        return

    corrected_lines = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "|" not in line:
                continue

            # Split into text and filename (current wrong order)
            left, right = line.split("|", 1)

            # Trim whitespace
            left = left.strip()
            right = right.strip()

            # Detect which part is the filename
            # If left ends with .wav, it's already correct
            if left.lower().endswith(".wav"):
                corrected_lines.append(f"{left}|{right}")
            else:
                # Swap order: filename.wav|text
                corrected_lines.append(f"{right}|{left}")

    # Write corrected file
    with path.open("w", encoding="utf-8") as f:
        for line in corrected_lines:
            f.write(line + "\n")

    print("metadata.csv corrected successfully.")


def convert_flac_to_wav_and_cleanup(
    input_folder=r"G:/text ts/audio_data/audio",
    target_rate=16000  # or 22050
):
    input_path = Path(input_folder)

    if not input_path.exists():
        print(f"Folder not found: {input_folder}")
        return

    flac_files = list(input_path.glob("*.flac"))

    if not flac_files:
        print("No FLAC files found.")
        return

    print(f"Found {len(flac_files)} FLAC files. Converting...")

    for flac_file in flac_files:
        wav_file = flac_file.with_suffix(".wav")

        # ffmpeg command
        cmd = [
            "ffmpeg",
            "-y",                 # overwrite output
            "-i", str(flac_file),  # input file
            "-ac", "1",           # mono
            "-ar", str(target_rate),  # sample rate
            "-sample_fmt", "s16",  # 16-bit PCM
            str(wav_file)
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

        if wav_file.exists():
            print(f"Converted: {flac_file.name} → {wav_file.name}")
            flac_file.unlink()  # delete original FLAC
        else:
            print(f"FAILED: {flac_file.name}")

    print("All conversions complete. FLAC files removed.")


if __name__ == "__main__":
    # convert_flac_to_wav_and_cleanup(target_rate=22050)
    # fix_metadata_file()
