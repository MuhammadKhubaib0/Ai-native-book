"""
Python integration example for multimodal fusion in the VLA Capstone project.
Demonstrates how to combine vision, language, and action modalities effectively.
"""
import asyncio
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import json

# Import VLA system components
from ..models.multimodal_input import MultimodalInput
from ..models.voice_command import VoiceCommand
from ..models.action_step import ActionStep, ActionType
from ..models.action_sequence import ActionSequence, ActionSequenceStatus
from ..models.vla_system_state import VLASystemState, Pose
from ..services.vision_integration import VisionIntegrationService
from ..services.whisper_processor import WhisperAudioProcessor
from ..services.llm_service import LLMService, LLMConfig
from ..services.multimodal_fusion import MultimodalFusionService, FusionMethod
from ..services.action_sequencer import ActionSequencer
from ..services.conflict_resolver import ConflictResolver, ConflictType, ResolutionStrategy
from ..services.confidence_manager import ConfidenceManager
from ..services.action_validator import ActionValidator
from ..config import settings
from ..validation.multimodal_validation import MultimodalValidationService


class MultimodalFusionExample:
    """
    Example implementation of multimodal fusion combining vision, language, and action.
    """
    
    def __init__(self):
        """Initialize the multimodal fusion example."""
        # Initialize services
        self.vision_service = VisionIntegrationService()
        self.whisper_service = WhisperAudioProcessor()
        self.llm_service = LLMService(LLMConfig(
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        ))
        self.fusion_service = MultimodalFusionService(fusion_method=FusionMethod.ATTENTION_BASED)
        self.action_sequencer = ActionSequencer()
        self.conflict_resolver = ConflictResolver()
        self.confidence_manager = ConfidenceManager()
        self.action_validator = ActionValidator()
        self.validation_service = MultimodalValidationService()
        
        # Robot capabilities
        self.robot_capabilities = [
            "navigation", "manipulation", "perception", "interaction",
            "object_detection", "grasping", "mobile_manipulation"
        ]
        
        # Environment context
        self.environment_context = {
            "layout": "structured_home_office",
            "objects": [
                {"id": "cup_1", "class": "cup", "position": {"x": 1.0, "y": 0.5, "z": 0.8}, "color": "red", "status": "visible"},
                {"id": "box_1", "class": "box", "position": {"x": 1.2, "y": 0.7, "z": 0.0}, "color": "blue", "status": "visible"},
                {"id": "desk_1", "class": "desk", "position": {"x": 1.5, "y": 0.0, "z": 0.0}, "status": "stationary"},
                {"id": "chair_1", "class": "chair", "position": {"x": 2.0, "y": 0.5, "z": 0.0}, "status": "stationary"}
            ],
            "navigation_targets": ["kitchen", "bedroom", "office", "living_room", "dining_room"],
            "robot_position": {"x": 0.0, "y": 0.0, "z": 0.0}
        }
    
    async def create_multimodal_input(self, 
                                     voice_command: str, 
                                     vision_data: Optional[Dict[str, Any]] = None,
                                     sensor_data: Optional[Dict[str, Any]] = None) -> MultimodalInput:
        """
        Create a multimodal input combining voice, vision, and sensor data.
        
        :param voice_command: Natural language command
        :param vision_data: Vision data (optional)
        :param sensor_data: Sensor data (optional)
        :return: Multimodal input object
        """
        # Process voice command to get transcription and confidence
        # In a real system, this would come from live audio
        # For this example, we'll simulate the processing
        transcription = voice_command
        confidence = 0.9  # Simulated high confidence for text input
        
        voice_cmd = VoiceCommand(
            id=f"voice_cmd_{int(datetime.now().timestamp())}",
            transcribed_text=transcription,
            intent="unknown",  # Will be determined by LLM
            parameters={},
            confidence=confidence,
            timestamp=datetime.now()
        )
        
        # Create multimodal input
        multimodal_input = MultimodalInput(
            id=f"mm_input_{uuid.uuid4()}",
            voice_input_id=voice_cmd.transcribed_text,
            visual_data=vision_data,
            sensor_data=sensor_data,
            confidence=confidence,
            timestamp=datetime.now()
        )
        
        return multimodal_input
    
    async def fuse_modalities(self, multimodal_input: MultimodalInput) -> Tuple[Dict[str, Any], float]:
        """
        Fuse the different modalities in the multimodal input.
        
        :param multimodal_input: Input with multiple modalities
        :return: Fused result and overall confidence
        """
        # Extract modalities
        voice_data = {"text": multimodal_input.voice_input_id} if multimodal_input.voice_input_id else None
        vision_data = multimodal_input.visual_data
        sensor_data = multimodal_input.sensor_data
        
        # Detect potential conflicts between modalities
        conflicts = self.conflict_resolver.detect_conflicts(voice_data, vision_data, sensor_data)
        
        if conflicts:
            print(f"Detected {len(conflicts)} conflicts between modalities, resolving...")
            
            # Resolve conflicts
            resolution_results = self.conflict_resolver.resolve_conflicts(
                conflicts, voice_data, vision_data, sensor_data
            )
            
            # Apply resolution to data if needed
            for result in resolution_results:
                print(f"  Resolved {result.conflict_type.value} with {result.strategy_used.value} strategy")
        
        # Perform fusion
        fused_result, confidence = self.fusion_service.fuse_modalities(
            voice_data=voice_data,
            vision_data=vision_data,
            sensor_data=sensor_data
        )
        
        return fused_result, confidence
    
    async def generate_action_sequence_from_fusion(self, 
                                                 fusion_result: Dict[str, Any], 
                                                 fusion_confidence: float) -> Optional[ActionSequence]:
        """
        Generate an action sequence based on the fusion result.
        
        :param fusion_result: Result from multimodal fusion
        :param fusion_confidence: Confidence in the fusion result
        :return: Action sequence or None if generation failed
        """
        try:
            # Extract intent and parameters from fusion result
            intent = fusion_result.get("intent", "unknown")
            parameters = fusion_result.get("parameters", {})
            
            # Validate confidence level
            if fusion_confidence < settings.minimum_confidence_score:
                print(f"Fusion confidence {fusion_confidence} below threshold {settings.minimum_confidence_score}")
                return None
            
            # Generate action sequence using LLM
            action_steps = await self.llm_service.generate_action_sequence(
                intent=intent,
                parameters=parameters,
                context={
                    "fusion_result": fusion_result,
                    "robot_capabilities": self.robot_capabilities,
                    "environment_context": self.environment_context
                }
            )
            
            if not action_steps:
                print("LLM did not generate any action steps")
                return None
            
            # Create action sequence
            action_sequence = ActionSequence(
                id=f"fusion_seq_{uuid.uuid4()}",
                voice_command_id=f"fusion_cmd_{uuid.uuid4()}",
                sequence=action_steps,
                description=f"Fused action sequence for: {intent}",
                status=ActionSequenceStatus.PENDING
            )
            
            # Validate the action sequence
            validation_issues = self.action_validator.validate_action_sequence(action_sequence)
            if validation_issues:
                print(f"Generated action sequence has validation issues: {len(validation_issues)} issues")
                for issue in validation_issues:
                    print(f"  - {issue}")
            
            return action_sequence
            
        except Exception as e:
            print(f"Error generating action sequence from fusion: {str(e)}")
            return None
    
    async def process_multimodal_command(self, 
                                       voice_command: str,
                                       vision_data: Optional[Dict[str, Any]] = None,
                                       sensor_data: Optional[Dict[str, Any]] = None) -> Optional[ActionSequence]:
        """
        Process a multimodal command through the complete fusion pipeline.
        
        :param voice_command: Natural language command
        :param vision_data: Vision data (optional)
        :param sensor_data: Sensor data (optional)
        :return: Action sequence or None if processing failed
        """
        print(f"Processing multimodal command: '{voice_command}'")
        
        # Create multimodal input
        multimodal_input = await self.create_multimodal_input(
            voice_command, vision_data, sensor_data
        )
        
        # Validate multimodal input
        validation_result = self.validation_service.validate_multimodal_input(multimodal_input)
        if not validation_result.is_valid:
            print(f"Invalid multimodal input: {validation_result.errors}")
            return None
        
        # Fuse modalities
        fusion_result, fusion_confidence = await self.fuse_modalities(multimodal_input)
        
        print(f"Fusion result: {fusion_result}, confidence: {fusion_confidence:.3f}")
        
        # Generate action sequence from fusion result
        action_sequence = await self.generate_action_sequence_from_fusion(fusion_result, fusion_confidence)
        
        return action_sequence
    
    async def demonstrate_early_fusion_approach(self) -> Dict[str, Any]:
        """
        Demonstrate early fusion approach where modalities are fused at the feature level.
        
        :return: Results of early fusion demonstration
        """
        print("Demonstrating Early Fusion Approach")
        print("-" * 40)
        
        # Example: Simple navigation command with visual context
        voice_command = "Go to the red cup"
        
        # Vision data showing a red cup at a specific location
        vision_data = {
            "objects": [
                {
                    "class": "cup",
                    "color": "red",
                    "position": [1.2, 0.8, 0.8],  # x, y, z in meters
                    "bbox": [0.2, 0.3, 0.4, 0.5],  # normalized coordinates
                    "confidence": 0.92,
                    "id": "red_cup_1"
                },
                {
                    "class": "table",
                    "position": [1.0, 0.5, 0.0],
                    "confidence": 0.98
                }
            ],
            "scene_description": "A red cup is on a table"
        }
        
        sensor_data = {
            "timestamp": datetime.now().timestamp()
        }
        
        # Switch to early fusion method temporarily
        original_method = self.fusion_service.fusion_method
        self.fusion_service.fusion_method = FusionMethod.EARLY_FUSION
        
        # Process with early fusion
        result = await self.process_multimodal_command(voice_command, vision_data, sensor_data)
        
        # Restore original method
        self.fusion_service.fusion_method = original_method
        
        return {
            "fusion_method": "early",
            "command": voice_command,
            "action_sequence": result.dict() if result else None,
            "notes": "Early fusion combines raw features from all modalities"
        }
    
    async def demonstrate_late_fusion_approach(self) -> Dict[str, Any]:
        """
        Demonstrate late fusion approach where modalities are fused at the decision level.
        
        :return: Results of late fusion demonstration
        """
        print("Demonstrating Late Fusion Approach")
        print("-" * 40)
        
        # Example: Complex manipulation command
        voice_command = "Grasp the object that is red and cylindrical"
        
        # Vision data showing multiple objects
        vision_data = {
            "objects": [
                {
                    "class": "cup",
                    "color": "red",
                    "shape": "cylindrical",
                    "position": [1.1, 0.7, 0.8],
                    "confidence": 0.88,
                    "id": "red_cylindrical_cup"
                },
                {
                    "class": "ball",
                    "color": "red", 
                    "shape": "spherical",
                    "position": [0.8, 0.9, 0.8],
                    "confidence": 0.91,
                    "id": "red_ball"
                },
                {
                    "class": "box", 
                    "color": "blue",
                    "shape": "rectangular",
                    "position": [1.3, 0.6, 0.8],
                    "confidence": 0.85,
                    "id": "blue_box"
                }
            ],
            "scene_description": "Multiple objects with different colors and shapes"
        }
        
        sensor_data = {
            "timestamp": datetime.now().timestamp()
        }
        
        # Switch to late fusion method temporarily
        original_method = self.fusion_service.fusion_method
        self.fusion_service.fusion_method = FusionMethod.LATE_FUSION
        
        # Process with late fusion
        result = await self.process_multimodal_command(voice_command, vision_data, sensor_data)
        
        # Restore original method
        self.fusion_service.fusion_method = original_method
        
        return {
            "fusion_method": "late",
            "command": voice_command,
            "action_sequence": result.dict() if result else None,
            "notes": "Late fusion combines decisions from individual modalities"
        }
    
    async def demonstrate_attention_based_fusion(self) -> Dict[str, Any]:
        """
        Demonstrate attention-based fusion approach using learned attention weights.
        
        :return: Results of attention-based fusion demonstration
        """
        print("Demonstrating Attention-Based Fusion Approach")
        print("-" * 40)
        
        # Example: Command where visual information is critical
        voice_command = "Go to the object I'm pointing to"
        
        # Vision data showing the robot's view with a highlighted object
        vision_data = {
            "objects": [
                {
                    "class": "cup",
                    "color": "green",
                    "position": [1.5, 0.5, 0.8],
                    "confidence": 0.95,
                    "id": "target_cup",
                    "pointing_indicator": True  # Indicates this is the pointed-at object
                },
                {
                    "class": "bottle",
                    "color": "transparent",
                    "position": [1.2, 0.8, 0.8],
                    "confidence": 0.78
                },
                {
                    "class": "box",
                    "color": "white",
                    "position": [0.9, 0.3, 0.8],
                    "confidence": 0.82
                }
            ],
            "scene_description": "Robot's view with a highlighted target object",
            "pointing_target": [1.5, 0.5, 0.8]  # Coordinates of pointed target
        }
        
        sensor_data = {
            "timestamp": datetime.now().timestamp(),
            "gaze_direction": [1.5, 0.5, 0.8],  # Simulated gaze direction matching vision
            "arm_configuration": "pointing_right"
        }
        
        # Process with attention-based fusion (default method)
        result = await self.process_multimodal_command(voice_command, vision_data, sensor_data)
        
        return {
            "fusion_method": "attention",
            "command": voice_command,
            "action_sequence": result.dict() if result else None,
            "notes": "Attention-based fusion weights modalities based on relevance"
        }
    
    async def demonstrate_conflict_resolution(self) -> Dict[str, Any]:
        """
        Demonstrate conflict resolution between different modalities.
        
        :return: Results of conflict resolution demonstration
        """
        print("Demonstrating Conflict Resolution in Multimodal Fusion")
        print("-" * 60)
        
        # Example: Voice command says "kitchen" but vision shows "bedroom" scene
        voice_command = "Go to the kitchen"
        
        # Vision data showing bedroom objects
        vision_data = {
            "objects": [
                {
                    "class": "bed",
                    "position": [0.5, 0.5, 0.0],
                    "confidence": 0.95
                },
                {
                    "class": "nightstand",
                    "position": [1.0, 0.2, 0.0],
                    "confidence": 0.89
                },
                {
                    "class": "lamp",
                    "position": [0.9, 0.3, 0.6],
                    "confidence": 0.78
                }
            ],
            "scene_description": "Bedroom scene with bed, nightstand, and lamp"
        }
        
        sensor_data = {
            "timestamp": datetime.now().timestamp()
        }
        
        # Process the conflicting command
        print(f"Processing conflicting command: '{voice_command}' (current scene: bedroom)")
        
        # Create multimodal input
        multimodal_input = await self.create_multimodal_input(
            voice_command, vision_data, sensor_data
        )
        
        # Validate multimodal input
        validation_result = self.validation_service.validate_multimodal_input(multimodal_input)
        if not validation_result.is_valid:
            print(f"Invalid multimodal input: {validation_result.errors}")
            return {
                "command": voice_command,
                "conflict_detected": True,
                "validation_errors": validation_result.errors,
                "notes": "Input validation caught the conflict"
            }
        
        # Detect conflicts before fusion
        conflicts = self.conflict_resolver.detect_conflicts(
            {"text": voice_command}, vision_data, sensor_data
        )
        
        if conflicts:
            print(f"Detected {len(conflicts)} conflicts:")
            for i, (conf_type, source1_data, source2_data) in enumerate(conflicts):
                print(f"  {i+1}. {conf_type.value}: {source1_data} vs {source2_data}")
            
            # Resolve conflicts
            resolution_results = self.conflict_resolver.resolve_conflicts(
                conflicts, 
                {"text": voice_command}, 
                vision_data, 
                sensor_data
            )
            
            print(f"Applied {len(resolution_results)} resolution strategies:")
            for i, resolution in enumerate(resolution_results):
                print(f"  {i+1}. {resolution.strategy_used.value}: {resolution.conflict_type.value}")
        
        # Perform fusion with conflict-resolution results
        # In a real implementation, we'd use the resolution results to guide fusion
        # For this example, we'll proceed with normal fusion
        fusion_result, fusion_confidence = self.fusion_service.fuse_modalities(
            voice_data={"text": voice_command},
            vision_data=vision_data,
            sensor_data=sensor_data
        )
        
        print(f"Post-conflict-resolution fusion result: {fusion_result}")
        print(f"Confidence: {fusion_confidence:.3f}")
        
        return {
            "command": voice_command,
            "conflict_detected": len(conflicts) > 0,
            "conflicts_resolved": len(resolution_results),
            "fusion_result": fusion_result,
            "fusion_confidence": fusion_confidence,
            "resolution_strategies": [r.strategy_used.value for r in resolution_results]
        }
    
    async def run_complete_multimodal_fusion_example(self):
        """
        Run a complete example of multimodal fusion with various scenarios.
        """
        print("VLA Capstone - Complete Multimodal Fusion Example")
        print("=" * 80)
        
        try:
            # 1. Simple case (navigation to visible object)
            print("\n[1] Simple Navigation Example:")
            simple_nav_result = await self.process_multimodal_command(
                "Go to the red cup",
                vision_data={
                    "objects": [
                        {
                            "class": "cup",
                            "color": "red",
                            "position": [1.0, 0.5, 0.8],
                            "confidence": 0.92
                        }
                    ]
                }
            )
            
            if simple_nav_result:
                print(f"  Generated {len(simple_nav_result.sequence)}-step sequence")
            else:
                print("  Failed to generate action sequence")
            
            # 2. Complex manipulation example
            print("\n[2] Complex Manipulation Example:")
            manipulation_result = await self.process_multimodal_command(
                "Pick up the blue box and place it on the table",
                vision_data={
                    "objects": [
                        {
                            "class": "box",
                            "color": "blue",
                            "position": [1.2, 0.7, 0.8],
                            "confidence": 0.88,
                            "id": "blue_box_1"
                        },
                        {
                            "class": "table",
                            "position": [1.0, 0.5, 0.0],
                            "confidence": 0.95,
                            "id": "table_1"
                        }
                    ]
                }
            )
            
            if manipulation_result:
                print(f"  Generated {len(manipulation_result.sequence)}-step manipulation sequence")
            else:
                print("  Failed to generate manipulation sequence")
            
            # 3. Demonstrate different fusion methods
            print("\n[3] Fusion Method Comparisons:")
            early_fusion_result = await self.demonstrate_early_fusion_approach()
            late_fusion_result = await self.demonstrate_late_fusion_approach()
            attention_fusion_result = await self.demonstrate_attention_based_fusion()
            
            print(f"  Early Fusion: {early_fusion_result['action_sequence']['sequence'] if early_fusion_result['action_sequence'] else 'Failed'}")
            print(f"  Late Fusion: {late_fusion_result['action_sequence']['sequence'] if late_fusion_result['action_sequence'] else 'Failed'}")
            print(f"  Attention Fusion: {attention_fusion_result['action_sequence']['sequence'] if attention_fusion_result['action_sequence'] else 'Failed'}")
            
            # 4. Demonstrate conflict resolution
            print("\n[4] Conflict Resolution Example:")
            conflict_result = await self.demonstrate_conflict_resolution()
            print(f"  Conflicts detected: {conflict_result.get('conflict_detected', False)}")
            print(f"  Resolutions applied: {len(conflict_result.get('resolution_strategies', []))}")
            
            # 5. Confidence-based decision making
            print("\n[5] Confidence-Based Decision Making:")
            self.demonstrate_confidence_management()
            
            print("\n" + "=" * 80)
            print("Multimodal Fusion Example Completed Successfully!")
            
        except Exception as e:
            print(f"\nError in multimodal fusion example: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def demonstrate_confidence_management(self):
        """
        Demonstrate confidence-based decision making in multimodal fusion.
        """
        print("Demonstrating Confidence-Based Decision Making")
        print("-" * 50)
        
        # Example confidence scenarios
        confidence_scenarios = [
            {
                "name": "High visual, low language confidence",
                "voice_confidence": 0.4,
                "vision_confidence": 0.9,
                "sensor_confidence": 0.7,
                "description": "Trust vision more for object identification"
            },
            {
                "name": "High language, low visual confidence", 
                "voice_confidence": 0.9,
                "vision_confidence": 0.3,
                "sensor_confidence": 0.6,
                "description": "Rely on language command when vision is unreliable"
            },
            {
                "name": "All modalities high confidence",
                "voice_confidence": 0.85,
                "vision_confidence": 0.92,
                "sensor_confidence": 0.88,
                "description": "Fuse all modalities with high reliability"
            },
            {
                "name": "All modalities low confidence",
                "voice_confidence": 0.15,
                "vision_confidence": 0.25,
                "sensor_confidence": 0.2,
                "description": "Request clarification or abort"
            }
        ]
        
        for scenario in confidence_scenarios:
            print(f"\nScenario: {scenario['name']}")
            print(f"  Description: {scenario['description']}")
            print(f"  Voice confidence: {scenario['voice_confidence']:.2f}")
            print(f"  Vision confidence: {scenario['vision_confidence']:.2f}")
            print(f"  Sensor confidence: {scenario['sensor_confidence']:.2f}")
            
            # Calculate overall confidence using confidence manager
            overall_confidence = self.confidence_manager.calculate_overall_confidence(
                voice_confidence=scenario["voice_confidence"],
                vision_confidence=scenario["vision_confidence"],
                sensor_confidence=scenario["sensor_confidence"]
            )
            
            print(f"  Overall confidence: {overall_confidence:.2f}")
            
            # Determine if execution should proceed based on confidence
            should_execute = overall_confidence >= settings.minimum_confidence_score
            print(f"  Execute action: {'YES' if should_execute else 'NO'} (threshold: {settings.minimum_confidence_score})")
            
            if not should_execute:
                print(f"    Reason: Overall confidence ({overall_confidence:.2f}) below threshold ({settings.minimum_confidence_score})")


class AdvancedMultimodalFusionExample(MultimodalFusionExample):
    """
    Advanced multimodal fusion example with additional capabilities.
    """
    
    def __init__(self):
        super().__init__()
        
        # Additional advanced capabilities
        self.enable_domain_randomization = True
        self.enable_synthetic_data_generation = True
        self.enable_cross_modal_verification = True
        self.temporal_consistency_checking = True
        
        # Learning and adaptation parameters
        self.performance_history = []
        self.adaptation_threshold = 0.7  # Threshold for adapting fusion strategy
    
    async def generate_synthetic_multimodal_data(self, scenario_type: str = "navigation") -> MultimodalInput:
        """
        Generate synthetic multimodal data for training/testing.
        
        :param scenario_type: Type of scenario to generate data for
        :return: Synthetic multimodal input
        """
        synthetic_data = {
            "id": f"synthetic_mm_{uuid.uuid4()}",
            "timestamp": datetime.now(),
            "confidence": 0.9  # Synthetic data has high confidence
        }
        
        if scenario_type == "navigation":
            # Generate synthetic navigation scenario
            target_x, target_y = np.random.uniform(-5, 5, size=2)  # Random target position
            synthetic_data["voice_input_id"] = f"Go to position x={target_x:.1f}, y={target_y:.1f}"
            
            synthetic_data["visual_data"] = {
                "objects": [
                    {
                        "class": "navigation_target",
                        "position": [target_x, target_y, 0.0],
                        "confidence": 0.98,
                        "id": f"target_{uuid.uuid4()}"
                    },
                    {
                        "class": "obstacle",
                        "position": [target_x + np.random.uniform(-1, 1), target_y + np.random.uniform(-1, 1), 0.0],
                        "confidence": 0.85
                    }
                ]
            }
            
            synthetic_data["sensor_data"] = {
                "robot_position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "lidar_readings": [1.0] * 360  # Simulated clear path
            }
        
        elif scenario_type == "manipulation":
            # Generate synthetic manipulation scenario
            object_types = ["cup", "box", "ball", "bottle"]
            colors = ["red", "blue", "green", "yellow"]
            obj_type = np.random.choice(object_types)
            color = np.random.choice(colors)
            
            synthetic_data["voice_input_id"] = f"Pick up the {color} {obj_type}"
            
            obj_x, obj_y = np.random.uniform(0.5, 2.0, size=2)
            synthetic_data["visual_data"] = {
                "objects": [
                    {
                        "class": obj_type,
                        "color": color,
                        "position": [obj_x, obj_y, 0.8],
                        "confidence": 0.95,
                        "id": f"{color}_{obj_type}_{uuid.uuid4()}"
                    },
                    {
                        "class": "table",
                        "position": [obj_x-0.1, obj_y-0.1, 0.0],
                        "confidence": 0.99
                    }
                ]
            }
            
            synthetic_data["sensor_data"] = {
                "robot_position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "gripper_state": "open",
                "arm_configuration": "home"
            }
        
        else:
            # Default scenario
            synthetic_data["voice_input_id"] = "Perform a basic action"
            synthetic_data["visual_data"] = {
                "objects": [
                    {
                        "class": "generic_object",
                        "position": [1.0, 1.0, 0.8],
                        "confidence": 0.8
                    }
                ]
            }
            synthetic_data["sensor_data"] = {
                "robot_position": {"x": 0.0, "y": 0.0, "z": 0.0}
            }
        
        mm_input = MultimodalInput(**synthetic_data)
        return mm_input
    
    async def perform_cross_modal_verification(self, fusion_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform verification across modalities to ensure consistency.
        
        :param fusion_result: Result from multimodal fusion
        :return: Verification results
        """
        verification_results = {
            "consistent": True,
            "issues": [],
            "confidence_adjustments": [],
            "recommnedations": []
        }
        
        # Example verification checks
        if "target_location" in fusion_result.get("parameters", {}):
            target_loc = fusion_result["parameters"]["target_location"]
            
            # If there's a specific target object, verify it makes sense in the context
            if "target_object" in fusion_result["parameters"]:
                obj_class = fusion_result["parameters"]["target_object"]
                
                # This would check if the target location is sensible for the object type
                # For example, cups are usually on surfaces like tables
                if obj_class == "cup" and target_loc.get("z", 0) < 0.5:
                    verification_results["issues"].append(
                        f"Cup target location seems too low (z={target_loc['z']}) - cups are typically above surfaces"
                    )
        
        # Check for action consistency
        action_type = fusion_result.get("action_type", "")
        if action_type == "manipulation" and "navigation" in str(fusion_result.get("parameters", {})):
            # Navigation during manipulation might indicate a multi-step task
            verification_results["recommnedations"].append(
                "Detected navigation during manipulation request - consider breaking into separate navigation and manipulation steps"
            )
        
        # Check confidence consistency across modalities
        if "confidence_breakdown" in fusion_result:
            conf_breakdown = fusion_result["confidence_breakdown"]
            voice_conf = conf_breakdown.get("voice", 0.5)
            vision_conf = conf_breakdown.get("vision", 0.5)
            
            # Large mismatch might indicate conflicting information
            if abs(voice_conf - vision_conf) > 0.4:
                verification_results["issues"].append(
                    f"Large confidence mismatch between voice ({voice_conf:.2f}) and vision ({vision_conf:.2f})"
                )
        
        verification_results["consistent"] = len(verification_results["issues"]) == 0
        return verification_results
    
    async def adapt_fusion_strategy_based_on_performance(self) -> FusionMethod:
        """
        Adapt the fusion strategy based on recent performance history.
        
        :return: Recommended fusion method
        """
        if len(self.performance_history) < 5:
            # Not enough data to adapt, use default
            return FusionMethod.ATTENTION_BASED
        
        # Calculate recent success rate
        recent_successes = [item["success"] for item in self.performance_history[-10:]]
        success_rate = sum(recent_successes) / len(recent_successes)
        
        if success_rate >= self.adaptation_threshold:
            # If performing well, keep current strategy
            print(f"Performance good ({success_rate:.2f}), maintaining current fusion strategy")
            return self.fusion_service.fusion_method
        else:
            # If performing poorly, try a different strategy
            current_method = self.fusion_service.fusion_method
            
            if current_method == FusionMethod.ATTENTION_BASED:
                print(f"Performance poor ({success_rate:.2f}), switching from attention to late fusion")
                return FusionMethod.LATE_FUSION
            elif current_method == FusionMethod.LATE_FUSION:
                print(f"Performance poor ({success_rate:.2f}), switching from late to early fusion")
                return FusionMethod.EARLY_FUSION
            elif current_method == FusionMethod.EARLY_FUSION:
                print(f"Performance poor ({success_rate:.2f}), switching from early to attention fusion")
                return FusionMethod.ATTENTION_BASED
            else:
                return FusionMethod.ATTENTION_BASED  # Default fallback
    
    async def process_with_adaptive_fusion(self, 
                                         voice_command: str,
                                         vision_data: Optional[Dict[str, Any]] = None,
                                         sensor_data: Optional[Dict[str, Any]] = None) -> Optional[ActionSequence]:
        """
        Process a multimodal command using adaptive fusion strategy.
        
        :param voice_command: Natural language command
        :param vision_data: Vision data (optional)
        :param sensor_data: Sensor data (optional)
        :return: Action sequence or None if processing failed
        """
        # Determine the best fusion method based on recent performance
        recommended_method = await self.adapt_fusion_strategy_based_on_performance()
        
        # Temporarily change fusion method
        original_method = self.fusion_service.fusion_method
        self.fusion_service.fusion_method = recommended_method
        
        print(f"Using adaptive fusion method: {recommended_method.value}")
        
        try:
            # Process with the selected method
            result = await self.process_multimodal_command(voice_command, vision_data, sensor_data)
            
            # Record performance for future adaptation
            self.performance_history.append({
                "command": voice_command,
                "fusion_method": recommended_method.value,
                "success": result is not None,
                "timestamp": datetime.now()
            })
            
            # Keep only recent history
            if len(self.performance_history) > 50:
                self.performance_history = self.performance_history[-50:]
            
            return result
            
        finally:
            # Restore original method
            self.fusion_service.fusion_method = original_method
    
    async def run_advanced_multimodal_fusion_example(self):
        """
        Run the advanced multimodal fusion example with additional capabilities.
        """
        print("VLA Capstone - Advanced Multimodal Fusion Example")
        print("=" * 80)
        
        try:
            # 1. Generate synthetic training data
            print("\n[1] Generating Synthetic Multimodal Data:")
            synthetic_inputs = []
            for scenario_type in ["navigation", "manipulation", "perception"]:
                for i in range(3):  # Generate 3 examples of each type
                    synthetic_input = await self.generate_synthetic_multimodal_data(scenario_type)
                    synthetic_inputs.append(synthetic_input)
                    print(f"  Generated {scenario_type} example {i+1}")
            
            print(f"  Generated {len(synthetic_inputs)} synthetic examples")
            
            # 2. Adaptive fusion demonstration
            print("\n[2] Adaptive Fusion Strategy Demonstration:")
            adaptive_result = await self.process_with_adaptive_fusion(
                "Go to the kitchen and find the red cup",
                vision_data={
                    "objects": [
                        {
                            "class": "cup",
                            "color": "red",
                            "position": [1.5, 0.8, 0.8],
                            "confidence": 0.88
                        },
                        {
                            "class": "table",
                            "position": [1.0, 0.5, 0.0],
                            "confidence": 0.95
                        }
                    ]
                }
            )
            
            if adaptive_result:
                print(f"  Adaptive fusion generated {len(adaptive_result.sequence)}-step sequence")
            else:
                print("  Adaptive fusion failed to generate sequence")
            
            # 3. Cross-modal verification demonstration
            print("\n[3] Cross-Modal Verification Example:")
            
            # Create a fusion result that would have verification issues
            test_fusion_result = {
                "action_type": "manipulation",
                "parameters": {
                    "target_object": "cup",
                    "target_location": {"x": 0.3, "y": 0.2, "z": 0.1}  # Unusually low for a cup
                },
                "confidence_breakdown": {
                    "voice": 0.9,
                    "vision": 0.45  # Low vision confidence indicates possible mismatch
                }
            }
            
            verification = await self.perform_cross_modal_verification(test_fusion_result)
            print(f"  Verification consistent: {verification['consistent']}")
            print(f"  Issues found: {len(verification['issues'])}")
            if verification["issues"]:
                for issue in verification["issues"]:
                    print(f"    - {issue}")
            
            # 4. Temporal consistency demonstration
            print("\n[4] Temporal Consistency Example:")
            await self.demonstrate_temporal_consistency()
            
            # 5. Domain randomization example
            print("\n[5] Domain Randomization for Synthetic Data:")
            await self.demonstrate_domain_randomization()
            
            print("\n" + "=" * 80)
            print("Advanced Multimodal Fusion Example Completed Successfully!")
            
        except Exception as e:
            print(f"\nError in advanced multimodal fusion example: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def demonstrate_temporal_consistency(self):
        """
        Demonstrate temporal consistency checking for multimodal inputs.
        """
        print("Demonstrating Temporal Consistency Checking")
        print("-" * 50)
        
        # Simulate a sequence of related commands over time
        command_sequence = [
            ("Go to the table", {"objects": [{"class": "table", "position": [1.0, 0.5, 0.0]}]}),
            ("Find the cup on the table", {"objects": [{"class": "cup", "position": [1.2, 0.7, 0.8], "on_surface": "table"}]}),
            ("Pick up the cup", {"objects": [{"class": "cup", "position": [1.2, 0.7, 0.8], "status": "graspable"}]}),
            ("Move to the kitchen", {"objects": []}),  # Vision might not see kitchen specifically
            ("Place the cup on the counter", {"objects": [{"class": "counter", "position": [2.0, 1.0, 0.9]}]})
        ]
        
        previous_context = None
        consistency_issues = 0
        
        for i, (command, vision_data) in enumerate(command_sequence):
            print(f"\nStep {i+1}: {command}")
            
            # Create multimodal input
            mm_input = await self.create_multimodal_input(command, vision_data, {"timestamp": time.time()})
            
            # Check temporal consistency with previous context
            if previous_context:
                # In a real implementation, this would check for consistency between
                # the current state and the expected state after previous actions
                # For this example, we'll just simulate the check
                consistency_ok = await self._check_temporal_consistency(mm_input, previous_context)
                
                if not consistency_ok:
                    consistency_issues += 1
                    print(f"  ⚠️  Potential temporal consistency issue detected")
                else:
                    print(f"  ✓ Temporal consistency maintained")
            else:
                print(f"  - No previous context to check against")
            
            # Update context for next iteration
            previous_context = {
                "command": command,
                "vision_data": vision_data,
                "timestamp": time.time()
            }
        
        print(f"\nTotal consistency issues detected: {consistency_issues}")
    
    async def _check_temporal_consistency(self, current_input: MultimodalInput, previous_context: Dict[str, Any]) -> bool:
        """
        Check temporal consistency between current input and previous context.
        
        :param current_input: Current multimodal input
        :param previous_context: Previous context
        :return: True if consistent, False otherwise
        """
        # This is a simplified check - in reality, this would be much more complex
        # looking at robot state, object locations, environmental changes, etc.
        
        # For example: if the previous action was "pick up cup" and now we're
        # asked to "find the cup", the cup should no longer be at its previous location
        prev_command = previous_context.get("command", "").lower()
        current_command = current_input.voice_input_id.lower()
        
        # Check if we picked up an object but now are asked to find it in the same location
        if ("pick" in prev_command or "grasp" in prev_command or "take" in prev_command):
            if "find" in current_command or "locate" in current_command or "detect" in current_command:
                # Could be inconsistent if the object was picked up but is expected to still be visible
                return False  # Simulate inconsistency for this example
        
        return True  # Default to consistent
    
    async def demonstrate_domain_randomization(self):
        """
        Demonstrate domain randomization for generating diverse synthetic data.
        """
        print("Demonstrating Domain Randomization")
        print("-" * 40)
        
        # Simulate domain randomization parameters
        lighting_conditions = ["bright", "dim", "backlit", "shadowed"]
        textures = ["wood", "metal", "plastic", "fabric", "tile"]
        backgrounds = ["office", "home", "kitchen", "outdoor", "industrial"]
        
        print("Generating synthetic data with domain randomization:")
        
        for i in range(3):  # Generate 3 randomized scenarios
            lighting = np.random.choice(lighting_conditions)
            texture = np.random.choice(textures)
            background = np.random.choice(backgrounds)
            
            print(f"  Scenario {i+1}: Lighting={lighting}, Texture={texture}, Background={background}")
            
            # In a real implementation, this would randomize the simulation environment
            # and generate corresponding synthetic data
            # For this example, we'll just simulate the process
            synthetic_input = await self.generate_synthetic_multimodal_data("navigation")
            print(f"    Generated synthetic input: {synthetic_input.id}")
        
        print(f"\nDomain randomization helps improve generalization across different environments")


class EducationalMultimodalFusionExample(AdvancedMultimodalFusionExample):
    """
    Educational example with explanations and learning components for students.
    """
    
    def __init__(self):
        super().__init__()
        self.explanation_enabled = True
    
    async def process_with_explanation(self, 
                                     voice_command: str,
                                     vision_data: Optional[Dict[str, Any]] = None,
                                     sensor_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a multimodal command with detailed explanations for educational purposes.
        
        :param voice_command: Natural language command
        :param vision_data: Vision data (optional)
        :param sensor_data: Sensor data (optional)
        :return: Processing results with explanations
        """
        print(f"\n🔄 Processing multimodal command: '{voice_command}'")
        print("="*60)
        
        # Step 1: Create multimodal input
        print(f"📝 Step 1: Creating multimodal input from voice command")
        multimodal_input = await self.create_multimodal_input(voice_command, vision_data, sensor_data)
        print(f"   Created multimodal input: {multimodal_input.id}")
        
        # Step 2: Validate input
        print(f"\n✅ Step 2: Validating multimodal input")
        validation_result = self.validation_service.validate_multimodal_input(multimodal_input)
        if validation_result.is_valid:
            print(f"   ✅ Validation passed")
        else:
            print(f"   ❌ Validation failed: {validation_result.errors}")
            return {
                "success": False,
                "error": f"Validation failed: {validation_result.errors}",
                "explanation": "The input did not pass validation checks",
                "multimodal_input": multimodal_input.dict()
            }
        
        # Step 3: Detect conflicts
        print(f"\n🔍 Step 3: Detecting potential conflicts between modalities")
        voice_data = {"text": multimodal_input.voice_input_id} if multimodal_input.voice_input_id else None
        conflicts = self.conflict_resolver.detect_conflicts(voice_data, vision_data, sensor_data)
        if conflicts:
            print(f"   ⚠️  Detected {len(conflicts)} conflicts:")
            for i, (conf_type, source1, source2) in enumerate(conflicts):
                print(f"     {i+1}. {conf_type.value}: {source1} vs {source2}")
            
            print(f"\n🔧 Step 3b: Resolving conflicts")
            resolution_results = self.conflict_resolver.resolve_conflicts(conflicts, voice_data, vision_data, sensor_data)
            print(f"   Applied {len(resolution_results)} resolution strategies")
        else:
            print(f"   ✅ No conflicts detected")
        
        # Step 4: Perform fusion
        print(f"\n🔗 Step 4: Performing multimodal fusion (method: {self.fusion_service.fusion_method.value})")
        fusion_result, fusion_confidence = self.fusion_service.fuse_modalities(
            voice_data=voice_data,
            vision_data=vision_data,
            sensor_data=sensor_data
        )
        print(f"   Fusion result: {fusion_result}")
        print(f"   Fusion confidence: {fusion_confidence:.3f}")
        
        # Step 5: Cross-modal verification
        print(f"\n🔍 Step 5: Performing cross-modal verification")
        verification = await self.perform_cross_modal_verification({
            "parameters": fusion_result.get("parameters", {}),
            "action_type": fusion_result.get("action_type", ""),
            "confidence_breakdown": {"voice": 0.8, "vision": 0.9}  # Simulated
        })
        print(f"   Verification consistent: {verification['consistent']}")
        if verification['issues']:
            print(f"   Issues found: {verification['issues']}")
        
        # Step 6: Generate action sequence
        print(f"\n🤖 Step 6: Generating action sequence with LLM")
        action_sequence = await self.generate_action_sequence_from_fusion(fusion_result, fusion_confidence)
        
        if action_sequence:
            print(f"   ✅ Generated action sequence with {len(action_sequence.sequence)} steps:")
            for i, step in enumerate(action_sequence.sequence):
                print(f"     {i+1}. {step.action_type.value}: {step.parameters}")
        else:
            print(f"   ❌ Failed to generate action sequence")
        
        # Step 7: Validate action sequence
        print(f"\n✅ Step 7: Validating action sequence")
        validation_issues = self.action_validator.validate_action_sequence(action_sequence) if action_sequence else []
        if validation_issues:
            print(f"   ⚠️  Validation issues: {len(validation_issues)}")
            for issue in validation_issues:
                print(f"     - {issue}")
        else:
            print(f"   ✅ Action sequence validation passed")
        
        print(f"\n🎯 Final Result:")
        if action_sequence:
            print(f"   ✅ Multimodal command processed successfully")
            print(f"   📋 Action sequence ID: {action_sequence.id}")
            print(f"   🔢 Steps: {len(action_sequence.sequence)}")
            print(f"   💪 Fusion confidence: {fusion_confidence:.3f}")
        else:
            print(f"   ❌ Process failed to generate actions")
        
        return {
            "success": action_sequence is not None,
            "action_sequence": action_sequence.dict() if action_sequence else None,
            "fusion_result": fusion_result,
            "fusion_confidence": fusion_confidence,
            "validation_result": validation_result,
            "conflicts": [c[0].value for c in conflicts] if conflicts else [],
            "explanation": "Complete multimodal processing pipeline executed",
            "timestamp": datetime.now()
        }
    
    async def run_educational_example(self):
        """
        Run educational example with detailed explanations.
        """
        print("🎓 VLA Capstone - Educational Multimodal Fusion Example")
        print("=" * 80)
        
        # Educational examples with increasing complexity
        educational_examples = [
            {
                "command": "Move forward 1 meter",
                "vision_data": None,
                "explanation": "Simple navigation command to demonstrate basic processing"
            },
            {
                "command": "Go to the red cup",
                "vision_data": {
                    "objects": [
                        {"class": "cup", "color": "red", "position": [1.0, 0.5, 0.8], "confidence": 0.92}
                    ]
                },
                "explanation": "Navigation command with specific visual target"
            },
            {
                "command": "Pick up the blue box",
                "vision_data": {
                    "objects": [
                        {"class": "box", "color": "blue", "position": [1.2, 0.7, 0.8], "confidence": 0.88}
                    ]
                },
                "explanation": "Manipulation command with visual confirmation"
            },
            {
                "command": "Find the green bottle and bring it to me",
                "vision_data": {
                    "objects": [
                        {"class": "bottle", "color": "green", "position": [2.0, 1.0, 0.8], "confidence": 0.85},
                        {"class": "table", "position": [1.5, 0.5, 0.0], "confidence": 0.98}
                    ]
                },
                "explanation": "Complex command with perception, navigation, and manipulation"
            }
        ]
        
        for i, example in enumerate(educational_examples):
            print(f"\n📚 Example {i+1}: {example['command']}")
            print(f"   Purpose: {example['explanation']}")
            
            result = await self.process_with_explanation(
                example["command"],
                example["vision_data"]
            )
            
            print(f"   Result: {'✅ Success' if result['success'] else '❌ Failed'}")
            print(f"   Action steps: {len(result['action_sequence']['sequence']) if result['action_sequence'] else 0}")
        
        print("\n" + "=" * 80)
        print("🎓 Educational Multimodal Fusion Example Completed!")
        
        print("\n📋 Key Learning Points:")
        print("   1. Multimodal fusion combines multiple sensory inputs for better understanding")
        print("   2. Conflict detection and resolution handle discrepancies between modalities")
        print("   3. Confidence management determines when to proceed or request clarification")
        print("   4. Cross-modal verification ensures consistency across modalities")
        print("   5. Action validation ensures executability of generated sequences")


def run_multimodal_fusion_examples():
    """
    Run the multimodal fusion integration examples.
    """
    print("VLA Capstone - Multimodal Fusion Integration Examples")
    print("=" * 80)
    
    # Basic example
    print("\n[1] Running Basic Multimodal Fusion Example...")
    basic_example = MultimodalFusionExample()
    asyncio.run(basic_example.run_complete_multimodal_fusion_example())
    
    print("\n" + "-" * 80)
    
    # Advanced example
    print("\n[2] Running Advanced Multimodal Fusion Example...")
    advanced_example = AdvancedMultimodalFusionExample()
    asyncio.run(advanced_example.run_advanced_multimodal_fusion_example())
    
    print("\n" + "-" * 80)
    
    # Educational example
    print("\n[3] Running Educational Multimodal Fusion Example...")
    educational_example = EducationalMultimodalFusionExample()
    asyncio.run(educational_example.run_educational_example())
    
    print("\n" + "=" * 80)
    print("All Multimodal Fusion Integration Examples Completed!")


# Example of batch processing multiple multimodal inputs
async def batch_multimodal_processing_example():
    """
    Example of processing multiple multimodal inputs in batch.
    """
    print("Batch Multimodal Processing Example")
    print("-" * 40)
    
    fusion_service = MultimodalFusionExample()
    
    # Create a batch of multimodal inputs to process
    batch_inputs = [
        {
            "voice_command": "Go to the kitchen",
            "vision_data": {
                "objects": [{"class": "kitchen", "position": [3.0, 2.0, 0.0]}]  # Simulated
            }
        },
        {
            "voice_command": "Pick up the red cup",
            "vision_data": {
                "objects": [
                    {"class": "cup", "color": "red", "position": [1.0, 0.5, 0.8], "confidence": 0.9}
                ]
            }
        },
        {
            "voice_command": "Move to the table",
            "vision_data": {
                "objects": [
                    {"class": "table", "position": [1.5, 0.0, 0.0], "confidence": 0.95}
                ]
            }
        }
    ]
    
    results = []
    for i, input_data in enumerate(batch_inputs):
        print(f"\nProcessing batch item {i+1}/{len(batch_inputs)}: '{input_data['voice_command']}'")
        
        sequence = await fusion_service.process_multimodal_command(
            input_data["voice_command"],
            input_data["vision_data"]
        )
        
        result = {
            "index": i,
            "command": input_data["voice_command"],
            "success": sequence is not None,
            "steps": len(sequence.sequence) if sequence else 0,
            "timestamp": datetime.now().isoformat()
        }
        results.append(result)
    
    print(f"\nBatch processing completed:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['command']} -> {result['steps']} steps")
    
    successful = sum(1 for r in results if r["success"])
    print(f"\nSummary: {successful}/{len(results)} commands processed successfully")


if __name__ == "__main__":
    # Run the main examples
    run_multimodal_fusion_examples()
    
    print("\n" + "="*80)
    print("Additional Examples:")
    
    # Run batch processing example
    print("\n[4] Batch Multimodal Processing Example:")
    asyncio.run(batch_multimodal_processing_example())
    
    print(f"\n🎉 All multimodal fusion examples completed!")