"""
Service for creating and managing prompts for robotics applications using LLMs.
"""
from typing import Dict, Any, List
from enum import Enum


class RobotActionType(Enum):
    """Enumeration of common robot action types."""
    NAVIGATION = "navigation"
    MANIPULATION = "manipulation"
    PERCEPTION = "perception"
    INTERACTION = "interaction"
    OTHER = "other"


class PromptEngineeringService:
    """
    Service for creating and managing prompts for robotics applications using LLMs.
    """
    
    def __init__(self):
        """Initialize the prompt engineering service."""
        # Define action-specific prompt templates
        self.action_templates = {
            RobotActionType.NAVIGATION: self._get_navigation_template(),
            RobotActionType.MANIPULATION: self._get_manipulation_template(),
            RobotActionType.PERCEPTION: self._get_perception_template(),
            RobotActionType.INTERACTION: self._get_interaction_template(),
            RobotActionType.OTHER: self._get_general_template()
        }
    
    def generate_action_prompt(
        self, 
        intent: str, 
        parameters: Dict[str, Any], 
        robot_capabilities: List[str] = None,
        environment_context: Dict[str, Any] = None,
        previous_actions: List[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a prompt to convert a natural language command into robot actions.
        
        :param intent: The intent extracted from the command
        :param parameters: Parameters extracted from the command
        :param robot_capabilities: List of capabilities the robot supports
        :param environment_context: Information about the current environment
        :param previous_actions: List of previously executed actions
        :return: Formatted prompt string
        """
        # Determine the action type based on intent
        action_type = self._determine_action_type(intent)
        
        # Get the appropriate template
        template = self.action_templates.get(action_type, self.action_templates[RobotActionType.OTHER])
        
        # Format the prompt with the specific information
        prompt = template.format(
            intent=intent,
            parameters=parameters,
            robot_capabilities=robot_capabilities or [],
            environment_context=environment_context or {},
            previous_actions=previous_actions or []
        )
        
        return prompt
    
    def _determine_action_type(self, intent: str) -> RobotActionType:
        """
        Determine the action type based on the intent.
        
        :param intent: The intent string
        :return: Corresponding RobotActionType
        """
        intent_lower = intent.lower()
        
        navigation_keywords = ["navigate", "move", "go", "walk", "drive", "turn", "rotation", "position", "location"]
        manipulation_keywords = ["pick", "grasp", "take", "place", "put", "move object", "grab", "lift", "drop"]
        perception_keywords = ["see", "look", "find", "detect", "identify", "search", "locate", "scan", "perceive"]
        interaction_keywords = ["speak", "talk", "say", "tell", "greet", "interact", "communicate"]
        
        if any(keyword in intent_lower for keyword in navigation_keywords):
            return RobotActionType.NAVIGATION
        elif any(keyword in intent_lower for keyword in manipulation_keywords):
            return RobotActionType.MANIPULATION
        elif any(keyword in intent_lower for keyword in perception_keywords):
            return RobotActionType.PERCEPTION
        elif any(keyword in intent_lower for keyword in interaction_keywords):
            return RobotActionType.INTERACTION
        else:
            return RobotActionType.OTHER
    
    def _get_navigation_template(self) -> str:
        """
        Get the prompt template for navigation actions.
        
        :return: Navigation prompt template
        """
        return """
        Convert the following navigation command into specific robot actions:
        Intent: {intent}
        Parameters: {parameters}
        
        Robot Capabilities: {robot_capabilities}
        Environment Context: {environment_context}
        Previous Actions: {previous_actions}
        
        Provide a sequence of navigation actions with specific coordinates or directions.
        Each action should be a discrete, executable navigation task.
        
        Format the response as a JSON array of action steps, where each step has:
        - id: a unique identifier
        - action_type: "navigation"
        - parameters: specific parameters for the navigation action (e.g., {"x": 1.0, "y": 2.0, "theta": 0.0} for go-to-pose)
        - timeout: maximum time to wait for action completion in seconds
        - order: order of this step in the sequence
        
        Example response format:
        [
          {{
            "id": "step_1",
            "action_type": "navigation",
            "parameters": {{"x": 1.0, "y": 2.0, "theta": 0.0}},
            "timeout": 10,
            "order": 0
          }}
        ]
        
        Only respond with the JSON array, nothing else.
        """
    
    def _get_manipulation_template(self) -> str:
        """
        Get the prompt template for manipulation actions.
        
        :return: Manipulation prompt template
        """
        return """
        Convert the following manipulation command into specific robot actions:
        Intent: {intent}
        Parameters: {parameters}
        
        Robot Capabilities: {robot_capabilities}
        Environment Context: {environment_context}
        Previous Actions: {previous_actions}
        
        Provide a sequence of manipulation actions with specific object references and positions.
        Each action should be a discrete, executable manipulation task.
        
        Format the response as a JSON array of action steps, where each step has:
        - id: a unique identifier
        - action_type: "manipulation"
        - parameters: specific parameters for the manipulation action (e.g., {"object_id": "red_cube", "position": [0.5, 0.5, 0.2]})
        - timeout: maximum time to wait for action completion in seconds
        - order: order of this step in the sequence
        
        Example response format:
        [
          {{
            "id": "step_1",
            "action_type": "manipulation",
            "parameters": {{"object_id": "red_cube", "action": "approach"}},
            "timeout": 10,
            "order": 0
          }},
          {{
            "id": "step_2",
            "action_type": "manipulation",
            "parameters": {{"object_id": "red_cube", "action": "grasp"}},
            "timeout": 15,
            "order": 1
          }}
        ]
        
        Only respond with the JSON array, nothing else.
        """
    
    def _get_perception_template(self) -> str:
        """
        Get the prompt template for perception actions.
        
        :return: Perception prompt template
        """
        return """
        Convert the following perception command into specific robot actions:
        Intent: {intent}
        Parameters: {parameters}
        
        Robot Capabilities: {robot_capabilities}
        Environment Context: {environment_context}
        Previous Actions: {previous_actions}
        
        Provide a sequence of perception actions to detect or identify objects or features.
        Each action should be a discrete, executable perception task.
        
        Format the response as a JSON array of action steps, where each step has:
        - id: a unique identifier
        - action_type: "perception"
        - parameters: specific parameters for the perception action (e.g., {"object_type": "person", "search_area": "room_1"})
        - timeout: maximum time to wait for action completion in seconds
        - order: order of this step in the sequence
        
        Example response format:
        [
          {{
            "id": "step_1",
            "action_type": "perception",
            "parameters": {{"object_type": "person", "action": "detect"}},
            "timeout": 5,
            "order": 0
          }}
        ]
        
        Only respond with the JSON array, nothing else.
        """
    
    def _get_interaction_template(self) -> str:
        """
        Get the prompt template for interaction actions.
        
        :return: Interaction prompt template
        """
        return """
        Convert the following interaction command into specific robot actions:
        Intent: {intent}
        Parameters: {parameters}
        
        Robot Capabilities: {robot_capabilities}
        Environment Context: {environment_context}
        Previous Actions: {previous_actions}
        
        Provide a sequence of interaction actions to communicate with humans or systems.
        Each action should be a discrete, executable interaction task.
        
        Format the response as a JSON array of action steps, where each step has:
        - id: a unique identifier
        - action_type: "interaction"
        - parameters: specific parameters for the interaction action (e.g., {"text": "Hello, how can I help?", "recipient": "human_1"})
        - timeout: maximum time to wait for action completion in seconds
        - order: order of this step in the sequence
        
        Example response format:
        [
          {{
            "id": "step_1",
            "action_type": "interaction",
            "parameters": {{"text": "Hello, how can I help?", "action": "speak"}},
            "timeout": 5,
            "order": 0
          }}
        ]
        
        Only respond with the JSON array, nothing else.
        """
    
    def _get_general_template(self) -> str:
        """
        Get the general prompt template for other actions.
        
        :return: General prompt template
        """
        return """
        Convert the following command into specific robot actions:
        Intent: {intent}
        Parameters: {parameters}
        
        Robot Capabilities: {robot_capabilities}
        Environment Context: {environment_context}
        Previous Actions: {previous_actions}
        
        Provide a sequence of actions that accomplish the intent.
        Each action should be a discrete, executable robot task.
        
        Format the response as a JSON array of action steps, where each step has:
        - id: a unique identifier
        - action_type: appropriate action type (navigation, manipulation, perception, interaction, other)
        - parameters: specific parameters for the action
        - timeout: maximum time to wait for action completion in seconds
        - order: order of this step in the sequence
        
        Example response format:
        [
          {{
            "id": "step_1",
            "action_type": "navigation",
            "parameters": {{"x": 1.0, "y": 2.0}},
            "timeout": 10,
            "order": 0
          }}
        ]
        
        Only respond with the JSON array, nothing else.
        """
    
    def create_system_prompt(self) -> str:
        """
        Create a system prompt that guides the LLM's behavior for robotics applications.
        
        :return: System prompt string
        """
        return """
        You are an assistant that converts natural language commands into robot action sequences. 
        Your responses should be valid JSON arrays of action steps that follow the specified format. 
        Each action step should be a discrete, executable robot behavior that matches the robot's capabilities.
        
        Always consider safety when generating actions. Ensure actions are physically possible and appropriate 
        for the robot's current state and environment. If a command seems unsafe or impossible, generate 
        actions that would allow the robot to ask for clarification or move to a safe state.
        
        Focus on creating specific, executable actions rather than high-level plans.
        """
    
    def create_validation_prompt(self, action_sequence: List[Dict], intent: str) -> str:
        """
        Create a validation prompt to verify the correctness of an action sequence.
        
        :param action_sequence: The action sequence to validate
        :param intent: The original intent
        :return: Validation prompt string
        """
        return f"""
        Validate the following action sequence for the intent: {intent}
        
        Action Sequence:
        {action_sequence}
        
        Does this action sequence appropriately fulfill the given intent?
        Are the actions in the correct order?
        Are the parameters appropriate for the task?
        Would executing these actions accomplish the intended goal?
        
        Respond with "VALID" if the sequence is appropriate, or "INVALID" if there are issues.
        If INVALID, briefly explain what the issues are.
        """


class AdvancedPromptEngineeringService(PromptEngineeringService):
    """
    Advanced prompt engineering service with additional features.
    """
    
    def __init__(self):
        super().__init__()
        self.safety_prompts_enabled = True
        self.context_awareness_enabled = True
    
    def generate_context_aware_prompt(
        self,
        intent: str,
        parameters: Dict[str, Any],
        robot_state: Dict[str, Any],
        environment_map: Dict[str, Any],
        task_history: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a prompt that incorporates contextual information.
        
        :param intent: The intent extracted from the command
        :param parameters: Parameters extracted from the command
        :param robot_state: Current state of the robot
        :param environment_map: Map of the environment
        :param task_history: History of previously attempted tasks
        :return: Context-aware prompt string
        """
        # Build a comprehensive context string
        context_str = f"""
        Current Robot State:
        {robot_state}
        
        Environment Map:
        {environment_map}
        
        Task Execution History:
        {task_history}
        """
        
        # Use the base method but include the context
        base_prompt = self.generate_action_prompt(
            intent=intent,
            parameters=parameters,
            robot_capabilities=robot_state.get("capabilities", []),
            environment_context={"map": environment_map, "state": robot_state}
        )
        
        # Append context information
        full_prompt = f"{base_prompt}\n\n{context_str}"
        
        return full_prompt
    
    def generate_safety_aware_prompt(
        self,
        intent: str,
        parameters: Dict[str, Any],
        safety_constraints: List[str]
    ) -> str:
        """
        Generate a prompt that incorporates safety constraints.
        
        :param intent: The intent extracted from the command
        :param parameters: Parameters extracted from the command
        :param safety_constraints: List of safety constraints to consider
        :return: Safety-aware prompt string
        """
        # Create a base prompt
        base_prompt = self.generate_action_prompt(
            intent=intent,
            parameters=parameters
        )
        
        # Add safety constraints to the prompt
        safety_instruction = f"""
        
        SAFETY CONSTRAINTS:
        {safety_constraints}
        
        Ensure that all generated actions comply with the above safety constraints.
        If the requested action conflicts with safety constraints, generate actions 
        that achieve the goal in a safe manner or request clarification.
        """
        
        full_prompt = f"{base_prompt}{safety_instruction}"
        
        return full_prompt


# Example usage:
if __name__ == "__main__":
    # Create the prompt engineering service
    prompt_service = PromptEngineeringService()
    
    # Example: Generate a prompt for a navigation command
    intent = "navigation"
    parameters = {"target_location": "kitchen", "waypoint_1": {"x": 1.0, "y": 2.0}}
    
    prompt = prompt_service.generate_action_prompt(
        intent=intent,
        parameters=parameters,
        robot_capabilities=["navigation", "obstacle_avoidance"],
        environment_context={"map": "home_layout_v2", "obstacles": ["table", "chair"]}
    )
    
    print("Generated prompt:")
    print(prompt)
    
    # Create the system prompt
    system_prompt = prompt_service.create_system_prompt()
    print("\nSystem prompt:")
    print(system_prompt)
    
    # Example of using the advanced service
    advanced_service = AdvancedPromptEngineeringService()
    safety_prompt = advanced_service.generate_safety_aware_prompt(
        intent="navigation",
        parameters={"x": 5.0, "y": 5.0},
        safety_constraints=["avoid stairs", "maintain 1m distance from humans", "don't enter restricted areas"]
    )
    
    print("\nSafety-aware prompt:")
    print(safety_prompt)