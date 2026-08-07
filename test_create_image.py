import json, uuid, requests, time, os

IMAGE_GEN_SERVER_URL = "https://3ma9jsmvdp48he-8188.proxy.runpod.net"

def normalize_queue_item(item):
    # Some ComfyUI builds return [ {job} ]
    if isinstance(item, list) and len(item) > 0 and isinstance(item[0], dict):
        return item[0]
    # Normal case: item is already a dict
    if isinstance(item, dict):
        return item
    return None
 

def generate_image(prompt):
    if not comfyui_alive():
        print("ComfyUI server is NOT alive or unreachable.")
        return None

    # 1. Load workflow
    workflow_path = "resources/comfyui_api/image_workflow.json"
    with open(workflow_path, "r") as f:
        workflow = json.load(f)

    # 2. Insert prompt
    workflow["6"]["inputs"]["text"] = (
        prompt
    )

    # 3. Insert random filename prefix 
    random_prefix = str(uuid.uuid4())
    workflow["78"]["inputs"]["filename_prefix"] = random_prefix
    workflow["28"]["inputs"]["lora_1"]["on"] = "false"
    # 4. Submit workflow
    resp = requests.post(
        f"{IMAGE_GEN_SERVER_URL}/prompt",
        json={"prompt": workflow}
    )
    data = resp.json()
    prompt_id = data["prompt_id"]

    print("Prompt ID:", prompt_id)
    result = None
    initialwait = True
    start_time = time.time()
    MAX_WAIT = 300  # 5 minutes

    while True:
        if time.time() - start_time > MAX_WAIT:
            print("ERROR: Image generation timed out.")
            return None

        if initialwait:
            time.sleep(20)
            initialwait = False
            continue

        queue = requests.get(f"{IMAGE_GEN_SERVER_URL}/queue").json()

        all_items = (
            queue.get("queue_pending", []) +
            queue.get("queue_running", []) +
            queue.get("queue_done", [])
        )

        print("QUEUE:", all_items)
        # ⭐ If queue is empty, job is finished — fetch history
        if not all_items:
            print("Queue empty — job finished. Fetching history…")
            history = requests.get(f"{IMAGE_GEN_SERVER_URL}/history/{prompt_id}").json()
            result = history
            print(result)
            break

        # ⭐ Otherwise check for completed job
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



    print("FINAL RESULT:", result)


    # 6. Extract output filename
    # result is: { "<prompt_id>": { ... } }
    prompt_result = result[prompt_id]

    # SaveImage output is inside "outputs"
    output_node = prompt_result["outputs"]["78"]
    filename = output_node["images"][0]["filename"]

    print("Generated filename:", filename)

    # 7. Download image
    img_data = requests.get(
        f"{IMAGE_GEN_SERVER_URL}/view?filename={filename}"
    ).content

    # 8. Save to images folder
    save_path = os.path.join("images", filename)
    with open(save_path, "wb") as f:
        f.write(img_data)

    print("Saved to:", save_path)

    return filename

def comfyui_alive():
    try:
        r = requests.get(f"{IMAGE_GEN_SERVER_URL}/system_stats", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# Test
test_prompt = (
    "Photorealistic: farm scene, real photo of young man 45yo, brown hair, "
        "a farmer, blue shirt, straw hat, denim trousers, boots, leaning on a tree."
)
generate_image(test_prompt)
