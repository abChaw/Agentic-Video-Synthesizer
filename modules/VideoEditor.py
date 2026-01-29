import subprocess
import os

class VideoEditor:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def stitch_clips(self, clip_paths, final_filename="final_video.mp4"):
        """Concatenates video files using FFmpeg with Windows shell support."""
        list_file = "temp_list.txt"
        with open(list_file, "w") as f:
            for path in clip_paths:
                
                clean_path = path.replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        output_path = os.path.join(self.output_dir, final_filename)
        
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_path]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, shell=True)
            print(f"[Editor] Success! Video saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"[Editor] Stitching failed: {e}")
            return None
        finally:
            if os.path.exists(list_file):
                os.remove(list_file)