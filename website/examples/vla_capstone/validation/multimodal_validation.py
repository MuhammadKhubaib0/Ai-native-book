"""
Validation service for multimodal inputs in the VLA system.
"""
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
from ..models.multimodal_input import MultimodalInput
from ..models.vla_system_state import VLASystemState
from ..config import settings


class ValidationResult(BaseModel):
    """Result of validation process."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    confidence_score: Optional[float] = None


class MultimodalValidationService:
    """
    Service for validating multimodal inputs in the VLA system.
    """
    
    def __init__(self):
        """Initialize the multimodal validation service."""
        self.min_visual_objects = 1  # Minimum number of objects for valid vision input
        self.max_visual_objects = 50  # Maximum number of objects for valid vision input
        self.min_audio_duration = 0.1  # Minimum audio duration in seconds
        self.max_audio_duration = 60.0  # Maximum audio duration in seconds
        self.required_spatial_fields = ["x", "y", "z"]  # Required fields for spatial data
        self.confidence_threshold = settings.minimum_confidence_score
    
    def validate_multimodal_input(self, multimodal_input: MultimodalInput) -> ValidationResult:
        """
        Validate a multimodal input object.
        
        :param multimodal_input: The multimodal input to validate
        :return: Validation result
        """
        errors = []
        warnings = []
        
        # Validate ID
        if not multimodal_input.id or len(multimodal_input.id.strip()) == 0:
            errors.append("Multimodal input ID is required")
        
        # Validate visual data if present
        if multimodal_input.visual_data is not None:
            visual_errors, visual_warnings = self._validate_visual_data(multimodal_input.visual_data)
            errors.extend(visual_errors)
            warnings.extend(visual_warnings)
        
        # Validate sensor data if present
        if multimodal_input.sensor_data is not None:
            sensor_errors, sensor_warnings = self._validate_sensor_data(multimodal_input.sensor_data)
            errors.extend(sensor_errors)
            warnings.extend(sensor_warnings)
        
        # Validate confidence
        if not (0.0 <= multimodal_input.confidence <= 1.0):
            errors.append(f"Confidence must be between 0.0 and 1.0, got {multimodal_input.confidence}")
        
        # Validate timestamp
        if multimodal_input.timestamp is None:
            errors.append("Timestamp is required for multimodal input")
        
        # Check at least one modality is present
        if (multimodal_input.visual_data is None and 
            multimodal_input.sensor_data is None and 
            multimodal_input.voice_input_id is None):
            errors.append("At least one modality (visual, sensor, or voice) must be present")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_visual_data(self, visual_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate visual data component of multimodal input.
        
        :param visual_data: Visual data to validate
        :return: Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check for required visual data fields
        if not isinstance(visual_data, dict):
            errors.append("Visual data must be a dictionary")
            return errors, warnings
        
        # Validate objects in visual data
        objects = visual_data.get("objects", [])
        if not isinstance(objects, list):
            errors.append("Visual data objects must be a list")
        elif len(objects) < self.min_visual_objects:
            warnings.append(f"Fewer than {self.min_visual_objects} objects detected, may impact performance")
        elif len(objects) > self.max_visual_objects:
            errors.append(f"More than {self.max_visual_objects} objects detected, exceeds limit")
        
        # Validate each object
        for i, obj in enumerate(objects):
            if not isinstance(obj, dict):
                errors.append(f"Object {i} in visual data is not a dictionary")
                continue
            
            # Check required object properties
            if "class" not in obj:
                errors.append(f"Object {i} is missing required 'class' property")
            
            if "bbox" not in obj:
                errors.append(f"Object {i} is missing required 'bbox' property")
            else:
                bbox = obj["bbox"]
                if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                    errors.append(f"Object {i} has invalid bbox format (should be [x,y,w,h])")
        
        # Validate image data if present
        image_data = visual_data.get("image")
        if image_data:
            if not isinstance(image_data, dict):
                errors.append("Image data must be a dictionary")
            else:
                required_image_fields = ["width", "height", "data"]
                for field in required_image_fields:
                    if field not in image_data:
                        errors.append(f"Image data is missing required field: {field}")
        
        # Validate depth data if present
        depth_data = visual_data.get("depth")
        if depth_data:
            if not isinstance(depth_data, dict):
                errors.append("Depth data must be a dictionary")
            else:
                if "depth_map" not in depth_data:
                    errors.append("Depth data is missing required 'depth_map' property")
        
        # Validate pose data if present
        pose_data = visual_data.get("pose")
        if pose_data:
            pose_errors, pose_warnings = self._validate_pose_data(pose_data)
            errors.extend(pose_errors)
            warnings.extend(pose_warnings)
        
        return errors, warnings
    
    def _validate_sensor_data(self, sensor_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate sensor data component of multimodal input.
        
        :param sensor_data: Sensor data to validate
        :return: Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(sensor_data, dict):
            errors.append("Sensor data must be a dictionary")
            return errors, warnings
        
        # Validate timestamp
        if "timestamp" not in sensor_data:
            errors.append("Sensor data is missing required 'timestamp' field")
        
        # Validate specific sensor types
        if "lidar" in sensor_data:
            lidar_errors, lidar_warnings = self._validate_lidar_data(sensor_data["lidar"])
            errors.extend(lidar_errors)
            warnings.extend(lidar_warnings)
        
        if "imu" in sensor_data:
            imu_errors, imu_warnings = self._validate_imu_data(sensor_data["imu"])
            errors.extend(imu_errors)
            warnings.extend(imu_warnings)
        
        if "camera" in sensor_data:
            camera_errors, camera_warnings = self._validate_camera_data(sensor_data["camera"])
            errors.extend(camera_errors)
            warnings.extend(camera_warnings)
        
        return errors, warnings
    
    def _validate_lidar_data(self, lidar_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate LIDAR sensor data.
        
        :param lidar_data: LIDAR data to validate
        :return: Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(lidar_data, dict):
            errors.append("LIDAR data must be a dictionary")
            return errors, warnings
        
        required_fields = ["ranges", "min_range", "max_range"]
        for field in required_fields:
            if field not in lidar_data:
                errors.append(f"LIDAR data is missing required field: {field}")
        
        if "ranges" in lidar_data:
            ranges = lidar_data["ranges"]
            if not isinstance(ranges, list):
                errors.append("LIDAR ranges must be a list")
            else:
                for i, range_val in enumerate(ranges):
                    if not isinstance(range_val, (int, float)):
                        errors.append(f"LIDAR range {i} is not a number")
        
        return errors, warnings
    
    def _validate_imu_data(self, imu_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate IMU sensor data.
        
        :param imu_data: IMU data to validate
        :return: Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(imu_data, dict):
            errors.append("IMU data must be a dictionary")
            return errors, warnings
        
        required_fields = ["linear_acceleration", "angular_velocity", "orientation"]
        for field in required_fields:
            if field not in imu_data:
                errors.append(f"IMU data is missing required field: {field}")
        
        # Check vector fields have correct structure
        for field in ["linear_acceleration", "angular_velocity"]:
            if field in imu_data:
                vec = imu_data[field]
                if not isinstance(vec, (list, tuple)) or len(vec) != 3:
                    errors.append(f"{field} must be a 3-element vector [x,y,z]")
        
        for field in ["orientation"]:
            if field in imu_data:
                quat = imu_data[field]
                if not isinstance(quat, (list, tuple)) or len(quat) != 4:
                    errors.append(f"{field} must be a 4-element quaternion [x,y,z,w]")
        
        return errors, warnings
    
    def _validate_camera_data(self, camera_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate camera sensor data.
        
        :param camera_data: Camera data to validate
        :return: Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(camera_data, dict):
            errors.append("Camera data must be a dictionary")
            return errors, warnings
        
        required_fields = ["image_data", "width", "height", "timestamp"]
        for field in required_fields:
            if field not in camera_data:
                errors.append(f"Camera data is missing required field: {field}")
        
        # Check image data format
        img_data = camera_data.get("image_data")
        if img_data:
            if not isinstance(img_data, (str, bytes)):
                warnings.append("Camera image_data should be string or bytes")
        
        # Validate image dimensions
        width = camera_data.get("width")
        height = camera_data.get("height")
        if width and height:
            if not isinstance(width, int) or width <= 0:
                errors.append("Camera width must be a positive integer")
            if not isinstance(height, int) or height <= 0:
                errors.append("Camera height must be a positive integer")
        
        return errors, warnings
    
    def _validate_pose_data(self, pose_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate pose data.
        
        :param pose_data: Pose data to validate
        :return: Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(pose_data, dict):
            errors.append("Pose data must be a dictionary")
            return errors, warnings
        
        # Check position
        position = pose_data.get("position")
        if position is None:
            errors.append("Pose data is missing required 'position' field")
        else:
            pos_errors, pos_warnings = self._validate_position(position)
            errors.extend(pos_errors)
            warnings.extend(pos_warnings)
        
        # Check orientation
        orientation = pose_data.get("orientation")
        if orientation is None:
            errors.append("Pose data is missing required 'orientation' field")
        else:
            quat_errors, quat_warnings = self._validate_quaternion(orientation)
            errors.extend(quat_errors)
            warnings.extend(quat_warnings)
        
        return errors, warnings
    
    def _validate_position(self, position: Any) -> Tuple[List[str], List[str]]:
        """
        Validate position data.
        
        :param position: Position data to validate
        :return: Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(position, (list, tuple, dict)):
            errors.append("Position must be a list, tuple, or dictionary")
            return errors, warnings
        
        if isinstance(position, dict):
            for field in self.required_spatial_fields:
                if field not in position:
                    errors.append(f"Position dictionary is missing required field: {field}")
        elif isinstance(position, (list, tuple)):
            if len(position) < 3:
                errors.append(f"Position vector must have at least 3 elements (x,y,z), got {len(position)}")
        
        return errors, warnings
    
    def _validate_quaternion(self, quaternion: Any) -> Tuple[List[str], List[str]]:
        """
        Validate quaternion data.
        
        :param quaternion: Quaternion data to validate
        :return: Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(quaternion, (list, tuple, dict)):
            errors.append("Quaternion must be a list, tuple, or dictionary")
            return errors, warnings
        
        if isinstance(quaternion, dict):
            required_fields = ["x", "y", "z", "w"]
            for field in required_fields:
                if field not in quaternion:
                    errors.append(f"Quaternion dictionary is missing required field: {field}")
        elif isinstance(quaternion, (list, tuple)):
            if len(quaternion) != 4:
                errors.append(f"Quaternion vector must have exactly 4 elements (x,y,z,w), got {len(quaternion)}")
        
        return errors, warnings
    
    def validate_system_state(self, system_state: VLASystemState) -> ValidationResult:
        """
        Validate the VLA system state.
        
        :param system_state: The system state to validate
        :return: Validation result
        """
        errors = []
        warnings = []
        
        # Validate ID
        if not system_state.id or len(system_state.id.strip()) == 0:
            errors.append("System state ID is required")
        
        # Validate system status
        valid_statuses = ["idle", "listening", "processing", "executing", "error"]
        if system_state.system_status not in valid_statuses:
            errors.append(f"Invalid system status: {system_state.system_status}. Must be one of {valid_statuses}")
        
        # Validate robot pose if present
        if system_state.robot_pose is not None:
            pose_errors, pose_warnings = self._validate_pose_data({
                "position": {
                    "x": system_state.robot_pose.x,
                    "y": system_state.robot_pose.y,
                    "z": system_state.robot_pose.z
                },
                "orientation": system_state.robot_pose.rotation
            })
            errors.extend(pose_errors)
            warnings.extend(pose_warnings)
        
        # Validate timestamps
        if system_state.last_update is None:
            errors.append("System state must have a last_update timestamp")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_multimodal_fusion_result(
        self,
        fusion_result: Dict[str, Any],
        input_modalities: List[str]
    ) -> ValidationResult:
        """
        Validate the result of multimodal fusion.
        
        :param fusion_result: The fusion result to validate
        :param input_modalities: List of input modalities used in fusion
        :return: Validation result
        """
        errors = []
        warnings = []
        
        # Check if fusion result has required fields
        required_fields = ["fused_output", "confidence", "method"]
        for field in required_fields:
            if field not in fusion_result:
                errors.append(f"Fusion result is missing required field: {field}")
        
        # Validate confidence
        if "confidence" in fusion_result:
            confidence = fusion_result["confidence"]
            if not (0.0 <= confidence <= 1.0):
                errors.append(f"Fusion confidence must be between 0.0 and 1.0, got {confidence}")
        
        # Check that fusion result contains appropriate output based on input modalities
        if "fused_output" in fusion_result:
            fused_output = fusion_result["fused_output"]
            
            # If the input was for action generation, check for action steps
            if "action" in input_modalities and isinstance(fused_output, list):
                for i, output in enumerate(fused_output):
                    if not isinstance(output, dict) or "action_type" not in output:
                        warnings.append(f"Fusion output {i} might not be a valid action")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_confidence_consistency(
        self,
        multimodal_input: MultimodalInput,
        fusion_result: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate that confidence values are consistent between input and fusion result.
        
        :param multimodal_input: Original multimodal input
        :param fusion_result: Result of fusion process
        :return: Validation result
        """
        errors = []
        warnings = []
        
        # Get input confidence
        input_confidence = multimodal_input.confidence
        
        # Get result confidence
        result_confidence = fusion_result.get("confidence", 0.5)  # Default to 0.5 if not specified
        
        # Check that result confidence is not higher than input confidence
        # (fusion shouldn't artificially inflate confidence)
        if result_confidence > input_confidence + 0.1:  # Allow small margin
            warnings.append(
                f"Result confidence ({result_confidence}) is significantly higher than "
                f"input confidence ({input_confidence}). Fusion should not increase confidence beyond input."
            )
        
        # Check if confidence is below acceptable threshold
        if result_confidence < self.confidence_threshold:
            warnings.append(
                f"Result confidence ({result_confidence}) is below "
                f"minimum threshold ({self.confidence_threshold})"
            )
        
        # Check for confidence propagation consistency
        visual_data = multimodal_input.visual_data
        if visual_data and "confidence" in visual_data:
            if result_confidence > visual_data["confidence"] and "vision" in str(result_confidence):
                warnings.append("Result confidence is higher than visual input confidence")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class AdvancedMultimodalValidationService(MultimodalValidationService):
    """
    Advanced validation service with additional checks for complex scenarios.
    """
    
    def __init__(self):
        super().__init__()
        self.enable_temporal_consistency = True
        self.enable_cross_modal_verification = True
        self.enable_behavioral_validation = True
    
    def validate_temporal_consistency(
        self,
        current_input: MultimodalInput,
        previous_input: Optional[MultimodalInput] = None,
        max_time_diff: float = 1.0
    ) -> ValidationResult:
        """
        Validate temporal consistency between current and previous inputs.
        
        :param current_input: Current multimodal input
        :param previous_input: Previous multimodal input for comparison
        :param max_time_diff: Maximum allowed time difference in seconds
        :return: Validation result
        """
        if not previous_input:
            return ValidationResult(is_valid=True)  # No previous input to compare
        
        errors = []
        warnings = []
        
        # Calculate time difference
        time_diff = abs((current_input.timestamp - previous_input.timestamp).total_seconds())
        
        if time_diff > max_time_diff:
            warnings.append(f"Large time gap between inputs: {time_diff:.2f}s")
        
        # Check for spatial consistency if robot poses are available
        if (hasattr(current_input, 'robot_pose') and 
            hasattr(previous_input, 'robot_pose')):
            # Calculate distance between poses
            pos1 = current_input.robot_pose
            pos2 = previous_input.robot_pose
            distance = ((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2 + (pos1.z - pos2.z)**2)**0.5
            
            # Check if distance is too large for the time elapsed (unrealistic movement)
            max_reasonable_speed = 2.0  # meters per second
            max_distance = max_reasonable_speed * time_diff
            if distance > max_distance:
                warnings.append(
                    f"Robot movement ({distance:.2f}m) too fast for time elapsed ({time_diff:.2f}s)"
                )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_cross_modal_consistency(self, multimodal_input: MultimodalInput) -> ValidationResult:
        """
        Validate consistency between different modalities in the input.
        
        :param multimodal_input: Multimodal input to validate
        :return: Validation result
        """
        errors = []
        warnings = []
        
        # Check for consistency between visual and sensor data
        if multimodal_input.visual_data and multimodal_input.sensor_data:
            # Example: Check if detected objects are consistent with distance sensor readings
            objects = multimodal_input.visual_data.get("objects", [])
            lidar_ranges = multimodal_input.sensor_data.get("lidar", {}).get("ranges", [])
            
            if objects and lidar_ranges:
                # Simple check: if an object is very close, distance sensors should detect something nearby
                for obj in objects:
                    obj_distance = obj.get("distance", float('inf'))
                    
                    # If the object is very close (< 0.5m), distance sensors should reflect this
                    if obj_distance < 0.5:
                        # Find the closest distance reading
                        if lidar_ranges:
                            closest_distance = min(lidar_ranges)
                            if closest_distance > 1.0:  # Sensor says it's far but vision says it's close
                                warnings.append(
                                    f"Vision detects object at {obj_distance}m but sensors indicate closest object at {closest_distance}m"
                                )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_with_environment_context(
        self,
        multimodal_input: MultimodalInput,
        environment_map: Optional[Dict[str, Any]] = None,
        robot_capabilities: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate input with respect to environment context and robot capabilities.
        
        :param multimodal_input: Multimodal input to validate
        :param environment_map: Map of the environment
        :param robot_capabilities: List of robot capabilities
        :return: Validation result
        """
        errors = []
        warnings = []
        
        # Validate with environment map
        if environment_map:
            # Check if detected objects are in expected locations
            visual_objects = multimodal_input.visual_data.get("objects", []) if multimodal_input.visual_data else []
            
            for obj in visual_objects:
                obj_class = obj.get("class")
                obj_position = obj.get("position", {})
                
                # Check if position is within environment bounds
                bounds = environment_map.get("bounds", {})
                if bounds:
                    x, y = obj_position.get("x", 0), obj_position.get("y", 0)
                    if (x < bounds.get("min_x", float("-inf")) or x > bounds.get("max_x", float("inf")) or
                        y < bounds.get("min_y", float("-inf")) or y > bounds.get("max_y", float("inf"))):
                        warnings.append(f"Detected object {obj_class} at position ({x}, {y}) outside environment bounds")
        
        # Validate against robot capabilities
        if robot_capabilities:
            # Check if the tasks suggested by the input are supported by the robot
            if multimodal_input.visual_data:
                objects = multimodal_input.visual_data.get("objects", [])
                for obj in objects:
                    obj_class = obj.get("class")
                    
                    # Check if robot can manipulate this type of object
                    if obj_class in ["fragile_item", "heavy_object"] and "precision_manipulation" not in robot_capabilities:
                        warnings.append(f"Robot may not be able to safely handle {obj_class} without precision manipulation capability")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


# Example usage:
if __name__ == "__main__":
    from datetime import datetime
    import uuid
    
    # Create a validation service
    validator = MultimodalValidationService()
    
    # Create a sample multimodal input to validate
    sample_input = MultimodalInput(
        id=str(uuid.uuid4()),
        visual_data={
            "objects": [
                {
                    "class": "cup",
                    "bbox": [0.1, 0.2, 0.3, 0.4],
                    "confidence": 0.9
                }
            ],
            "image": {
                "width": 640,
                "height": 480,
                "data": "mock_image_data"
            }
        },
        sensor_data={
            "lidar": {
                "ranges": [1.0, 1.1, 0.9, 1.2],
                "min_range": 0.1,
                "max_range": 10.0
            },
            "timestamp": datetime.now()
        },
        confidence=0.85,
        timestamp=datetime.now()
    )
    
    # Validate the multimodal input
    result = validator.validate_multimodal_input(sample_input)
    print(f"Validation result: is_valid={result.is_valid}")
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    
    # Validate a fusion result
    fusion_result = {
        "fused_output": [
            {
                "action_type": "navigation",
                "target_position": [1.0, 2.0, 0.0]
            }
        ],
        "confidence": 0.78,
        "method": "early_fusion"
    }
    
    fusion_validation = validator.validate_multimodal_fusion_result(
        fusion_result, 
        ["vision", "language"]
    )
    print(f"\nFusion validation: is_valid={fusion_validation.is_valid}")
    print(f"Fusion errors: {fusion_validation.errors}")
    
    # Example with advanced validation
    advanced_validator = AdvancedMultimodalValidationService()
    
    # Create a second input for temporal consistency check
    sample_input2 = MultimodalInput(
        id=str(uuid.uuid4()),
        visual_data=sample_input.visual_data,
        sensor_data=sample_input.sensor_data,
        confidence=0.80,
        timestamp=datetime.now()
    )
    
    # Check temporal consistency
    temporal_result = advanced_validator.validate_temporal_consistency(
        sample_input2, sample_input
    )
    print(f"\nTemporal consistency check: warnings={temporal_result.warnings}")
    
    # Check cross-modal consistency
    cross_modal_result = advanced_validator.validate_cross_modal_consistency(sample_input)
    print(f"Cross-modal consistency: warnings={cross_modal_result.warnings}")
    
    # Validate with environment context
    env_map = {
        "bounds": {
            "min_x": -5.0, "max_x": 5.0,
            "min_y": -5.0, "max_y": 5.0
        }
    }
    robot_caps = ["navigation", "manipulation", "perception"]
    
    env_validation = advanced_validator.validate_with_environment_context(
        sample_input, env_map, robot_caps
    )
    print(f"Environment context validation: warnings={env_validation.warnings}")