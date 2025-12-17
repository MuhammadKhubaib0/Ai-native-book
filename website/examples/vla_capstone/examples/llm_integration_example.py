"""
Python integration example for LLM (Large Language Model) integration in the VLA Capstone project.
Demonstrates how to integrate LLM capabilities for action planning and task decomposition.
"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Import VLA system components
from ..models.action_step import ActionStep, ActionType
from ..models.action_sequence import ActionSequence, ActionSequenceStatus
from ..models.voice_command import VoiceCommand
from ..models.multimodal_input import MultimodalInput
from ..models.vla_system_state import VLASystemState
from ..services.llm_service import LLMService, LLMConfig
from ..services.prompt_engineering import PromptEngineeringService
from ..services.task_decomposition import TaskDecompositionService
from ..services.action_sequencer import ActionSequencer
from ..services.action_validator import ActionValidator
from ..config import settings
from ..validation.action_validation import validate_action_sequence


class LLMIntegrationExample:
    """
    Example implementation of LLM integration for action planning and task decomposition.
    """
    
    def __init__(self):
        """Initialize the LLM integration example."""
        # Initialize LLM service
        self.llm_config = LLMConfig(
            api_key=settings.openai_api_key,
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        self.llm_service = LLMService(self.llm_config)
        
        # Initialize supporting services
        self.prompt_engineering = PromptEngineeringService()
        self.task_decomposer = TaskDecompositionService()
        self.action_sequencer = ActionSequencer()
        self.action_validator = ActionValidator()
        
        # Robot capabilities for action generation
        self.robot_capabilities = [
            "navigation",
            "manipulation", 
            "perception",
            "interaction",
            "grasping",
            "object_transport",
            "spatial_reasoning",
            "multi_step_planning"
        ]
        
        # Environment context
        self.environment_context = {
            "layout": "structured_home_office",
            "robot_position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "available_objects": [
                {"class": "cup", "id": "cup_1", "position": {"x": 1.0, "y": 0.5}, "color": "red"},
                {"class": "box", "id": "box_1", "position": {"x": 1.5, "y": -0.5}, "color": "blue"},
                {"class": "desk", "id": "desk_1", "position": {"x": 2.0, "y": 0.0}, "type": "furniture"},
                {"class": "chair", "id": "chair_1", "position": {"x": 1.8, "y": 0.2}, "type": "furniture"}
            ],
            "navigation_targets": ["kitchen", "bedroom", "office", "living_room"]
        }
    
    async def generate_simple_navigation_action(self, target_location: str) -> Optional[ActionSequence]:
        """
        Generate a simple navigation action sequence.
        
        :param target_location: Target location for navigation
        :return: Action sequence or None if generation failed
        """
        print(f"Generating navigation action to {target_location}...")
        
        try:
            # Create a voice command representing the navigation request
            voice_command = VoiceCommand(
                id=f"nav_cmd_{uuid.uuid4()}",
                transcribed_text=f"Go to the {target_location}",
                intent="navigation",
                parameters={"target_location": target_location},
                confidence=0.9,
                timestamp=datetime.now()
            )
            
            # Generate action sequence using LLM
            action_steps = await self.llm_service.generate_action_sequence(
                intent="navigation",
                parameters={"target_location": target_location},
                context={
                    "robot_capabilities": self.robot_capabilities,
                    "environment_context": self.environment_context
                }
            )
            
            if not action_steps:
                print("LLM did not generate any action steps")
                return None
            
            # Create action sequence
            action_sequence = ActionSequence(
                id=f"nav_seq_{uuid.uuid4()}",
                voice_command_id=voice_command.id,
                sequence=action_steps,
                description=f"Navigation action to {target_location}",
                status=ActionSequenceStatus.PENDING
            )
            
            # Validate the action sequence
            validation_result = validate_action_sequence(action_sequence)
            if validation_result.errors:
                print(f"Generated action sequence has validation issues: {validation_result.errors}")
                # In a real implementation, we might try to fix validation issues
                # For this example, we'll return the sequence as is
            
            return action_sequence
            
        except Exception as e:
            print(f"Error generating navigation action: {str(e)}")
            return None
    
    async def generate_complex_manipulation_action(self, command: str) -> Optional[ActionSequence]:
        """
        Generate a complex manipulation action sequence.
        
        :param command: Natural language command for manipulation
        :return: Action sequence or None if generation failed
        """
        print(f"Generating manipulation action for command: '{command}'")
        
        try:
            # Decompose the complex command into subtasks
            subtasks = await self.task_decomposer.decompose_task(
                command=command,
                robot_capabilities=self.robot_capabilities,
                environment_context=self.environment_context
            )
            
            # Generate action steps for each subtask using LLM
            all_action_steps = []
            for i, subtask in enumerate(subtasks):
                # Generate actions for this subtask
                subtask_actions = await self.llm_service.generate_action_sequence(
                    intent=subtask.description,
                    parameters={"subtask": subtask.to_dict()},
                    context={
                        "robot_capabilities": self.robot_capabilities,
                        "environment_context": self.environment_context
                    }
                )
                
                if subtask_actions:
                    all_action_steps.extend(subtask_actions)
            
            if not all_action_steps:
                print("LLM did not generate any actions for the manipulation command")
                return None
            
            # Sequence the actions
            action_sequence = self.action_sequencer.sequence_actions(
                actions=[
                    {
                        "id": step.id,
                        "action_type": step.action_type,
                        "parameters": step.parameters,
                        "timeout": step.timeout,
                        "order": step.order
                    }
                    for step in all_action_steps
                ]
            )
            
            # Validate the action sequence
            validation_result = validate_action_sequence(action_sequence)
            if validation_result.errors:
                print(f"Generated action sequence has validation issues: {validation_result.errors}")
            
            action_sequence.description = f"Complex manipulation for: {command}"
            
            return action_sequence
            
        except Exception as e:
            print(f"Error generating manipulation action: {str(e)}")
            return None
    
    async def generate_multimodal_action_sequence(self, multimodal_input: MultimodalInput) -> Optional[ActionSequence]:
        """
        Generate an action sequence from multimodal input using LLM.
        
        :param multimodal_input: Multimodal input with vision and language
        :return: Action sequence or None if generation failed
        """
        print(f"Generating action sequence from multimodal input...")
        
        try:
            # Create a context that combines vision and language information
            multimodal_context = {
                "voice_command": multimodal_input.voice_input_id,
                "visual_objects": multimodal_input.visual_data.get("objects", []) if multimodal_input.visual_data else [],
                "robot_capabilities": self.robot_capabilities,
                "environment_context": self.environment_context
            }
            
            # Use LLM to generate action sequence based on multimodal context
            action_steps = await self.llm_service.generate_action_sequence(
                intent="multimodal_command_interpretation",
                parameters={"multimodal_input": multimodal_input.dict()},
                context=multimodal_context
            )
            
            if not action_steps:
                print("LLM did not generate any action steps for multimodal input")
                return None
            
            # Create action sequence
            action_sequence = ActionSequence(
                id=f"mm_seq_{uuid.uuid4()}",
                voice_command_id=multimodal_input.voice_input_id or f"mm_cmd_{uuid.uuid4()}",
                sequence=action_steps,
                description="Action sequence from multimodal input",
                status=ActionSequenceStatus.PENDING
            )
            
            # Validate the sequence
            validation_result = validate_action_sequence(action_sequence)
            if validation_result.errors:
                print(f"Generated action sequence has validation issues: {validation_result.errors}")
            
            return action_sequence
            
        except Exception as e:
            print(f"Error generating multimodal action sequence: {str(e)}")
            return None
    
    async def demonstrate_task_decomposition(self) -> Dict[str, Any]:
        """
        Demonstrate the task decomposition capabilities of the LLM integration.
        
        :return: Dictionary with decomposition results
        """
        print("Demonstrating Task Decomposition with LLM Integration")
        print("-" * 60)
        
        # Complex command examples
        complex_commands = [
            "Go to the kitchen, find the red cup on the table, pick it up, and bring it to me",
            "Move to the office, get the book from the shelf, and place it on the desk",
            "Navigate to the living room, locate the remote control, grasp it, and return to the charging station"
        ]
        
        results = {
            "commands": [],
            "decomposition_results": [],
            "total_subtasks": 0
        }
        
        for i, command in enumerate(complex_commands):
            print(f"\nCommand {i+1}: '{command}'")
            
            # Decompose the task
            subtasks = await self.task_decomposer.decompose_task(
                command=command,
                robot_capabilities=self.robot_capabilities,
                environment_context=self.environment_context
            )
            
            print(f"  Decomposed into {len(subtasks)} subtasks:")
            for j, subtask in enumerate(subtasks):
                print(f"    {j+1}. {subtask.description}")
                print(f"         Type: {subtask.task_type}")
                print(f"         Parameters: {subtask.parameters}")
            
            results["commands"].append(command)
            results["decomposition_results"].append({
                "command": command,
                "subtasks": [subtask.to_dict() for subtask in subtasks],
                "count": len(subtasks)
            })
            results["total_subtasks"] += len(subtasks)
        
        print(f"\nTask Decomposition Summary:")
        print(f"  Total commands processed: {len(complex_commands)}")
        print(f"  Total subtasks generated: {results['total_subtasks']}")
        print(f"  Average subtasks per command: {results['total_subtasks']/len(complex_commands):.1f}")
        
        return results
    
    async def demonstrate_prompt_engineering(self):
        """
        Demonstrate prompt engineering capabilities for different types of commands.
        """
        print("\nDemonstrating Prompt Engineering for Different Command Types")
        print("-" * 60)
        
        # Different command types to demonstrate
        command_sets = [
            {
                "type": "navigation",
                "commands": [
                    "Move forward 2 meters",
                    "Go to the kitchen", 
                    "Turn left and proceed to the door"
                ]
            },
            {
                "type": "manipulation",
                "commands": [
                    "Pick up the red cup",
                    "Grasp the pen and place it in the drawer",
                    "Take the book and put it on the shelf"
                ]
            },
            {
                "type": "perception",
                "commands": [
                    "Find the blue ball in the room",
                    "Detect all chairs in the office",
                    "Identify objects on the table"
                ]
            }
        ]
        
        for command_set in command_sets:
            print(f"\n{command_set['type'].title()} Commands:")
            
            for command in command_set["commands"]:
                print(f"  '{command}' -> ", end="")
                
                # Generate appropriate prompt for the command
                prompt = self.prompt_engineering.generate_action_generation_prompt(
                    intent=command_set["type"],
                    parameters={"command": command},
                    robot_capabilities=self.robot_capabilities,
                    environment_context=self.environment_context
                )
                
                # In a real implementation, we would process this prompt with the LLM
                # For this demo, we'll just show how the prompt would be structured
                
                print(f"Prompt generated (length: {len(prompt)} chars)")
                
                # Show first 100 characters of the prompt
                print(f"    Prompt preview: {prompt[:100]}...")
    
    async def run_complete_integration_example(self):
        """
        Run a complete integration example demonstrating all LLM capabilities.
        """
        print("VLA Capstone - Complete LLM Integration Example")
        print("=" * 80)
        
        try:
            # 1. Simple navigation example
            print("\n[1] Simple Navigation Example:")
            nav_sequence = await self.generate_simple_navigation_action("kitchen")
            if nav_sequence:
                print(f"  Generated navigation sequence with {len(nav_sequence.sequence)} steps:")
                for i, step in enumerate(nav_sequence.sequence):
                    print(f"    {i+1}. {step.action_type.value}: {step.parameters}")
            else:
                print("  Failed to generate navigation sequence")
            
            # 2. Complex manipulation example
            print("\n[2] Complex Manipulation Example:")
            manipulation_command = "Go to the table, find the red cup, and bring it to me"
            manipulation_sequence = await self.generate_complex_manipulation_action(manipulation_command)
            if manipulation_sequence:
                print(f"  Generated manipulation sequence with {len(manipulation_sequence.sequence)} steps:")
                for i, step in enumerate(manipulation_sequence.sequence):
                    print(f"    {i+1}. {step.action_type.value}: {step.parameters}")
            else:
                print("  Failed to generate manipulation sequence")
            
            # 3. Task decomposition example
            print("\n[3] Task Decomposition Example:")
            decomposition_results = await self.demonstrate_task_decomposition()
            
            # 4. Prompt engineering example
            print("\n[4] Prompt Engineering Example:")
            await self.demonstrate_prompt_engineering()
            
            # 5. Multimodal integration example
            print("\n[5] Multimodal Integration Example:")
            multimodal_input = MultimodalInput(
                id="mm_input_123",
                visual_data={
                    "objects": [
                        {
                            "class": "cup",
                            "bbox": [0.2, 0.3, 0.4, 0.5],
                            "confidence": 0.9,
                            "position": [1.0, 0.5, 0.0]
                        }
                    ]
                },
                sensor_data=None,
                voice_input_id="Pick up the red cup on the table",
                confidence=0.85,
                timestamp=datetime.now()
            )
            
            mm_sequence = await self.generate_multimodal_action_sequence(multimodal_input)
            if mm_sequence:
                print(f"  Generated multimodal sequence with {len(mm_sequence.sequence)} steps:")
                for i, step in enumerate(mm_sequence.sequence):
                    print(f"    {i+1}. {step.action_type.value}: {step.parameters}")
            else:
                print("  Failed to generate multimodal sequence")
            
            print("\n" + "=" * 80)
            print("LLM Integration Example Completed Successfully!")
            
        except Exception as e:
            print(f"\nError in LLM integration example: {str(e)}")
            import traceback
            traceback.print_exc()


class AdvancedLLMIntegrationExample(LLMIntegrationExample):
    """
    Advanced LLM integration example with additional capabilities.
    """
    
    def __init__(self):
        super().__init__()
        
        # Additional advanced capabilities
        self.enable_chain_of_thought = True
        self.enable_context_learning = True
        self.enable_multi_agent_coordination = False
        self.response_format_preference = "json"  # Options: "json", "xml", "text"
    
    async def generate_chain_of_thought_action_sequence(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Generate an action sequence using chain-of-thought reasoning.
        
        :param command: Natural language command
        :return: Dictionary with reasoning steps and action sequence
        """
        print(f"Generating action sequence using chain-of-thought for: '{command}'")
        
        try:
            # Create a chain-of-thought prompt
            cot_prompt = f"""
            Think step-by-step to break down the command and generate appropriate actions:
            
            Command: "{command}"
            
            Step 1: What is the overall goal?
            Step 2: What objects or locations are involved?
            Step 3: What sequence of actions would achieve this goal?
            Step 4: How should the robot execute each action?
            
            Finally, provide the action sequence in JSON format:
            {{
              "reasoning": [
                {{"step": 1, "thought": "...", "conclusion": "..."}},
                ...
              ],
              "action_sequence": [
                {{
                  "id": "...",
                  "action_type": "navigation|manipulation|perception|other",
                  "parameters": {{"x": 1.0, "y": 1.0, "action": "grasp", ...}},
                  "timeout": 10,
                  "order": 0
                }}
              ]
            }}
            """
            
            # In a real implementation, we would call the LLM with this prompt
            # For this example, we'll simulate the response
            
            simulated_response = {
                "reasoning": [
                    {"step": 1, "thought": "The goal is to bring a cup to the user", "conclusion": "Need to find, grasp, and transport a cup"},
                    {"step": 2, "thought": "The key object is a cup, likely in the environment", "conclusion": "Need to perceive to locate cup"},
                    {"step": 3, "thought": "Action sequence: navigate to cup, perceive cup, grasp cup, navigate to user, place cup", "conclusion": "Five-step sequence"},
                    {"step": 4, "thought": "Each step has specific parameters for robot execution", "conclusion": "Detailed action parameters required"}
                ],
                "action_sequence": [
                    {
                        "id": "cot_step_1",
                        "action_type": "navigation",
                        "parameters": {"target_location": "area_with_cups", "approach": "direct"},
                        "timeout": 15,
                        "order": 0
                    },
                    {
                        "id": "cot_step_2",
                        "action_type": "perception",
                        "parameters": {"action": "detect", "object_type": "cup"},
                        "timeout": 5,
                        "order": 1
                    },
                    {
                        "id": "cot_step_3",
                        "action_type": "manipulation",
                        "parameters": {"action": "grasp", "object_id": "detected_cup"},
                        "timeout": 10,
                        "order": 2
                    },
                    {
                        "id": "cot_step_4",
                        "action_type": "navigation", 
                        "parameters": {"target_location": "user_position", "approach": "safe"},
                        "timeout": 20,
                        "order": 3
                    },
                    {
                        "id": "cot_step_5",
                        "action_type": "manipulation",
                        "parameters": {"action": "place", "object_id": "held_cup"},
                        "timeout": 8,
                        "order": 4
                    }
                ]
            }
            
            # Validate the generated action sequence
            action_steps = [
                ActionStep(
                    id=item["id"],
                    action_sequence_id="cot_seq_123",
                    action_type=ActionType[item["action_type"].upper()],
                    parameters=item["parameters"],
                    timeout=item["timeout"],
                    order=item["order"]
                )
                for item in simulated_response["action_sequence"]
            ]
            
            action_sequence = ActionSequence(
                id="cot_seq_123",
                voice_command_id="cot_cmd_123",
                sequence=action_steps,
                description=f"Chain-of-thought for: {command}",
                status=ActionSequenceStatus.PENDING
            )
            
            validation_result = validate_action_sequence(action_sequence)
            if validation_result.errors:
                print(f"Chain-of-thought sequence validation issues: {validation_result.errors}")
            
            return {
                "command": command,
                "reasoning_steps": simulated_response["reasoning"],
                "action_sequence": action_sequence,
                "confidence": 0.85  # Simulated confidence
            }
            
        except Exception as e:
            print(f"Error in chain-of-thought generation: {str(e)}")
            return None
    
    async def generate_context_aware_action_sequence(self, command: str, previous_actions: List[ActionStep] = None) -> Optional[ActionSequence]:
        """
        Generate an action sequence considering previous actions and context.
        
        :param command: Natural language command
        :param previous_actions: List of previously executed actions
        :return: Context-aware action sequence or None
        """
        print(f"Generating context-aware action for: '{command}'")
        
        try:
            # Create context from previous actions
            context = {
                "robot_capabilities": self.robot_capabilities,
                "environment_context": self.environment_context,
                "previous_actions": [action.dict() for action in previous_actions] if previous_actions else [],
                "current_state": {
                    "robot_position": self.environment_context["robot_position"],
                    "held_object": None,  # Would come from actual robot state
                    "last_action_outcome": "success" if previous_actions else "none"
                }
            }
            
            # Use LLM to generate action considering context
            action_steps = await self.llm_service.generate_action_sequence(
                intent="context_aware_command",
                parameters={"command": command},
                context=context
            )
            
            if not action_steps:
                print("LLM did not generate any actions with context")
                return None
            
            # Create action sequence
            action_sequence = ActionSequence(
                id=f"context_seq_{uuid.uuid4()}",
                voice_command_id=f"context_cmd_{uuid.uuid4()}",
                sequence=action_steps,
                description=f"Context-aware action for: {command}",
                status=ActionSequenceStatus.PENDING
            )
            
            validation_result = validate_action_sequence(action_sequence)
            if validation_result.errors:
                print(f"Context-aware sequence validation issues: {validation_result.errors}")
            
            return action_sequence
            
        except Exception as e:
            print(f"Error in context-aware generation: {str(e)}")
            return None
    
    async def run_advanced_integration_example(self):
        """
        Run the advanced integration example with chain-of-thought and context awareness.
        """
        print("VLA Capstone - Advanced LLM Integration Example")
        print("=" * 80)
        
        try:
            # 1. Chain of thought example
            print("\n[1] Chain of Thought Reasoning Example:")
            cot_result = await self.generate_chain_of_thought_action_sequence(
                "I spilled my drink. Can you get me a cloth to clean it up?"
            )
            
            if cot_result:
                print(f"  Generated {len(cot_result['action_sequence'].sequence)}-step sequence with reasoning:")
                for i, thought in enumerate(cot_result['reasoning_steps']):
                    print(f"    Reasoning {i+1}: {thought['thought']} -> {thought['conclusion']}")
                
                print("  Action Steps:")
                for i, step in enumerate(cot_result['action_sequence'].sequence):
                    print(f"    {i+1}. {step.action_type.value}: {step.parameters}")
            else:
                print("  Chain of thought generation failed")
            
            # 2. Context-aware example
            print("\n[2] Context-Aware Example:")
            
            # Create some previous actions to provide context
            previous_actions = [
                ActionStep(
                    id="prev_1",
                    action_sequence_id="prev_seq",
                    action_type=ActionType.NAVIGATION,
                    parameters={"x": 1.0, "y": 1.0},
                    timeout=10,
                    order=0
                ),
                ActionStep(
                    id="prev_2",
                    action_sequence_id="prev_seq",
                    action_type=ActionType.PERCEPTION,
                    parameters={"action": "detect", "target": "spilled_drink"},
                    timeout=5,
                    order=1
                )
            ]
            
            context_sequence = await self.generate_context_aware_action_sequence(
                "Now get me a cloth",
                previous_actions=previous_actions
            )
            
            if context_sequence:
                print(f"  Generated {len(context_sequence.sequence)}-step context-aware sequence:")
                for i, step in enumerate(context_sequence.sequence):
                    print(f"    {i+1}. {step.action_type.value}: {step.parameters}")
            else:
                print("  Context-aware generation failed")
            
            # 3. Complex multi-step task
            print("\n[3] Complex Multi-Step Task Example:")
            complex_task = "Go to the kitchen, find a clean plate, pick it up, move to the table, and set it down"
            
            # Break down the complex task manually for this example
            subtasks = [
                "navigate to kitchen",
                "identify clean plate", 
                "grasp plate",
                "navigate to table",
                "place plate on table"
            ]
            
            print(f"  Complex task '{complex_task}' broken into {len(subtasks)} subtasks")
            
            # Generate sequence for the complex task
            complex_sequence = await self.generate_complex_manipulation_action(complex_task)
            
            if complex_sequence:
                print(f"  Generated {len(complex_sequence.sequence)}-step sequence for complex task")
                for i, step in enumerate(complex_sequence.sequence):
                    print(f"    {i+1}. {step.action_type.value}: {step.parameters}")
            else:
                print("  Complex task generation failed")
            
            print("\n" + "=" * 80)
            print("Advanced LLM Integration Example Completed Successfully!")
            
        except Exception as e:
            print(f"\nError in advanced integration example: {str(e)}")
            import traceback
            traceback.print_exc()


def run_llm_integration_examples():
    """
    Run the LLM integration examples.
    """
    print("VLA Capstone - LLM Integration Examples")
    print("=" * 80)
    
    # Basic example
    print("\n[1] Running Basic LLM Integration Example...")
    basic_example = LLMIntegrationExample()
    asyncio.run(basic_example.run_complete_integration_example())
    
    print("\n" + "-" * 80)
    
    # Advanced example
    print("\n[2] Running Advanced LLM Integration Example...")
    advanced_example = AdvancedLLMIntegrationExample()
    asyncio.run(advanced_example.run_advanced_integration_example())
    
    print("\n" + "=" * 80)
    print("LLM Integration Examples Completed!")


class LLMAPIIntegrationExample:
    """
    Example of integrating with the LLM service through its API.
    """
    
    def __init__(self, api_endpoint: str = f"http://localhost:{settings.server_port}/llm/generate_action"):
        self.api_endpoint = api_endpoint
    
    async def call_llm_api(self, command: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Call the LLM service API to generate actions.
        
        :param command: Natural language command
        :param context: Additional context for the command
        :return: API response or None if call failed
        """
        import aiohttp
        
        payload = {
            "command": command,
            "context": context or {},
            "options": {
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_endpoint, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        print(f"API call failed with status {response.status}")
                        return None
        except Exception as e:
            print(f"Error calling LLM API: {str(e)}")
            return None
    
    async def demonstrate_api_integration(self):
        """
        Demonstrate LLM API integration.
        """
        print("Demonstrating LLM API Integration")
        print("-" * 40)
        
        # Example commands to send to API
        test_commands = [
            {"command": "Move forward 1 meter", "context": {"environment": "indoor", "capabilities": ["navigation"]}},
            {"command": "Pick up the red cup", "context": {"environment": "kitchen", "capabilities": ["manipulation", "perception"]}},
            {"command": "Go to the table", "context": {"environment": "office", "capabilities": ["navigation", "perception"]}}
        ]
        
        for i, test_case in enumerate(test_commands):
            print(f"\nAPI Test {i+1}: '{test_case['command']}'")
            
            # In a real implementation, this would call the actual API
            # For this example, we'll just show what the call would look like
            print(f"  Would call API: {self.api_endpoint}")
            print(f"  Payload: {json.dumps(test_case, indent=2)}")
            
            # Simulated response for demonstration
            simulated_response = {
                "success": True,
                "action_sequence": {
                    "id": f"api_seq_{i+1}",
                    "voice_command_id": f"api_cmd_{i+1}",
                    "sequence": [
                        {
                            "id": f"step_{i+1}_1",
                            "action_type": "navigation" if "move" in test_case['command'].lower() or "go" in test_case['command'].lower() else "manipulation",
                            "parameters": {"command": test_case['command']},
                            "timeout": 10,
                            "order": 0
                        }
                    ],
                    "description": f"API-generated sequence for: {test_case['command']}",
                    "status": "pending"
                },
                "confidence": 0.85,
                "processing_time": 1.2
            }
            
            print(f"  Simulated API response: {len(simulated_response['action_sequence']['sequence'])} steps generated")
        
        print(f"\nAPI Integration Demo Completed!")


# Example of using LLM with different models
class MultiModelLLMExample:
    """
    Example of using different LLM models for different types of tasks.
    """
    
    def __init__(self):
        # Different LLM configurations for different tasks
        self.navigation_llm = LLMService(LLMConfig(
            model_name="gpt-4",  # Good for complex planning
            temperature=0.2,
            max_tokens=200
        ))
        
        self.simple_command_llm = LLMService(LLMConfig(
            model_name="gpt-3.5-turbo",  # Good for simple tasks, faster
            temperature=0.7,
            max_tokens=100
        ))
        
        self.reasoning_llm = LLMService(LLMConfig(
            model_name="gpt-4",  # Better for reasoning tasks
            temperature=0.3,
            max_tokens=500
        ))
    
    async def select_appropriate_llm(self, command: str) -> LLMService:
        """
        Select the appropriate LLM based on the command type.
        
        :param command: Natural language command
        :return: Appropriate LLM service
        """
        command_lower = command.lower()
        
        # Simple commands (movement, basic actions) - use faster model
        if any(word in command_lower for word in ["move", "go", "turn", "stop", "wait"]):
            return self.simple_command_llm
        
        # Complex navigation or reasoning tasks - use more powerful model
        elif any(word in command_lower for word in ["navigate", "plan", "route", "calculate", "think", "reason"]):
            return self.reasoning_llm
        
        # Default to navigation LLM
        else:
            return self.navigation_llm
    
    async def generate_action_with_model_selection(self, command: str) -> Optional[ActionSequence]:
        """
        Generate actions using the most appropriate LLM for the command.
        
        :param command: Natural language command
        :return: Generated action sequence
        """
        print(f"Selecting appropriate LLM for command: '{command}'")
        
        # Select appropriate model
        llm_service = await self.select_appropriate_llm(command)
        
        # Generate actions with the selected model
        action_steps = await llm_service.generate_action_sequence(
            intent="command_execution",
            parameters={"command": command},
            context={
                "robot_capabilities": ["navigation", "manipulation", "perception"],
                "environment_context": {
                    "layout": "indoor",
                    "objects": ["table", "chair", "cup"]
                }
            }
        )
        
        if not action_steps:
            return None
        
        # Create and return action sequence
        action_sequence = ActionSequence(
            id=f"model_sel_seq_{uuid.uuid4()}",
            voice_command_id=f"model_sel_cmd_{uuid.uuid4()}",
            sequence=action_steps,
            description=f"Model-selected sequence for: {command}",
            status=ActionSequenceStatus.PENDING
        )
        
        return action_sequence
    
    async def run_model_selection_example(self):
        """
        Run the model selection example.
        """
        print("VLA Capstone - LLM Model Selection Example")
        print("=" * 60)
        
        test_commands = [
            "Move forward",
            "Navigate to the kitchen and find a cup",
            "Calculate the most efficient path to the bedroom",
            "Go to position x=1, y=2",
            "Think about what I might want next after drinking"
        ]
        
        for i, command in enumerate(test_commands):
            print(f"\n[{i+1}] Processing command: '{command}'")
            
            # Generate with model selection
            sequence = await self.generate_action_with_model_selection(command)
            
            if sequence:
                print(f"  Used {sequence.id.split('_')[2]} model and generated {len(sequence.sequence)} steps:")
                for j, step in enumerate(sequence.sequence):
                    print(f"    {j+1}. {step.action_type.value}: {step.parameters}")
            else:
                print(f"  Failed to generate action sequence")


# Utility function for batch processing commands
async def batch_process_commands(commands: List[str], llm_integration: LLMIntegrationExample) -> List[Dict[str, Any]]:
    """
    Process multiple commands in batch.
    
    :param commands: List of commands to process
    :param llm_integration: LLM integration service
    :return: List of processing results
    """
    results = []
    
    for i, command in enumerate(commands):
        print(f"Processing command {i+1}/{len(commands)}: '{command}'")
        
        # For this example, we'll use simple navigation as the command type
        # In a real implementation, you'd need to classify the command type
        sequence = await llm_integration.generate_simple_navigation_action(command.split()[-1] if len(command.split()) > 0 else "kitchen")
        
        result = {
            "command": command,
            "command_index": i,
            "generated_sequence": sequence is not None,
            "step_count": len(sequence.sequence) if sequence else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        results.append(result)
    
    return results


if __name__ == "__main__":
    # Run the main examples
    run_llm_integration_examples()
    
    print("\n" + "=" * 80)
    print("Additional Examples:")
    
    # Run API integration example
    print("\n[3] LLM API Integration Example:")
    api_example = LLMAPIIntegrationExample()
    asyncio.run(api_example.demonstrate_api_integration())
    
    # Run model selection example
    print("\n[4] Multi-Model LLM Example:")
    multi_model_example = MultiModelLLMExample()
    asyncio.run(multi_model_example.run_model_selection_example())
    
    # Run batch processing example
    print("\n[5] Batch Command Processing Example:")
    llm_example = LLMIntegrationExample()
    batch_commands = ["Go to kitchen", "Navigate to bedroom", "Move forward", "Go to office"]
    
    async def run_batch_example():
        batch_results = await batch_process_commands(batch_commands, llm_example)
        print(f"\nBatch processing results:")
        for result in batch_results:
            print(f"  Command '{result['command']}': {'✓' if result['generated_sequence'] else '✗'} ({result['step_count']} steps)")
    
    asyncio.run(run_batch_example())
    
    print(f"\nAll LLM integration examples completed!")