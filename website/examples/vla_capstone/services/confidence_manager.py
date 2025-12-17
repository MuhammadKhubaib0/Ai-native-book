"""
Service for managing and making decisions based on confidence levels across modalities.
"""
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
from ..models.action_step import ActionStep
from ..models.multimodal_input import MultimodalInput
from ..config import settings
import numpy as np
import math


class ConfidenceSource(Enum):
    """Enumeration of different confidence sources."""
    VOICE_RECOGNITION = "voice_recognition"
    INTENT_EXTRACTOR = "intent_extractor"
    OBJECT_DETECTION = "object_detection"
    DEPTH_ESTIMATION = "depth_estimation"
    SEMANTIC_SEGMENTATION = "semantic_segmentation"
    LANGUAGE_MODEL = "language_model"
    ACTION_PLANNER = "action_planner"
    SENSORS = "sensors"
    FUSION_PROCESS = "fusion_process"


class UncertaintyType(Enum):
    """Enumeration of different types of uncertainty."""
    ALEATORIC = "aleatoric"  # Data uncertainty (noise in observations)
    EPISTEMIC = "epistemic"  # Model uncertainty (lack of knowledge)
    SYSTEMATIC = "systematic"  # Systematic errors (biased models)
    CONTEXTUAL = "contextual"  # Uncertainty due to context


class ConfidenceLevel(Enum):
    """Enumeration of different confidence levels."""
    VERY_LOW = (0.0, 0.2, "Very Low")
    LOW = (0.2, 0.4, "Low")
    MEDIUM = (0.4, 0.7, "Medium")
    HIGH = (0.7, 0.9, "High")
    VERY_HIGH = (0.9, 1.0, "Very High")
    
    def __init__(self, min_val: float, max_val: float, description: str):
        self.min_val = min_val
        self.max_val = max_val
        self.description = description
    
    @classmethod
    def get_level(cls, confidence: float) -> 'ConfidenceLevel':
        """Get the confidence level for a given confidence value."""
        for level in cls:
            if level.min_val <= confidence < level.max_val:
                return level
        return cls.VERY_HIGH  # For confidence = 1.0


class ConfidenceManager:
    """
    Service for managing and making decisions based on confidence levels across modalities.
    """
    
    def __init__(self):
        """Initialize the confidence manager."""
        self.minimum_confidence_threshold = settings.minimum_confidence_score
        self.confidence_weights = {
            ConfidenceSource.VOICE_RECOGNITION: 0.3,
            ConfidenceSource.INTENT_EXTRACTOR: 0.2,
            ConfidenceSource.OBJECT_DETECTION: 0.4,
            ConfidenceSource.DEPTH_ESTIMATION: 0.3,
            ConfidenceSource.SEMANTIC_SEGMENTATION: 0.3,
            ConfidenceSource.LANGUAGE_MODEL: 0.5,
            ConfidenceSource.ACTION_PLANNER: 0.4,
            ConfidenceSource.SENSORS: 0.6,
            ConfidenceSource.FUSION_PROCESS: 0.7
        }
        self.uncertainty_propagation_enabled = True
    
    def calculate_overall_confidence(
        self,
        voice_confidence: Optional[float] = None,
        vision_confidence: Optional[float] = None,
        sensor_confidence: Optional[float] = None,
        other_confidences: Optional[Dict[ConfidenceSource, float]] = None
    ) -> float:
        """
        Calculate overall confidence based on multiple modality confidences.
        
        :param voice_confidence: Confidence in voice processing
        :param vision_confidence: Confidence in vision processing
        :param sensor_confidence: Confidence in sensor processing
        :param other_confidences: Confidences from other sources
        :return: Overall confidence score
        """
        if other_confidences is None:
            other_confidences = {}
        
        # Collect all confidences with their weights
        all_confidences = []
        
        if voice_confidence is not None:
            weight = self.confidence_weights.get(ConfidenceSource.VOICE_RECOGNITION, 0.3)
            all_confidences.append((voice_confidence, weight))
        
        if vision_confidence is not None:
            weight = self.confidence_weights.get(ConfidenceSource.OBJECT_DETECTION, 0.4)  # Using object detection as general vision weight
            all_confidences.append((vision_confidence, weight))
        
        if sensor_confidence is not None:
            weight = self.confidence_weights.get(ConfidenceSource.SENSORS, 0.6)
            all_confidences.append((sensor_confidence, weight))
        
        # Add other confidences
        for source, conf in other_confidences.items():
            weight = self.confidence_weights.get(source, 0.5)
            all_confidences.append((conf, weight))
        
        if not all_confidences:
            return 0.5  # Default confidence if no inputs provided
        
        # Calculate weighted average confidence
        weighted_sum = sum(conf * weight for conf, weight in all_confidences)
        total_weight = sum(weight for conf, weight in all_confidences)
        
        if total_weight == 0:
            return 0.5  # Default if all weights are 0
        
        overall_confidence = weighted_sum / total_weight
        
        # Apply uncertainty propagation if enabled
        if self.uncertainty_propagation_enabled:
            overall_confidence = self._apply_uncertainty_propagation(
                overall_confidence, all_confidences
            )
        
        # Ensure confidence is within bounds
        return max(0.0, min(1.0, overall_confidence))
    
    def _apply_uncertainty_propagation(
        self,
        base_confidence: float,
        confidences_with_weights: List[Tuple[float, float]]
    ) -> float:
        """
        Apply uncertainty propagation to adjust confidence based on input uncertainties.
        
        :param base_confidence: Base confidence calculated without propagation
        :param confidences_with_weights: List of (confidence, weight) tuples
        :return: Adjusted confidence with uncertainty propagation applied
        """
        # Calculate the entropy-like uncertainty measure
        uncertainties = [1 - conf for conf, _ in confidences_with_weights]
        
        # Weighted uncertainty
        weighted_uncertainty = sum(unc * weight for (unc, weight) in zip(uncertainties, [w for _, w in confidences_with_weights]))
        total_weights = sum(w for _, w in confidences_with_weights)
        
        if total_weights > 0:
            avg_uncertainty = weighted_uncertainty / total_weights
            # Reduce confidence based on average uncertainty
            adjusted_confidence = base_confidence * (1 - avg_uncertainty)
        else:
            adjusted_confidence = base_confidence
        
        return max(0.0, min(1.0, adjusted_confidence))
    
    def should_execute_action(self, confidence: float) -> bool:
        """
        Determine if an action should be executed based on confidence.
        
        :param confidence: Confidence in the action decision
        :return: True if action should be executed, False otherwise
        """
        return confidence >= self.minimum_confidence_threshold
    
    def get_confidence_recommendation(
        self,
        confidence: float,
        action_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a recommendation based on confidence level.
        
        :param confidence: The confidence value to evaluate
        :param action_type: Type of action being considered
        :return: Recommendation dictionary
        """
        level = ConfidenceLevel.get_level(confidence)
        recommendation = {
            "confidence_level": level,
            "recommendation": "",
            "safety_level": "safe",
            "action_advice": "proceed"
        }
        
        if level == ConfidenceLevel.VERY_LOW:
            recommendation["recommendation"] = "Do not proceed without human intervention"
            recommendation["safety_level"] = "unsafe"
            recommendation["action_advice"] = "abort_and_request_help"
        elif level == ConfidenceLevel.LOW:
            recommendation["recommendation"] = "Request clarification before proceeding"
            recommendation["safety_level"] = "cautious"
            recommendation["action_advice"] = "request_clarification"
        elif level == ConfidenceLevel.MEDIUM:
            recommendation["recommendation"] = "Proceed with caution"
            recommendation["safety_level"] = "cautious"
            recommendation["action_advice"] = "proceed_cautiously"
        elif level == ConfidenceLevel.HIGH:
            recommendation["recommendation"] = "Confident to proceed"
            recommendation["action_advice"] = "proceed"
        else:  # VERY_HIGH
            recommendation["recommendation"] = "Highly confident to proceed"
            recommendation["action_advice"] = "proceed_confidently"
        
        # Adjust recommendation based on action type if provided
        if action_type:
            if action_type.lower() in ["manipulation", "grasp", "pick"]:
                # Manipulation requires higher caution
                if level in [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM]:
                    recommendation["action_advice"] = "request_clarification"
                    recommendation["recommendation"] = f"Request confirmation before {action_type} action at this confidence level"
        
        return recommendation
    
    def assess_uncertainty_type(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any]
    ) -> List[Tuple[UncertaintyType, float]]:
        """
        Assess the types of uncertainty in the inputs and outputs.
        
        :param inputs: Input data to the system
        :param outputs: Output from the system
        :return: List of (uncertainty_type, uncertainty_score) tuples
        """
        uncertainties = []
        
        # Assess aleatoric uncertainty (data uncertainty)
        aleatoric_score = self._assess_aleatoric_uncertainty(inputs, outputs)
        uncertainties.append((UncertaintyType.ALEATORIC, aleatoric_score))
        
        # Assess epistemic uncertainty (model uncertainty)
        epistemic_score = self._assess_epistemic_uncertainty(inputs, outputs)
        uncertainties.append((UncertaintyType.EPISTEMIC, epistemic_score))
        
        # Assess systematic uncertainty
        systematic_score = self._assess_systematic_uncertainty(inputs, outputs)
        uncertainties.append((UncertaintyType.SYSTEMATIC, systematic_score))
        
        # Assess contextual uncertainty
        contextual_score = self._assess_contextual_uncertainty(inputs, outputs)
        uncertainties.append((UncertaintyType.CONTEXTUAL, contextual_score))
        
        return uncertainties
    
    def _assess_aleatoric_uncertainty(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any]
    ) -> float:
        """
        Assess aleatoric uncertainty (data uncertainty).
        
        :param inputs: Input data
        :param outputs: Output data
        :return: Aleatoric uncertainty score
        """
        # Aleatoric uncertainty comes from noise in observations
        # This might be estimated by looking at variance in sensor readings or noise levels in audio
        uncertainty_score = 0.0
        
        # Check for sensor noise indicators
        sensor_readings = inputs.get("sensors", {}).get("readings", [])
        for reading in sensor_readings:
            if "noise_level" in reading:
                uncertainty_score = max(uncertainty_score, reading["noise_level"])
        
        # Check for audio noise indicators
        voice_confidence = inputs.get("voice", {}).get("confidence", 1.0)
        if voice_confidence < 0.7:
            # Lower confidence may indicate noisy audio
            uncertainty_score = max(uncertainty_score, 1.0 - voice_confidence)
        
        # Check for image quality indicators
        vision_quality = inputs.get("vision", {}).get("quality", 1.0)
        if vision_quality < 0.7:
            uncertainty_score = max(uncertainty_score, 1.0 - vision_quality)
        
        return min(uncertainty_score, 1.0)
    
    def _assess_epistemic_uncertainty(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any]
    ) -> float:
        """
        Assess epistemic uncertainty (model uncertainty).
        
        :param inputs: Input data
        :param outputs: Output data
        :return: Epistemic uncertainty score
        """
        # Epistemic uncertainty reflects lack of knowledge
        # This might be estimated by comparing model confidence with expected performance
        uncertainty_score = 0.0
        
        # Check if the input is outside the training distribution
        # For example, unusual object configurations or contexts
        objects = inputs.get("vision", {}).get("objects", [])
        if len(objects) > 10:  # More objects than usually encountered
            uncertainty_score = 0.3  # Increase uncertainty for complex scenes
        
        # Check for novel combinations of actions and contexts
        voice_intent = inputs.get("voice", {}).get("intent", "unknown")
        if voice_intent == "unknown":
            uncertainty_score = max(uncertainty_score, 0.5)
        
        return min(uncertainty_score, 1.0)
    
    def _assess_systematic_uncertainty(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any]
    ) -> float:
        """
        Assess systematic uncertainty (systematic errors).
        
        :param inputs: Input data
        :param outputs: Output data
        :return: Systematic uncertainty score
        """
        # Systematic uncertainty comes from consistent biases in the system
        # This is harder to measure directly without ground truth
        uncertainty_score = 0.0
        
        # Check for environmental factors that could cause systematic errors
        lighting_conditions = inputs.get("vision", {}).get("lighting", "normal")
        if lighting_conditions in ["very_dark", "very_bright"]:
            # Vision models often have systematic issues in extreme lighting
            uncertainty_score = 0.4
        
        # Check for calibration issues
        sensor_calibrated = inputs.get("sensors", {}).get("calibrated", True)
        if not sensor_calibrated:
            uncertainty_score = max(uncertainty_score, 0.5)
        
        return min(uncertainty_score, 1.0)
    
    def _assess_contextual_uncertainty(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any]
    ) -> float:
        """
        Assess contextual uncertainty.
        
        :param inputs: Input data
        :param outputs: Output data
        :return: Contextual uncertainty score
        """
        # Contextual uncertainty comes from unfamiliar contexts
        uncertainty_score = 0.0
        
        # Check if the environment context is familiar
        environment_context = inputs.get("context", {}).get("environment", "unknown")
        if environment_context not in ["office", "home", "laboratory"]:  # Known environments
            uncertainty_score = 0.3  # Unfamiliar environment increases uncertainty
        
        # Check for conflicting context information
        # For example, voice command suggests indoor action but GPS suggests outdoor location
        location_context = inputs.get("context", {}).get("location", "unknown")
        if "outdoor" in location_context and "navigation" in inputs.get("voice", {}).get("intent", ""):
            uncertainty_score = max(uncertainty_score, 0.4)  # Different handling needed for outdoor navigation
        
        return min(uncertainty_score, 1.0)
    
    def make_decision_with_confidence(
        self,
        possible_actions: List[ActionStep],
        confidences: List[float],
        action_types: Optional[List[str]] = None
    ) -> Tuple[Optional[ActionStep], float, Dict[str, Any]]:
        """
        Make a decision among possible actions based on their confidences.
        
        :param possible_actions: List of possible action steps
        :param confidences: List of confidence scores for each action
        :param action_types: List of action types (optional)
        :return: Selected action, confidence in choice, and decision metadata
        """
        if not possible_actions or not confidences:
            return None, 0.0, {"reason": "no actions provided"}
        
        if len(possible_actions) != len(confidences):
            raise ValueError("Number of actions must match number of confidences")
        
        # Find the action with the highest confidence
        max_confidence_idx = np.argmax(confidences)
        selected_action = possible_actions[max_confidence_idx]
        selected_confidence = confidences[max_confidence_idx]
        
        # If action types provided, apply special logic for certain types
        decision_metadata = {
            "selected_index": max_confidence_idx,
            "confidence_threshold_met": selected_confidence >= self.minimum_confidence_threshold,
            "all_confidences": confidences,
            "recommendation": self.get_confidence_recommendation(selected_confidence)
        }
        
        # Check for safety-critical action types
        if action_types:
            selected_type = action_types[max_confidence_idx]
            if selected_type in ["manipulation", "grasp"]:
                # For manipulation, require higher confidence or apply safety checks
                if selected_confidence < 0.85:  # Higher threshold for manipulation
                    decision_metadata["safety_advice"] = "confidence below manipulation safety threshold"
                    decision_metadata["recommendation"]["action_advice"] = "request_human_approval"
        
        # Check for competing high-confidence actions
        high_conf_actions = [i for i, conf in enumerate(confidences) if conf > 0.9]
        if len(high_conf_actions) > 1:
            decision_metadata["competing_high_confidence"] = high_conf_actions
            decision_metadata["decision_strategy"] = "highest_confidence_selected"
        else:
            decision_metadata["decision_strategy"] = "single_high_confidence_action"
        
        return selected_action, selected_confidence, decision_metadata
    
    def combine_confidences(
        self,
        confidence_list: List[float],
        combination_method: str = "mean"
    ) -> float:
        """
        Combine multiple confidence scores using the specified method.
        
        :param confidence_list: List of confidence values to combine
        :param combination_method: Method to use for combination ('mean', 'min', 'max', 'weighted')
        :return: Combined confidence value
        """
        if not confidence_list:
            return 0.5  # Default confidence
        
        if combination_method == "mean":
            return sum(confidence_list) / len(confidence_list)
        elif combination_method == "min":
            return min(confidence_list)
        elif combination_method == "max":
            return max(confidence_list)
        elif combination_method == "weighted":
            # Weighted by inverse index (more recent results have higher weight)
            weights = [i + 1 for i in range(len(confidence_list))]
            weighted_sum = sum(c * w for c, w in zip(confidence_list, weights))
            total_weight = sum(weights)
            return weighted_sum / total_weight if total_weight > 0 else 0.5
        else:
            # Default to mean
            return sum(confidence_list) / len(confidence_list)
    
    def adjust_for_task_complexity(self, base_confidence: float, task_complexity: int) -> float:
        """
        Adjust confidence based on task complexity.
        
        :param base_confidence: Base confidence score
        :param task_complexity: Complexity level (1-5 scale)
        :return: Adjusted confidence
        """
        # Complexity reduces confidence: higher complexity leads to lower effective confidence
        complexity_penalty = (task_complexity - 1) * 0.1  # Up to 0.4 penalty for complexity 5
        adjusted_confidence = base_confidence * (1.0 - complexity_penalty)
        
        return max(0.0, adjusted_confidence)


class BayesianConfidenceManager(ConfidenceManager):
    """
    Advanced confidence manager using Bayesian inference for confidence updates.
    """
    
    def __init__(self):
        super().__init__()
        self.prior_confidence = 0.5
        self.success_history = []
        self.failure_history = []
    
    def bayesian_update(
        self,
        prior: float,
        likelihood: float,
        evidence: float
    ) -> float:
        """
        Perform a Bayesian update of confidence.
        
        :param prior: Prior confidence
        :param likelihood: Likelihood of evidence given hypothesis
        :param evidence: Marginal probability of evidence
        :return: Updated confidence (posterior)
        """
        # Bayes rule: P(H|E) = P(E|H) * P(H) / P(E)
        if evidence == 0:
            return prior  # Cannot update with zero evidence
        
        posterior = (likelihood * prior) / evidence
        return min(1.0, posterior)  # Ensure confidence is within bounds
    
    def update_confidence_with_feedback(
        self,
        source: ConfidenceSource,
        initial_confidence: float,
        feedback: bool  # True for success, False for failure
    ) -> float:
        """
        Update confidence based on outcome feedback.
        
        :param source: The source of the confidence estimate
        :param initial_confidence: The initial confidence value
        :param feedback: Outcome feedback (True for success, False for failure)
        :return: Updated confidence value
        """
        # Record the outcome in history
        if feedback:
            self.success_history.append((source, initial_confidence))
        else:
            self.failure_history.append((source, initial_confidence))
        
        # Calculate a likelihood based on historical accuracy
        # For simplicity, we'll calculate the accuracy of predictions near the confidence level
        accuracy = self._calculate_calibrated_accuracy(initial_confidence, source)
        
        if feedback:
            # If the action succeeded, increase confidence based on past accuracy
            updated_confidence = self.bayesian_update(initial_confidence, accuracy, 0.7)  # 0.7 as evidence
        else:
            # If the action failed, decrease confidence
            updated_confidence = self.bayesian_update(initial_confidence, 1 - accuracy, 0.7)  # 1-accuracy as evidence of failure
        
        return updated_confidence
    
    def _calculate_calibrated_accuracy(self, confidence: float, source: ConfidenceSource) -> float:
        """
        Calculate the historical accuracy for predictions of similar confidence levels.
        
        :param confidence: The confidence level to evaluate
        :param source: The source of confidence
        :return: Calibrated accuracy
        """
        # Define confidence bins
        bin_size = 0.2
        bin_center = ((confidence + bin_size/2) // bin_size) * bin_size
        bin_center = min(0.9, max(0.1, bin_center))  # Keep in range [0.1, 0.9]
        
        # Find all predictions in the same bin for this source
        relevant_successes = [
            pred_conf for src, pred_conf in self.success_history
            if src == source and abs(pred_conf - bin_center) <= bin_size/2
        ]
        relevant_failures = [
            pred_conf for src, pred_conf in self.failure_history
            if src == source and abs(pred_conf - bin_center) <= bin_size/2
        ]
        
        total_predictions = len(relevant_successes) + len(relevant_failures)
        
        if total_predictions == 0:
            return confidence  # Default to the original confidence if no history
        
        accuracy = len(relevant_successes) / total_predictions
        
        # Keep the accuracy within reasonable bounds
        return max(0.05, min(0.95, accuracy))
    
    def predict_future_confidence(self, current_confidence: float, source: ConfidenceSource) -> float:
        """
        Predict the likely confidence of the same source in the future.
        
        :param current_confidence: Current confidence in the source
        :param source: The source of confidence
        :return: Predicted future confidence
        """
        # Use historical accuracy as a predictor
        calibrated_accuracy = self._calculate_calibrated_accuracy(current_confidence, source)
        
        # Apply a smoothing factor based on the amount of history available
        history_count = sum(1 for src, _ in (self.success_history + self.failure_history) if src == source)
        
        if history_count < 5:
            # Not enough history, be conservative
            return (current_confidence + calibrated_accuracy) / 2
        else:
            # More history available, trust calibration more
            return calibrated_accuracy


# Example usage:
if __name__ == "__main__":
    # Create a confidence manager
    conf_manager = ConfidenceManager()
    
    # Example confidence values from different sources
    voice_conf = 0.85
    vision_conf = 0.92
    sensor_conf = 0.78
    
    # Calculate overall confidence
    overall_conf = conf_manager.calculate_overall_confidence(
        voice_confidence=voice_conf,
        vision_confidence=vision_conf,
        sensor_confidence=sensor_conf
    )
    
    print(f"Overall confidence: {overall_conf:.3f}")
    print(f"Confidence level: {ConfidenceLevel.get_level(overall_conf).description}")
    
    # Check if action should be executed
    should_execute = conf_manager.should_execute_action(overall_conf)
    print(f"Should execute action: {should_execute}")
    
    # Get confidence recommendation
    recommendation = conf_manager.get_confidence_recommendation(overall_conf)
    print(f"Recommendation: {recommendation['recommendation']}")
    
    # Example with action selection
    from ..models.action_step import ActionStep, ActionType
    
    actions = [
        ActionStep(
            id="action_1",
            action_sequence_id="seq_123",
            action_type=ActionType.NAVIGATION,
            parameters={"x": 1.0, "y": 2.0},
            timeout=10,
            order=0
        ),
        ActionStep(
            id="action_2",
            action_sequence_id="seq_123",
            action_type=ActionType.MANIPULATION,
            parameters={"action": "grasp", "object": "cup"},
            timeout=15,
            order=1
        )
    ]
    
    action_confidences = [0.89, 0.65]  # Different confidences for each action
    action_types = ["navigation", "manipulation"]
    
    selected_action, selected_conf, metadata = conf_manager.make_decision_with_confidence(
        actions, action_confidences, action_types
    )
    
    print(f"\nSelected action: {selected_action.action_type.value} with confidence {selected_conf:.3f}")
    print(f"Decision metadata: {metadata}")
    
    # Example of uncertainty assessment
    inputs = {
        "voice": {"intent": "navigation", "confidence": 0.85},
        "vision": {"objects": ["kitchen"], "quality": 0.8, "lighting": "normal"},
        "sensors": {"readings": [{"type": "distance", "value": 1.0}], "calibrated": True},
        "context": {"environment": "home"}
    }
    
    outputs = {"action": "navigate_to_kitchen"}
    
    uncertainties = conf_manager.assess_uncertainty_type(inputs, outputs)
    print(f"\nUncertainty assessment:")
    for uncertainty_type, score in uncertainties:
        print(f"  {uncertainty_type.value}: {score:.3f}")
    
    # Example with Bayesian confidence manager
    bayes_manager = BayesianConfidenceManager()
    
    # Simulate updating confidence based on feedback
    initial_conf = 0.8
    print(f"\nInitial confidence: {initial_conf}")
    
    # Update with positive feedback (action succeeded)
    updated_conf_success = bayes_manager.update_confidence_with_feedback(
        ConfidenceSource.ACTION_PLANNER, initial_conf, True
    )
    print(f"Confidence after success: {updated_conf_success:.3f}")
    
    # Update with negative feedback (action failed)
    updated_conf_failure = bayes_manager.update_confidence_with_feedback(
        ConfidenceSource.ACTION_PLANNER, initial_conf, False
    )
    print(f"Confidence after failure: {updated_conf_failure:.3f}")
    
    # Predict future confidence
    predicted_conf = bayes_manager.predict_future_confidence(
        initial_conf, ConfidenceSource.ACTION_PLANNER
    )
    print(f"Predicted future confidence: {predicted_conf:.3f}")