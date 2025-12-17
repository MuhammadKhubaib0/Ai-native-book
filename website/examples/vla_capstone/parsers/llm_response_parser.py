"""
Parser for converting LLM responses into structured action sequences.
"""
import json
import re
from typing import Dict, List, Any, Optional, Union
from ..models.action_step import ActionStep, ActionType


class LLMResponseParseError(Exception):
    """Custom exception for LLM response parsing errors."""
    pass


class LLMResponseParser:
    """
    Parser for converting LLM responses into structured action sequences.
    """
    
    def __init__(self):
        """Initialize the parser."""
        self.parsing_strategies = {
            "json_array": self._parse_json_array,
            "json_object": self._parse_json_object,
            "text_descriptions": self._parse_text_descriptions,
            "mixed_format": self._parse_mixed_format
        }
    
    def parse_response(self, llm_response: str) -> List[Dict[str, Any]]:
        """
        Parse an LLM response into a list of action dictionaries.
        
        :param llm_response: Raw response from the LLM
        :return: List of action dictionaries
        """
        # Determine the best parsing strategy
        strategy = self._select_parsing_strategy(llm_response)
        
        # Apply the chosen strategy
        try:
            parsed_actions = self.parsing_strategies[strategy](llm_response)
            return self._validate_and_normalize_actions(parsed_actions)
        except Exception as e:
            raise LLMResponseParseError(f"Failed to parse LLM response using {strategy} strategy: {str(e)}")
    
    def _select_parsing_strategy(self, response: str) -> str:
        """
        Select the most appropriate parsing strategy based on the response content.
        
        :param response: LLM response string
        :return: Name of the parsing strategy to use
        """
        response_lower = response.lower()
        
        # Check for JSON array format
        if response.strip().startswith('[') or '"sequence"' in response_lower:
            return "json_array"
        
        # Check for JSON object format
        if response.strip().startswith('{') and ('actions' in response_lower or 'steps' in response_lower):
            return "json_object"
        
        # Check for text descriptions (no clear JSON)
        if not (response.strip().startswith('{') or response.strip().startswith('[')):
            # Check if it describes actions in natural language
            action_keywords = ["move", "navigate", "go", "pick", "grasp", "turn", "look", "detect"]
            if any(keyword in response_lower for keyword in action_keywords):
                return "text_descriptions"
        
        # Default to mixed format which tries multiple approaches
        return "mixed_format"
    
    def _parse_json_array(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse a JSON array of action steps.
        
        :param response: LLM response containing JSON array
        :return: List of action dictionaries
        """
        # Extract JSON if it's embedded in text
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response
        
        try:
            actions = json.loads(json_str)
            if not isinstance(actions, list):
                raise LLMResponseParseError("Expected JSON array of actions")
            return actions
        except json.JSONDecodeError as e:
            raise LLMResponseParseError(f"Invalid JSON: {str(e)}")
    
    def _parse_json_object(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse a JSON object that contains an array of actions.
        
        :param response: LLM response containing JSON object
        :return: List of action dictionaries
        """
        # Extract JSON if it's embedded in text
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response
        
        try:
            data = json.loads(json_str)
            # Look for common action array field names
            for field_name in ['actions', 'steps', 'action_sequence', 'sequence', 'plan']:
                if field_name in data and isinstance(data[field_name], list):
                    return data[field_name]
            
            # If no standard field found, return the entire object as an action
            return [data]
        except json.JSONDecodeError as e:
            raise LLMResponseParseError(f"Invalid JSON: {str(e)}")
    
    def _parse_text_descriptions(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse action descriptions from natural language text.
        
        :param response: LLM response containing text descriptions
        :return: List of action dictionaries
        """
        # This is a simplified approach - in practice, you'd use more sophisticated NLP
        lines = response.split('\n')
        
        actions = []
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines and common non-action lines
            if not line or line.startswith('#') or '```' in line:
                continue
            
            # Look for action-like patterns in the line
            if any(action_word in line.lower() for action_word in 
                   ['navigate', 'move', 'go', 'pick', 'grasp', 'turn', 'look', 'detect']):
                
                # Extract action type and parameters using simple pattern matching
                action_dict = self._extract_action_from_text(line, i)
                if action_dict:
                    actions.append(action_dict)
        
        return actions
    
    def _extract_action_from_text(self, text: str, order: int) -> Optional[Dict[str, Any]]:
        """
        Extract action information from a text description.
        
        :param text: Text description of an action
        :param order: Order of this action in the sequence
        :return: Action dictionary or None if extraction fails
        """
        # Normalize the text
        text_lower = text.lower()
        
        # Define patterns for extracting action information
        # This is a simplified implementation - in practice, you'd use more sophisticated NLP
        action_types = {
            "navigation": ["navigate", "move", "go", "drive", "walk", "turn", "rotation"],
            "manipulation": ["pick", "grasp", "take", "place", "put", "lift", "drop"],
            "perception": ["see", "look", "find", "detect", "identify", "scan"],
            "interaction": ["say", "speak", "talk", "greet", "communicate"]
        }
        
        # Determine action type
        action_type = "other"
        for type_name, keywords in action_types.items():
            if any(keyword in text_lower for keyword in keywords):
                action_type = type_name
                break
        
        # Extract parameters using simple pattern matching
        parameters = {}
        
        # Extract coordinates (for navigation)
        coord_matches = re.findall(r'(-?\d+\.?\d*)', text)
        if len(coord_matches) >= 2 and action_type == "navigation":
            parameters["x"] = float(coord_matches[0])
            parameters["y"] = float(coord_matches[1])
            if len(coord_matches) >= 3:
                parameters["theta"] = float(coord_matches[2])
        
        # Extract object information (for manipulation/perception)
        object_matches = re.findall(r'(?:to|the|a|an)\s+([a-zA-Z][a-zA-Z0-9_\-]*)', text)
        if object_matches and action_type in ["manipulation", "perception"]:
            parameters["object"] = object_matches[0]
        
        # Create the action dictionary
        action_dict = {
            "id": f"extracted_{order}",
            "action_type": action_type,
            "parameters": parameters,
            "timeout": 10,  # Default timeout
            "order": order
        }
        
        return action_dict
    
    def _parse_mixed_format(self, response: str) -> List[Dict[str, Any]]:
        """
        Try multiple parsing strategies to handle mixed formats.
        
        :param response: LLM response in mixed format
        :return: List of action dictionaries
        """
        strategies_to_try = ["json_array", "json_object", "text_descriptions"]
        
        for strategy in strategies_to_try:
            try:
                result = self.parsing_strategies[strategy](response)
                if result:  # If we got a valid result, return it
                    return result
            except LLMResponseParseError:
                continue  # Try the next strategy
        
        # If all strategies failed, raise an error
        raise LLMResponseParseError("Could not parse LLM response with any strategy")
    
    def _validate_and_normalize_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and normalize action dictionaries.
        
        :param actions: List of action dictionaries to validate
        :return: Validated and normalized list of action dictionaries
        """
        validated_actions = []
        
        for i, action in enumerate(actions):
            # Ensure required fields exist
            normalized_action = {
                "id": action.get("id", f"action_{i}"),
                "action_type": self._normalize_action_type(action.get("action_type", "other")),
                "parameters": action.get("parameters", {}),
                "timeout": int(action.get("timeout", 10)),
                "order": int(action.get("order", i))
            }
            
            # Validate action type
            try:
                ActionType[normalized_action["action_type"].upper()]
            except KeyError:
                # If the action type is not in our enum, default to OTHER
                normalized_action["action_type"] = "other"
            
            validated_actions.append(normalized_action)
        
        # Sort by order
        validated_actions.sort(key=lambda x: x["order"])
        
        return validated_actions
    
    def _normalize_action_type(self, action_type: str) -> str:
        """
        Normalize action type strings to a consistent format.
        
        :param action_type: Raw action type string
        :return: Normalized action type string
        """
        if not action_type:
            return "other"
        
        # Convert to uppercase and check against our ActionType enum
        action_type_upper = action_type.upper()
        
        # Handle special cases and aliases
        normalization_map = {
            "NAVIGATE": "NAVIGATION",
            "MOVE": "NAVIGATION",
            "GO": "NAVIGATION",
            "PICK_UP": "MANIPULATION",
            "GRAB": "MANIPULATION",
            "TAKE": "MANIPULATION",
            "SEE": "PERCEPTION",
            "LOOK": "PERCEPTION",
            "DETECT": "PERCEPTION",
            "TALK": "INTERACTION",
            "SPEAK": "INTERACTION",
            "COMMUNICATE": "INTERACTION"
        }
        
        normalized = normalization_map.get(action_type_upper, action_type_upper)
        
        # Validate against the enum
        try:
            ActionType[normalized]
        except KeyError:
            # If the normalized type is still invalid, return "OTHER"
            return "other"
        
        return normalized.lower()


class RobustLLMResponseParser(LLMResponseParser):
    """
    A more robust parser with additional error recovery and validation features.
    """
    
    def __init__(self):
        super().__init__()
        self.max_action_count = 50  # Maximum number of actions to parse
        self.max_param_length = 100  # Maximum length of parameter values
    
    def parse_response_with_validation(self, llm_response: str, expected_actions: int = None) -> List[Dict[str, Any]]:
        """
        Parse an LLM response with additional validation.
        
        :param llm_response: Raw response from the LLM
        :param expected_actions: Expected number of actions (optional)
        :return: List of validated action dictionaries
        """
        # First, parse the response
        parsed_actions = self.parse_response(llm_response)
        
        # Apply additional validation
        validated_actions = self._additional_validation(parsed_actions, expected_actions)
        
        return validated_actions
    
    def _additional_validation(
        self, 
        actions: List[Dict[str, Any]], 
        expected_actions: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        Apply additional validation rules.
        
        :param actions: List of action dictionaries to validate
        :param expected_actions: Expected number of actions (optional)
        :return: Validated list of action dictionaries
        """
        if len(actions) > self.max_action_count:
            raise LLMResponseParseError(f"Too many actions ({len(actions)}) in response, max allowed is {self.max_action_count}")
        
        # If expected number of actions is provided, warn if it doesn't match (but don't fail)
        if expected_actions is not None and len(actions) != expected_actions:
            print(f"Warning: Expected {expected_actions} actions, but found {len(actions)}")
        
        validated_actions = []
        for action in actions:
            # Validate parameter lengths
            validated_params = {}
            for key, value in action["parameters"].items():
                str_value = str(value)
                if len(str_value) > self.max_param_length:
                    # Truncate long parameter values
                    validated_params[key] = str_value[:self.max_param_length] + "..."
                else:
                    validated_params[key] = value
            
            action["parameters"] = validated_params
            validated_actions.append(action)
        
        # Check for reasonable timeout values
        for action in validated_actions:
            if action["timeout"] <= 0 or action["timeout"] > 3600:  # More than 1 hour seems unreasonable
                print(f"Warning: Unreasonable timeout {action['timeout']} for action {action['id']}, adjusting to 10 seconds")
                action["timeout"] = 10
                
        return validated_actions
    
    def _extract_action_from_text(self, text: str, order: int) -> Optional[Dict[str, Any]]:
        """
        Enhanced text extraction with better pattern recognition.
        
        :param text: Text description of an action
        :param order: Order of this action in the sequence
        :return: Action dictionary or None if extraction fails
        """
        # Base implementation from parent class
        action_dict = super()._extract_action_from_text(text, order)
        
        if action_dict:
            # Enhance the action with additional properties
            self._enhance_action_with_context(action_dict, text)
        
        return action_dict
    
    def _enhance_action_with_context(self, action_dict: Dict[str, Any], text: str):
        """
        Enhance an action with context derived from the original text.
        
        :param action_dict: Action dictionary to enhance
        :param text: Original text describing the action
        """
        # Add context about required precision based on the action description
        high_precision_indicators = ["precisely", "carefully", "gently", "slowly", "accurately"]
        if any(indicator in text.lower() for indicator in high_precision_indicators):
            action_dict["parameters"]["precision_required"] = True
            
        # Add safety context
        safety_related_indicators = ["carefully", "safely", "slowly", "stop", "avoid", "be careful"]
        if any(indicator in text.lower() for indicator in safety_related_indicators):
            action_dict["parameters"]["safety_important"] = True
            
        # Add timing context
        time_related_indicators = ["immediately", "now", "quickly", "fast", "slowly", "carefully", "pause"]
        if any(indicator in text.lower() for indicator in time_related_indicators):
            action_dict["parameters"]["timing_sensitive"] = True


# Example usage:
if __name__ == "__main__":
    # Create a parser
    parser = LLMResponseParser()
    
    # Example 1: JSON array response
    json_response = '''
    [
      {
        "id": "step_1",
        "action_type": "navigation",
        "parameters": {"x": 1.0, "y": 2.0, "theta": 0.0},
        "timeout": 10,
        "order": 0
      },
      {
        "id": "step_2",
        "action_type": "perception",
        "parameters": {"object_type": "cup", "action": "detect"},
        "timeout": 5,
        "order": 1
      }
    ]
    '''
    
    try:
        parsed = parser.parse_response(json_response)
        print("Parsed JSON response:")
        for action in parsed:
            print(f"  {action['action_type']}: {action['parameters']}")
    except LLMResponseParseError as e:
        print(f"Parsing failed: {e}")
    
    # Example 2: Text description
    text_response = '''
    First, navigate to the kitchen. Go to coordinates (1.5, 2.0).
    Then, look for a red cup on the table.
    Finally, grasp the cup carefully.
    '''
    
    try:
        text_parsed = parser.parse_response(text_response)
        print("\nParsed text response:")
        for action in text_parsed:
            print(f"  {action['action_type']}: {action['parameters']}")
    except LLMResponseParseError as e:
        print(f"Text parsing failed: {e}")
    
    # Example with robust parser
    robust_parser = RobustLLMResponseParser()
    
    # Parse with validation
    try:
        validated = robust_parser.parse_response_with_validation(json_response, expected_actions=2)
        print("\nValidated response:")
        for action in validated:
            print(f"  {action['action_type']}: {action['parameters']}")
    except LLMResponseParseError as e:
        print(f"Validation failed: {e}")