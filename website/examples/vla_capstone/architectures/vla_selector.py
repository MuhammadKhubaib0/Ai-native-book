"""
Service for selecting appropriate VLA (Vision-Language-Action) architectures.
"""
import importlib
from typing import Dict, Any, Optional, List, Type
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from ..models.action_step import ActionStep
from ..models.multimodal_input import MultimodalInput


class VLAArchitectureType(Enum):
    """Enumeration of different VLA architecture types."""
    RT1 = "RT1"
    RT2 = "RT2"
    OPENVLA = "OpenVLA"
    PALM_E = "PaLM-E"
    BC_Z = "BC-Z"
    VIMA = "VIMA"
    COMPOSABLE_TASK_PLANNING = "ComposableTaskPlanning"


class VLAProcessor(ABC):
    """
    Abstract base class for VLA processors implementing different architectures.
    """
    
    @abstractmethod
    def process(self, multimodal_input: MultimodalInput) -> List[ActionStep]:
        """
        Process multimodal input and generate action steps.
        
        :param multimodal_input: Input containing vision, language, and other modalities
        :return: List of action steps to execute
        """
        pass
    
    @abstractmethod
    def get_capability_description(self) -> str:
        """
        Get a description of the architecture's capabilities.
        
        :return: Capability description
        """
        pass


class RT1Processor(VLAProcessor):
    """
    Processor implementing the RT-1 architecture.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the RT-1 processor.
        
        :param model_path: Path to the RT-1 model (if using a pre-trained one)
        """
        self.model_path = model_path
        self.capability_description = (
            "RT-1: Robot Transformer 1 - A transformer-based model that maps language and vision "
            "to robot actions. Uses a fixed set of primitive actions and is trained on large-scale "
            "robotics datasets."
        )
    
    def process(self, multimodal_input: MultimodalInput) -> List[ActionStep]:
        """
        Process multimodal input using the RT-1 architecture.
        
        :param multimodal_input: Input containing vision, language, and other modalities
        :return: List of action steps to execute
        """
        actions = []
        
        # RT-1 processes language commands and visual observations to generate motor commands
        # This is a simplified implementation; real RT-1 uses a large transformer model
        
        # Extract information from multimodal input
        visual_data = multimodal_input.visual_data
        sensor_data = multimodal_input.sensor_data
        
        # Determine action based on visual and sensor data
        if visual_data and sensor_data:
            # Look for actionable objects in the scene
            if "object_detected" in visual_data and visual_data["object_detected"]:
                # For RT-1, we map common objects to basic actions
                action = ActionStep(
                    id="rt1_action_1",
                    action_sequence_id=multimodal_input.id,
                    action_type="navigation",  # RT-1 supports navigation
                    parameters={
                        "target_position": visual_data.get("object_position", [0.0, 0.0, 0.0]),
                        "object_class": visual_data.get("object_class", "unknown")
                    },
                    timeout=10,
                    order=0
                )
                actions.append(action)
        
        return actions
    
    def get_capability_description(self) -> str:
        """Get a description of the RT-1 architecture's capabilities."""
        return self.capability_description


class RT2Processor(VLAProcessor):
    """
    Processor implementing the RT-2 architecture.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the RT-2 processor.
        
        :param model_path: Path to the RT-2 model (if using a pre-trained one)
        """
        self.model_path = model_path
        self.capability_description = (
            "RT-2: Robot Transformer 2 - An extension of RT-1 that incorporates "
            "large language models to improve generalization and reasoning capabilities. "
            "Can follow more complex language instructions and handle novel situations."
        )
    
    def process(self, multimodal_input: MultimodalInput) -> List[ActionStep]:
        """
        Process multimodal input using the RT-2 architecture.
        
        :param multimodal_input: Input containing vision, language, and other modalities
        :return: List of action steps to execute
        """
        actions = []
        
        # RT-2 uses language models to better interpret commands and plan actions
        # This is a simplified implementation; real RT-2 uses large language models
        
        # Extract information from multimodal input
        visual_data = multimodal_input.visual_data
        sensor_data = multimodal_input.sensor_data
        
        # Use more sophisticated reasoning to determine actions
        if visual_data and sensor_data:
            # RT-2 can handle more complex object interactions
            if "object_detected" in visual_data and visual_data["object_detected"]:
                object_class = visual_data.get("object_class", "unknown")
                
                if object_class in ["cup", "bottle"]:
                    # For RT-2, we can plan more complex actions
                    # Approach the object
                    approach_action = ActionStep(
                        id="rt2_approach_action",
                        action_sequence_id=multimodal_input.id,
                        action_type="navigation",
                        parameters={
                            "target_position": visual_data.get("object_position", [0.0, 0.0, 0.0]),
                            "object_class": object_class
                        },
                        timeout=10,
                        order=0
                    )
                    actions.append(approach_action)
                    
                    # Grasp the object
                    grasp_action = ActionStep(
                        id="rt2_grasp_action",
                        action_sequence_id=multimodal_input.id,
                        action_type="manipulation",
                        parameters={
                            "object_class": object_class,
                            "object_position": visual_data.get("object_position", [0.0, 0.0, 0.0])
                        },
                        timeout=15,
                        order=1
                    )
                    actions.append(grasp_action)
        
        return actions
    
    def get_capability_description(self) -> str:
        """Get a description of the RT-2 architecture's capabilities."""
        return self.capability_description


class OpenVLAProcessor(VLAProcessor):
    """
    Processor implementing the OpenVLA architecture.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the OpenVLA processor.
        
        :param model_path: Path to the OpenVLA model (if using a pre-trained one)
        """
        self.model_path = model_path
        self.capability_description = (
            "OpenVLA: Open Vision-Language-Action model that supports open-vocabulary "
            "manipulation and is trained on diverse datasets. Offers better generalization "
            "to novel objects and environments compared to earlier architectures."
        )
    
    def process(self, multimodal_input: MultimodalInput) -> List[ActionStep]:
        """
        Process multimodal input using the OpenVLA architecture.
        
        :param multimodal_input: Input containing vision, language, and other modalities
        :return: List of action steps to execute
        """
        actions = []
        
        # OpenVLA uses a unified vision-language model for better object recognition
        # and action generation in diverse environments
        
        # Extract information from multimodal input
        visual_data = multimodal_input.visual_data
        sensor_data = multimodal_input.sensor_data
        
        # OpenVLA can recognize and interact with a wider variety of objects
        if visual_data and sensor_data:
            # Process each detected object with OpenVLA's open-vocabulary capabilities
            detected_objects = visual_data.get("objects", [])
            
            for i, obj in enumerate(detected_objects):
                object_class = obj.get("class", "unknown")
                position = obj.get("position", [0.0, 0.0, 0.0])
                
                # Generate appropriate action based on object class
                if object_class in ["cup", "bottle", "box"]:
                    # Grasp action for containers
                    grasp_action = ActionStep(
                        id=f"openvla_grasp_{i}",
                        action_sequence_id=multimodal_input.id,
                        action_type="manipulation",
                        parameters={
                            "object_class": object_class,
                            "object_position": position,
                            "grasp_type": "top_grasp" if object_class in ["cup", "bottle"] else "side_grasp"
                        },
                        timeout=15,
                        order=i * 2  # Leave space for potential approach action
                    )
                    actions.append(grasp_action)
                elif object_class in ["door", "drawer"]:
                    # Interaction action for doors/drawers
                    interact_action = ActionStep(
                        id=f"openvla_interact_{i}",
                        action_sequence_id=multimodal_input.id,
                        action_type="manipulation",
                        parameters={
                            "object_class": object_class,
                            "object_position": position,
                            "interaction_type": "open"
                        },
                        timeout=20,
                        order=i * 2
                    )
                    actions.append(interact_action)
        
        return actions
    
    def get_capability_description(self) -> str:
        """Get a description of the OpenVLA architecture's capabilities."""
        return self.capability_description


class PaLM_EProcessor(VLAProcessor):
    """
    Processor implementing the PaLM-E architecture.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the PaLM-E processor.
        
        :param model_path: Path to the PaLM-E model (if using a pre-trained one)
        """
        self.model_path = model_path
        self.capability_description = (
            "PaLM-E: Pathways Language Model for Embodied AI - A large-scale embodied "
            "multimodal model that combines vision, language, and action capabilities. "
            "Excels at complex reasoning and planning tasks in physical environments."
        )
    
    def process(self, multimodal_input: MultimodalInput) -> List[ActionStep]:
        """
        Process multimodal input using the PaLM-E architecture.
        
        :param multimodal_input: Input containing vision, language, and other modalities
        :return: List of action steps to execute
        """
        actions = []
        
        # PaLM-E uses large language models for complex reasoning and planning
        # This is a simplified implementation; real PaLM-E uses large multimodal models
        
        # Extract information from multimodal input
        visual_data = multimodal_input.visual_data
        sensor_data = multimodal_input.sensor_data
        
        # PaLM-E can perform complex multi-step reasoning
        if visual_data and sensor_data:
            # Example of complex reasoning: if multiple objects detected, plan a sequence
            objects = visual_data.get("objects", [])
            
            if len(objects) > 1:
                # Plan a sequence to interact with multiple objects
                for i, obj in enumerate(objects):
                    object_class = obj.get("class", "unknown")
                    position = obj.get("position", [0.0, 0.0, 0.0])
                    
                    # Approach object
                    approach_action = ActionStep(
                        id=f"palme_approach_{i}",
                        action_sequence_id=multimodal_input.id,
                        action_type="navigation",
                        parameters={
                            "target_position": position,
                            "object_class": object_class
                        },
                        timeout=10,
                        order=i * 2
                    )
                    actions.append(approach_action)
                    
                    # Manipulate object
                    manipulate_action = ActionStep(
                        id=f"palme_manipulate_{i}",
                        action_sequence_id=multimodal_input.id,
                        action_type="manipulation",
                        parameters={
                            "object_class": object_class,
                            "object_position": position,
                            "manipulation_type": "grasp" if object_class in ["cup", "box"] else "touch"
                        },
                        timeout=15,
                        order=i * 2 + 1
                    )
                    actions.append(manipulate_action)
            elif objects:
                # Single object reasoning
                obj = objects[0]
                object_class = obj.get("class", "unknown")
                
                # Complex reasoning about the object and context
                if object_class == "container":
                    # Plan to open and manipulate contents
                    open_action = ActionStep(
                        id="palme_open",
                        action_sequence_id=multimodal_input.id,
                        action_type="manipulation",
                        parameters={
                            "object_class": object_class,
                            "action": "open",
                            "reasoning": "Opening container to access contents"
                        },
                        timeout=20,
                        order=0
                    )
                    actions.append(open_action)
        
        return actions
    
    def get_capability_description(self) -> str:
        """Get a description of the PaLM-E architecture's capabilities."""
        return self.capability_description


class BCZProcessor(VLAProcessor):
    """
    Processor implementing the BC-Z architecture.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the BC-Z processor.
        
        :param model_path: Path to the BC-Z model (if using a pre-trained one)
        """
        self.model_path = model_path
        self.capability_description = (
            "BC-Z: Behavioral Cloning with Z-scale demonstrations - A model trained "
            "on large-scale human demonstration data. Excels at fine motor control "
            "and imitation learning for complex manipulation tasks."
        )
    
    def process(self, multimodal_input: MultimodalInput) -> List[ActionStep]:
        """
        Process multimodal input using the BC-Z architecture.
        
        :param multimodal_input: Input containing vision, language, and other modalities
        :return: List of action steps to execute
        """
        actions = []
        
        # BC-Z focuses on imitation learning from human demonstrations
        # This is a simplified implementation
        
        # Extract information from multimodal input
        visual_data = multimodal_input.visual_data
        sensor_data = multimodal_input.sensor_data
        
        if visual_data and sensor_data:
            # BC-Z excels at precise manipulation tasks
            detected_objects = visual_data.get("objects", [])
            
            for i, obj in enumerate(detected_objects):
                object_class = obj.get("class", "unknown")
                
                if object_class in ["small_object", "tool", "utensil"]:
                    # Plan precise manipulation
                    precision_action = ActionStep(
                        id=f"bcz_precision_{i}",
                        action_sequence_id=multimodal_input.id,
                        action_type="manipulation",
                        parameters={
                            "object_class": object_class,
                            "grasp_type": "precision_pinch",
                            "approach_vector": [0, 0, -1],  # Approach from above
                            "gripper_width": 0.01,  # Precise grip
                            "trajectory_smoothing": True
                        },
                        timeout=25,
                        order=i
                    )
                    actions.append(precision_action)
        
        return actions
    
    def get_capability_description(self) -> str:
        """Get a description of the BC-Z architecture's capabilities."""
        return self.capability_description


class VLASelector:
    """
    Service for selecting appropriate VLA architectures based on task requirements.
    """
    
    def __init__(self):
        """Initialize the VLA selector with available architectures."""
        self.available_processors = {
            VLAArchitectureType.RT1: RT1Processor,
            VLAArchitectureType.RT2: RT2Processor,
            VLAArchitectureType.OPENVLA: OpenVLAProcessor,
            VLAArchitectureType.PALM_E: PaLM_EProcessor,
            VLAArchitectureType.BC_Z: BCZProcessor,
            # VIMA and ComposableTaskPlanning would be added here if implemented
        }
        
        # Performance metrics for different architectures
        self.performance_metrics = {
            VLAArchitectureType.RT1: {
                "language_understanding": 0.7,
                "vision_accuracy": 0.8,
                "action_success_rate": 0.75,
                "generalization": 0.6,
                "computational_efficiency": 0.9,
                "multistep_reasoning": 0.4
            },
            VLAArchitectureType.RT2: {
                "language_understanding": 0.85,
                "vision_accuracy": 0.82,
                "action_success_rate": 0.8,
                "generalization": 0.75,
                "computational_efficiency": 0.7,
                "multistep_reasoning": 0.7
            },
            VLAArchitectureType.OPENVLA: {
                "language_understanding": 0.8,
                "vision_accuracy": 0.9,
                "action_success_rate": 0.85,
                "generalization": 0.85,
                "computational_efficiency": 0.6,
                "multistep_reasoning": 0.75
            },
            VLAArchitectureType.PALM_E: {
                "language_understanding": 0.95,
                "vision_accuracy": 0.88,
                "action_success_rate": 0.82,
                "generalization": 0.9,
                "computational_efficiency": 0.3,
                "multistep_reasoning": 0.95
            },
            VLAArchitectureType.BC_Z: {
                "language_understanding": 0.6,
                "vision_accuracy": 0.75,
                "action_success_rate": 0.88,
                "generalization": 0.7,
                "computational_efficiency": 0.75,
                "multistep_reasoning": 0.5
            }
        }
    
    def select_architecture(
        self,
        task_requirements: Dict[str, Any],
        environment_constraints: Optional[Dict[str, Any]] = None,
        computational_limits: Optional[Dict[str, Any]] = None
    ) -> VLAArchitectureType:
        """
        Select the most appropriate VLA architecture based on requirements.
        
        :param task_requirements: Requirements for the task (complexity, precision, etc.)
        :param environment_constraints: Constraints of the environment
        :param computational_limits: Computational resources available
        :return: Selected VLA architecture type
        """
        # Define scoring function for architectures based on requirements
        scores = {}
        
        for arch_type in self.available_processors:
            # Get performance metrics for this architecture
            metrics = self.performance_metrics.get(arch_type, {})
            
            # Calculate score based on task requirements
            score = 0.0
            
            # Language understanding importance
            lang_imp = task_requirements.get("language_complexity", 0.5)
            score += metrics.get("language_understanding", 0.5) * lang_imp
            
            # Vision accuracy importance
            vision_imp = task_requirements.get("vision_precision", 0.5)
            score += metrics.get("vision_accuracy", 0.5) * vision_imp
            
            # Action success importance
            action_imp = task_requirements.get("action_success_importance", 0.5)
            score += metrics.get("action_success_rate", 0.5) * action_imp
            
            # Generalization importance
            gen_imp = task_requirements.get("novel_object_handling", 0.5)
            score += metrics.get("generalization", 0.5) * gen_imp
            
            # Multistep reasoning importance
            reasoning_imp = task_requirements.get("multistep_reasoning", 0.3)
            score += metrics.get("multistep_reasoning", 0.5) * reasoning_imp
            
            # Apply computational efficiency penalty if resources are limited
            if computational_limits:
                resource_limit = computational_limits.get("compute_power", 1.0)  # 0-1 scale
                efficiency = metrics.get("computational_efficiency", 0.5)
                if efficiency < resource_limit:
                    score *= (efficiency / resource_limit)  # Reduce score if architecture is too demanding
            
            scores[arch_type] = score
        
        # Return the architecture with the highest score
        best_arch = max(scores, key=scores.get)
        return best_arch
    
    def create_processor(
        self,
        architecture_type: VLAArchitectureType,
        model_path: Optional[str] = None
    ) -> VLAProcessor:
        """
        Create a processor instance for the specified architecture.
        
        :param architecture_type: Type of VLA architecture to create
        :param model_path: Path to the model if using a pre-trained one
        :return: Instance of the VLA processor
        """
        if architecture_type not in self.available_processors:
            raise ValueError(f"Architecture {architecture_type} is not available")
        
        processor_class = self.available_processors[architecture_type]
        return processor_class(model_path)
    
    def get_architecture_recommendation(
        self,
        scenario: str,
        agent_capabilities: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get a recommendation for which architecture to use in a given scenario.
        
        :param scenario: Scenario or task description
        :param agent_capabilities: List of robot/machine capabilities
        :param constraints: Additional constraints (environmental, computational, etc.)
        :return: Recommendation dictionary with architecture and reasoning
        """
        # Define requirements based on scenario
        requirements = self._map_scenario_to_requirements(scenario)
        
        # Select the best architecture
        best_arch = self.select_architecture(requirements, constraints)
        
        # Get the processor class and its capabilities
        processor_class = self.available_processors[best_arch]
        processor_instance = processor_class()
        capabilities = processor_instance.get_capability_description()
        
        # Compile recommendation
        recommendation = {
            "recommended_architecture": best_arch.value,
            "reasoning": self._explain_architecture_choice(best_arch, requirements, scenario),
            "capabilities": capabilities,
            "performance_expected": self.performance_metrics.get(best_arch, {}),
            "implementation_notes": self._get_implementation_notes(best_arch)
        }
        
        return recommendation
    
    def _map_scenario_to_requirements(self, scenario: str) -> Dict[str, float]:
        """
        Map a scenario description to specific requirements.
        
        :param scenario: Scenario description
        :return: Dictionary of requirements and their importance (0-1)
        """
        requirements = {
            "language_complexity": 0.5,
            "vision_precision": 0.5,
            "action_success_importance": 0.5,
            "novel_object_handling": 0.5,
            "multistep_reasoning": 0.5
        }
        
        scenario_lower = scenario.lower()
        
        # Adjust requirements based on scenario
        if any(keyword in scenario_lower for keyword in ["complex instruction", "reasoning", "plan", "strategy"]):
            requirements["language_complexity"] = 0.8
            requirements["multistep_reasoning"] = 0.9
        
        if any(keyword in scenario_lower for keyword in ["precision", "fine manipulation", "careful", "delicate"]):
            requirements["vision_precision"] = 0.9
            requirements["action_success_importance"] = 0.8
        
        if any(keyword in scenario_lower for keyword in ["novel", "new object", "unseen", "generalize"]):
            requirements["novel_object_handling"] = 0.9
        
        if any(keyword in scenario_lower for keyword in ["pick and place", "move object", "grasp"]):
            requirements["action_success_importance"] = 0.8
        
        return requirements
    
    def _explain_architecture_choice(
        self,
        architecture: VLAArchitectureType,
        requirements: Dict[str, float],
        scenario: str
    ) -> str:
        """
        Explain why a particular architecture was chosen.
        
        :param architecture: The chosen architecture
        :param requirements: Task requirements
        :param scenario: Task scenario
        :return: Explanation string
        """
        explanations = {
            VLAArchitectureType.RT1: (
                "RT-1 was selected for its reliability and computational efficiency. "
                "It's well-suited for standard navigation and manipulation tasks with "
                "predefined objects. Best choice when computational resources are limited."
            ),
            VLAArchitectureType.RT2: (
                "RT-2 was selected for its improved language understanding and generalization "
                "capabilities over RT-1. Good for tasks requiring interpretation of more complex "
                "language commands while maintaining reasonable efficiency."
            ),
            VLAArchitectureType.OPENVLA: (
                "OpenVLA was selected for its open-vocabulary capabilities and better "
                "generalization to novel objects. Ideal for tasks involving unknown or "
                "varied objects that require visual recognition."
            ),
            VLAArchitectureType.PALM_E: (
                "PaLM-E was selected for its superior reasoning capabilities for complex "
                "multi-step tasks requiring high-level planning and understanding. Best for "
                "tasks that need complex decision-making and reasoning."
            ),
            VLAArchitectureType.BC_Z: (
                "BC-Z was selected for its precision in manipulation tasks, especially "
                "those requiring fine motor control and imitation of human-like behaviors. "
                "Best for delicate manipulation tasks."
            )
        }
        
        return explanations.get(architecture, f"Architecture {architecture.value} selected")
    
    def _get_implementation_notes(self, architecture: VLAArchitectureType) -> List[str]:
        """
        Get implementation notes for a specific architecture.
        
        :param architecture: The architecture to get notes for
        :return: List of implementation notes
        """
        notes = {
            VLAArchitectureType.RT1: [
                "Requires pre-trained model checkpoint",
                "Efficient for deployment on edge devices",
                "Works best with a predefined action space"
            ],
            VLAArchitectureType.RT2: [
                "Higher computational requirements than RT-1",
                "Better performance with larger language model integration",
                "Can adapt to new tasks with minimal retraining"
            ],
            VLAArchitectureType.OPENVLA: [
                "State-of-the-art performance on open-vocabulary tasks",
                "Requires significant computational resources",
                "Best with diverse training data"
            ],
            VLAArchitectureType.PALM_E: [
                "Very high computational requirements",
                "Excellent for complex reasoning tasks",
                "May require cloud-based inference"
            ],
            VLAArchitectureType.BC_Z: [
                "Excels at fine manipulation tasks",
                "Requires high-quality demonstration data",
                "Good for repetitive precision tasks"
            ]
        }
        
        return notes.get(architecture, ["Implementation notes not available"])


# Example usage:
if __name__ == "__main__":
    # Create a VLA selector
    selector = VLASelector()
    
    # Example 1: Select architecture for a complex reasoning task
    requirements = {
        "language_complexity": 0.9,
        "vision_precision": 0.8,
        "action_success_importance": 0.8,
        "novel_object_handling": 0.7,
        "multistep_reasoning": 0.9
    }
    
    arch = selector.select_architecture(requirements)
    print(f"Selected architecture for complex task: {arch.value}")
    
    # Example 2: Get recommendation for a specific scenario
    recommendation = selector.get_architecture_recommendation(
        "Navigate to kitchen, find and grasp a red cup, then bring it to the counter",
        constraints={"compute_power": 0.6}  # Limited computational power
    )
    
    print(f"\nArchitectural recommendation:")
    print(f"  Architecture: {recommendation['recommended_architecture']}")
    print(f"  Reasoning: {recommendation['reasoning']}")
    print(f"  Expected performance: {recommendation['performance_expected']}")
    
    # Example 3: Create and use a specific processor
    processor = selector.create_processor(VLAArchitectureType.OPENVLA)
    print(f"\nCreated processor: {type(processor).__name__}")
    print(f"Capabilities: {processor.get_capability_description()}")
    
    # Example 4: Compare architectures for different scenarios
    scenarios = [
        "Simple pick and place in structured environment",
        "Complex reasoning with novel objects",
        "Precision manipulation of small objects",
        "Navigation with complex language instructions"
    ]
    
    print(f"\nArchitecture recommendations for different scenarios:")
    for scenario in scenarios:
        rec = selector.get_architecture_recommendation(scenario)
        print(f"  {scenario[:40]}... -> {rec['recommended_architecture']}")