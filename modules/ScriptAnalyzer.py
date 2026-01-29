import json
import requests
import google.generativeai as genai

class ScriptAnalyzer:
    """Uses Gemini Pro to transform raw scripts into structured visual scenes."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        # Encapsulation: Keeping the API client private to the class
        genai.configure(api_key=api_key)
        self.__model = genai.GenerativeModel(model_name,
            generation_config={"response_mime_type": "application/json"})
        self.__system_instruction = (
            "You are a film director. Convert the input script into a JSON list. "
            "Each item must have a 'scene_number' and a 'visual_prompt' describing "
            "the shot in detail (lighting, camera angle, subject)."
        )

    def parse_script(self, script_text):
        """Sends script to Gemini and returns a structured list of scenes."""
        print(f"[ScriptAnalyzer] Analyzing: {script_text[:30]}...")
        
        
        prompt = (
            f"Convert this script into a JSON list of 3 scenes. "
            f"Use this exact structure: "
            f"[ {{\"scene_id\": 1, \"visual_prompt\": \"description\"}} ] "
            f"Script: {script_text}"
        )
        
        try:
            response = self.__model.generate_content(prompt)
            return self.__extract_json(response.text)
        except Exception as e:
            print(f"[Error] Gemini API Call Failed: {e}")
            return []

    def __extract_json(self, text):
        """Robustly extracts JSON even if the model adds markdown backticks."""
        try:
            
            clean_text = text.replace("```json", "").replace("```", "").strip()
            
            
            start = clean_text.find("[")
            end = clean_text.rfind("]") + 1
            if start != -1 and end != 0:
                clean_text = clean_text[start:end]
                
            return json.loads(clean_text)
        except Exception as e:
            print(f"[Error] JSON Parsing failed. Raw response: {text[:50]}...")
            return []    

    def __call_gemini_api(self, prompt: str):
        """Internal method to handle the specific API call logic."""
        combined_prompt = f"{self.__system_instruction}\n\nScript: {prompt}"
        response = self.__model.generate_content(combined_prompt)
        return response.text

    def __clean_json_response(self, text: str):
        """Internal method to strip markdown and parse JSON."""
        
        clean_text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            print("[Error] Gemini returned invalid JSON. Check your system prompt.")
            return []

class ComfyUIGenerator:
    """Manages the lifecycle of a video generation task in ComfyUI."""
    
    def __init__(self, server_address="127.0.0.1:8188"):
        self.url = f"http://{server_address}"

    def generate_scene(self, visual_prompt: str, workflow_path: str):
        """Loads a workflow JSON, injects the prompt, and triggers generation."""
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        prompt_id = self.__send_to_queue(workflow)
        return self.__poll_until_done(prompt_id)

    def __send_to_queue(self, workflow):
        resp = requests.post(f"{self.url}/prompt", json={"prompt": workflow})
        return resp.json().get('prompt_id')

    def __poll_until_done(self, prompt_id):
        
        pass

class AgenticVideoSynthesizer:
    """Orchestrator class following the Facade Pattern."""
    
    def __init__(self, analyzer: ScriptAnalyzer, generator: ComfyUIGenerator):
        self.analyzer = analyzer
        self.generator = generator

    def start_production(self, script: str, workflow_file: str):
        
        scenes = self.analyzer.parse_script(script)
        
        
        for scene in scenes:
            print(f"Action: Generating Scene {scene['scene_number']}...")
            self.generator.generate_scene(scene['visual_prompt'], workflow_file)
