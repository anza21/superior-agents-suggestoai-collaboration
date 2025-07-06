import requests
import json
import time

def generate_image_comfyui(prompt, workflow_path="agent/scripts/_comfyui_image_api.json"):
    url = "http://172.30.224.1:8188/prompt"
    # Διόρθωσε τα εισαγωγικά στο prompt
    prompt = prompt.replace('"', '"').replace("'", '"')
    with open(workflow_path, "r") as f:
        workflow = json.load(f)
    # Βρες το node που έχει το prompt και άλλαξέ το (flat dict format)
    for node_id, node in workflow.items():
        if isinstance(node, dict) and node.get("class_type", "").lower().startswith("cliptextencode") and "inputs" in node and "text" in node["inputs"]:
            node["inputs"]["text"] = prompt
    response = requests.post(url, json=workflow)
    if response.status_code == 200:
        job_id = response.json().get("job_id")
        for _ in range(60):
            result = requests.get(f"http://172.30.224.1:8188/history/{job_id}")
            if result.status_code == 200 and "outputs" in result.json():
                outputs = result.json()["outputs"]
                if outputs:
                    image_path = outputs[0]["filename"]
                    print("Image saved as", image_path)
                    return image_path
            time.sleep(1)
        print("Timeout waiting for image.")
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    generate_image_comfyui("A futuristic smartwatch, product photo, white background, high detail", workflow_path="agent/scripts/_comfyui_image_api.json") 