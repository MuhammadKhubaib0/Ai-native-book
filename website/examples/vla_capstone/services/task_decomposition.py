"""
Service for decomposing complex commands into simpler, executable tasks using LLMs.
"""
import json
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from ..services.llm_service import LLMService, LLMConfig
from ..config import settings


class TaskType(Enum):
    """Enumeration of task types that can be decomposed."""
    NAVIGATION = "navigation"
    MANIPULATION = "manipulation"
    PERCEPTION = "perception"
    COMPOSITE = "composite"
    SEQUENCE = "sequence"
    CONDITIONAL = "conditional"


class Subtask(BaseModel):
    """Model representing a decomposed subtask."""
    id: str
    description: str
    task_type: TaskType
    parameters: Dict[str, Any]
    dependencies: List[str]  # IDs of tasks that must be completed before this one
    estimated_duration: float  # In seconds


class TaskDecompositionService:
    """
    Service for decomposing complex commands into simpler, executable tasks using LLMs.
    """
    
    def __init__(self):
        """Initialize the task decomposition service."""
        # Initialize LLM service with configuration
        self.llm_config = LLMConfig(
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        self.llm_service = LLMService(self.llm_config)
    
    async def decompose_task(
        self, 
        command: str, 
        robot_capabilities: List[str] = None,
        environment_context: Dict[str, Any] = None,
        max_depth: int = 3
    ) -> List[Subtask]:
        """
        Decompose a complex command into a sequence of simpler tasks.
        
        :param command: The complex command to decompose
        :param robot_capabilities: List of capabilities the robot supports
        :param environment_context: Information about the current environment
        :param max_depth: Maximum depth for recursive decomposition
        :return: List of subtasks that decompose the original command
        """
        # Create a prompt for task decomposition
        prompt = self._create_decomposition_prompt(
            command=command,
            robot_capabilities=robot_capabilities,
            environment_context=environment_context,
            max_depth=max_depth
        )
        
        # Generate the decomposition using the LLM
        response = await self.llm_service.generate_action_sequence(
            intent="task_decomposition", 
            parameters={"command": command},
            context={"prompt": prompt}
        )
        
        # Parse the response and convert to Subtask objects
        # Note: This is a simplified approach - in practice, you'd need to call the LLM API directly
        # to handle the task decomposition specifically
        subtasks = await self._parse_decomposition_response(command, robot_capabilities, environment_context)
        
        return subtasks
    
    def _create_decomposition_prompt(
        self, 
        command: str, 
        robot_capabilities: List[str], 
        environment_context: Dict[str, Any],
        max_depth: int
    ) -> str:
        """
        Create a prompt to decompose a complex command.
        
        :param command: The command to decompose
        :param robot_capabilities: List of robot capabilities
        :param environment_context: Environment information
        :param max_depth: Maximum depth for decomposition
        :return: Formatted prompt string
        """
        capabilities_str = ", ".join(robot_capabilities or [])
        environment_str = json.dumps(environment_context or {}, indent=2)
        
        prompt = f"""
        Decompose the following complex command into simpler, executable tasks:
        Command: {command}
        
        Robot Capabilities: {capabilities_str}
        Environment Context: {environment_str}
        Maximum Decomposition Depth: {max_depth}
        
        Break down the command into the smallest possible executable tasks.
        Each task should be something the robot can perform directly.
        
        Return the result as a JSON array of subtasks, where each subtask has:
        - id: a unique identifier
        - description: a human-readable description of the task
        - task_type: the type of task (navigation, manipulation, perception, composite, sequence, conditional)
        - parameters: specific parameters needed for the task
        - dependencies: an array of task IDs that must be completed before this task
        - estimated_duration: estimated time to complete the task in seconds
        
        Example response format:
        [
          {{
            "id": "task_1",
            "description": "Navigate to the kitchen",
            "task_type": "navigation",
            "parameters": {{"destination": "kitchen"}},
            "dependencies": [],
            "estimated_duration": 10.0
          }},
          {{
            "id": "task_2",
            "description": "Detect the red cup",
            "task_type": "perception",
            "parameters": {{"object": "red cup"}},
            "dependencies": ["task_1"],
            "estimated_duration": 5.0
          }}
        ]
        
        Make sure the tasks form a logical sequence to accomplish the original command.
        Only return the JSON array, nothing else.
        """
        
        return prompt
    
    async def _parse_decomposition_response(
        self,
        command: str,
        robot_capabilities: List[str] = None,
        environment_context: Dict[str, Any] = None
    ) -> List[Subtask]:
        """
        Parse the LLM's response to a task decomposition prompt.
        
        Note: This is a placeholder implementation that creates example tasks.
        In a real implementation, you would call the LLM API and parse its response.
        
        :param command: The original command
        :param robot_capabilities: Robot capabilities
        :param environment_context: Environment context
        :return: List of subtasks
        """
        import uuid
        
        # This is a simplified implementation that creates example tasks
        # In a real implementation, you would process the actual LLM response
        
        # For demonstration, we'll create some example subtasks based on common command patterns
        subtasks = []
        
        if "kitchen" in command.lower():
            # Common tasks for going to the kitchen
            nav_task = Subtask(
                id=str(uuid.uuid4()),
                description="Navigate to the kitchen",
                task_type=TaskType.NAVIGATION,
                parameters={"destination": "kitchen"},
                dependencies=[],
                estimated_duration=15.0
            )
            subtasks.append(nav_task)
            
            if "cup" in command.lower():
                # Additional tasks if looking for an object
                perception_task = Subtask(
                    id=str(uuid.uuid4()),
                    description="Look for a cup",
                    task_type=TaskType.PERCEPTION,
                    parameters={"object_type": "cup"},
                    dependencies=[nav_task.id],
                    estimated_duration=5.0
                )
                subtasks.append(perception_task)
                
                if "pick" in command.lower() or "grasp" in command.lower():
                    manipulation_task = Subtask(
                        id=str(uuid.uuid4()),
                        description="Grasp the cup",
                        task_type=TaskType.MANIPULATION,
                        parameters={"object_id": "detected_cup"},
                        dependencies=[perception_task.id],
                        estimated_duration=8.0
                    )
                    subtasks.append(manipulation_task)
        
        # If no specific pattern matched, create a general task
        if not subtasks:
            general_task = Subtask(
                id=str(uuid.uuid4()),
                description=command,
                task_type=TaskType.COMPOSITE,
                parameters={"original_command": command},
                dependencies=[],
                estimated_duration=10.0
            )
            subtasks.append(general_task)
        
        return subtasks
    
    def create_execution_plan(self, subtasks: List[Subtask]) -> Dict[str, Any]:
        """
        Create an execution plan from the decomposed subtasks.
        
        :param subtasks: List of subtasks to include in the plan
        :return: Execution plan dictionary
        """
        # Build a dependency graph
        task_graph = {}
        for task in subtasks:
            task_graph[task.id] = {
                'task': task,
                'dependencies': task.dependencies,
                'dependents': []  # Tasks that depend on this one
            }
        
        # Add reverse dependencies
        for task_id, task_info in task_graph.items():
            for dep_id in task_info['dependencies']:
                if dep_id in task_graph:
                    task_graph[dep_id]['dependents'].append(task_id)
        
        # Determine execution order based on dependencies
        execution_order = self._topological_sort(task_graph)
        
        # Create the execution plan
        plan = {
            'tasks': [task_graph[task_id]['task'] for task_id in execution_order],
            'dependencies': {task_id: task_info['dependencies'] for task_id, task_info in task_graph.items()},
            'execution_order': execution_order
        }
        
        return plan
    
    def _topological_sort(self, graph: Dict[str, Dict]) -> List[str]:
        """
        Perform topological sort on the task dependency graph.
        
        :param graph: The task dependency graph
        :return: List of task IDs in execution order
        """
        # Calculate in-degrees
        in_degree = {task_id: 0 for task_id in graph}
        for task_id, task_info in graph.items():
            for dep_id in task_info['dependencies']:
                if dep_id in in_degree:
                    in_degree[task_id] += 1
        
        # Find tasks with no dependencies
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        sorted_order = []
        
        while queue:
            current = queue.pop(0)
            sorted_order.append(current)
            
            # Reduce in-degree of dependent tasks
            for dependent in graph[current]['dependents']:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check if all tasks were included (no cycles)
        if len(sorted_order) != len(graph):
            raise ValueError("Dependency cycle detected in task graph")
        
        return sorted_order


class HierarchicalTaskDecompositionService(TaskDecompositionService):
    """
    Advanced task decomposition service with hierarchical decomposition capabilities.
    """
    
    async def decompose_hierarchical(
        self, 
        command: str, 
        robot_capabilities: List[str] = None,
        environment_context: Dict[str, Any] = None,
        max_depth: int = 3,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """
        Decompose a complex command hierarchically into multiple levels.
        
        :param command: The complex command to decompose
        :param robot_capabilities: List of robot capabilities
        :param environment_context: Environment information
        :param max_depth: Maximum depth for decomposition
        :param current_depth: Current depth in the recursion
        :return: Hierarchical decomposition dictionary
        """
        if current_depth >= max_depth:
            # At max depth, treat as atomic task
            return {
                "type": "atomic",
                "command": command,
                "capabilities": robot_capabilities,
                "depth": current_depth
            }
        
        # Create a hierarchical decomposition prompt
        prompt = self._create_hierarchical_decomposition_prompt(
            command=command,
            robot_capabilities=robot_capabilities,
            environment_context=environment_context,
            max_depth=max_depth,
            current_depth=current_depth
        )
        
        # For this implementation, we'll create a hierarchical structure based on common patterns
        # In a real implementation, you would use the LLM to do the decomposition
        hierarchical_tasks = self._create_hierarchical_tasks(
            command, 
            robot_capabilities, 
            environment_context,
            max_depth,
            current_depth
        )
        
        return {
            "type": "hierarchical",
            "original_command": command,
            "subtasks": hierarchical_tasks,
            "depth": current_depth,
            "capabilities": robot_capabilities
        }
    
    def _create_hierarchical_decomposition_prompt(
        self,
        command: str,
        robot_capabilities: List[str],
        environment_context: Dict[str, Any],
        max_depth: int,
        current_depth: int
    ) -> str:
        """
        Create a prompt for hierarchical task decomposition.
        
        :param command: The command to decompose
        :param robot_capabilities: Robot capabilities
        :param environment_context: Environment context
        :param max_depth: Maximum depth
        :param current_depth: Current depth
        :return: Hierarchical decomposition prompt
        """
        capabilities_str = ", ".join(robot_capabilities or [])
        environment_str = json.dumps(environment_context or {}, indent=2)
        
        prompt = f"""
        Decompose the following complex command hierarchically:
        Command: {command}
        
        Robot Capabilities: {capabilities_str}
        Environment Context: {environment_str}
        Maximum Depth: {max_depth}
        Current Depth: {current_depth}
        
        Break down the command into a hierarchy of subtasks.
        At each level, decompose into the most logical sub-components.
        Consider what higher-level goals need to be achieved and how they break down.
        
        Return the result as a nested JSON structure with:
        - type: "composite" or "atomic"
        - description: description of this task level
        - subtasks: array of subtasks (for composite tasks)
        - command: the specific command to execute (for atomic tasks)
        - estimated_duration: estimated time to complete this task
        - depth: the current depth in the hierarchy
        
        Example response format:
        {{
          "type": "composite",
          "description": "Make coffee",
          "subtasks": [
            {{
              "type": "composite",
              "description": "Get coffee materials",
              "subtasks": [
                {{
                  "type": "atomic", 
                  "command": "navigate to kitchen",
                  "estimated_duration": 10.0,
                  "depth": 2
                }},
                {{
                  "type": "atomic",
                  "command": "find coffee beans",
                  "estimated_duration": 5.0,
                  "depth": 2
                }}
              ],
              "estimated_duration": 15.0,
              "depth": 1
            }}
          ],
          "estimated_duration": 30.0,
          "depth": 0
        }}
        
        Only return the JSON structure, nothing else.
        """
        
        return prompt
    
    def _create_hierarchical_tasks(
        self,
        command: str,
        robot_capabilities: List[str],
        environment_context: Dict[str, Any],
        max_depth: int,
        current_depth: int
    ) -> List[Dict[str, Any]]:
        """
        Create hierarchical tasks for the given command.
        
        :param command: The command to decompose
        :param robot_capabilities: Robot capabilities
        :param environment_context: Environment context
        :param max_depth: Maximum depth
        :param current_depth: Current depth
        :return: List of hierarchical tasks
        """
        import uuid
        
        # This is a simplified implementation that creates example hierarchical tasks
        # In a real implementation, you would process the actual LLM response
        
        # For demonstration, decompose based on common command patterns
        if "make coffee" in command.lower() and current_depth < max_depth:
            return [
                {
                    "id": str(uuid.uuid4()),
                    "type": "composite",
                    "description": "Get coffee materials",
                    "subtasks": [
                        {
                            "id": str(uuid.uuid4()),
                            "type": "atomic",
                            "command": "navigate to kitchen",
                            "estimated_duration": 10.0,
                            "depth": current_depth + 1
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "type": "atomic",
                            "command": "locate coffee machine",
                            "estimated_duration": 5.0,
                            "depth": current_depth + 1
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "type": "atomic",
                            "command": "locate coffee beans",
                            "estimated_duration": 5.0,
                            "depth": current_depth + 1
                        }
                    ],
                    "estimated_duration": 20.0,
                    "depth": current_depth
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "composite",
                    "description": "Prepare coffee",
                    "subtasks": [
                        {
                            "id": str(uuid.uuid4()),
                            "type": "atomic",
                            "command": "grasp coffee container",
                            "estimated_duration": 8.0,
                            "depth": current_depth + 1
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "type": "atomic",
                            "command": "operate coffee machine",
                            "estimated_duration": 120.0,
                            "depth": current_depth + 1
                        }
                    ],
                    "estimated_duration": 128.0,
                    "depth": current_depth
                }
            ]
        elif current_depth >= max_depth:
            # At max depth, return an atomic task
            return [{
                "id": str(uuid.uuid4()),
                "type": "atomic",
                "command": command,
                "estimated_duration": 10.0,
                "depth": current_depth
            }]
        else:
            # For other commands, create a simple decomposition
            return [{
                "id": str(uuid.uuid4()),
                "type": "composite",
                "description": f"Process command: {command}",
                "subtasks": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "atomic",
                        "command": command,
                        "estimated_duration": 10.0,
                        "depth": current_depth + 1
                    }
                ],
                "estimated_duration": 10.0,
                "depth": current_depth
            }]


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    # Example of how to use the TaskDecompositionService
    async def example():
        service = TaskDecompositionService()
        
        # Example command
        command = "Go to the kitchen and pick up the red cup"
        capabilities = ["navigation", "manipulation", "perception", "object_recognition"]
        environment = {"rooms": ["kitchen", "living_room"], "objects": ["red cup", "table"]}
        
        # Decompose the task
        subtasks = await service.decompose_task(
            command=command,
            robot_capabilities=capabilities,
            environment_context=environment
        )
        
        print("Decomposed subtasks:")
        for i, task in enumerate(subtasks):
            print(f"{i+1}. {task.description}")
            print(f"   Type: {task.task_type.value}")
            print(f"   Parameters: {task.parameters}")
            print(f"   Dependencies: {task.dependencies}")
            print(f"   Estimated duration: {task.estimated_duration}s")
            print()
        
        # Create an execution plan
        plan = service.create_execution_plan(subtasks)
        print("Execution order:", plan['execution_order'])
    
    # Run the example
    # asyncio.run(example())
    
    # Example of hierarchical decomposition
    async def hierarchical_example():
        service = HierarchicalTaskDecompositionService()
        
        command = "Make coffee"
        capabilities = ["navigation", "manipulation", "perception", "object_recognition", "tool_operation"]
        environment = {"kitchen": {"coffee_machine": "available", "coffee_beans": "available"}}
        
        hierarchical = await service.decompose_hierarchical(
            command=command,
            robot_capabilities=capabilities,
            environment_context=environment,
            max_depth=3
        )
        
        print("Hierarchical decomposition:")
        print(json.dumps(hierarchical, indent=2))
    
    # Run the hierarchical example
    # asyncio.run(hierarchical_example())