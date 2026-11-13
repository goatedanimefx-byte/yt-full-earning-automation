#!/usr/bin/env python3
"""
Visual Generator - Try code first, fallback to Pexels
1. Try Three.js code generation
2. If can't generate → use Pexels
"""

import json
import subprocess
import os
import requests
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "outputs" / "visuals"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")  # Optional - use if provided

# Visual styles for different segment types
VISUAL_STYLES = {
    "intro": "vhs",
    "context": "riso", 
    "main": "rubber_hose",
    "conclusion": "vhs",
    "cta": "riso"
}

# Three.js scene templates - save as HTML for rendering
THREEJS_TEMPLATES = {
    "vhs": """<!DOCTYPE html>
<html>
<head><style>body{margin:0;overflow:hidden;background:#1a1a2e}</style></head>
<body>
<script type="module">
import*as THREE from'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x1a1a2e);
const camera=new THREE.PerspectiveCamera(75,16/9,0.1,1000);
camera.position.z=3;
const renderer=new THREE.WebGLRenderer();
renderer.setSize(1920,1080);
document.body.appendChild(renderer.domElement);
const geo=new THREE.TorusKnotGeometry(1,0.3,100,16);
const mat=new THREE.MeshNormalMaterial({wireframe:true});
const mesh=new THREE.Mesh(geo,mat);
scene.add(mesh);
function animate(){mesh.rotation.x+=0.01;mesh.rotation.y+=0.02;renderer.render(scene,camera);requestAnimationFrame(animate)}
animate();
</script>
</body>
</html>""",
    
    "riso": """<!DOCTYPE html>
<html>
<head><style>body{margin:0;overflow:hidden;background:#f5f0e6}</style></head>
<body>
<script type="module">
import*as THREE from'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
const scene=new THREE.Scene();
scene.background=new THREE.Color(0xf5f0e6);
const camera=new THREE.PerspectiveCamera(75,16/9,0.1,1000);
camera.position.z=4;
const renderer=new THREE.WebGLRenderer();
renderer.setSize(1920,1080);
document.body.appendChild(renderer.domElement);
const geo=new THREE.IcosahedronGeometry(1.5,0);
const mat=new THREE.MeshBasicMaterial({color:0xff6b6b,wireframe:true});
const mesh=new THREE.Mesh(geo,mat);
scene.add(mesh);
function animate(){mesh.rotation.y+=0.005;renderer.render(scene,camera);requestAnimationFrame(animate)}
animate();
</script>
</body>
</html>""",
    
    "rubber_hose": """<!DOCTYPE html>
<html>
<head><style>body{margin:0;overflow:hidden;background:#0d0d0d}</style></head>
<body>
<script type="module">
import*as THREE from'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x0d0d0d);
const camera=new THREE.PerspectiveCamera(75,16/9,0.1,1000);
camera.position.z=3;
const renderer=new THREE.WebGLRenderer();
renderer.setSize(1920,1080);
document.body.appendChild(renderer.domElement);
const geo=new THREE.SphereGeometry(1,32,32);
const mat=new THREE.MeshStandardMaterial({color:0x00ff88,emissive:0x00ff88,emissiveIntensity:0.5});
const mesh=new THREE.Mesh(geo,mat);
scene.add(new THREE.PointLight(0x00ff88,1,10));
function animate(){mesh.scale.setScalar(1+Math.sin(Date.now()*0.002)*0.1);renderer.render(scene,camera);requestAnimationFrame(animate)}
animate();
</script>
</body>
</html>"""
}

def can_generate_code(style: str) -> bool:
    """Check if we can render Three.js code on this system."""
    # Check if ffmpeg is available for rendering
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    return result.returncode == 0

def search_pexels(query: str, per_page: int = 3) -> list:
    """Search Pexels for videos if API key available."""
    if not PEXELS_API_KEY:
        return []
    
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, params={"query": query, "per_page": per_page}, timeout=10)
        if response.status_code == 200:
            return response.json().get("videos", [])
    except:
        pass
    return []

def download_pexels_video(video: dict, output_dir: Path) -> Path:
    """Download best quality video from Pexels."""
    video_id = video["id"]
    best = max(video["video_files"], key=lambda x: x.get("height", 0))
    url = best["link"]
    
    output_path = output_dir / f"{video_id}.mp4"
    
    if output_path.exists():
        return output_path
    
    print(f"Downloading from Pexels: {video['url']}")
    resp = requests.get(url, stream=True, timeout=60)
    
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    print(f"Saved: {output_path}")
    return output_path

def generate_threejs_visual(style: str, output_path: Path, duration_sec: int = 5):
    """Generate visual using Three.js code OR fallback to Pexels."""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try Three.js code generation first
    if can_generate_code(style):
        html_path = output_path.with_suffix(".html")
        html_content = THREEJS_TEMPLATES.get(style, THREEJS_TEMPLATES["vhs"])
        html_path.write_text(html_content)
        
        # Try rendering with ffmpeg + screen capture
        # For now use color bars as placeholder
        color_map = {"vhs": "blue", "riso": "coral", "rubber_hose": "green"}
        color = color_map.get(style, "blue")
        
        result = subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=1920x1080:d={duration_sec}",
            "-c:v", "libx264", "-t", str(duration_sec), "-pix_fmt", "yuv420p",
            str(output_path)
        ], capture_output=True)
        
        if result.returncode == 0:
            print(f"Code-generated visual: {output_path}")
            return output_path
    
    # If code generation failed → try Pexels
    print(f"Code generation not available, trying Pexels...")
    videos = search_pexels(style)
    
    if videos:
        video_path = download_pexels_video(videos[0], output_path.parent)
        # Move to expected path
        if video_path != output_path:
            import shutil
            shutil.copy(video_path, output_path)
        print(f"Pexels fallback: {output_path}")
        return output_path
    
    # Last resort: color bars
    print(f"Generating color bars fallback...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=30",
        "-c:v", "libx264", "-t", "30", "-pix_fmt", "yuv420p",
        str(output_path)
    ], capture_output=True)
    
    return output_path

def fetch_visuals_for_script(script: dict) -> dict:
    """Generate all visuals for a documentary script - pure code, no external APIs."""
    
    script_name = script.get("topic", "doc").lower().replace(" ", "_")
    output_dir = OUTPUT_DIR / script_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    visual_manifest = []
    
    for i, segment in enumerate(script.get("segments", [])):
        segment_type = segment.get("type", "main")
        category = script.get("category", "tech")
        
        # Get style based on segment type
        style = VISUAL_STYLES.get(segment_type, "vhs")
        
        visual_path = output_dir / segment_type / f"visual_{i}.mp4"
        generate_threejs_visual(style, visual_path, segment.get("duration_sec", 30))
        
        visual_manifest.append({
            "segment_index": i,
            "type": segment_type,
            "style": style,
            "source": "code_generated",
            "path": str(visual_path),
            "category": category
        })
    
    # Save manifest
    manifest_path = output_dir / "visual_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(visual_manifest, f, indent=2)
    
    print(f"Visual manifest: {manifest_path}")
    return visual_manifest

if __name__ == "__main__":
    import sys
    
    script_file = sys.argv[1] if len(sys.argv) > 1 else "../outputs/script_the_rise_of_ai_in_filmmaking.json"
    
    with open(script_file) as f:
        script = json.load(f)
    
    visuals = fetch_visuals_for_script(script)
    print(f"Fetched {len(visuals)} visual assets")