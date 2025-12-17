"""
Unit tests for conflict resolution in multimodal fusion.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from ..models.multimodal_input import MultimodalInput
from ..models.action_step import ActionStep, ActionType
from ..services.conflict_resolver import (
    ConflictResolver, 
    AdvancedConflictResolver, 
    ConflictType, 
    ResolutionStrategy
)
from ..services.multimodal_fusion import MultimodalFusionService
from ..services.confidence_manager import ConfidenceManager


class TestConflictResolution(unittest.TestCase):
    """
    Test suite for conflict resolution functionality.
    """
    
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.conflict_resolver = ConflictResolver()
        self.fusion_service = MultimodalFusionService()
        self.confidence_manager = ConfidenceManager()
    
    def test_detect_competing_intents_conflict(self):
        """
        Test detection of competing intents between voice and vision.
        """
        # Voice says to go somewhere, vision detects an object to manipulate
        voice_data = {
            "intent": "navigation",
            "transcribed_text": "Go to the kitchen",
            "confidence": 0.8
        }
        
        vision_data = {
            "objects": [
                {
                    "class": "red cup",
                    "bbox": [0.2, 0.3, 0.4, 0.5],
                    "confidence": 0.9
                }
            ],
            "scene_description": "A red cup is on the table"
        }
        
        conflicts = self.conflict_resolver.detect_conflicts(voice_data, vision_data, None)
        
        # Should detect competing intents (navigation vs manipulation)
        competing_intent_conflicts = [c for c in conflicts if c[0] == ConflictType.COMPETING_INTENTS]
        self.assertGreater(len(competing_intent_conflicts), 0)
    
    def test_detect_spatial_inconsistency_conflict(self):
        """
        Test detection of spatial inconsistencies.
        """
        # Voice commands to go to kitchen, but vision shows bedroom
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
        
        conflicts = self.conflict_resolver.detect_conflicts(voice_data, vision_data, None)
        
        # Should detect spatial inconsistency
        spatial_conflicts = [c for c in conflicts if c[0] == ConflictType.SPATIAL_INCONSISTENCY]
        self.assertGreater(len(spatial_conflicts), 0)
    
    def test_detect_contradictory_information_conflict(self):
        """
        Test detection of contradictory information between modalities.
        """
        # Voice mentions a red cup, but vision doesn't see any red cup
        voice_data = {
            "transcribed_text": "Pick up the red cup on the table",
            "confidence": 0.75,
            "parameters": {"target_object": "red cup"}
        }
        
        vision_data = {
            "objects": [
                {
                    "class": "blue bottle",
                    "bbox": [0.3, 0.4, 0.5, 0.6],
                    "confidence": 0.85
                },
                {
                    "class": "table",
                    "bbox": [0.0, 0.0, 1.0, 1.0],
                    "confidence": 0.9
                }
            ],
            "confidence": 0.82
        }
        
        conflicts = self.conflict_resolver.detect_conflicts(voice_data, vision_data, None)
        
        # Should detect contradictory information
        contradictory_conflicts = [c for c in conflicts if c[0] == ConflictType.CONTRADICTORY_INFORMATION]
        self.assertGreater(len(contradictory_conflicts), 0)
    
    def test_resolve_by_higher_confidence(self):
        """
        Test resolution by preferring the source with higher confidence.
        """
        source1_data = {"intent": "navigation", "confidence": 0.6}
        source2_data = {"objects": [{"class": "cup"}], "confidence": 0.85}
        
        result = self.conflict_resolver._resolve_by_confidence(
            ConflictType.CONTRADICTORY_INFORMATION, 
            source1_data, 
            source2_data
        )
        
        # Should prefer source2 since it has higher confidence
        self.assertEqual(result.resolved_decision["preferred_source"], "source2")
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(result.strategy_used, ResolutionStrategy.PREFER_HIGHER_CONFIDENCE)
    
    def test_resolve_by_fusion(self):
        """
        Test resolution by fusing information from both sources.
        """
        source1_data = {"intent": "navigation", "target": "kitchen", "confidence": 0.7}
        source2_data = {"objects": [{"class": "table"}, {"class": "cup"}], "confidence": 0.8}
        
        result = self.conflict_resolver._resolve_by_fusion(
            ConflictType.COMPETING_INTENTS, 
            source1_data, 
            source2_data
        )
        
        # Should have fused data from both sources
        self.assertIn("fused_from", result.resolved_decision)
        self.assertIn("source1", result.resolved_decision["fused_from"])
        self.assertIn("source2", result.resolved_decision["fused_from"])
        self.assertEqual(result.strategy_used, ResolutionStrategy.FUSE_INFORMATION)
        
        # Confidence should be averaged
        expected_confidence = (0.7 + 0.8) / 2
        self.assertAlmostEqual(result.confidence, expected_confidence, places=1)
    
    def test_resolve_by_context(self):
        """
        Test resolution using contextual information.
        """
        voice_data = {
            "intent": "navigation",
            "transcribed_text": "Go to the kitchen",
            "confidence": 0.7,
            "parameters": {"target_location": "kitchen"}
        }
        
        vision_data = {
            "objects": [
                {
                    "class": "bed",
                    "bbox": [0.1, 0.2, 0.8, 0.9],
                    "confidence": 0.9
                }
            ],
            "confidence": 0.85
        }
        
        sensor_data = {
            "readings": [
                {"type": "occupancy", "value": False}
            ]
        }
        
        result = self.conflict_resolver._resolve_by_context(
            ConflictType.SPATIAL_INCONSISTENCY,
            {"voice_intent": "kitchen"},
            {"vision_location": "bedroom"},
            voice_data,
            vision_data,
            sensor_data
        )
        
        self.assertEqual(result.strategy_used, ResolutionStrategy.USE_CONTEXT)
        # The context resolution should provide some decision
        self.assertIn("decision", result.resolved_decision)
    
    def test_resolve_by_clarification(self):
        """
        Test resolution that requires clarification.
        """
        source1_data = {"intent": "manipulation", "object": "red cup", "confidence": 0.6}
        source2_data = {"objects": [{"class": "blue bottle", "confidence": 0.8}]}
        
        result = self.conflict_resolver._resolve_by_clarification(
            ConflictType.CONTRADICTORY_INFORMATION,
            source1_data,
            source2_data
        )
        
        # Should indicate that clarification is needed
        self.assertEqual(result.strategy_used, ResolutionStrategy.REQUEST_CLARIFICATION)
        self.assertIn("requires_clarification", result.resolved_decision)
        self.assertIn("suggested_question", result.resolved_decision)
        self.assertEqual(result.confidence, 0.0)  # Low confidence when clarification needed
    
    def test_multiple_conflict_resolution(self):
        """
        Test resolving multiple conflicts at once.
        """
        # Create multiple conflicts
        conflicts = [
            (ConflictType.CONTRADICTORY_INFORMATION, 
             {"voice_obj": "red cup", "confidence": 0.6}, 
             {"vision_obj": "blue bottle", "confidence": 0.8}),
            (ConflictType.SPATIAL_INCONSISTENCY, 
             {"voice_location": "kitchen", "confidence": 0.7}, 
             {"vision_location": "bedroom", "confidence": 0.9})
        ]
        
        voice_data = {"intent": "manipulation", "transcribed_text": "Pick up the red cup", "confidence": 0.6}
        vision_data = {"objects": [{"class": "blue bottle"}], "confidence": 0.8}
        sensor_data = {"readings": [], "confidence": 0.85}
        
        results = self.conflict_resolver.resolve_conflicts(
            conflicts, voice_data, vision_data, sensor_data
        )
        
        # Should have resolved all conflicts
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result.conflict_resolved)
    
    def test_multimodal_input_conflict_resolution(self):
        """
        Test conflict resolution in the full multimodal input processing pipeline.
        """
        voice_data = {
            "intent": "navigation",
            "transcribed_text": "Go to the kitchen",
            "confidence": 0.75
        }
        
        vision_data = {
            "objects": [
                {
                    "class": "bed",
                    "bbox": [0.1, 0.2, 0.8, 0.9],
                    "confidence": 0.88
                }
            ],
            "scene_description": "Bedroom scene",
            "confidence": 0.85
        }
        
        # Process input with conflict resolution
        final_decision, confidence, resolution_results = self.conflict_resolver.resolve_multimodal_input(
            voice_data, vision_data, None
        )
        
        # Should have detected and resolved conflicts
        self.assertIn("conflict_resolution_applied", final_decision)
        self.assertGreater(len(resolution_results), 0)
        self.assertGreaterEqual(confidence, 0.0)
    
    def test_simple_fusion_when_no_conflicts(self):
        """
        Test that simple fusion is performed when no conflicts are detected.
        """
        voice_data = {
            "intent": "navigation",
            "transcribed_text": "Move forward",
            "confidence": 0.8
        }
        
        vision_data = {
            "objects": [],
            "scene_description": "Clear path ahead",
            "confidence": 0.85
        }
        
        # Process input - should not detect conflicts
        final_decision, confidence, resolution_results = self.conflict_resolver.resolve_multimodal_input(
            voice_data, vision_data, None
        )
        
        # Should not have applied conflict resolution
        self.assertNotIn("conflict_resolution_applied", final_decision)
        self.assertEqual(len(resolution_results), 0)  # No resolutions performed
        self.assertGreaterEqual(confidence, 0.75)  # High confidence due to agreement


class TestAdvancedConflictResolution(unittest.TestCase):
    """
    Advanced tests for conflict resolution with learning capabilities.
    """
    
    def setUp(self):
        """
        Set up test fixtures for advanced tests.
        """
        self.advanced_resolver = AdvancedConflictResolver()
    
    def test_learning_from_resolution_outcomes(self):
        """
        Test that the resolver learns from resolution outcomes.
        """
        # Simulate several resolution attempts with known outcomes
        self.advanced_resolver.learn_from_resolution(
            ConflictType.SPATIAL_INCONSISTENCY,
            ResolutionStrategy.USE_CONTEXT,
            True  # Successful resolution
        )
        
        self.advanced_resolver.learn_from_resolution(
            ConflictType.SPATIAL_INCONSISTENCY, 
            ResolutionStrategy.USE_CONTEXT, 
            True  # Another successful resolution
        )
        
        self.advanced_resolver.learn_from_resolution(
            ConflictType.SPATIAL_INCONSISTENCY,
            ResolutionStrategy.PREFER_HIGHER_CONFIDENCE,
            False  # Unsuccessful resolution
        )
        
        # Check that the learned patterns are recorded
        spatial_context_pattern = f"{ConflictType.SPATIAL_INCONSISTENCY.value}_{ResolutionStrategy.USE_CONTEXT.value}"
        self.assertIn(spatial_context_pattern, self.advanced_resolver.conflict_patterns)
        
        pattern_data = self.advanced_resolver.conflict_patterns[spatial_context_pattern]
        self.assertEqual(pattern_data["attempts"], 2)
        self.assertEqual(pattern_data["successes"], 2)
        self.assertEqual(pattern_data["success_rate"], 1.0)
    
    def test_advisory_resolution_strategy(self):
        """
        Test that the resolver provides advisory strategies based on learned patterns.
        """
        # First, teach the resolver about successful strategies
        self.advanced_resolver.learn_from_resolution(
            ConflictType.COMPETING_INTENTS,
            ResolutionStrategy.FUSE_INFORMATION,
            True
        )
        self.advanced_resolver.learn_from_resolution(
            ConflictType.COMPETING_INTENTS,
            ResolutionStrategy.FUSE_INFORMATION,
            True
        )
        self.advanced_resolver.learn_from_resolution(
            ConflictType.COMPETING_INTENTS,
            ResolutionStrategy.PREFER_HIGHER_CONFIDENCE,
            False
        )
        
        # Get advisory strategy for competing intents
        advisory_strategy = self.advanced_resolver.get_advisory_resolution(
            ConflictType.COMPETING_INTENTS
        )
        
        # Should prefer the strategy with higher success rate
        self.assertEqual(advisory_strategy, ResolutionStrategy.FUSE_INFORMATION)
    
    def test_conflict_statistics(self):
        """
        Test that conflict statistics are properly maintained.
        """
        # Add several learning examples
        examples = [
            (ConflictType.SPATIAL_INCONSISTENCY, ResolutionStrategy.USE_CONTEXT, True),
            (ConflictType.SPATIAL_INCONSISTENCY, ResolutionStrategy.USE_CONTEXT, False),
            (ConflictType.CONTRADICTORY_INFORMATION, ResolutionStrategy.FUSE_INFORMATION, True),
            (ConflictType.CONTRADICTORY_INFORMATION, ResolutionStrategy.FUSE_INFORMATION, True),
            (ConflictType.COMPETING_INTENTS, ResolutionStrategy.PREFER_HIGHER_CONFIDENCE, False)
        ]
        
        for conflict_type, strategy, success in examples:
            self.advanced_resolver.learn_from_resolution(conflict_type, strategy, success)
        
        # Check that all patterns are recorded
        self.assertEqual(len(self.advanced_resolver.conflict_patterns), 3)  # 3 unique conflict-strategy pairs
        
        # Check statistics for one pattern
        spatial_context_pattern = f"{ConflictType.SPATIAL_INCONSISTENCY.value}_{ResolutionStrategy.USE_CONTEXT.value}"
        pattern_stats = self.advanced_resolver.conflict_patterns[spatial_context_pattern]
        self.assertEqual(pattern_stats["attempts"], 2)
        self.assertEqual(pattern_stats["successes"], 1)
        self.assertEqual(pattern_stats["success_rate"], 0.5)
    
    def test_resolution_with_context_learning(self):
        """
        Test resolution with context-based learning.
        """
        # Simulate a scenario with context
        conflict_type = ConflictType.SPATIAL_INCONSISTENCY
        context = {
            "environment": "indoor",
            "lighting": "bright",
            "robot_location": [0.0, 0.0, 0.0]
        }
        
        # First, establish some learning history
        self.advanced_resolver.learn_from_resolution(
            conflict_type,
            ResolutionStrategy.USE_CONTEXT,
            True,
            context
        )
        
        # Get advisory strategy based on context
        advisory_strategy = self.advanced_resolver.get_advisory_resolution(
            conflict_type,
            context
        )
        
        # The advisory system should consider the learned patterns
        self.assertIsNotNone(advisory_strategy)
    
    def test_mixed_conflict_resolution_strategies(self):
        """
        Test performance when multiple conflict types are present.
        """
        # Create a complex scenario with multiple conflicts
        conflicts = [
            (ConflictType.SPATIAL_INCONSISTENCY, 
             {"voice_location": "kitchen", "confidence": 0.7}, 
             {"vision_location": "bedroom", "confidence": 0.85}),
            (ConflictType.CONTRADICTORY_INFORMATION, 
             {"voice_obj": "red cup", "confidence": 0.6}, 
             {"vision_obj": "blue bottle", "confidence": 0.8})
        ]
        
        voice_data = {"intent": "navigation", "transcribed_text": "Go to kitchen and pick red cup", "confidence": 0.6}
        vision_data = {"objects": [{"class": "blue bottle"}], "confidence": 0.8}
        sensor_data = {"readings": [], "confidence": 0.75}
        
        # Resolve conflicts using learned strategies
        results = self.advanced_resolver.resolve_conflicts(
            conflicts, voice_data, vision_data, sensor_data
        )
        
        # Should have resolved both conflicts
        self.assertEqual(len(results), 2)
        
        # Each result should be properly formed
        for result in results:
            self.assertTrue(result.conflict_resolved)
            self.assertIsNotNone(result.resolved_decision)
            self.assertIsNotNone(result.confidence)
            self.assertIsNotNone(result.strategy_used)
    
    def test_performance_comparison(self):
        """
        Compare performance of basic vs advanced resolver.
        """
        # Create a conflict scenario
        voice_data = {
            "intent": "manipulation",
            "transcribed_text": "Pick up the red cup",
            "confidence": 0.7
        }
        
        vision_data = {
            "objects": [
                {
                    "class": "blue bottle",
                    "bbox": [0.3, 0.4, 0.5, 0.6],
                    "confidence": 0.85
                }
            ],
            "confidence": 0.8
        }
        
        # Simulate having learned that fusion works well for this type of conflict
        self.advanced_resolver.learn_from_resolution(
            ConflictType.CONTRADICTORY_INFORMATION,
            ResolutionStrategy.FUSE_INFORMATION,
            True
        )
        
        # Run conflict detection
        conflicts = self.advanced_resolver.detect_conflicts(voice_data, vision_data, None)
        
        # Basic resolver would use default strategy
        basic_results = self.advanced_resolver.resolve_conflicts(
            conflicts, voice_data, vision_data, None,
            strategy=self.advanced_resolver.default_strategy
        )
        
        # Advanced resolver may use learned strategy
        advisory_strategy = self.advanced_resolver.get_advisory_resolution(
            ConflictType.CONTRADICTORY_INFORMATION
        )
        
        # The strategies might be different based on learning
        # This test mainly ensures both approaches work without error
        self.assertGreater(len(basic_results), 0)
        self.assertTrue(basic_results[0].conflict_resolved)


if __name__ == '__main__':
    # Run the tests
    unittest.main()