import os
import sys
from dotenv import load_dotenv

from modules.ScriptAnalyzer import ScriptAnalyzer
from modules.ComfyUIGenerator import ComfyUIGenerator
from modules.VideoEditor import VideoEditor

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
COMFY_URL = os.getenv("COMFY_URL", "127.0.0.1:8188")

class AgenticVideoSynthesizer:
    def __init__(self, director, generator, editor):
        
        self.director = director
        self.generator = generator
        self.editor = editor

    def start_production(self, script: str, workflow_file: str):
       
        scenes = self.director.parse_script(script)
        
        # Hardcode a single test scene to save time/credits
        # scenes = [{
        #     "scene_id": 1, 
        #     "visual_prompt": "A test scene of a robotic hand holding a glowing crystal, cinematic lighting"
        # }]
        # --------------------

        downloaded_clips = []

        for scene in scenes:
            s_num = scene.get('scene_id')
            s_prompt = scene.get('visual_prompt')
            
            print(f"\n🧪 TEST MODE: Processing Scene {s_num}")
            local_clip_path = self.generator.generate_scene(s_prompt, workflow_file)
            
            if local_clip_path:
                downloaded_clips.append(local_clip_path)

        if downloaded_clips:
            self.editor.stitch_clips(downloaded_clips, "test_output.mp4")


    def test_single_scene(self, workflow_file: str):
        """Isolated test for the ComfyUI -> Local Download -> FFmpeg Stitch pipeline."""
        print("\n🧪 [Quick Test] Starting Single Scene Generation...")
        test_prompt = "A cinematic shot of a futuristic car in the rain, neon reflections."
        
        # 1. Generate and Download
        clip_path = self.generator.generate_scene(test_prompt, workflow_file)
        
        if clip_path:
            print(f"✅ Clip downloaded to: {clip_path}")
            # 2. Stitch (even a single clip test ensures FFmpeg is working)
            print("\n🎞️ Testing Editor stitching...")
            final_output = self.editor.stitch_clips([clip_path], "test_single_scene.mp4")
            if final_output:
                print(f"🚀 SUCCESS: {final_output} is ready.")
        else:
            print("TEST FAILED: Check the logs above for Pinggy or Node 50 errors.")                

def get_multiline_input():
    print("\n📝 Enter/Paste your story script.")
    print("👉 Type 'DONE' on a new line and press Enter when finished:")
    print("-" * 60)
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "DONE":
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines).strip()

if __name__ == "__main__":
    if not API_KEY:
        print("Error: GEMINI_API_KEY is missing")
        sys.exit(1)

    
    director_agent = ScriptAnalyzer(api_key=API_KEY)
    generator_agent = ComfyUIGenerator(server_address=COMFY_URL)
    editor_agent = VideoEditor()

    
    app = AgenticVideoSynthesizer(director_agent, generator_agent, editor_agent)

    
    user_story = get_multiline_input()
    
    if user_story:
        
        app.start_production(user_story, "workflows/wan.json")
    else:
        print("Empty story. Exiting.")
    # app.test_single_scene("workflows/wan.json")    