"""
Service for handling ambiguous commands by requesting clarification or making intelligent assumptions.
"""
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from ..models.voice_command import VoiceCommand
from ..models.action_sequence import ActionSequence
from ..services.llm_service import LLMService, LLMConfig
from ..config import settings
import uuid
from datetime import datetime


class AmbiguityType(Enum):
    """Enumeration of different types of ambiguities."""
    OBJECT_REFERENCE = "object_reference"  # "Pick up the object" - which object?
    LOCATION_REFERENCE = "location_reference"  # "Go to the room" - which room?
    ACTION_REFERENCE = "action_reference"  # "Do it" - what is "it"?
    QUANTITY_REFERENCE = "quantity_reference"  # "Move some distance" - how much?
    TEMPORAL_REFERENCE = "temporal_reference"  # "Do it later" - when is later?
    AMBIGUOUS_INTENT = "ambiguous_intent"  # Command could mean multiple things


class ResolutionStrategy(Enum):
    """Enumeration of different resolution strategies."""
    REQUEST_CLARIFICATION = "request_clarification"
    USE_CONTEXT = "use_context"
    DEFAULT_ACTION = "default_action"
    MULTIPLE_POSSIBILITIES = "multiple_possibilities"
    ASK_USER = "ask_user"


class AmbiguousCommandHandler:
    """
    Service for handling ambiguous commands by requesting clarification or making intelligent assumptions.
    """
    
    def __init__(self, llm_service: LLMService = None):
        """
        Initialize the ambiguous command handler.
        
        :param llm_service: Optional LLM service for generating clarifications
        """
        self.llm_service = llm_service or LLMService(LLMConfig(
            model_name=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        ))
        
        # Default resolution strategies for each ambiguity type
        self.default_strategies = {
            AmbiguityType.OBJECT_REFERENCE: ResolutionStrategy.REQUEST_CLARIFICATION,
            AmbiguityType.LOCATION_REFERENCE: ResolutionStrategy.REQUEST_CLARIFICATION,
            AmbiguityType.ACTION_REFERENCE: ResolutionStrategy.REQUEST_CLARIFICATION,
            AmbiguityType.QUANTITY_REFERENCE: ResolutionStrategy.USE_CONTEXT,
            AmbiguityType.TEMPORAL_REFERENCE: ResolutionStrategy.DEFAULT_ACTION,
            AmbiguityType.AMBIGUOUS_INTENT: ResolutionStrategy.MULTIPLE_POSSIBILITIES
        }
    
    def detect_ambiguity(self, voice_command: VoiceCommand) -> List[Tuple[AmbiguityType, str]]:
        """
        Detect potential ambiguities in a voice command.
        
        :param voice_command: The voice command to analyze
        :return: List of detected ambiguities with descriptions
        """
        ambiguities = []
        
        text = voice_command.transcribed_text.lower()
        
        # Check for object reference ambiguity
        object_pronouns = ["it", "that", "this", "the object", "something"]
        if any(pronoun in text for pronoun in object_pronouns):
            # Check if there's a specific object mentioned before or after
            if not self._has_clear_object_reference(text, voice_command):
                ambiguities.append((
                    AmbiguityType.OBJECT_REFERENCE,
                    f"Command contains ambiguous object reference: {text}"
                ))
        
        # Check for location reference ambiguity
        location_pronouns = ["the room", "there", "here", "that place", "the area"]
        if any(loc in text for loc in location_pronouns):
            if not self._has_clear_location_reference(text, voice_command):
                ambiguities.append((
                    AmbiguityType.LOCATION_REFERENCE,
                    f"Command contains ambiguous location reference: {text}"
                ))
        
        # Check for action reference ambiguity
        action_pronouns = ["do it", "that", "like that", "the same"]
        if any(action in text for action in action_pronouns):
            ambiguities.append((
                AmbiguityType.ACTION_REFERENCE,
                f"Command contains ambiguous action reference: {text}"
            ))
        
        # Check for quantity ambiguity
        vague_quantities = ["some", "a bit", "a lot", "a little", "a few", "much", "many"]
        if any(quant in text for quant in vague_quantities):
            ambiguities.append((
                AmbiguityType.QUANTITY_REFERENCE,
                f"Command contains ambiguous quantity reference: {text}"
            ))
        
        # Check for temporal ambiguity
        vague_times = ["later", "soon", "a bit", "when possible", "eventually"]
        if any(time in text for time in vague_times):
            ambiguities.append((
                AmbiguityType.TEMPORAL_REFERENCE,
                f"Command contains ambiguous temporal reference: {text}"
            ))
        
        # Check for ambiguous intent
        ambiguous_patterns = [
            ("go to", "location unclear"),
            ("pick up", "object unclear"),
            ("do", "action unclear")
        ]
        
        for pattern, description in ambiguous_patterns:
            if pattern in text:
                ambiguities.append((
                    AmbiguityType.AMBIGUOUS_INTENT,
                    f"Ambiguous intent detected: {description} in '{text}'"
                ))
        
        return ambiguities
    
    def _has_clear_object_reference(self, text: str, voice_command: VoiceCommand) -> bool:
        """
        Check if the command has a clear object reference.
        
        :param text: The command text
        :param voice_command: The voice command to analyze
        :return: True if there's a clear object reference, False otherwise
        """
        # Check for specific object names in the command
        specific_objects = ["red cup", "blue ball", "table", "chair", "book", "box"]
        
        for obj in specific_objects:
            if obj in text:
                return True
        
        # In a real implementation, you'd check against a list of known objects
        # in the environment or recent context
        return False
    
    def _has_clear_location_reference(self, text: str, voice_command: VoiceCommand) -> bool:
        """
        Check if the command has a clear location reference.
        
        :param text: The command text
        :param voice_command: The voice command to analyze
        :return: True if there's a clear location reference, False otherwise
        """
        # Check for specific room names in the command
        specific_locations = ["kitchen", "living room", "bedroom", "office", "bathroom", "dining room"]
        
        for loc in specific_locations:
            if loc in text:
                return True
        
        # In a real implementation, you'd check against a map of known locations
        return False
    
    def resolve_ambiguity(
        self,
        voice_command: VoiceCommand,
        ambiguity_type: AmbiguityType,
        strategy: ResolutionStrategy = None
    ) -> Dict[str, Any]:
        """
        Resolve an ambiguity using the specified strategy.
        
        :param voice_command: The ambiguous voice command
        :param ambiguity_type: Type of ambiguity to resolve
        :param strategy: Strategy to use (uses default if not specified)
        :return: Resolution result
        """
        if strategy is None:
            strategy = self.default_strategies.get(ambiguity_type, ResolutionStrategy.REQUEST_CLARIFICATION)
        
        if strategy == ResolutionStrategy.REQUEST_CLARIFICATION:
            return self._request_clarification(voice_command, ambiguity_type)
        elif strategy == ResolutionStrategy.USE_CONTEXT:
            return self._use_context(voice_command, ambiguity_type)
        elif strategy == ResolutionStrategy.DEFAULT_ACTION:
            return self._use_default_action(voice_command, ambiguity_type)
        elif strategy == ResolutionStrategy.MULTIPLE_POSSIBILITIES:
            return self._generate_possibilities(voice_command, ambiguity_type)
        elif strategy == ResolutionStrategy.ASK_USER:
            return self._ask_user(voice_command, ambiguity_type)
        else:
            # Default to requesting clarification
            return self._request_clarification(voice_command, ambiguity_type)
    
    def _request_clarification(self, voice_command: VoiceCommand, ambiguity_type: AmbiguityType) -> Dict[str, Any]:
        """
        Generate a request for clarification.
        
        :param voice_command: The ambiguous voice command
        :param ambiguity_type: Type of ambiguity
        :return: Clarification request
        """
        clarification_prompts = {
            AmbiguityType.OBJECT_REFERENCE: f"I heard '{voice_command.transcribed_text}', but I'm not sure which object you mean. Could you specify which object?",
            AmbiguityType.LOCATION_REFERENCE: f"I heard '{voice_command.transcribed_text}', but I'm not sure which location you mean. Could you specify which room or area?",
            AmbiguityType.ACTION_REFERENCE: f"I heard '{voice_command.transcribed_text}', but I'm not sure what action you're referring to. Could you clarify what you'd like me to do?",
            AmbiguityType.QUANTITY_REFERENCE: f"I heard '{voice_command.transcribed_text}', but I'm not sure about the amount. Could you specify the distance, quantity, or extent?",
            AmbiguityType.TEMPORAL_REFERENCE: f"I heard '{voice_command.transcribed_text}', but I'm not sure when you'd like me to do this. Could you specify the time?",
            AmbiguityType.AMBIGUOUS_INTENT: f"I heard '{voice_command.transcribed_text}', but I'm not sure what you mean. Could you rephrase or be more specific?"
        }
        
        prompt = clarification_prompts.get(ambiguity_type, f"I didn't understand '{voice_command.transcribed_text}'. Could you clarify?")
        
        return {
            "resolution_type": "clarification_requested",
            "clarification_prompt": prompt,
            "ambiguity_type": ambiguity_type.value,
            "requires_user_input": True
        }
    
    def _use_context(self, voice_command: VoiceCommand, ambiguity_type: AmbiguityType) -> Dict[str, Any]:
        """
        Resolve ambiguity using contextual information.
        
        :param voice_command: The ambiguous voice command
        :param ambiguity_type: Type of ambiguity
        :return: Resolution based on context
        """
        # For quantity references, use common defaults
        if ambiguity_type == AmbiguityType.QUANTITY_REFERENCE:
            text = voice_command.transcribed_text.lower()
            
            # Default values based on context
            if "move" in text or "go" in text or "forward" in text:
                default_distance = 1.0  # 1 meter
                return {
                    "resolution_type": "context_applied",
                    "resolved_parameters": {"distance": default_distance, "unit": "meters"},
                    "ambiguity_type": ambiguity_type.value,
                    "context_used": f"Assumed distance of {default_distance}m as default"
                }
        
        # For other types, return a default resolution
        return {
            "resolution_type": "context_applied",
            "message": "Using contextual defaults to resolve ambiguity",
            "ambiguity_type": ambiguity_type.value
        }
    
    def _use_default_action(self, voice_command: VoiceCommand, ambiguity_type: AmbiguityType) -> Dict[str, Any]:
        """
        Resolve ambiguity by using a default action.
        
        :param voice_command: The ambiguous voice command
        :param ambiguity_type: Type of ambiguity
        :return: Default action resolution
        """
        return {
            "resolution_type": "default_action",
            "message": "Executing default action due to ambiguity",
            "ambiguity_type": ambiguity_type.value,
            "default_taken": True
        }
    
    def _generate_possibilities(self, voice_command: VoiceCommand, ambiguity_type: AmbiguityType) -> Dict[str, Any]:
        """
        Generate multiple possible interpretations of an ambiguous command.
        
        :param voice_command: The ambiguous voice command
        :param ambiguity_type: Type of ambiguity
        :return: Multiple possible interpretations
        """
        # This would generate multiple possible action sequences in a real implementation
        # For now, we'll simulate this with potential interpretations
        
        possible_interpretations = []
        
        if ambiguity_type == AmbiguityType.AMBIGUOUS_INTENT:
            # Generate different possible intents
            original_text = voice_command.transcribed_text.lower()
            
            if "go" in original_text:
                possible_interpretations.append({
                    "intent": "navigation",
                    "action": "move forward 1 meter",
                    "confidence": 0.7
                })
                possible_interpretations.append({
                    "intent": "navigation", 
                    "action": "move to default location",
                    "confidence": 0.3
                })
        
        return {
            "resolution_type": "multiple_possibilities",
            "possible_interpretations": possible_interpretations,
            "ambiguity_type": ambiguity_type.value,
            "requires_user_choice": True
        }
    
    def _ask_user(self, voice_command: VoiceCommand, ambiguity_type: AmbiguityType) -> Dict[str, Any]:
        """
        Generate a question to ask the user for clarification.
        
        :param voice_command: The ambiguous voice command
        :param ambiguity_type: Type of ambiguity
        :return: Question to ask the user
        """
        question_prompts = {
            AmbiguityType.OBJECT_REFERENCE: "Which specific object would you like me to interact with?",
            AmbiguityType.LOCATION_REFERENCE: "Which specific location would you like me to go to?",
            AmbiguityType.ACTION_REFERENCE: "What specific action would you like me to perform?",
            AmbiguityType.QUANTITY_REFERENCE: "How much or how far would you like me to move?",
            AmbiguityType.TEMPORAL_REFERENCE: "When would you like me to perform this action?",
            AmbiguityType.AMBIGUOUS_INTENT: "Could you rephrase that command or be more specific about what you'd like me to do?"
        }
        
        question = question_prompts.get(ambiguity_type, "Could you please clarify your command?")
        
        return {
            "resolution_type": "user_question",
            "question": question,
            "ambiguity_type": ambiguity_type.value,
            "requires_user_response": True
        }
    
    def handle_ambiguous_command(
        self, 
        voice_command: VoiceCommand,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an ambiguous command comprehensively.
        
        :param voice_command: The ambiguous voice command
        :param context: Additional context (optional)
        :return: Comprehensive handling result
        """
        # Detect ambiguities
        ambiguities = self.detect_ambiguity(voice_command)
        
        if not ambiguities:
            # No ambiguities detected, return the original command
            return {
                "command_id": voice_command.id,
                "is_ambiguous": False,
                "original_command": voice_command.transcribed_text,
                "action_sequence": None
            }
        
        # Process each detected ambiguity
        resolution_results = []
        for ambiguity_type, description in ambiguities:
            resolution = self.resolve_ambiguity(voice_command, ambiguity_type)
            resolution_results.append({
                "ambiguity_type": ambiguity_type.value,
                "description": description,
                "resolution": resolution
            })
        
        # Determine the overall handling approach
        needs_clarification = any(
            r["resolution"]["requires_user_input"] or r["resolution"]["requires_user_response"] 
            for r in resolution_results
        )
        
        return {
            "command_id": voice_command.id,
            "is_ambiguous": True,
            "original_command": voice_command.transcribed_text,
            "detected_ambiguities": [{"type": a[0].value, "description": a[1]} for a in ambiguities],
            "resolution_attempts": resolution_results,
            "needs_clarification": needs_clarification,
            "action_sequence": None  # Would be generated after resolution
        }


class AdvancedAmbiguousCommandHandler(AmbiguousCommandHandler):
    """
    Advanced handler with LLM-powered disambiguation and learning capabilities.
    """
    
    def __init__(self, llm_service: LLMService = None):
        super().__init__(llm_service)
        self.disambiguation_history = []
    
    async def resolve_with_llm(
        self,
        voice_command: VoiceCommand,
        ambiguity_type: AmbiguityType,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Use an LLM to generate potential resolutions for ambiguous commands.
        
        :param voice_command: The ambiguous voice command
        :param ambiguity_type: Type of ambiguity
        :param context: Additional context
        :return: LLM-generated resolution
        """
        # Build a prompt for the LLM to resolve the ambiguity
        prompt = self._build_disambiguation_prompt(voice_command, ambiguity_type, context)
        
        # Generate response using LLM
        try:
            # For this implementation, we'll create a simulated response
            # In a real implementation, this would call the LLM service
            simulated_response = {
                "resolution_type": "llm_suggestion",
                "suggested_interpretation": f"Interpret '{voice_command.transcribed_text}' as {ambiguity_type.value} with context {context}",
                "confidence": 0.85,
                "alternative_interpretations": [
                    {"interpretation": "first possible meaning", "confidence": 0.6},
                    {"interpretation": "second possible meaning", "confidence": 0.4}
                ]
            }
            
            # In a real implementation, you would call:
            # response = await self.llm_service.generate_action_sequence(
            #     intent="disambiguate_command",
            #     parameters={"command": voice_command.transcribed_text, "ambiguity_type": ambiguity_type.value},
            #     context={"prompt": prompt}
            # )
            
            return simulated_response
        except Exception as e:
            # Fallback to basic resolution if LLM fails
            return self.resolve_ambiguity(voice_command, ambiguity_type)
    
    def _build_disambiguation_prompt(
        self,
        voice_command: VoiceCommand,
        ambiguity_type: AmbiguityType,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build a prompt for the LLM to resolve the ambiguity.
        
        :param voice_command: The ambiguous voice command
        :param ambiguity_type: Type of ambiguity
        :param context: Additional context
        :return: Formatted prompt string
        """
        context_str = str(context) if context else "No additional context available"
        
        prompt = f"""
        A user gave the command: "{voice_command.transcribed_text}"
        The system detected the following ambiguity: {ambiguity_type.value}
        Additional context: {context_str}
        
        Provide a clear interpretation of what the user likely meant.
        If multiple interpretations are possible, list the top 3 possibilities with confidence scores.
        
        Format the response as a JSON object with these fields:
        - "interpretation": Your primary interpretation
        - "confidence": Confidence score (0-1)
        - "alternatives": Array of alternative interpretations with confidence scores
        - "clarification_question": A question to ask the user if needed
        
        Example response format:
        {{
          "interpretation": "User wants to navigate to the kitchen",
          "confidence": 0.85,
          "alternatives": [
            {{"interpretation": "User wants to navigate to the bedroom", "confidence": 0.10}},
            {{"interpretation": "User wants to navigate to the office", "confidence": 0.05}}
          ],
          "clarification_question": "Did you mean the kitchen?"
        }}
        """
        
        return prompt
    
    async def learn_from_resolution(
        self,
        original_command: str,
        ambiguity_type: AmbiguityType,
        resolution_strategy: ResolutionStrategy,
        user_feedback: str
    ):
        """
        Learn from how a user resolved an ambiguous command.
        
        :param original_command: The original ambiguous command
        :param ambiguity_type: Type of ambiguity that was resolved
        :param resolution_strategy: Strategy that was used
        :param user_feedback: User's feedback or clarification
        """
        learning_record = {
            "timestamp": datetime.now().isoformat(),
            "command": original_command,
            "ambiguity_type": ambiguity_type.value,
            "resolution_strategy": resolution_strategy.value,
            "user_feedback": user_feedback,
            "learned_context": self._extract_learning_context(original_command, user_feedback)
        }
        
        self.disambiguation_history.append(learning_record)
    
    def _extract_learning_context(self, command: str, feedback: str) -> Dict[str, Any]:
        """
        Extract useful context from a command and its resolution for future learning.
        
        :param command: The original command
        :param feedback: User's feedback or clarification
        :return: Learning context
        """
        # Simple extraction - in a real system, this would use NLP techniques
        return {
            "command_keywords": command.split(),
            "feedback_keywords": feedback.split(),
            "similar_patterns": self._find_similar_patterns(command)
        }
    
    def _find_similar_patterns(self, command: str) -> List[str]:
        """
        Find similar command patterns from history.
        
        :param command: The command to match
        :return: List of similar patterns from history
        """
        similar_patterns = []
        
        # Compare with past commands in history
        for record in self.disambiguation_history:
            # Simple similarity check based on keywords
            record_keywords = set(record["command"].lower().split())
            command_keywords = set(command.lower().split())
            common_keywords = record_keywords.intersection(command_keywords)
            
            if len(common_keywords) > 0:
                similar_patterns.append(record["command"])
        
        return similar_patterns


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    # Create a basic handler
    handler = AmbiguousCommandHandler()
    
    # Test with ambiguous commands
    ambiguous_commands = [
        VoiceCommand(
            id="cmd-1",
            transcribed_text="Go to the room",
            intent="navigation",
            parameters={},
            confidence=0.8,
        ),
        VoiceCommand(
            id="cmd-2",
            transcribed_text="Pick it up",
            intent="manipulation",
            parameters={},
            confidence=0.7,
        ),
        VoiceCommand(
            id="cmd-3",
            transcribed_text="Move some distance",
            intent="navigation",
            parameters={},
            confidence=0.75,
        )
    ]
    
    for cmd in ambiguous_commands:
        print(f"\nProcessing command: '{cmd.transcribed_text}'")
        
        # Detect ambiguities
        ambiguities = handler.detect_ambiguity(cmd)
        print(f"Ambiguities detected: {[(a[0].value, a[1]) for a in ambiguities]}")
        
        if ambiguities:
            # Handle the first ambiguity for demonstration
            ambiguity_type, description = ambiguities[0]
            resolution = handler.resolve_ambiguity(cmd, ambiguity_type)
            print(f"Resolution: {resolution}")
    
    # Example with advanced handler
    async def advanced_example():
        advanced_handler = AdvancedAmbiguousCommandHandler()
        
        voice_cmd = VoiceCommand(
            id="cmd-4",
            transcribed_text="Do the thing like before",
            intent="unknown",
            parameters={},
            confidence=0.6
        )
        
        # Detect ambiguity
        ambiguities = advanced_handler.detect_ambiguity(voice_cmd)
        print(f"\nAdvanced handler - Ambiguities for '{voice_cmd.transcribed_text}':")
        for amb_type, desc in ambiguities:
            print(f"  {amb_type.value}: {desc}")
        
        if ambiguities:
            # Get LLM-based resolution
            resolution = await advanced_handler.resolve_with_llm(
                voice_cmd, 
                ambiguities[0][0],  # Use the first detected ambiguity
                {"recent_actions": ["moved to kitchen", "picked up cup"]}
            )
            print(f"LLM Resolution: {resolution}")
        
        # Simulate learning from a resolution
        await advanced_handler.learn_from_resolution(
            "Do the thing like before",
            AmbiguityType.ACTION_REFERENCE,
            ResolutionStrategy.REQUEST_CLARIFICATION,
            "I meant to pick up the cup like before"
        )
        
        print(f"Learning history now has {len(advanced_handler.disambiguation_history)} entries")
    
    # Run the advanced example
    # asyncio.run(advanced_example())