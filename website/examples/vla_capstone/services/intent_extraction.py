"""
Service for extracting intent and parameters from transcribed voice commands.
"""
import re
from typing import Tuple, Dict, Any
from ..config import settings


def extract_intent(transcribed_text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Extract intent and parameters from the transcribed text.
    
    :param transcribed_text: The transcribed voice command
    :return: Tuple of (intent, parameters)
    """
    # Normalize the text
    text = transcribed_text.strip().lower()
    
    # Define patterns for common commands
    patterns = {
        "navigation": [
            (r"move (forward|backward|left|right) ([0-9.]+) (meters|feet|steps?)", 
             lambda m: {"direction": m.group(1), "distance": float(m.group(2)), "unit": m.group(3)}),
            (r"go to the (kitchen|bedroom|living room|bathroom|office)", 
             lambda m: {"location": m.group(1).replace(" ", "_")}),
            (r"go (forward|backward) ([0-9.]+) (meters|feet|steps?)", 
             lambda m: {"direction": m.group(1), "distance": float(m.group(2)), "unit": m.group(3)}),
            (r"turn (left|right) (?:by|) ?([0-9.]+)? degrees?", 
             lambda m: {"direction": m.group(1), "angle": float(m.group(2)) if m.group(2) else 90.0}),
            (r"navigate to coordinates? \[?([0-9.-]+), ?([0-9.-]+)\]?", 
             lambda m: {"x": float(m.group(1)), "y": float(m.group(2))}),
        ],
        "manipulation": [
            (r"(pick up|grasp|take) the (.+)", 
             lambda m: {"action": m.group(1), "object": m.group(2)}),
            (r"move the (.+) to the (.+)", 
             lambda m: {"object": m.group(1), "destination": m.group(2)}),
            (r"pick (up|down) the (.+)", 
             lambda m: {"action": f"pick_{m.group(1)}", "object": m.group(2)}),
        ],
        "perception": [
            (r"what do you see", 
             lambda m: {"task": "describe_scene"}),
            (r"find the (.+)", 
             lambda m: {"object": m.group(1)}),
            (r"look for (.+)", 
             lambda m: {"object": m.group(1)}),
            (r"detect (.+)", 
             lambda m: {"object": m.group(1)}),
        ],
        "stop": [
            (r"stop the robot?", 
             lambda m: {"action": "stop"}),
            (r"halt", 
             lambda m: {"action": "stop"}),
        ],
        "speed": [
            (r"set speed to ([0-9.]+)", 
             lambda m: {"speed": float(m.group(1))}),
            (r"speed up", 
             lambda m: {"adjustment": "increase"}),
            (r"slow down", 
             lambda m: {"adjustment": "decrease"}),
        ]
    }
    
    # Try to match the text against each pattern
    for intent, intent_patterns in patterns.items():
        for pattern, param_extractor in intent_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    parameters = param_extractor(match)
                    return intent, parameters
                except (ValueError, IndexError) as e:
                    # If parameter extraction fails, continue to the next pattern
                    continue
    
    # If no pattern matches, return a default intent
    return "unknown", {"raw_text": transcribed_text}


def extract_navigation_parameters(text: str) -> Dict[str, Any]:
    """
    Extract navigation-specific parameters from the text.
    
    :param text: The input text
    :return: Dictionary of navigation parameters
    """
    params = {}
    
    # Look for distance
    distance_match = re.search(r"([0-9.]+) (meters?|feet|steps?)", text)
    if distance_match:
        params["distance"] = float(distance_match.group(1))
        params["unit"] = distance_match.group(2)
    
    # Look for direction
    if "forward" in text:
        params["direction"] = "forward"
    elif "backward" in text or "back" in text:
        params["direction"] = "backward"
    elif "left" in text:
        params["direction"] = "left"
    elif "right" in text:
        params["direction"] = "right"
    
    # Look for angle (for turning)
    angle_match = re.search(r"([0-9.]+) degrees?", text)
    if angle_match:
        params["angle"] = float(angle_match.group(1))
    
    return params


def extract_manipulation_parameters(text: str) -> Dict[str, Any]:
    """
    Extract manipulation-specific parameters from the text.
    
    :param text: The input text
    :return: Dictionary of manipulation parameters
    """
    params = {}
    
    # Look for object to manipulate
    object_match = re.search(r"(?:the |)(.+?)(?: to | to the|,|\.|$)", text)
    if object_match:
        params["object"] = object_match.group(1).strip()
    
    # Look for destination (for move operations)
    to_match = re.search(r"to (?:the |)(.+?)(?:\.|$)", text)
    if to_match:
        params["destination"] = to_match.group(1).strip()
    
    return params


# Example usage:
if __name__ == "__main__":
    test_commands = [
        "Move forward 2 meters",
        "Go to the kitchen",
        "Turn left 90 degrees",
        "Pick up the red cube",
        "Find the blue ball",
        "Stop the robot"
    ]
    
    for command in test_commands:
        intent, params = extract_intent(command)
        print(f"Command: '{command}' -> Intent: '{intent}', Params: {params}")