#!/usr/bin/env python3
"""
Thumbnail Generator - Auto-generate thumbnails from video frames
Pure code - uses ffmpeg to extract frames + PIL for design
"""

import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

OUTPUT_DIR = Path(__file__).parent / "outputs" / "thumbnails"

# Thumbnail styles
STYLES = {
    "vhs": {"bg": "#1a1a2e", "accent": "#00ffff", "font_color": "white"},
    "riso": {"bg": "#f5f0e6", "accent": "#ff6b6b", "font_color": "black"},
    "rubber_hose": {"bg": "#0d0d0d", "accent": "#00ff88", "font_color": "white"},
    "bold": {"bg": "#ff0000", "accent": "#ffff00", "font_color": "white"},
    "minimal": {"bg": "#ffffff", "accent": "#000000", "font_color": "black"},
}

def extract_frame(video_path: str, timestamp: str = "00:00:05") -> Path:
    """Extract a frame from video at given timestamp."""
    output_path = OUTPUT_DIR / "temp_frame.jpg"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "ffmpeg", "-y", "-ss", timestamp,
        "-i", video_path,
        "-vframes", "1", "-q:v", "2",
        str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True)
    return output_path if output_path.exists() else None

def create_text_layer(text: str, style: dict, width: int = 1280, height: int = 720) -> Image.Image:
    """Create text overlay for thumbnail."""
    img = Image.new("RGB", (width, height), style["bg"])
    draw = ImageDraw.Draw(img)
    
    # Try to load font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 80)
        small_font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Split text into words for wrapping
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 20:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    
    # Draw main text (title)
    y = height // 3
    for line in lines[:3]:  # Max 3 lines
        draw.text((width//2, y), line, font=font, fill=style["font_color"], anchor="mm")
        y += 80
    
    # Draw accent bar
    draw.rectangle([50, height-100, width-50, height-90], fill=style["accent"])
    
    return img

def generate_thumbnail(
    video_path: str = None,
    title: str = "Documentary",
    style: str = "vhs",
    output_name: str = "thumbnail.jpg"
) -> Path:
    """Generate thumbnail - either from video frame or pure code."""
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / output_name
    
    style_data = STYLES.get(style, STYLES["vhs"])
    
    # Try to extract frame from video
    frame = None
    if video_path and Path(video_path).exists():
        frame = extract_frame(video_path)
    
    if frame and frame.exists():
        # Use video frame as base
        img = Image.open(frame)
        img = img.resize((1280, 720))
        # Add overlay
        overlay = create_text_layer(title, style_data)
        img = Image.blend(img, overlay, 0.3)
    else:
        # Pure code thumbnail
        img = create_text_layer(title, style_data)
    
    img.save(output_path, quality=95)
    print(f"Thumbnail: {output_path}")
    return output_path

def generate_ab_thumbnails(video_path: str, title: str, variations: int = 2) -> list:
    """Generate A/B test thumbnails with different styles."""
    
    styles = list(STYLES.keys())
    thumbnails = []
    
    for i in range(min(variations, len(styles))):
        style = styles[i]
        output_name = f"thumbnail_{style}.jpg"
        path = generate_thumbnail(video_path, title, style, output_name)
        thumbnails.append({"style": style, "path": str(path)})
    
    return thumbnails

if __name__ == "__main__":
    # Test
    generate_thumbnail(title="The Rise of AI", style="vhs")
    print("Thumbnail generated!")