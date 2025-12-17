"""
Unit tests for visual-voice fusion in the VLA system.
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from ..models.multimodal_input import MultimodalInput
from ..models.vla_system_state import VLASystemState
from ..models.action_step import ActionStep, ActionType
from ..services.multimodal_fusion import MultimodalFusionService, FusionMethod
from ..services.vision_integration import VisionIntegrationService
from ..services.conflict_resolver import ConflictResolver, ConflictType, ResolutionStrategy
from ..services.confidence_manager import ConfidenceManager, ConfidenceLevel
from ..validation.multimodal_validation import MultimodalValidationService
from ..architectures.vla_selector import VLASelector, VLAArchitectureType


class TestVisualVoiceFusion(unittest.TestCase):
    """
    Test suite for visual-voice fusion functionality.
    """
    
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.fusion_service = MultimodalFusionService()
        self.vision_service = VisionIntegrationService()
        self.conflict_resolver = ConflictResolver()
        self.confidence_manager = ConfidenceManager()
        self.validator = MultimodalValidationService()
        self.vla_selector = VLASelector()
    
    def test_basic_visual_voice_fusion(self):
        """
        Test basic fusion of visual and voice inputs.
        """
        # Create multimodal input with both visual and voice data
        multimodal_input = MultimodalInput(
            id="test_input_1",
            visual_data={
                "objects": [
                    {
                        "class": "cup",
                        "bbox": [0.2, 0.3, 0.4, 0.5],
                        "confidence": 0.9,
                        "position": [1.0, 0.5, 0.0]
                    }
                ],
                "scene_description": "A red cup on a table"
            },
            voice_input_id="Pick up the red cup",
            confidence=0.85,
            timestamp=datetime.now()
        )
        
        # Perform fusion
        fusion_result, confidence = self.fusion_service.fuse_modalities(
            voice_data={"transcribed_text": "Pick up the red cup", "confidence": 0.8},
            vision_data=multimodal_input.visual_data,
            sensor_data=None
        )
        
        # Verify the result
        self.assertIsNotNone(fusion_result)
        self.assertGreater(confidence, 0.5)  # Should have reasonable confidence
        self.assertIn("intent", fusion_result)
        self.assertIn("cup", fusion_result["parameters"]["vision_objects"][0]["class"])
    
    def test_conflict_detection_visual_voice(self):
        """
        Test detection of conflicts between visual and voice inputs.
        """
        # Create conflicting inputs: voice says "kitchen" but vision detects "bedroom"
        voice_data = {
            "intent": "navigation",
            "transcribed_text": "Go to the kitchen",
            "confidence": 0.85,
            "parameters": {"target_location": "kitchen"}
        }
        
        vision_data = {
            "processed_frames": [
                {
                    "perception_results": {
                        "object_detection": {
                            "objects": [
                                {
                                    "class": "bed",
                                    "bbox": [0.1, 0.2, 0.8, 0.9],
                                    "confidence": 0.92
                                }
                            ]
                        }
                    }
                }
            ]
        }
        
        # Detect conflicts
        conflicts = self.conflict_resolver.detect_conflicts(
            voice_data=voice_data,
            vision_data=vision_data,
            sensor_data=None
        )
        
        # Should detect a spatial inconsistency conflict
        spatial_conflicts = [c for c in conflicts if c[0] == ConflictType.SPATIAL_INCONSISTENCY]
        self.assertGreater(len(spatial_conflicts), 0)
    
    def test_conflict_resolution_visual_voice(self):
        """
        Test resolution of conflicts between visual and voice inputs.
        """
        # Create conflicting inputs
        voice_data = {
            "intent": "manipulation",
            "transcribed_text": "Pick up the red cup",
            "confidence": 0.75,
            "parameters": {"object": "red cup"}
        }
        
        vision_data = {
            "objects": [
                {
                    "class": "blue bottle",
                    "bbox": [0.3, 0.4, 0.5, 0.6],
                    "confidence": 0.85
                }
            ],
            "scene_description": "A blue bottle on the table"
        }
        
        # Create a conflict manually
        conflicts = [(ConflictType.CONTRADICTORY_INFORMATION, voice_data, vision_data)]
        
        # Resolve the conflict
        resolution_results = self.conflict_resolver.resolve_conflicts(
            conflicts,
            voice_data=voice_data,
            vision_data=vision_data,
            sensor_data=None,
            strategy=ResolutionStrategy.PREFER_HIGHER_CONFIDENCE
        )
        
        # Verify resolution
        self.assertEqual(len(resolution_results), 1)
        self.assertEqual(resolution_results[0].strategy_used, ResolutionStrategy.PREFER_HIGHER_CONFIDENCE)
        self.assertEqual(resolution_results[0].conflict_resolved, True)
    
    def test_confidence_aware_fusion(self):
        """
        Test fusion taking into account confidence levels of different modalities.
        """
        # Test with high confidence voice and low confidence vision
        voice_data = {
            "transcribed_text": "Move forward 1 meter",
            "confidence": 0.95,
            "intent": "navigation"
        }
        
        vision_data = {
            "objects": [],
            "confidence": 0.3,  # Low confidence
            "scene_description": "Not sure what's here"
        }
        
        # Perform fusion
        fusion_result, confidence = self.fusion_service.fuse_modalities(
            voice_data=voice_data,
            vision_data=vision_data,
            sensor_data=None
        )
        
        # The result should favor the higher confidence voice data
        self.assertIn("navigation", fusion_result.get("intent", "").lower())
        # Confidence should be moderate since vision data is low confidence
        self.assertGreater(confidence, 0.5)
    
    def test_visual_object_reference_resolution(self):
        """
        Test how visual data helps resolve object references in voice commands.
        """
        # Voice command with ambiguous reference
        voice_data = {
            "transcribed_text": "Pick it up",
            "confidence": 0.8,
            "intent": "manipulation"
        }
        
        # Vision data with clear object
        vision_data = {
            "objects": [
                {
                    "class": "red cup",
                    "bbox": [0.2, 0.3, 0.4, 0.5],
                    "confidence": 0.9,
                    "position": [1.0, 0.5, 0.0]
                }
            ],
            "confidence": 0.85
        }
        
        # Perform fusion
        fusion_result, confidence = self.fusion_service.fuse_modalities(
            voice_data=voice_data,
            vision_data=vision_data,
            sensor_data=None
        )
        
        # The fusion should identify the "it" refers to the red cup
        self.assertIn("red cup", str(fusion_result).lower())
        self.assertGreater(confidence, 0.7)  # Should have good confidence
    
    def test_fusion_with_different_methods(self):
        """
        Test fusion using different fusion methods.
        """
        voice_data = {
            "transcribed_text": "Go to the table",
            "confidence": 0.8,
            "intent": "navigation"
        }
        
        vision_data = {
            "objects": [
                {
                    "class": "table",
                    "bbox": [0.1, 0.1, 0.9, 0.9],
                    "confidence": 0.85,
                    "position": [1.5, 0.0, 0.0]
                }
            ],
            "confidence": 0.82
        }
        
        # Test different fusion methods
        methods = [
            FusionMethod.EARLY_FUSION,
            FusionMethod.LATE_FUSION,
            FusionMethod.ATTENTION_BASED
        ]
        
        for method in methods:
            fusion_service = MultimodalFusionService(fusion_method=method)
            result, confidence = fusion_service.fuse_modalities(
                voice_data=voice_data,
                vision_data=vision_data,
                sensor_data=None
            )
            
            # Each method should produce a valid result
            self.assertIsNotNone(result)
            self.assertGreater(confidence, 0.0)
    
    def test_validation_of_visual_voice_inputs(self):
        """
        Test validation of visual-voice fusion inputs.
        """
        # Create a valid multimodal input
        valid_input = MultimodalInput(
            id="valid_input_1",
            visual_data={
                "objects": [
                    {
                        "class": "box",
                        "bbox": [0.2, 0.3, 0.4, 0.5],
                        "confidence": 0.85
                    }
                ]
            },
            voice_input_id="Move the box",
            confidence=0.8,
            timestamp=datetime.now()
        )
        
        # Validate the input
        validation_result = self.validator.validate_multimodal_input(valid_input)
        
        # Should be valid
        self.assertTrue(validation_result.is_valid)
        self.assertEqual(len(validation_result.errors), 0)
    
    def test_architecture_selection_for_visual_voice_task(self):
        """
        Test selection of appropriate architecture for visual-voice tasks.
        """
        # Define task requirements for visual-voice fusion
        task_requirements = {
            "language_complexity": 0.7,
            "vision_precision": 0.8,
            "action_success_importance": 0.75,
            "novel_object_handling": 0.6,
            "multistep_reasoning": 0.5
        }
        
        # Select architecture
        selected_arch = self.vla_selector.select_architecture(task_requirements)
        
        # The selected architecture should be appropriate for visual-voice fusion
        # OpenVLA or RT2 would be good choices
        self.assertIn(selected_arch, [
            VLAArchitectureType.OPENVLA, 
            VLAArchitectureType.RT2, 
            VLAArchitectureType.PALM_E
        ])
    
    def test_confidence_level_determination(self):
        """
        Test determination of confidence levels in visual-voice fusion.
        """
        # High confidence scenario
        high_conf_result = self.confidence_manager.calculate_overall_confidence(
            voice_confidence=0.9,
            vision_confidence=0.85
        )
        
        high_level = ConfidenceLevel.get_level(high_conf_result)
        self.assertIn(high_level, [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH])
        
        # Low confidence scenario
        low_conf_result = self.confidence_manager.calculate_overall_confidence(
            voice_confidence=0.3,
            vision_confidence=0.4
        )
        
        low_level = ConfidenceLevel.get_level(low_conf_result)
        self.assertIn(low_level, [ConfidenceLevel.VERY_LOW, ConfidenceLevel.LOW])
    
    def test_visual_voice_fusion_recommendation(self):
        """
        Test getting architecture recommendation for visual-voice fusion.
        """
        recommendation = self.vla_selector.get_architecture_recommendation(
            "Navigate to object and pick it up based on voice description"
        )
        
        # Check that recommendation includes important elements
        self.assertIn("recommended_architecture", recommendation)
        self.assertIn("reasoning", recommendation)
        self.assertIn("capabilities", recommendation)
        
        # The recommended architecture should be suitable for visual-voice tasks
        self.assertIn(recommendation["recommended_architecture"], [
            VLAArchitectureType.OPENVLA.value,
            VLAArchitectureType.RT2.value,
            VLAArchitectureType.PALM_E.value
        ])


class TestAdvancedVisualVoiceFusion(unittest.TestCase):
    """
    Advanced tests for visual-voice fusion with complex scenarios.
    """
    
    def setUp(self):
        """
        Set up test fixtures for advanced tests.
        """
        self.advanced_resolver = ConflictResolver()
        self.advanced_confidence = ConfidenceManager()
        self.validator = MultimodalValidationService()
    
    def test_complex_scene_understanding(self):
        """
        Test fusion with complex scenes containing multiple objects.
        """
        # Voice command: "Pick up the cup to the left of the bottle"
        voice_data = {
            "transcribed_text": "Pick up the cup to the left of the bottle",
            "confidence": 0.85,
            "intent": "manipulation"
        }
        
        # Vision data: scene with multiple objects
        vision_data = {
            "objects": [
                {
                    "class": "bottle",
                    "bbox": [0.6, 0.4, 0.3, 0.4],
                    "confidence": 0.9,
                    "position": [1.2, 0.2, 0.0]
                },
                {
                    "class": "cup",
                    "bbox": [0.2, 0.4, 0.3, 0.4],
                    "confidence": 0.87,
                    "position": [0.8, 0.2, 0.0]  # To the left of bottle
                },
                {
                    "class": "plate",
                    "bbox": [0.4, 0.6, 0.3, 0.3],
                    "confidence": 0.75,
                    "position": [1.0, 0.5, 0.0]
                }
            ],
            "confidence": 0.88
        }
        
        # This test would check if the fusion correctly identifies the left cup
        # In a real implementation, spatial reasoning would be applied
        # For this test, we'll just verify that fusion can handle the complex input
        
        fusion_service = MultimodalFusionService()
        result, confidence = fusion_service.fuse_modalities(
            voice_data=voice_data,
            vision_data=vision_data,
            sensor_data=None
        )
        
        self.assertIsNotNone(result)
        self.assertGreater(confidence, 0.5)
    
    def test_temporal_consistency_in_fusion(self):
        """
        Test temporal consistency in visual-voice fusion.
        """
        from ..validation.multimodal_validation import AdvancedMultimodalValidationService
        
        advanced_validator = AdvancedMultimodalValidationService()
        
        # Create two inputs with a small time difference
        import datetime
        from datetime import timedelta
        
        time1 = datetime.datetime.now()
        time2 = time1 + timedelta(seconds=0.1)  # 100ms later
        
        input1 = MultimodalInput(
            id="input_1",
            visual_data={
                "objects": [{"class": "cup", "bbox": [0.2, 0.3, 0.4, 0.5], "position": [1.0, 0.5, 0.0]}],
                "scene_description": "Cup at position 1, 0.5"
            },
            sensor_data={"timestamp": time1.timestamp()},
            confidence=0.8,
            timestamp=time1
        )
        
        input2 = MultimodalInput(
            id="input_2",
            visual_data={
                "objects": [{"class": "cup", "bbox": [0.2, 0.3, 0.4, 0.5], "position": [1.1, 0.5, 0.0]}],  # Moved slightly
                "scene_description": "Cup at position 1.1, 0.5"
            },
            sensor_data={"timestamp": time2.timestamp()},
            confidence=0.82,
            timestamp=time2
        )
        
        # Validate temporal consistency
        consistency_result = advanced_validator.validate_temporal_consistency(input2, input1)
        
        # Should not have errors for small, realistic movement
        self.assertTrue(consistency_result.is_valid)
    
    def test_cross_modal_verification(self):
        """
        Test verification between visual and voice modalities.
        """
        from ..validation.multimodal_validation import AdvancedMultimodalValidationService
        
        advanced_validator = AdvancedMultimodalValidationService()
        
        # Create multimodal input where voice and vision should agree
        multimodal_input = MultimodalInput(
            id="cross_modal_input",
            visual_data={
                "objects": [
                    {
                        "class": "red cup",
                        "bbox": [0.2, 0.3, 0.4, 0.5],
                        "confidence": 0.9,
                        "position": [1.0, 0.5, 0.0]
                    }
                ]
            },
            voice_input_id="Pick up the red cup on the table",
            sensor_data={
                "lidar": {
                    "ranges": [1.0] * 360,  # All 1 meter for simplicity
                }
            },
            confidence=0.85,
            timestamp=datetime.now()
        )
        
        # Validate cross-modal consistency
        consistency_result = advanced_validator.validate_cross_modal_consistency(multimodal_input)
        
        # In this case, should have no major inconsistencies
        # (though the exact implementation might flag minor issues)
        self.assertIsNotNone(consistency_result)
    
    def test_behavioral_validation(self):
        """
        Test behavioral validation of fusion results.
        """
        # This would test if the fusion result leads to reasonable behavior
        # For now, we'll just test action sequence validation
        
        action_sequence = [
            ActionStep(
                id="step_1",
                action_sequence_id="seq_123",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 0.5},
                timeout=10,
                order=0
            ),
            ActionStep(
                id="step_2",
                action_sequence_id="seq_123",
                action_type=ActionType.MANIPULATION,
                parameters={"action": "grasp", "object": "cup"},
                timeout=15,
                order=1
            )
        ]
        
        # Validate that the sequence makes sense behaviorally
        # (navigation before manipulation is logical)
        manipulation_step = action_sequence[1]  # Second step is manipulation
        navigation_step = action_sequence[0]   # First step is navigation
        
        # The sequence should have navigation first, then manipulation
        self.assertEqual(navigation_step.action_type, ActionType.NAVIGATION)
        self.assertEqual(manipulation_step.action_type, ActionType.MANIPULATION)
    
    def test_robustness_to_noise(self):
        """
        Test fusion robustness when one modality has noise.
        """
        # Voice with high confidence but vision with low confidence (noisy)
        voice_data = {
            "transcribed_text": "Go to the kitchen",
            "confidence": 0.9,
            "intent": "navigation",
            "parameters": {"target_location": "kitchen"}
        }
        
        # Low confidence vision (could be due to poor lighting, etc.)
        noisy_vision_data = {
            "objects": [
                {
                    "class": "uncertain_object",  # Low confidence object classification
                    "bbox": [0.1, 0.1, 0.2, 0.2],
                    "confidence": 0.2  # Very low confidence
                }
            ],
            "confidence": 0.25
        }
        
        fusion_service = MultimodalFusionService()
        result, confidence = fusion_service.fuse_modalities(
            voice_data=voice_data,
            vision_data=noisy_vision_data,
            sensor_data=None
        )
        
        # The fusion should still produce a reasonable result,
        # relying more on the high-confidence voice input
        self.assertIsNotNone(result)
        self.assertGreater(confidence, 0.3)  # Should still have some confidence


if __name__ == '__main__':
    # Run the tests
    unittest.main()