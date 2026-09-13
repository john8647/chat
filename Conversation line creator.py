# Conversation line creator
from pathlib import Path
import subprocess
import requests
import json
import os
import time

AUDIO_GEN_SERVER_URL = "https://tsj9jgc3hzg8dn-8188.proxy.runpod.net"
VOICE_MODEL_FILE = "voice - best one UK version 9-Leah.mp3"
DIALOG_FILE = "G:/text ts/metadata.csv"


def normalize_queue_item(item):
    if isinstance(item, list) and len(item) > 0 and isinstance(item[0], dict):
        return item[0]
    if isinstance(item, dict):
        return item
    return None


def comfyui_alive():
    try:
        r = requests.get(f"{AUDIO_GEN_SERVER_URL}/system_stats", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def generate_audio(dialog_script):
    global VOICE_MODEL_FILE
    if not comfyui_alive():
        print(
            f"Error: ComfyUI server is NOT alive or unreachable.  Was about to say {dialog_script}")
        return None
    workflow_path = "resources/comfyui_api/audio_workflow.json"
    with open(workflow_path, "r") as f:
        workflow = json.load(f)

    workflow["3"]["inputs"]["audio"] = VOICE_MODEL_FILE
    workflow["2"]["inputs"]["text"] = dialog_script

    resp = requests.post(f"{AUDIO_GEN_SERVER_URL}/prompt",
                         json={"prompt": workflow})

    data = resp.json()
    prompt_id = data["prompt_id"]
    result = None
    initialwait = True
    start_time = time.time()
    MAX_WAIT = 300

    while True:
        if time.time() - start_time > MAX_WAIT:
            print("ERROR: Audio generation timed out.")
            return None

        if initialwait:
            time.sleep(5)
            initialwait = False
            continue

        queue = requests.get(f"{AUDIO_GEN_SERVER_URL}/queue").json()
        all_items = (
            queue.get("queue_pending", []) +
            queue.get("queue_running", []) +
            queue.get("queue_done", [])
        )

        if not all_items:
            history_data = requests.get(
                f"{AUDIO_GEN_SERVER_URL}/history/{prompt_id}").json()
            result = history_data
            break

        for raw_item in all_items:
            item = normalize_queue_item(raw_item)
            if not item:
                continue
            if item.get("prompt_id") == prompt_id:
                status = item.get("status")
                if status in ("completed", "success", "done") or "outputs" in item:
                    result = item
                    break

        if result is not None:
            break

        time.sleep(1)

    # print("starting search")
    history_data = requests.get(
        f"{AUDIO_GEN_SERVER_URL}/history/{prompt_id}"
    ).json()

    # 1. Get the inner object for this prompt_id
    prompt_result = history_data.get(prompt_id)
    # print("no history")
    if not prompt_result:
        print("ERROR: No history entry for prompt_id", prompt_id)
        print(json.dumps(history_data, indent=4))
        # print("no history")
        return None

    # 2. Get outputs
    outputs = prompt_result.get("outputs", {})
    if not outputs:
        print("ERROR: Audio outputs missing in history for", prompt_id)
        print(json.dumps(prompt_result, indent=4))
        return None

    # 3. Find the audio node (13 here, but we’ll scan)
    # print("Audio file on he way: 1")
    audio_node = None
    for node_id, node_data in outputs.items():
        if isinstance(node_data, dict) and isinstance(node_data.get("audio"), list) and node_data["audio"]:
            audio_node = node_data
            break
    # print("Audio file on he way: 2")
    if not audio_node:
        print("ERROR: Audio output node not found in outputs")
        print(json.dumps(outputs, indent=4))
        return None

    audio_list = audio_node["audio"]
    audio_info = audio_list[0]
    audio_filename = audio_info["filename"]
    subfolder = audio_info.get("subfolder", "")

    # print("Audio file:", audio_filename, "subfolder:", subfolder)

    audio_data = requests.get(
        f"{AUDIO_GEN_SERVER_URL}/view?filename={audio_filename}&subfolder={subfolder}"
    ).content

    # print("Audio file on he way: 3")
    AUDIO_OUTPUT_DIR = os.path.join("G:/text ts/audio_data", "audio")
    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
    safe_filename = os.path.basename(audio_filename)
    save_path = os.path.join(AUDIO_OUTPUT_DIR, safe_filename)

    with open(save_path, "wb") as f:
        f.write(audio_data)

    return safe_filename


def generate_audio_for_dialog_file():
    global DIALOG_FILE
    dialog_file = DIALOG_FILE
    try:
        with open(dialog_file, "r", encoding="utf-8-sig") as f:
            phrases = [line.strip() for line in f if line.strip()]
    except UnicodeDecodeError:
        with open(dialog_file, "r", encoding="cp1252") as f:
            phrases = [line.strip() for line in f if line.strip()]

    audio_output_dir = os.path.join("G:/text ts/audio_data", "audio")
    results = []

    for index, phrase in enumerate(phrases, start=1):
        print(f"Generating {index:04d}: {phrase}")
        generated_filename = generate_audio(phrase)
        if generated_filename is None:
            print(f"ERROR: Could not generate audio for line {index:04d}")
            continue

        numbered_filename = f"{index:04d}.flac"
        generated_path = os.path.join(audio_output_dir, generated_filename)
        numbered_path = os.path.join(audio_output_dir, numbered_filename)
        os.replace(generated_path, numbered_path)
        results.append(f"{phrase} | {numbered_filename}")

    with open(dialog_file, "w", encoding="utf-8") as f:
        f.write("\n".join(results))
        if results:
            f.write("\n")


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
    generate_audio_for_dialog_file()
    convert_flac_to_wav_and_cleanup(target_rate=22050)
