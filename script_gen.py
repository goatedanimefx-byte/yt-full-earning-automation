#!/usr/bin/env python3
"""
Script Generator - Built-in templates, no external API needed
Generates documentary scripts from topic + structure templates
"""

import json
import random
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "outputs"

# Documentary structures by category
SCRIPT_TEMPLATES = {
    "tech": {
        "intro": ["In the span of a decade, {topic} has transformed from experimental curiosity to {impact}.", 
                  "What started as {origin} has become one of the most {adj} developments of our time."],
        "context": ["To understand where we're going, we need to understand where {topic} came from.",
                   "The journey began when {founder} first {action} in {year}."],
        "main": ["Today, {topic} impacts {sector1}, {sector2}, and {sector3} in ways few predicted.",
                "Experts predict that by {future_year}, {stat} will reshape the global economy."],
        "conclusion": ["The story of {topic} is far from over. What comes next may surprise even the believers.",
                      "One thing is certain: {topic} has changed everything."],
        "cta": ["Subscribe for more deep dives into the tech shaping our future.",
                "Hit the bell and join the conversation below."]
    },
    "science": {
        "intro": ["For centuries, scientists have {action} about {topic}. Now we have answers.",
                  "Deep within {location}, researchers made a discovery that challenges everything we knew."],
        "context": ["The puzzle began when {scientist} noticed {observation} in {year}.",
                   "What seemed like {problem} turned out to be {breakthrough}."],
        "main": ["Through {method}, scientists now understand {discovery}.",
                "The implications extend to {field1}, {field2}, and beyond."],
        "conclusion": ["This is just the beginning. {topic} opens doors we never imagined.",
                      "The next generation of discoveries awaits."],
        "cta": ["Like and subscribe for more science content.",
                "Comment below what topic you want us to explore next."]
    },
    "history": {
        "intro": ["History remembers the loudest voices, but the true story of {topic} is {adj}.",
                  "Before the textbooks, before the monuments, there was {origin}."],
        "context": ["In {year}, {figure} faced a decision that would {impact}.",
                   "The world looked vastly different then. {setting}."],
        "main": ["What transpired next changed {region} forever.",
                "The consequences of {event} still ripple through {modern}."],
        "conclusion": ["{topic} reminds us that history is written by the victors, but truth persists.",
                      "Understanding our past is the key to shaping our future."],
        "cta": ["History repeats. Subscribe to learn from it.",
                "Smash that subscribe button for more historical deep dives."]
    }
}

TOPIC_DATA = {
    "tech": {
        "impact": ["daily reality", "trillion-dollar industry", "fundamental shift"],
        "origin": ["a garage experiment", "a university lab", "military research"],
        "adj": ["disruptive", "transformative", "revolutionary"],
        "founder": ["a small team of researchers", "a visionary entrepreneur", "a government program"],
        "action": ["demonstrated", "released", "pioneered"],
        "year": "2010",
        "sector1": "healthcare", "sector2": "finance", "sector3": "entertainment",
        "future_year": "2030", "stat": "it"
    },
    "science": {
        "action": ["wondered", "theorized", "debated"],
        "location": ["the lab", "deep space", "the ocean floor"],
        "scientist": ["Dr. Chen", "a team of researchers", "an anonymous peer"],
        "observation": ["an anomaly", "a pattern", "unexpected results"],
        "year": "2015",
        "problem": ["an error", "a mystery", "a contradiction"],
        "breakthrough": ["paradigm shift", "new understanding", "eureka moment"],
        "method": ["decades of research", "breakthrough technology", "international collaboration"],
        "discovery": ["the mechanism", "the truth", "the missing piece"],
        "field1": "medicine", "field2": "energy"
    },
    "history": {
        "adj": ["forgotten", "uncomfortable", "inspiring"],
        "origin": ["a small village", "a pivotal moment", "an unlikely hero"],
        "year": "1945",
        "figure": ["a lone visionary", "an ordinary citizen", "a reluctant leader"],
        "impact": ["the outcome of the war", "generations to come", "the course of history"],
        "setting": "The world was at a crossroads. Hope was scarce, but resolve was not.",
        "region": "the world", "event": "the turning point", "modern": "our modern world"
    }
}

def detect_category(topic: str) -> str:
    topic_lower = topic.lower()
    if any(w in topic_lower for w in ["ai", "tech", "software", "computer", "digital", "code"]): return "tech"
    elif any(w in topic_lower for w in ["science", "physics", "biology", "space", "discover"]): return "science"
    elif any(w in topic_lower for w in ["history", "war", "ancient", "civilization", "king"]): return "history"
    return "tech"

def fill_template(template: str, data: dict, topic: str) -> str:
    result = template
    for key, value in data.items():
        if isinstance(value, list): value = random.choice(value)
        result = result.replace(f"{{{key}}}", str(value))
    return result.replace("{topic}", topic)

def generate_script(topic: str, duration_min: int = 10) -> dict:
    category = detect_category(topic)
    templates = SCRIPT_TEMPLATES.get(category, SCRIPT_TEMPLATES["tech"])
    data = TOPIC_DATA.get(category, TOPIC_DATA["tech"]).copy()
    
    total_sec = duration_min * 60
    durations = {"intro": 30, "context": int(total_sec * 0.15), "main": int(total_sec * 0.55), "conclusion": int(total_sec * 0.20), "cta": 30}
    
    segments = []
    for seg_type in ["intro", "context", "main", "conclusion", "cta"]:
        template = random.choice(templates[seg_type])
        voiceover = fill_template(template, data.copy(), topic)
        
        if seg_type == "main":
            voiceover += f" {random.choice(['Consider this:', 'Here is the data:', 'The numbers tell the story:'])} "
            voiceover += f"Since 2020, adoption has grown {random.choice(['10x', 'exponentially', 'by orders of magnitude'])}. "
            voiceover += f"Experts forecast {random.choice(['massive', 'significant', 'transformative'])} growth ahead."
        
        segments.append({"type": seg_type, "duration_sec": durations[seg_type], "voiceover": voiceover, "visuals": f"{seg_type} segment"})
    
    return {"topic": topic, "category": category, "duration_min": duration_min, "segments": segments, "generated_at": "2026-01-01"}

def save_script(script: dict, output_path: Path):
    """Save script to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(script, f, indent=2)
    print(f"Script saved: {output_path}")

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "The Rise of AI in Filmmaking"
    
    script = generate_script(topic)
    output_file = OUTPUT_DIR / f"script_{topic.lower().replace(' ', '_')}.json"
    save_script(script, output_file)
    print(json.dumps(script, indent=2))