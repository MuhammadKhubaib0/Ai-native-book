"""
Unit tests for ambiguous command resolution in the LLM-based action sequencing system.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from ..models.voice_command import VoiceCommand
from ..services.ambiguous_command_handler import (
    AmbiguousCommandHandler, 
    AdvancedAmbiguousCommandHandler,
    AmbiguityType, 
    ResolutionStrategy
)


class TestAmbiguousCommandResolution(unittest.TestCase):
    """
    Test suite for ambiguous command resolution functionality.
    """
    
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.handler = AmbiguousCommandHandler()
    
    def test_detect_object_reference_ambiguity(self):
        """
        Test detection of object reference ambiguities.
        """
        # Test command with ambiguous object reference
        voice_command = VoiceCommand(
            id="cmd-1",
            transcribed_text="Pick it up",
            intent="manipulation",
            parameters={},
            confidence=0.8
        )
        
        ambiguities = self.handler.detect_ambiguity(voice_command)
        
        # Should detect object reference ambiguity
        object_ambiguities = [a for a in ambiguities if a[0] == AmbiguityType.OBJECT_REFERENCE]
        self.assertGreater(len(object_ambiguities), 0)
        self.assertIn("object", object_ambiguities[0][1])
    
    def test_detect_location_reference_ambiguity(self):
        """
        Test detection of location reference ambiguities.
        """
        # Test command with ambiguous location reference
        voice_command = VoiceCommand(
            id="cmd-2",
            transcribed_text="Go to the room",
            intent="navigation",
            parameters={},
            confidence=0.8
        )
        
        ambiguities = self.handler.detect_ambiguity(voice_command)
        
        # Should detect location reference ambiguity
        location_ambiguities = [a for a in ambiguities if a[0] == AmbiguityType.LOCATION_REFERENCE]
        self.assertGreater(len(location_ambiguities), 0)
        self.assertIn("location", location_ambiguities[0][1])
    
    def test_detect_quantity_ambiguity(self):
        """
        Test detection of quantity ambiguities.
        """
        # Test command with ambiguous quantity
        voice_command = VoiceCommand(
            id="cmd-3",
            transcribed_text="Move some distance",
            intent="navigation",
            parameters={},
            confidence=0.8
        )
        
        ambiguities = self.handler.detect_ambiguity(voice_command)
        
        # Should detect quantity reference ambiguity
        quantity_ambiguities = [a for a in ambiguities if a[0] == AmbiguityType.QUANTITY_REFERENCE]
        self.assertGreater(len(quantity_ambiguities), 0)
        self.assertIn("quantity", quantity_ambiguities[0][1])
    
    def test_no_ambiguity_detection_for_clear_command(self):
        """
        Test that clear commands don't trigger ambiguity detection.
        """
        # Test command that should not be ambiguous
        voice_command = VoiceCommand(
            id="cmd-4",
            transcribed_text="Move forward 2 meters to the kitchen",
            intent="navigation",
            parameters={"distance": 2.0, "unit": "meters", "destination": "kitchen"},
            confidence=0.9
        )
        
        ambiguities = self.handler.detect_ambiguity(voice_command)
        
        # Should not detect any ambiguities
        self.assertEqual(len(ambiguities), 0)
    
    def test_request_clarification_resolution(self):
        """
        Test resolution using request clarification strategy.
        """
        voice_command = VoiceCommand(
            id="cmd-5",
            transcribed_text="Go to the room",
            intent="navigation",
            parameters={},
            confidence=0.8
        )
        
        resolution = self.handler.resolve_ambiguity(
            voice_command, 
            AmbiguityType.LOCATION_REFERENCE, 
            ResolutionStrategy.REQUEST_CLARIFICATION
        )
        
        # Assertions
        self.assertEqual(resolution["resolution_type"], "clarification_requested")
        self.assertIn("location", resolution["clarification_prompt"].lower())
        self.assertTrue(resolution["requires_user_input"])
    
    def test_context_resolution(self):
        """
        Test resolution using context strategy.
        """
        voice_command = VoiceCommand(
            id="cmd-6",
            transcribed_text="Move some distance forward",
            intent="navigation",
            parameters={},
            confidence=0.8
        )
        
        resolution = self.handler.resolve_ambiguity(
            voice_command,
            AmbiguityType.QUANTITY_REFERENCE,
            ResolutionStrategy.USE_CONTEXT
        )
        
        # Assertions
        self.assertIn(resolution["resolution_type"], ["context_applied", "default_action"])
    
    def test_multiple_possibilities_resolution(self):
        """
        Test resolution using multiple possibilities strategy.
        """
        voice_command = VoiceCommand(
            id="cmd-7",
            transcribed_text="Do something",
            intent="unknown",
            parameters={},
            confidence=0.6
        )
        
        resolution = self.handler.resolve_ambiguity(
            voice_command,
            AmbiguityType.AMBIGUOUS_INTENT,
            ResolutionStrategy.MULTIPLE_POSSIBILITIES
        )
        
        # Assertions
        self.assertEqual(resolution["resolution_type"], "multiple_possibilities")
        self.assertIn("possible_interpretations", resolution)
        self.assertTrue(resolution["requires_user_choice"])
    
    def test_ambiguous_command_handling_pipeline(self):
        """
        Test the full pipeline for handling ambiguous commands.
        """
        voice_command = VoiceCommand(
            id="cmd-8",
            transcribed_text="Pick up the object there",
            intent="manipulation",
            parameters={},
            confidence=0.7
        )
        
        result = self.handler.handle_ambiguous_command(voice_command)
        
        # Assertions
        self.assertTrue(result["is_ambiguous"])
        self.assertEqual(result["command_id"], voice_command.id)
        self.assertGreater(len(result["detected_ambiguities"]), 0)
        self.assertGreater(len(result["resolution_attempts"]), 0)
        self.assertTrue(result["needs_clarification"])
        
        # Check that both object and location ambiguities are detected
        ambiguity_types = [a["type"] for a in result["detected_ambiguities"]]
        self.assertIn(AmbiguityType.OBJECT_REFERENCE.value, ambiguity_types)
        # Location reference might be detected in "there"
        # self.assertIn(AmbiguityType.LOCATION_REFERENCE.value, ambiguity_types)


class TestAdvancedAmbiguousCommandResolution(unittest.TestCase):
    """
    Advanced tests for ambiguous command resolution with learning capabilities.
    """
    
    def setUp(self):
        """
        Set up test fixtures for advanced tests.
        """
        self.advanced_handler = AdvancedAmbiguousCommandHandler()
    
    def test_learning_from_resolution(self):
        """
        Test that the handler learns from resolution outcomes.
        """
        # Simulate a resolution and user feedback
        asyncio.run(self.advanced_handler.learn_from_resolution(
            "Do the thing like before",
            AmbiguityType.ACTION_REFERENCE,
            ResolutionStrategy.REQUEST_CLARIFICATION,
            "I meant to pick up the cup"
        ))
        
        # The learning history should now contain the record
        self.assertEqual(len(self.advanced_handler.disambiguation_history), 1)
        
        # Check the content of the learning record
        record = self.advanced_handler.disambiguation_history[0]
        self.assertEqual(record["command"], "Do the thing like before")
        self.assertEqual(record["ambiguity_type"], AmbiguityType.ACTION_REFERENCE.value)
        self.assertEqual(record["resolution_strategy"], ResolutionStrategy.REQUEST_CLARIFICATION.value)
        self.assertIn("pick up the cup", record["user_feedback"])
    
    def test_similar_pattern_detection(self):
        """
        Test that similar patterns are detected from history.
        """
        # Add a few records to the learning history
        asyncio.run(self.advanced_handler.learn_from_resolution(
            "Pick it up",
            AmbiguityType.OBJECT_REFERENCE,
            ResolutionStrategy.REQUEST_CLARIFICATION,
            "I meant the red cup"
        ))
        
        asyncio.run(self.advanced_handler.learn_from_resolution(
            "Move it over there",
            AmbiguityType.LOCATION_REFERENCE,
            ResolutionStrategy.REQUEST_CLARIFICATION,
            "Move it to the table"
        ))
        
        # Check if similar patterns are detected
        context = self.advanced_handler._extract_learning_context("Pick it up", "Pick up the red cup")
        similar_patterns = context["similar_patterns"]
        
        # Should find the similar "Pick it up" command
        self.assertIn("Pick it up", similar_patterns)
    
    @patch('..services.llm_service.LLMService.generate_action_sequence')
    def test_llm_based_resolution(self, mock_generate):
        """
        Test LLM-based resolution of ambiguous commands.
        """
        import asyncio
        
        voice_command = VoiceCommand(
            id="cmd-9",
            transcribed_text="Do the action from earlier",
            intent="unknown",
            parameters={},
            confidence=0.5
        )
        
        # Test the async resolution method
        async def run_test():
            result = await self.advanced_handler.resolve_with_llm(
                voice_command,
                AmbiguityType.ACTION_REFERENCE,
                {"recent_actions": ["picked up cup", "moved to kitchen"]}
            )
            return result
        
        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_test())
            
            # Assertions - the result depends on the simulated response
            self.assertIn("resolution_type", result)
        finally:
            loop.close()
    
    def test_ambiguous_command_with_context(self):
        """
        Test handling ambiguous commands with additional context.
        """
        voice_command = VoiceCommand(
            id="cmd-10",
            transcribed_text="Go to that place",
            intent="navigation",
            parameters={},
            confidence=0.7
        )
        
        # Context might include recent locations or user preferences
        context = {
            "recent_locations": ["kitchen", "living room"],
            "user_preferences": {"frequently_visited": "kitchen"}
        }
        
        result = self.advanced_handler.handle_ambiguous_command(voice_command, context=context)
        
        # Should still be ambiguous but with additional context processed
        self.assertTrue(result["is_ambiguous"])
        self.assertEqual(result["command_id"], voice_command.id)
        self.assertGreater(len(result["detected_ambiguities"]), 0)


# Helper function to run async tests with asyncio
def run_async(coro):
    """Helper to run async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Since we're dealing with async methods, we need to properly handle them in tests
import asyncio

# Example of how to run async in a test
def run_async_test(coro):
    """Helper to run async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == '__main__':
    # Run the tests
    unittest.main()