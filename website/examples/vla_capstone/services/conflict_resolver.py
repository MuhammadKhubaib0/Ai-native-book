"""
Service for resolving conflicts between different modalities in the VLA system.
"""
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from ..models.action_step import ActionStep, ActionType
from ..models.multimodal_input import MultimodalInput
import uuid


class ConflictType(Enum):
    """Enumeration of different types of conflicts between modalities."""
    COMPETING_INTENTS = "competing_intents"
    CONTRADICTORY_INFORMATION = "contradictory_information"
    SPATIAL_INCONSISTENCY = "spatial_inconsistency"
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"
    CAPABILITY_MISMATCH = "capability_mismatch"
    SAFETY_CONFLICT = "safety_conflict"


class ResolutionStrategy(Enum):
    """Enumeration of different conflict resolution strategies."""
    PREFER_HIGHER_CONFIDENCE = "prefer_higher_confidence"
    PREFER_RECENT_INPUT = "prefer_recent_input"
    FUSE_INFORMATION = "fuse_information"
    REQUEST_CLARIFICATION = "request_clarification"
    USE_CONTEXT = "use_context"
    DEFAULT_FALLBACK = "default_fallback"


class ConflictResolutionResult:
    """Class to encapsulate the result of conflict resolution."""
    def __init__(self, resolved_decision: Dict[str, Any], confidence: float, strategy_used: ResolutionStrategy):
        self.resolved_decision = resolved_decision
        self.confidence = confidence
        self.strategy_used = strategy_used
        self.conflict_resolved = True


class ConflictResolver:
    """
    Service for resolving conflicts between different modalities in the VLA system.
    """
    
    def __init__(self):
        """Initialize the conflict resolver."""
        self.default_strategy = ResolutionStrategy.PREFER_HIGHER_CONFIDENCE
        self.conflict_history = []
    
    def detect_conflicts(
        self,
        voice_data: Optional[Dict[str, Any]] = None,
        vision_data: Optional[Dict[str, Any]] = None,
        sensor_data: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ConflictType, Dict[str, Any], Dict[str, Any]]]:
        """
        Detect conflicts between different modalities.
        
        :param voice_data: Data from voice modality
        :param vision_data: Data from vision modality
        :param sensor_data: Data from sensor modality
        :return: List of detected conflicts with details
        """
        conflicts = []
        
        # Check for competing intents
        if voice_data and vision_data:
            voice_intent = voice_data.get("intent", "unknown")
            # Check vision for action-relevant information
            vision_objects = vision_data.get("objects", [])
            if self._check_intent_conflict(voice_intent, vision_objects):
                conflicts.append((
                    ConflictType.COMPETING_INTENTS,
                    {"voice_intent": voice_intent},
                    {"vision_objects": vision_objects}
                ))
        
        # Check for contradictory spatial information
        if voice_data and vision_data:
            voice_location = voice_data.get("parameters", {}).get("target_location")
            vision_detected_location = self._extract_location_from_vision(vision_data)
            
            if voice_location and vision_detected_location and voice_location != vision_detected_location:
                conflicts.append((
                    ConflictType.SPATIAL_INCONSISTENCY,
                    {"voice_location": voice_location},
                    {"vision_location": vision_detected_location}
                ))
        
        # Check for contradictory information (e.g., object exists vs doesn't exist)
        if voice_data and vision_data:
            voice_object_refs = self._extract_object_references(voice_data)
            vision_detected_objects = [obj.get("class") for obj in vision_data.get("objects", [])]
            
            contradicting_refs = [ref for ref in voice_object_refs if ref not in vision_detected_objects]
            if contradicting_refs:
                conflicts.append((
                    ConflictType.CONTRADICTORY_INFORMATION,
                    {"referenced_objects": voice_object_refs},
                    {"detected_objects": vision_detected_objects}
                ))
        
        # Check for safety conflicts
        if sensor_data:
            safety_issues = self._check_safety_conflicts(sensor_data)
            if safety_issues:
                conflicts.append((
                    ConflictType.SAFETY_CONFLICT,
                    {"sensor_readings": sensor_data},
                    {"safety_issues": safety_issues}
                ))
        
        return conflicts
    
    def _check_intent_conflict(self, voice_intent: str, vision_objects: List[Dict[str, Any]]) -> bool:
        """
        Check if voice intent conflicts with vision information.
        
        :param voice_intent: Intent from voice command
        :param vision_objects: Objects detected by vision system
        :return: True if there's a conflict, False otherwise
        """
        # Example: If user says "pick up the red cup" but no red cup is detected
        if "pick" in voice_intent.lower() or "grasp" in voice_intent.lower():
            for obj in vision_objects:
                obj_class = obj.get("class", "").lower()
                if "cup" in obj_class and "red" in obj_class:
                    return False  # Found the red cup, no conflict
            return True  # Didn't find the red cup mentioned in voice
        
        return False
    
    def _extract_location_from_vision(self, vision_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract a location from vision data.
        
        :param vision_data: Vision data to analyze
        :return: Detected location or None
        """
        # In a real implementation, this would analyze the scene to identify rooms/locations
        # For this example, we'll just look for keywords in object descriptions
        for frame in vision_data.get("processed_frames", []):
            for obj in frame.get("perception_results", {}).get("object_detection", {}).get("objects", []):
                obj_class = obj.get("class", "").lower()
                if obj_class in ["kitchen", "bedroom", "office", "living room", "dining room"]:
                    return obj_class
        
        return None
    
    def _extract_object_references(self, voice_data: Dict[str, Any]) -> List[str]:
        """
        Extract object references from voice data.
        
        :param voice_data: Voice data to analyze
        :return: List of object references
        """
        text = voice_data.get("transcribed_text", "").lower()
        # Simple extraction - in real implementation, would use NLP
        possible_objects = ["cup", "box", "book", "chair", "table", "ball"]
        references = [obj for obj in possible_objects if obj in text]
        return references
    
    def _check_safety_conflicts(self, sensor_data: Dict[str, Any]) -> List[str]:
        """
        Check for safety conflicts in sensor data.
        
        :param sensor_data: Sensor data to analyze
        :return: List of safety issues detected
        """
        safety_issues = []
        
        for reading in sensor_data.get("readings", []):
            if reading.get("type") == "distance_sensor":
                distance = reading.get("value")
                if isinstance(distance, (int, float)) and distance < 0.3:  # Less than 30cm
                    safety_issues.append(f"Obstacle detected at {distance}m")
        
        return safety_issues
    
    def resolve_conflicts(
        self,
        conflicts: List[Tuple[ConflictType, Dict[str, Any], Dict[str, Any]]],
        voice_data: Optional[Dict[str, Any]] = None,
        vision_data: Optional[Dict[str, Any]] = None,
        sensor_data: Optional[Dict[str, Any]] = None,
        strategy: Optional[ResolutionStrategy] = None
    ) -> List[ConflictResolutionResult]:
        """
        Resolve a list of detected conflicts.
        
        :param conflicts: List of detected conflicts
        :param voice_data: Data from voice modality
        :param vision_data: Data from vision modality
        :param sensor_data: Data from sensority modality
        :param strategy: Strategy to use for resolution (uses default if not specified)
        :return: List of resolution results
        """
        if strategy is None:
            strategy = self.default_strategy
        
        resolution_results = []
        
        for conflict_type, source1_data, source2_data in conflicts:
            resolution = self._resolve_single_conflict(
                conflict_type, source1_data, source2_data,
                voice_data, vision_data, sensor_data, strategy
            )
            resolution_results.append(resolution)
        
        return resolution_results
    
    def _resolve_single_conflict(
        self,
        conflict_type: ConflictType,
        source1_data: Dict[str, Any],
        source2_data: Dict[str, Any],
        voice_data: Optional[Dict[str, Any]],
        vision_data: Optional[Dict[str, Any]],
        sensor_data: Optional[Dict[str, Any]],
        strategy: ResolutionStrategy
    ) -> ConflictResolutionResult:
        """
        Resolve a single conflict using the specified strategy.
        
        :param conflict_type: Type of conflict to resolve
        :param source1_data: Data from the first source
        :param source2_data: Data from the second source
        :param voice_data: Voice data context
        :param vision_data: Vision data context
        :param sensor_data: Sensor data context
        :param strategy: Strategy to use for resolution
        :return: Resolution result
        """
        if strategy == ResolutionStrategy.PREFER_HIGHER_CONFIDENCE:
            return self._resolve_by_confidence(conflict_type, source1_data, source2_data)
        elif strategy == ResolutionStrategy.PREFER_RECENT_INPUT:
            return self._resolve_by_recency(conflict_type, source1_data, source2_data)
        elif strategy == ResolutionStrategy.FUSE_INFORMATION:
            return self._resolve_by_fusion(conflict_type, source1_data, source2_data)
        elif strategy == ResolutionStrategy.USE_CONTEXT:
            return self._resolve_by_context(
                conflict_type, source1_data, source2_data,
                voice_data, vision_data, sensor_data
            )
        elif strategy == ResolutionStrategy.REQUEST_CLARIFICATION:
            return self._resolve_by_clarification(
                conflict_type, source1_data, source2_data
            )
        elif strategy == ResolutionStrategy.DEFAULT_FALLBACK:
            return self._resolve_by_default_fallback(
                conflict_type, source1_data, source2_data
            )
        else:
            # Default to using confidence
            return self._resolve_by_confidence(conflict_type, source1_data, source2_data)
    
    def _resolve_by_confidence(
        self,
        conflict_type: ConflictType,
        source1_data: Dict[str, Any],
        source2_data: Dict[str, Any]
    ) -> ConflictResolutionResult:
        """
        Resolve conflict by preferring the source with higher confidence.
        
        :param conflict_type: Type of conflict
        :param source1_data: Data from source 1
        :param source2_data: Data from source 2
        :return: Resolution result
        """
        # Extract confidence values - this is a simplified approach
        conf1 = source1_data.get("confidence", 0.5)
        conf2 = source2_data.get("confidence", 0.5)
        
        if conf1 >= conf2:
            resolved_decision = {"decision": source1_data, "preferred_source": "source1"}
            confidence = conf1
        else:
            resolved_decision = {"decision": source2_data, "preferred_source": "source2"}
            confidence = conf2
        
        return ConflictResolutionResult(resolved_decision, confidence, ResolutionStrategy.PREFER_HIGHER_CONFIDENCE)
    
    def _resolve_by_recency(
        self,
        conflict_type: ConflictType,
        source1_data: Dict[str, Any],
        source2_data: Dict[str, Any]
    ) -> ConflictResolutionResult:
        """
        Resolve conflict by preferring the more recent input.
        
        :param conflict_type: Type of conflict
        :param source1_data: Data from source 1
        :param source2_data: Data from source 2
        :return: Resolution result
        """
        # In a real implementation, this would check timestamps
        # For this example, we'll assume source2 is more recent
        resolved_decision = {"decision": source2_data, "preferred_source": "source2", "reason": "more recent"}
        confidence = source2_data.get("confidence", 0.5)
        
        return ConflictResolutionResult(resolved_decision, confidence, ResolutionStrategy.PREFER_RECENT_INPUT)
    
    def _resolve_by_fusion(
        self,
        conflict_type: ConflictType,
        source1_data: Dict[str, Any],
        source2_data: Dict[str, Any]
    ) -> ConflictResolutionResult:
        """
        Resolve conflict by fusing information from both sources.
        
        :param conflict_type: Type of conflict
        :param source1_data: Data from source 1
        :param source2_data: Data from source 2
        :return: Resolution result
        """
        # Combine information from both sources
        fused_data = {}
        
        # Merge the dictionaries, with source2 taking precedence in case of conflicts
        fused_data.update(source1_data)
        fused_data.update(source2_data)
        
        # Average the confidences
        conf1 = source1_data.get("confidence", 0.5)
        conf2 = source2_data.get("confidence", 0.5)
        confidence = (conf1 + conf2) / 2
        
        resolved_decision = {"decision": fused_data, "fused_from": ["source1", "source2"]}
        
        return ConflictResolutionResult(resolved_decision, confidence, ResolutionStrategy.FUSE_INFORMATION)
    
    def _resolve_by_context(
        self,
        conflict_type: ConflictType,
        source1_data: Dict[str, Any],
        source2_data: Dict[str, Any],
        voice_data: Optional[Dict[str, Any]],
        vision_data: Optional[Dict[str, Any]],
        sensor_data: Optional[Dict[str, Any]]
    ) -> ConflictResolutionResult:
        """
        Resolve conflict by using contextual information.
        
        :param conflict_type: Type of conflict
        :param source1_data: Data from source 1
        :param source2_data: Data from source 2
        :param voice_data: Voice data context
        :param vision_data: Vision data context
        :param sensor_data: Sensor data context
        :return: Resolution result
        """
        # The resolution depends on the specific context and conflict type
        if conflict_type == ConflictType.SPATIAL_INCONSISTENCY:
            # If vision doesn't see what voice user mentioned, check if it's occluded
            if sensor_data and self._check_occupancy_conflict(sensor_data):
                resolved_decision = {
                    "decision": source2_data,  # Vision data
                    "reason": "sensor data indicates potential occupancy"
                }
                confidence = source2_data.get("confidence", 0.5)
            else:
                # If no sensor issues, prefer voice if there's a reason to trust it
                # (e.g., user has privileged knowledge)
                resolved_decision = {
                    "decision": source1_data,
                    "reason": "voice command preferred due to user's privileged knowledge"
                }
                confidence = source1_data.get("confidence", 0.5)
        else:
            # Default behavior
            resolved_decision = {"decision": source1_data, "reason": "contextual resolution applied"}
            confidence = source1_data.get("confidence", 0.5)
        
        return ConflictResolutionResult(resolved_decision, confidence, ResolutionStrategy.USE_CONTEXT)
    
    def _check_occupancy_conflict(self, sensor_data: Dict[str, Any]) -> bool:
        """
        Check if sensor data indicates occupancy that might explain vision limitations.
        
        :param sensor_data: Sensor data to analyze
        :return: True if occupancy conflict detected
        """
        for reading in sensor_data.get("readings", []):
            if reading.get("type") == "occupancy":
                occupied = reading.get("value", False)
                if occupied:
                    return True
        return False
    
    def _resolve_by_clarification(
        self,
        conflict_type: ConflictType,
        source1_data: Dict[str, Any],
        source2_data: Dict[str, Any]
    ) -> ConflictResolutionResult:
        """
        Resolve conflict by indicating the need for clarification.
        
        :param conflict_type: Type of conflict
        :param source1_data: Data from source 1
        :param source2_data: Data from source 2
        :return: Resolution result
        """
        # In this case, we can't resolve automatically, so we indicate the conflict
        resolved_decision = {
            "decision": "conflict_not_resolved",
            "conflict_type": conflict_type.value,
            "source1_data": source1_data,
            "source2_data": source2_data,
            "requires_clarification": True,
            "suggested_question": self._generate_clarification_question(conflict_type)
        }
        confidence = 0.0  # We're not confident since we need clarification
        
        return ConflictResolutionResult(resolved_decision, confidence, ResolutionStrategy.REQUEST_CLARIFICATION)
    
    def _generate_clarification_question(self, conflict_type: ConflictType) -> str:
        """
        Generate a question to clarify the conflict.
        
        :param conflict_type: Type of conflict
        :return: Clarification question
        """
        questions = {
            ConflictType.COMPETING_INTENTS: "Could you clarify what action you'd like me to take?",
            ConflictType.CONTRADICTORY_INFORMATION: "I seem to perceive something differently than you described. Could you clarify?",
            ConflictType.SPATIAL_INCONSISTENCY: "I don't see what you're referring to in that location. Could you describe it more?",
            ConflictType.SAFETY_CONFLICT: "I detected a potential safety issue. Should I proceed with caution?",
            ConflictType.CAPABILITY_MISMATCH: "I may not be able to do exactly what you requested. Can we find an alternative?",
            ConflictType.TEMPORAL_INCONSISTENCY: "I'm not sure about the timing you mentioned. When would you like me to do this?"
        }
        
        return questions.get(conflict_type, "I'm uncertain about your request. Could you please clarify?")
    
    def _resolve_by_default_fallback(
        self,
        conflict_type: ConflictType,
        source1_data: Dict[str, Any],
        source2_data: Dict[str, Any]
    ) -> ConflictResolutionResult:
        """
        Resolve conflict using a default fallback approach.
        
        :param conflict_type: Type of conflict
        :param source1_data: Data from source 1
        :param source2_data: Data from source 2
        :return: Resolution result
        """
        # Default fallback: prefer source 1 (voice)
        resolved_decision = {"decision": source1_data, "reason": "default fallback"}
        confidence = source1_data.get("confidence", 0.5)
        
        return ConflictResolutionResult(resolved_decision, confidence, ResolutionStrategy.DEFAULT_FALLBACK)
    
    def resolve_multimodal_input(
        self,
        voice_data: Optional[Dict[str, Any]] = None,
        vision_data: Optional[Dict[str, Any]] = None,
        sensor_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], float, List[ConflictResolutionResult]]:
        """
        Resolve conflicts in a complete multimodal input.
        
        :param voice_data: Data from voice modality
        :param vision_data: Data from vision modality
        :param sensor_data: Data from sensor modality
        :return: Resolved decision, confidence, and resolution results
        """
        # Detect conflicts
        conflicts = self.detect_conflicts(voice_data, vision_data, sensor_data)
        
        if not conflicts:
            # No conflicts, just return a simple fusion of the inputs
            return self._simple_fusion(voice_data, vision_data, sensor_data)
        
        # Resolve conflicts
        resolution_results = self.resolve_conflicts(conflicts, voice_data, vision_data, sensor_data)
        
        # Combine the resolved decisions
        final_decision = self._combine_resolution_results(resolution_results, voice_data, vision_data, sensor_data)
        
        # Calculate overall confidence
        avg_confidence = sum(r.confidence for r in resolution_results) / len(resolution_results) if resolution_results else 0.5
        
        return final_decision, avg_confidence, resolution_results
    
    def _simple_fusion(
        self,
        voice_data: Optional[Dict[str, Any]],
        vision_data: Optional[Dict[str, Any]],
        sensor_data: Optional[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], float, List[ConflictResolutionResult]]:
        """
        Perform simple fusion when no conflicts are detected.
        
        :param voice_data: Data from voice modality
        :param vision_data: Data from vision modality
        :param sensor_data: Data from sensor modality
        :return: Fused decision, confidence, and empty resolution results list
        """
        decision = {
            "voice_data": voice_data,
            "vision_data": vision_data,
            "sensor_data": sensor_data,
            "fusion_method": "simple",
            "timestamp": str(datetime.now())
        }
        
        # Calculate average confidence
        confidences = []
        if voice_data and "confidence" in voice_data:
            confidences.append(voice_data["confidence"])
        if vision_data and "confidence" in vision_data:
            confidences.append(vision_data["confidence"])
        if sensor_data and "confidence" in sensor_data:
            confidences.append(sensor_data["confidence"])
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        return decision, avg_confidence, []
    
    def _combine_resolution_results(
        self,
        resolution_results: List[ConflictResolutionResult],
        voice_data: Optional[Dict[str, Any]],
        vision_data: Optional[Dict[str, Any]],
        sensor_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Combine multiple resolution results into a single decision.
        
        :param resolution_results: List of resolution results
        :param voice_data: Original voice data
        :param vision_data: Original vision data
        :param sensor_data: Original sensor data
        :return: Combined decision
        """
        combined_decision = {
            "resolved_elements": [],
            "resolution_summary": [],
            "original_data": {
                "voice": voice_data,
                "vision": vision_data,
                "sensor": sensor_data
            },
            "conflict_resolution_applied": True
        }
        
        for i, result in enumerate(resolution_results):
            combined_decision["resolved_elements"].append({
                "resolution_id": f"res_{i}",
                "strategy": result.strategy_used.value,
                "decision": result.resolved_decision,
                "confidence": result.confidence
            })
            
            combined_decision["resolution_summary"].append({
                "strategy": result.strategy_used.value,
                "confidence": result.confidence
            })
        
        return combined_decision


class AdvancedConflictResolver(ConflictResolver):
    """
    Advanced conflict resolver with machine learning-based resolution strategies.
    """
    
    def __init__(self):
        super().__init__()
        self.ml_resolution_enabled = True
        self.conflict_patterns = {}  # Would store learned conflict patterns
    
    def learn_from_resolution(
        self,
        conflict_type: ConflictType,
        resolution_strategy: ResolutionStrategy,
        resolution_successful: bool,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Learn from the effectiveness of different resolution strategies.
        
        :param conflict_type: Type of conflict
        :param resolution_strategy: Strategy that was used
        :param resolution_successful: Whether the resolution was successful
        :param context: Context information
        """
        pattern_key = f"{conflict_type.value}_{resolution_strategy.value}"
        
        if pattern_key not in self.conflict_patterns:
            self.conflict_patterns[pattern_key] = {
                "attempts": 0,
                "successes": 0,
                "success_rate": 0.0
            }
        
        pattern = self.conflict_patterns[pattern_key]
        pattern["attempts"] += 1
        if resolution_successful:
            pattern["successes"] += 1
        pattern["success_rate"] = pattern["successes"] / pattern["attempts"]
    
    def get_advisory_resolution(
        self,
        conflict_type: ConflictType,
        context: Optional[Dict[str, Any]] = None
    ) -> ResolutionStrategy:
        """
        Get an advisory resolution strategy based on learned patterns.
        
        :param conflict_type: Type of conflict
        :param context: Context information
        :return: Recommended resolution strategy
        """
        if not self.ml_resolution_enabled:
            return self.default_strategy
        
        # Find the strategy with the highest success rate for this conflict type
        best_strategy = self.default_strategy
        best_rate = 0.0
        
        for pattern_key, pattern_data in self.conflict_patterns.items():
            if conflict_type.value in pattern_key:
                if pattern_data["success_rate"] > best_rate:
                    strategy_part = pattern_key.split("_")[-1]
                    try:
                        best_strategy = ResolutionStrategy(strategy_part)
                        best_rate = pattern_data["success_rate"]
                    except ValueError:
                        # If the pattern key doesn't match a valid strategy, skip it
                        continue
        
        return best_strategy


# Example usage:
if __name__ == "__main__":
    from datetime import datetime
    
    # Create a conflict resolver
    resolver = ConflictResolver()
    
    # Example data with a potential conflict
    voice_data = {
        "intent": "navigation",
        "transcribed_text": "Go to the kitchen",
        "confidence": 0.85,
        "parameters": {"target_location": "kitchen"}
    }
    
    vision_data = {
        "objects": [{"class": "bedroom", "confidence": 0.92}],
        "scene_description": "Bedroom with bed and dresser",
        "confidence": 0.90,
        "processed_frames": [
            {
                "perception_results": {
                    "object_detection": {
                        "objects": [{"class": "bed", "bbox": [0.1, 0.2, 0.8, 0.9], "confidence": 0.92}]
                    }
                }
            }
        ]
    }
    
    sensor_data = {
        "readings": [
            {"type": "distance_sensor", "value": 0.5, "confidence": 0.98},
            {"type": "occupancy", "value": False}
        ],
        "confidence": 0.95
    }
    
    # Detect conflicts
    conflicts = resolver.detect_conflicts(voice_data, vision_data, sensor_data)
    print(f"Detected {len(conflicts)} conflicts:")
    for conflict_type, source1, source2 in conflicts:
        print(f"  - {conflict_type.value}: {source1} vs {source2}")
    
    # Resolve conflicts
    if conflicts:
        resolution_results = resolver.resolve_conflicts(conflicts, voice_data, vision_data, sensor_data)
        print(f"\nResolution results:")
        for result in resolution_results:
            print(f"  - Strategy: {result.strategy_used.value}")
            print(f"    Confidence: {result.confidence}")
            print(f"    Decision: {result.resolved_decision}")
    
    # Complete resolution process
    final_decision, confidence, resolution_results = resolver.resolve_multimodal_input(
        voice_data, vision_data, sensor_data
    )
    print(f"\nFinal decision confidence: {confidence}")
    print(f"Resolution applied: {len(resolution_results)} conflicts resolved")
    
    # Example with advanced resolver
    advanced_resolver = AdvancedConflictResolver()
    
    # Simulate learning from a few resolution attempts
    advanced_resolver.learn_from_resolution(
        ConflictType.SPATIAL_INCONSISTENCY,
        ResolutionStrategy.USE_CONTEXT,
        True  # Successful resolution
    )
    advanced_resolver.learn_from_resolution(
        ConflictType.SPATIAL_INCONSISTENCY,
        ResolutionStrategy.USE_CONTEXT,
        False  # Unsuccessful resolution
    )
    
    # Get advisory strategy
    advisory_strategy = advanced_resolver.get_advisory_resolution(ConflictType.SPATIAL_INCONSISTENCY)
    print(f"\nAdvisory strategy for spatial inconsistency: {advisory_strategy.value}")