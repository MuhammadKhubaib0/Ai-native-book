import asyncio
import openai
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from ..models.action_step import ActionStep, ActionType


# Load environment variables
load_dotenv()


class LLMConfig(BaseModel):
    """Configuration for the LLM service."""
    api_key: Optional[str] = None
    model_name: str = "gpt-4-turbo"  # Default to GPT-4 Turbo or Claude equivalent
    api_base: Optional[str] = None  # For Azure OpenAI or custom endpoints
    temperature: float = 0.3  # Lower temperature for more deterministic outputs
    max_tokens: int = 1000


class LLMService:
    """
    Service class for handling LLM interactions for action generation.
    """
    
    def __init__(self, config: LLMConfig = None):
        """
        Initialize the LLM service with configuration.
        
        :param config: LLMConfig object with service configuration
        """
        self.config = config or LLMConfig()
        
        # Set OpenAI API key
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required for LLM service")
        
        openai.api_key = api_key
        
        # Set API base if provided (for Azure OpenAI or custom endpoints)
        if self.config.api_base:
            openai.base_url = self.config.api_base
    
    async def generate_action_sequence(
        self, 
        intent: str, 
        parameters: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> List[ActionStep]:
        """
        Generate an action sequence based on intent and parameters using an LLM.
        
        :param intent: The intent extracted from the voice command
        :param parameters: Parameters extracted from the voice command
        :param context: Additional context for the action generation
        :return: List of ActionStep objects representing the action sequence
        """
        # Build the prompt for the LLM
        prompt = self._build_action_generation_prompt(intent, parameters, context)
        
        try:
            # Make the API call to OpenAI
            response = await openai.ChatCompletion.acreate(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # Extract the response text
            content = response['choices'][0]['message']['content']
            
            # Parse the LLM response into ActionStep objects
            action_steps = self._parse_llm_response(content)
            
            return action_steps
            
        except Exception as e:
            print(f"Error generating action sequence: {e}")
            # Return a default action sequence in case of error
            return self._get_default_action_sequence(intent, parameters)
    
    def _build_action_generation_prompt(
        self, 
        intent: str, 
        parameters: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build the prompt for the LLM based on intent, parameters, and context.
        
        :param intent: The intent extracted from the voice command
        :param parameters: Parameters extracted from the voice command
        :param context: Additional context for the action generation
        :return: Formatted prompt string
        """
        prompt = f"""
        Generate a sequence of robot actions based on the following command:
        Intent: {intent}
        Parameters: {parameters}
        """
        
        if context:
            prompt += f"\nAdditional Context: {context}"
        
        prompt += """
        
        Respond with a JSON array of action steps. Each action step should have:
        - id: a unique identifier
        - action_type: one of "navigation", "manipulation", "perception", "other"
        - parameters: specific parameters for the action
        - timeout: maximum time to wait for action completion in seconds
        - order: order of this step in the sequence
        
        Example response format:
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
            "action_type": "manipulation",
            "parameters": {"object_id": "red_cube"},
            "timeout": 15,
            "order": 1
          }
        ]
        
        Only respond with the JSON array, nothing else.
        """
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt that guides the LLM's behavior.
        
        :return: System prompt string
        """
        return """
        You are an assistant that converts natural language commands into robot action sequences. 
        Your responses should be valid JSON arrays of action steps that follow the specified format. 
        Each action step should be a discrete, executable robot behavior.
        Focus on safety and feasibility when generating actions.
        """
    
    def _parse_llm_response(self, response: str) -> List[ActionStep]:
        """
        Parse the LLM response into ActionStep objects.
        
        :param response: Raw response from the LLM
        :return: List of ActionStep objects
        """
        import json
        import uuid
        
        try:
            # Try to extract JSON from the response (in case the LLM included additional text)
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                steps_data = json.loads(json_str)
            else:
                # If no JSON found, try parsing the entire response
                steps_data = json.loads(response)
            
            action_steps = []
            for i, step_data in enumerate(steps_data):
                # Generate a new ID if not provided by LLM
                step_id = step_data.get('id', str(uuid.uuid4()))
                
                # Create ActionStep object
                action_step = ActionStep(
                    id=step_id,
                    action_sequence_id="",  # Will be set by the caller
                    action_type=ActionType(step_data.get('action_type', 'other')),
                    parameters=step_data.get('parameters', {}),
                    timeout=step_data.get('timeout', 10),
                    order=step_data.get('order', i)
                )
                
                action_steps.append(action_step)
            
            # Sort by order to ensure proper sequence
            action_steps.sort(key=lambda x: x.order)
            
            return action_steps
            
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print(f"Response was: {response}")
            return []
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return []
    
    def _get_default_action_sequence(
        self, 
        intent: str, 
        parameters: Dict[str, Any]
    ) -> List[ActionStep]:
        """
        Generate a default action sequence in case of LLM errors.
        
        :param intent: The intent extracted from the voice command
        :param parameters: Parameters extracted from the voice command
        :return: List of ActionStep objects
        """
        import uuid
        
        # Default response based on intent
        if intent.lower() in ['navigation', 'move', 'go to', 'navigate']:
            return [
                ActionStep(
                    id=str(uuid.uuid4()),
                    action_sequence_id="",  # Will be set by the caller
                    action_type=ActionType.NAVIGATION,
                    parameters=parameters,
                    timeout=10,
                    order=0
                )
            ]
        elif intent.lower() in ['manipulation', 'pick up', 'grasp', 'move object']:
            return [
                ActionStep(
                    id=str(uuid.uuid4()),
                    action_sequence_id="",  # Will be set by the caller
                    action_type=ActionType.MANIPULATION,
                    parameters=parameters,
                    timeout=15,
                    order=0
                )
            ]
        elif intent.lower() in ['perception', 'look', 'see', 'detect']:
            return [
                ActionStep(
                    id=str(uuid.uuid4()),
                    action_sequence_id="",  # Will be set by the caller
                    action_type=ActionType.PERCEPTION,
                    parameters=parameters,
                    timeout=5,
                    order=0
                )
            ]
        else:
            return [
                ActionStep(
                    id=str(uuid.uuid4()),
                    action_sequence_id="",  # Will be set by the caller
                    action_type=ActionType.OTHER,
                    parameters=parameters,
                    timeout=5,
                    order=0
                )
            ]


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    # Configuration
    config = LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4-turbo"
    )
    
    # Initialize service
    llm_service = LLMService(config)
    
    # Example of how to use the service
    async def example():
        intent = "navigation"
        parameters = {"x": 2.0, "y": 3.0, "theta": 1.57}
        
        try:
            action_sequence = await llm_service.generate_action_sequence(intent, parameters)
            for step in action_sequence:
                print(step.json(indent=2))
        except Exception as e:
            print(f"Error in action generation: {e}")
    
    # Run the example
    # asyncio.run(example())