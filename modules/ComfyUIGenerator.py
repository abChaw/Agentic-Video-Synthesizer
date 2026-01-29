import os
import json
import time
import requests

class ComfyUIGenerator:
    def __init__(self, server_address="127.0.0.1:8188"):
        
        self.base_url = server_address.rstrip('/')
        if not self.base_url.startswith("http"):
            self.base_url = f"http://{self.base_url}"
        
        
        self.client = requests.Session()
        self.client.headers.update({
            "Content-Type": "application/json",
            "X-Pinggy-No-Screen": "true",        
            "bypass-tunnel-reminder": "true",   
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        })
        print(f"[Generator] Connected to Tunnel: {self.base_url}")

    def generate_scene(self, visual_prompt, workflow_path):
        """Loads workflow, injects prompt into Node 6, and polls for Node 50 output."""
        if not os.path.exists(workflow_path):
            print(f"Error: Workflow file {workflow_path} not found.")
            return None

        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        # Update Workflow Nodes based on your 'wan.json' IDs
        workflow["6"]["inputs"]["text"] = visual_prompt
        workflow["3"]["inputs"]["seed"] = int(time.time())

        try:
            # 1. Queue the prompt
            res = self.client.post(f"{self.base_url}/prompt", json={"prompt": workflow, "client_id": "agent_studio"})
            res.raise_for_status()
            prompt_id = res.json()['prompt_id']
            print(f"Queued: {prompt_id}. Waiting for render...")

            # 2. Poll for History
            while True:
                history_res = self.client.get(f"{self.base_url}/history/{prompt_id}")
                history = history_res.json()
                if prompt_id in history:
                    break
                time.sleep(15) 

            # 3. Locate File in Node 50 
            node_output = history[prompt_id]['outputs'].get("50", {})
            target_file = None
            for key in ['images', 'videos', 'gifs', 'video']:
                if key in node_output and len(node_output[key]) > 0:
                    target_file = node_output[key][0]
                    break
            
            if not target_file:
                print(f"Error: Could not find output in Node 50. Structure: {node_output}")
                return None

            filename = target_file['filename']
            subfolder = target_file.get('subfolder', '')

            # 4. Download 
            print(f"✅ Found: {filename}. Downloading...")
            video_res = self.client.get(
                f"{self.base_url}/view", 
                params={"filename": filename, "subfolder": subfolder, "type": "output"},
                stream=True
            )
            
            if not os.path.exists("outputs"): os.makedirs("outputs")
            local_path = os.path.join("outputs", f"clip_{int(time.time())}.mp4")

            with open(local_path, "wb") as f:
                for chunk in video_res.iter_content(chunk_size=1024*1024):
                    if chunk: f.write(chunk)
            
            # Verify file was actually saved
            if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
                return local_path
            return None

        except Exception as e:
            print(f"Generation failed: {e}")
            return None