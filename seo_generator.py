#!/usr/bin/env python3
"""
SEO Generator - Title, Description, Tags for YouTube
"""

import json
import random
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "outputs"

TITLE_TEMPLATES = [
    "The Truth About {topic} (2024)",
    "{topic}: What Nobody Tells You",
    "How {topic} Changed Everything",
    "Why {topic} Matters More Than Ever",
    "The Complete Guide to {topic}",
    "{topic} - Full Documentary"
]

DESCRIPTION_TEMPLATE = """📽️ In this documentary about {topic}, we explore the ins and outs.

🎯 What you'll learn:
{points}

📌 Chapters:
{chapters}

---
💡 Want to learn more? Check out our digital products in the link below!

👇 SUBSCRIBE for more documentaries:
🔔 Enable notifications!

#documentary #{topic_hash} #educational #documentary"""

def generate_seo(script: dict, chapters: list) -> dict:
    """Generate Title, Description, and Tags."""
    
    topic = script.get("topic", "Unknown")
    category = script.get("category", "tech")
    
    # Generate title
    title_template = random.choice(TITLE_TEMPLATES)
    title = title_template.format(topic=topic)
    
    # Generate description
    points = [
        "The history and background",
        "Key insights and analysis",
        "What the future holds",
        "Actionable takeaways"
    ]
    chapters_text = "\n".join([f"{c['time']} - {c['title']}" for c in chapters[:5]])
    
    description = DESCRIPTION_TEMPLATE.format(
        topic=topic,
        points="\n".join([f"• {p}" for p in points]),
        chapters=chapters_text,
        topic_hash=topic.replace(" ", "").lower()
    )
    
    # Generate tags
    base_tags = ["documentary", "educational", category, topic.lower()]
    extra_tags = ["docu", "facts", "learning", "knowledge", "2024", "documentary2024"]
    tags = list(set(base_tags + extra_tags))[:15]
    
    seo_data = {
        "title": title,
        "description": description,
        "tags": tags,
        "category": "28"  # Education
    }
    
    # Save
    output_path = OUTPUT_DIR / "seo.json"
    with open(output_path, "w") as f:
        json.dump(seo_data, f, indent=2)
    
    print(f"SEO generated: {output_path}")
    return seo_data

if __name__ == "__main__":
    # Test
    test_script = {"topic": "AI in Filmmaking", "category": "tech"}
    test_chapters = [{"time": "0:00", "title": "Introduction"}]
    seo = generate_seo(test_script, test_chapters)
    print(seo)