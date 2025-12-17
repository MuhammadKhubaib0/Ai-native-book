"""
Service for handling object manipulation in the VLA system.
"""
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import numpy as np
import asyncio
from datetime import datetime
import math

from ..models.action_step import ActionStep, ActionType
from ..models.vla_system_state import Pose
from ..simulation.gazebo_integration import GazeboIntegrationService
from ..services.vision_integration import VisionIntegrationService
from ..config import settings


class GraspType(Enum):
    """Enumeration of different grasp types."""
    PINCH_GRASP = "pinch_grasp"
    POWER_GRASP = "power_grasp"
    LATERAL_GRASP = "lateral_grasp"
    SUPPORT_GRASP = "support_grasp"
    SUCTION_GRASP = "suction_grasp"


class ManipulationResult(Enum):
    """Enumeration of manipulation results."""
    SUCCESS = "success"
    GRASP_FAILED = "grasp_failed"
    COLLISION_DETECTED = "collision_detected"
    TARGET_UNREACHABLE = "target_unreachable"
    UNSUPPORTED_OBJECT = "unsupported_object"


class ObjectManipulationService:
    """
    Service for handling object manipulation tasks in the VLA system.
    """
    
    def __init__(self):
        """Initialize the object manipulation service."""
        self.gazebo_service = GazeboIntegrationService()
        self.vision_service = VisionIntegrationService()
        
        # Robot manipulation properties
        self.reach_radius = 1.0  # Max reach of the robot arm in meters
        self.max_object_weight = 5.0  # Maximum weight robot can lift in kg
        self.grasp_force_limit = 50.0  # Maximum grasp force in Newtons
        
        # Manipulator configuration
        self.arm_joints = ["shoulder", "elbow", "wrist"]
        self.end_effector = "gripper"
        
        # Object properties database (in a real implementation, this would connect to a knowledge base)
        self.object_properties = {
            "cup": {
                "shape": "cylindrical",
                "size": {"width": 0.08, "height": 0.1, "depth": 0.08},
                "weight": 0.15,
                "grasp_points": ["top_handle", "bottom_base"],
                "stability": "stable_when_supported"
            },
            "box": {
                "shape": "rectangular",
                "size": {"width": 0.2, "height": 0.15, "depth": 0.15},
                "weight": 0.5,
                "grasp_points": ["center_top", "sides"],
                "stability": "stable"
            },
            "book": {
                "shape": "rectangular_thin",
                "size": {"width": 0.2, "height": 0.03, "depth": 0.15},
                "weight": 0.8,
                "grasp_points": ["spine_edge", "center"],
                "stability": "unstable_if_not_supported"
            },
            "bottle": {
                "shape": "cylindrical_narrow",
                "size": {"width": 0.07, "height": 0.25, "depth": 0.07},
                "weight": 0.3,
                "grasp_points": ["neck", "bottom"],
                "stability": "stable_when_upright"
            }
        }
        
        # Grasp planning parameters
        self.approach_distance = 0.05  # Distance to approach target before grasp
        self.lift_distance = 0.1       # Distance to lift object after grasp
        self.clearance_height = 0.2    # Height to clear obstacles during transport
    
    async def grasp_object(self, object_id: str, robot_pose: Pose) -> Dict[str, Any]:
        """
        Execute a grasping action for the specified object.
        
        :param object_id: ID of the object to grasp
        :param robot_pose: Current pose of the robot
        :return: Grasp result with status and details
        """
        try:
            # Find the object in the environment
            object_info = await self._locate_object(object_id)
            if not object_info:
                return {
                    "result": ManipulationResult.TARGET_UNREACHABLE,
                    "message": f"Object '{object_id}' not found",
                    "timestamp": datetime.now()
                }
            
            # Check if object is reachable
            if not self._is_reachable(object_info["pose"], robot_pose):
                return {
                    "result": ManipulationResult.TARGET_UNREACHABLE,
                    "message": f"Object '{object_id}' is not within reach",
                    "timestamp": datetime.now()
                }
            
            # Determine appropriate grasp type based on object properties
            grasp_type = self._select_grasp_type(object_info["class"], object_info.get("properties", {}))
            
            # Plan the grasp trajectory
            grasp_trajectory = await self._plan_grasp_trajectory(
                object_info["pose"], 
                grasp_type, 
                robot_pose
            )
            
            if not grasp_trajectory:
                return {
                    "result": ManipulationResult.GRASP_FAILED,
                    "message": f"Could not plan grasp trajectory for '{object_id}'",
                    "timestamp": datetime.now()
                }
            
            # Execute the grasp
            grasp_success = await self._execute_grasp_trajectory(
                grasp_trajectory, 
                grasp_type, 
                object_info["properties"]
            )
            
            if grasp_success:
                # Verify grasp success
                grasp_verified = await self._verify_grasp_success(object_info["id"])
                
                if grasp_verified:
                    return {
                        "result": ManipulationResult.SUCCESS,
                        "message": f"Successfully grasped '{object_id}'",
                        "object_id": object_id,
                        "grasp_type": grasp_type.value,
                        "timestamp": datetime.now()
                    }
                else:
                    return {
                        "result": ManipulationResult.GRASP_FAILED,
                        "message": f"Grasp failed to secure '{object_id}'",
                        "timestamp": datetime.now()
                    }
            else:
                return {
                    "result": ManipulationResult.GRASP_FAILED,
                    "message": f"Grasp execution failed for '{object_id}'",
                    "timestamp": datetime.now()
                }
                
        except Exception as e:
            return {
                "result": ManipulationResult.GRASP_FAILED,
                "message": f"Error during grasp operation: {str(e)}",
                "timestamp": datetime.now()
            }
    
    async def place_object(self, object_id: str, target_pose: Pose, robot_pose: Pose) -> Dict[str, Any]:
        """
        Execute a placing action for the specified object.
        
        :param object_id: ID of the object to place
        :param target_pose: Target pose where to place the object
        :param robot_pose: Current pose of the robot
        :return: Place result with status and details
        """
        try:
            # Check if object is currently held
            if not await self._is_object_held(object_id):
                return {
                    "result": ManipulationResult.GRASP_FAILED,
                    "message": f"Cannot place '{object_id}' - it's not currently held",
                    "timestamp": datetime.now()
                }
            
            # Plan the placement trajectory
            place_trajectory = await self._plan_place_trajectory(target_pose, robot_pose)
            
            if not place_trajectory:
                return {
                    "result": ManipulationResult.TARGET_UNREACHABLE,
                    "message": f"Could not plan place trajectory to target pose",
                    "timestamp": datetime.now()
                }
            
            # Execute the placement
            place_success = await self._execute_place_trajectory(place_trajectory)
            
            if place_success:
                # Release the object
                release_success = await self._release_object(object_id)
                
                if release_success:
                    return {
                        "result": ManipulationResult.SUCCESS,
                        "message": f"Successfully placed '{object_id}'",
                        "object_id": object_id,
                        "target_pose": target_pose,
                        "timestamp": datetime.now()
                    }
                else:
                    return {
                        "result": ManipulationResult.GRASP_FAILED,
                        "message": f"Failed to release '{object_id}' after placement",
                        "timestamp": datetime.now()
                    }
            else:
                return {
                    "result": ManipulationResult.GRASP_FAILED,
                    "message": f"Place execution failed for '{object_id}'",
                    "timestamp": datetime.now()
                }
                
        except Exception as e:
            return {
                "result": ManipulationResult.GRASP_FAILED,
                "message": f"Error during place operation: {str(e)}",
                "timestamp": datetime.now()
            }
    
    async def move_object(self, object_id: str, target_pose: Pose, robot_pose: Pose) -> Dict[str, Any]:
        """
        Execute a move action for the specified object.
        
        :param object_id: ID of the object to move
        :param target_pose: Target pose where to move the object
        :param robot_pose: Current pose of the robot
        :return: Move result with status and details
        """
        try:
            # First, grasp the object if it's not already held
            object_held = await self._is_object_held(object_id)
            
            if not object_held:
                grasp_result = await self.grasp_object(object_id, robot_pose)
                if grasp_result["result"] != ManipulationResult.SUCCESS:
                    return grasp_result
            else:
                # Object is already held, we can proceed to move
                pass
            
            # Then place the object at the target location
            place_result = await self.place_object(object_id, target_pose, robot_pose)
            return place_result
            
        except Exception as e:
            return {
                "result": ManipulationResult.GRASP_FAILED,
                "message": f"Error during move operation: {str(e)}",
                "timestamp": datetime.now()
            }
    
    async def _locate_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        Locate an object in the environment.
        
        :param object_id: ID of the object to locate
        :return: Object information or None if not found
        """
        # In a real implementation, this would use perception and vision services
        # For this example, we'll simulate object detection
        try:
            # Get current objects from the simulation
            current_objects = await self.gazebo_service.get_tracked_objects()
            
            # Find the requested object
            for obj in current_objects:
                if obj["id"] == object_id or obj["id"] == object_id.lower():
                    # Get object class and properties
                    obj_class = obj["class"]
                    obj_properties = self.object_properties.get(obj_class, {})
                    
                    return {
                        "id": obj["id"],
                        "class": obj_class,
                        "pose": Pose(
                            x=obj["position"]["x"],
                            y=obj["position"]["y"],
                            z=obj["position"]["z"],
                            rotation=obj["orientation"]
                        ),
                        "properties": obj_properties,
                        "bbox": obj.get("bbox", {})
                    }
            
            # Try with class name match if ID doesn't match
            for obj in current_objects:
                if obj["class"] == object_id.lower():
                    obj_class = obj["class"]
                    obj_properties = self.object_properties.get(obj_class, {})
                    
                    return {
                        "id": obj["id"],
                        "class": obj["class"],
                        "pose": Pose(
                            x=obj["position"]["x"],
                            y=obj["position"]["y"],
                            z=obj["position"]["z"],
                            rotation=obj["orientation"]
                        ),
                        "properties": obj_properties,
                        "bbox": obj.get("bbox", {})
                    }
            
            return None
        except Exception as e:
            print(f"Error locating object {object_id}: {str(e)}")
            return None
    
    def _is_reachable(self, object_pose: Pose, robot_pose: Pose) -> bool:
        """
        Check if an object is reachable by the robot.
        
        :param object_pose: Pose of the object
        :param robot_pose: Pose of the robot
        :return: True if reachable, False otherwise
        """
        # Calculate distance between robot and object
        dx = object_pose.x - robot_pose.x
        dy = object_pose.y - robot_pose.y
        dz = object_pose.z - robot_pose.z
        
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        return distance <= self.reach_radius
    
    def _select_grasp_type(self, object_class: str, object_properties: Dict[str, Any]) -> GraspType:
        """
        Select the appropriate grasp type based on object properties.
        
        :param object_class: Class of the object
        :param object_properties: Properties of the object
        :return: Selected grasp type
        """
        # Select appropriate grasp based on object properties
        if object_class == "cup":
            # Cups with handles: lateral grasp on handle
            if "top_handle" in object_properties.get("grasp_points", []):
                return GraspType.LATERAL_GRASP
            else:
                # Pinch grasp at the rim
                return GraspType.PINCH_GRASP
        elif object_class == "box":
            # Power grasp on sides or edges
            return GraspType.POWER_GRASP
        elif object_class == "book":
            # Lateral grasp on spine
            return GraspType.LATERAL_GRASP
        elif object_class == "bottle":
            # Grasp the neck for bottles
            return GraspType.LATERAL_GRASP
        else:
            # Default to power grasp for unknown objects
            return GraspType.POWER_GRASP
    
    async def _plan_grasp_trajectory(self, object_pose: Pose, grasp_type: GraspType, robot_pose: Pose) -> Optional[List[Pose]]:
        """
        Plan a trajectory for grasping an object.
        
        :param object_pose: Pose of the object to grasp
        :param grasp_type: Type of grasp to use
        :param robot_pose: Current pose of the robot
        :return: Planned trajectory as a list of poses, or None if planning failed
        """
        try:
            # Calculate grasp pose based on object pose and grasp type
            grasp_pose = self._calculate_grasp_pose(object_pose, grasp_type)
            if not grasp_pose:
                return None
            
            # Calculate approach pose (slightly before grasp pose)
            approach_pose = self._calculate_approach_pose(grasp_pose)
            
            # Calculate lift pose (after grasp, lifted slightly)
            lift_pose = self._calculate_lift_pose(grasp_pose)
            
            # Return the trajectory: approach -> grasp -> lift
            trajectory = [approach_pose, grasp_pose, lift_pose]
            return trajectory
            
        except Exception as e:
            print(f"Error planning grasp trajectory: {str(e)}")
            return None
    
    def _calculate_grasp_pose(self, object_pose: Pose, grasp_type: GraspType) -> Optional[Pose]:
        """
        Calculate the appropriate grasp pose for the object.
        
        :param object_pose: Pose of the object to grasp
        :param grasp_type: Type of grasp to use
        :return: Grasp pose or None if not calculable
        """
        # Adjust the grasp pose based on the object pose and grasp type
        # This would involve complex inverse kinematics in a real implementation
        # For this example, we'll return a relative pose
        grasp_offset = {
            GraspType.PINCH_GRASP: (0.0, 0.0, 0.05),  # Slightly above object
            GraspType.POWER_GRASP: (0.0, 0.0, 0.0),   # At object level
            GraspType.LATERAL_GRASP: (0.05, 0.0, 0.0), # Approach from side
            GraspType.SUPPORT_GRASP: (0.0, 0.0, 0.0), # Same level as object
            GraspType.SUCTION_GRASP: (0.0, 0.0, 0.0), # Surface contact
        }
        
        offset = grasp_offset.get(grasp_type, (0.0, 0.0, 0.0))
        
        grasp_pose = Pose(
            x=object_pose.x + offset[0],
            y=object_pose.y + offset[1],
            z=object_pose.z + offset[2],
            rotation=object_pose.rotation  # Keep same orientation initially
        )
        
        # Adjust orientation based on grasp type
        rotation_adjustment = {
            GraspType.PINCH_GRASP: {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0},
            GraspType.POWER_GRASP: {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0},
            GraspType.LATERAL_GRASP: {"qx": 0.707, "qy": 0.0, "qz": 0.0, "qw": 0.707},  # 90-degree rotation
            GraspType.SUPPORT_GRASP: {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0},
            GraspType.SUCTION_GRASP: {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
        }
        
        grasp_pose.rotation = rotation_adjustment.get(grasp_type, grasp_pose.rotation)
        
        return grasp_pose
    
    def _calculate_approach_pose(self, grasp_pose: Pose) -> Pose:
        """
        Calculate the approach pose before the grasp.
        
        :param grasp_pose: The final grasp pose
        :return: Approach pose
        """
        # Move back from the grasp pose by approach_distance in the direction of the gripper
        # For simplicity, we'll assume the gripper faces along the X-axis
        
        approach_direction = 0.05  # 5cm back from grasp
        approach_pose = Pose(
            x=grasp_pose.x - approach_direction,
            y=grasp_pose.y,
            z=grasp_pose.z,
            rotation=grasp_pose.rotation
        )
        
        return approach_pose
    
    def _calculate_lift_pose(self, grasp_pose: Pose) -> Pose:
        """
        Calculate the lift pose after grasping.
        
        :param grasp_pose: The grasp pose
        :return: Lift pose
        """
        # Lift the object slightly after grasping
        lift_distance = 0.1  # 10cm lift
        lift_pose = Pose(
            x=grasp_pose.x,
            y=grasp_pose.y,
            z=grasp_pose.z + lift_distance,
            rotation=grasp_pose.rotation
        )
        
        return lift_pose
    
    async def _execute_grasp_trajectory(self, trajectory: List[Pose], grasp_type: GraspType, object_properties: Dict[str, Any]) -> bool:
        """
        Execute the grasp trajectory and perform the grasp.
        
        :param trajectory: List of poses to follow for the grasp
        :param grasp_type: Type of grasp to perform
        :param object_properties: Properties of the object to grasp
        :return: True if successful, False otherwise
        """
        try:
            # Verify object weight is within limits
            obj_weight = object_properties.get("weight", 0.0)
            if obj_weight > self.max_object_weight:
                print(f"Object weight {obj_weight}kg exceeds robot's max capacity {self.max_object_weight}kg")
                return False
            
            # Execute each pose in the trajectory
            for i, pose in enumerate(trajectory):
                await self._move_to_pose(pose)
                
                # If this is the final (grasp) pose, perform the grasp
                if i == 1:  # Grasp pose is the second in our trajectory
                    await self._perform_grasp(grasp_type, object_properties)
            
            return True
            
        except Exception as e:
            print(f"Error executing grasp trajectory: {str(e)}")
            return False
    
    async def _move_to_pose(self, pose: Pose):
        """
        Move the robot's end effector to the specified pose.
        
        :param pose: Target pose to move to
        """
        # In a real implementation, this would calculate inverse kinematics
        # and control the robot joints to reach the pose
        # For this simulation, we'll just log the movement
        print(f"Moving to pose: ({pose.x:.2f}, {pose.y:.2f}, {pose.z:.2f})")
        
        # Simulate movement time
        await asyncio.sleep(0.5)
    
    async def _perform_grasp(self, grasp_type: GraspType, object_properties: Dict[str, Any]):
        """
        Perform the actual grasp motion.
        
        :param grasp_type: Type of grasp to perform
        :param object_properties: Properties of the object being grasped
        """
        # In a real implementation, this would close the gripper with appropriate force
        # based on the grasp type and object properties
        # For this simulation, we'll just log the action
        print(f"Performing {grasp_type.value} grasp")
        
        # Simulate grasp action
        await asyncio.sleep(0.3)
    
    async def _verify_grasp_success(self, object_id: str) -> bool:
        """
        Verify that the grasp was successful.
        
        :param object_id: ID of the object that was grasped
        :return: True if grasp was successful, False otherwise
        """
        # In a real implementation, this would use sensors to verify the grasp
        # For this simulation, we'll just return True (assume success)
        print(f"Verifying grasp success for {object_id}")
        return True
    
    async def _is_object_held(self, object_id: str) -> bool:
        """
        Check if the specified object is currently held by the robot.
        
        :param object_id: ID of the object to check
        :return: True if object is held, False otherwise
        """
        # In a real implementation, this would check robot's grasp state
        # For this simulation, we'll just return False to simulate normal operation
        return False
    
    async def _execute_place_trajectory(self, trajectory: List[Pose]) -> bool:
        """
        Execute a placement trajectory.
        
        :param trajectory: List of poses to follow for placement
        :return: True if successful, False otherwise
        """
        try:
            for pose in trajectory:
                await self._move_to_pose(pose)
            
            return True
        except Exception as e:
            print(f"Error executing place trajectory: {str(e)}")
            return False
    
    async def _release_object(self, object_id: str) -> bool:
        """
        Release the specified object.
        
        :param object_id: ID of the object to release
        :return: True if successful, False otherwise
        """
        # In a real implementation, this would open the gripper
        # For this simulation, we'll just log the action
        print(f"Releasing object {object_id}")
        await asyncio.sleep(0.2)
        
        # Update internal state to reflect that the object is no longer held
        # (In a real implementation, this would communicate with the robot controller)
        
        return True
    
    async def _plan_place_trajectory(self, target_pose: Pose, robot_pose: Pose) -> Optional[List[Pose]]:
        """
        Plan a trajectory for placing an object.
        
        :param target_pose: Target pose where to place the object
        :param robot_pose: Current pose of the robot
        :return: Planned trajectory as a list of poses, or None if planning failed
        """
        try:
            # Calculate a safe trajectory to the target pose
            # This might involve raising the object to clearance height, 
            # moving to the target location, then lowering
            
            # Current position is assumed to be holding the object
            # So we start from a slightly elevated position
            current_elevated = Pose(
                x=robot_pose.x,
                y=robot_pose.y,
                z=min(robot_pose.z + 0.3, self.clearance_height),  # Move to clearance height
                rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
            )
            
            # Intermediate position at target height but away from final spot
            intermediate = Pose(
                x=target_pose.x,
                y=target_pose.y,
                z=min(target_pose.z + 0.3, self.clearance_height),  # Clearance height at target
                rotation=target_pose.rotation
            )
            
            # Final position just above target
            approach_position = Pose(
                x=target_pose.x,
                y=target_pose.y,
                z=target_pose.z + 0.05,  # Slightly above target
                rotation=target_pose.rotation
            )
            
            # Final target position
            target_position = target_pose
            
            trajectory = [current_elevated, intermediate, approach_position, target_position]
            return trajectory
            
        except Exception as e:
            print(f"Error planning place trajectory: {str(e)}")
            return None
    
    async def get_object_properties(self, object_class: str) -> Optional[Dict[str, Any]]:
        """
        Get known properties of an object class.
        
        :param object_class: Class of the object
        :return: Object properties or None if unknown
        """
        return self.object_properties.get(object_class, None)
    
    async def estimate_manipulability(self, object_id: str, robot_pose: Pose) -> Dict[str, Any]:
        """
        Estimate how easily the robot can manipulate the specified object.
        
        :param object_id: ID of the object to evaluate
        :param robot_pose: Current pose of the robot
        :return: Dictionary with manipulability assessment
        """
        object_info = await self._locate_object(object_id)
        if not object_info:
            return {
                "object_id": object_id,
                "manipulable": False,
                "reason": f"Object '{object_id}' not found",
                "estimated_success": 0.0,
                "recommended_grasp": None,
                "timestamp": datetime.now()
            }
        
        # Check if object is reachable
        if not self._is_reachable(object_info["pose"], robot_pose):
            return {
                "object_id": object_id,
                "manipulable": False,
                "reason": "Object not within reach",
                "estimated_success": 0.0,
                "recommended_grasp": None,
                "timestamp": datetime.now()
            }
        
        # Check if object is too heavy
        obj_weight = object_info["properties"].get("weight", 0.0)
        if obj_weight > self.max_object_weight:
            return {
                "object_id": object_id,
                "manipulable": False,
                "reason": f"Object too heavy: {obj_weight}kg (max: {self.max_object_weight}kg)",
                "estimated_success": 0.0,
                "recommended_grasp": None,
                "timestamp": datetime.now()
            }
        
        # Calculate estimated success based on object properties
        grasp_type = self._select_grasp_type(object_info["class"], object_info["properties"])
        
        # Estimate success based on grasp type and object properties
        # This is a simplified model - real systems would use more sophisticated analysis
        success_factors = {
            GraspType.PINCH_GRASP: 0.85,
            GraspType.POWER_GRASP: 0.95,
            GraspType.LATERAL_GRASP: 0.80,
            GraspType.SUPPORT_GRASP: 0.75,
            GraspType.SUCTION_GRASP: 0.70
        }
        
        estimated_success = success_factors.get(grasp_type, 0.6)
        
        # Adjust for object-specific factors
        if object_info["class"] == "book":
            # Books are harder to grasp stably
            estimated_success -= 0.1
        elif object_info["class"] == "bottle":
            # Bottles require careful grasp to avoid dropping
            estimated_success -= 0.05
        
        return {
            "object_id": object_id,
            "manipulable": True,
            "reason": "Object is reachable and within weight limits",
            "estimated_success": min(1.0, max(0.0, estimated_success)),
            "recommended_grasp": grasp_type.value,
            "object_properties": object_info["properties"],
            "timestamp": datetime.now()
        }


class AdvancedObjectManipulationService(ObjectManipulationService):
    """
    Advanced object manipulation service with additional capabilities.
    """
    
    def __init__(self):
        super().__init__()
        self.multi_object_manipulation_enabled = True
        self.dual_arm_manipulation_enabled = False  # Initially disabled
        self.compliant_control_enabled = True
        self.force_control_enabled = True
        
        # Storage for currently grasped objects
        self.grasped_objects = {}
    
    async def grasp_multiple_objects(self, object_list: List[Dict[str, Any]], robot_pose: Pose) -> Dict[str, Any]:
        """
        Grasp multiple objects in sequence.
        
        :param object_list: List of objects to grasp with their properties
        :param robot_pose: Current pose of the robot
        :return: Result of the multi-object grasp operation
        """
        if not self.multi_object_manipulation_enabled:
            return {
                "result": "not_supported",
                "message": "Multi-object manipulation is not enabled",
                "completed_operations": [],
                "failed_operations": [],
                "timestamp": datetime.now()
            }
        
        completed_operations = []
        failed_operations = []
        
        for obj in object_list:
            obj_id = obj.get("id")
            obj_class = obj.get("class", "")
            
            if not obj_id:
                failed_operations.append({
                    "object": obj,
                    "reason": "Missing object ID"
                })
                continue
            
            # Attempt to grasp the current object
            grasp_result = await self.grasp_object(obj_id, robot_pose)
            
            if grasp_result["result"] == ManipulationResult.SUCCESS:
                completed_operations.append({
                    "object_id": obj_id,
                    "result": grasp_result
                })
                
                # Update internal state to remember this object is grasped
                self.grasped_objects[obj_id] = {
                    "object_class": obj_class,
                    "grasp_time": datetime.now(),
                    "position_relative_to_robot": self._calculate_relative_position(obj_id, robot_pose)
                }
            else:
                failed_operations.append({
                    "object_id": obj_id,
                    "result": grasp_result
                })
        
        return {
            "result": "partial_success" if failed_operations and completed_operations else
                      "complete_success" if not failed_operations else
                      "complete_failure",
            "message": f"Multi-object grasp operation completed: {len(completed_operations)} succeeded, {len(failed_operations)} failed",
            "completed_operations": completed_operations,
            "failed_operations": failed_operations,
            "timestamp": datetime.now()
        }
    
    def _calculate_relative_position(self, object_id: str, robot_pose: Pose) -> Optional[Dict[str, float]]:
        """
        Calculate the position of a grasped object relative to the robot.
        
        :param object_id: ID of the object
        :param robot_pose: Current robot pose
        :return: Relative position as a dictionary, or None if object not found
        """
        # In a real implementation, this would track the exact relationship
        # between the robot and each grasped object
        # For this simulation, we'll return a default offset
        return {
            "x_offset": 0.1,  # 10cm in front of robot
            "y_offset": 0.0,  # Centered on robot
            "z_offset": 0.5   # 50cm above robot base
        }
    
    async def coordinated_manipulation(self, primary_object: str, secondary_objects: List[str], 
                                       robot_pose: Pose, operation_type: str) -> Dict[str, Any]:
        """
        Perform coordinated manipulation involving multiple objects.
        
        :param primary_object: Main object being manipulated
        :param secondary_objects: Supporting objects
        :param robot_pose: Current robot pose
        :param operation_type: Type of coordinated operation
        :return: Result of the coordinated manipulation
        """
        if not self.multi_object_manipulation_enabled:
            return {
                "result": "not_supported",
                "message": "Coordinated manipulation is not enabled",
                "timestamp": datetime.now()
            }
        
        results = {}
        
        # Grasp the primary object
        primary_result = await self.grasp_object(primary_object, robot_pose)
        results["primary"] = primary_result
        
        if primary_result["result"] != ManipulationResult.SUCCESS:
            return {
                "result": "primary_failure",
                "message": f"Primary object grasp failed: {primary_result['message']}",
                "results": results,
                "timestamp": datetime.now()
            }
        
        # If operation requires secondary objects, manipulate them too
        if secondary_objects:
            if operation_type in ["assembly", "construction", "stacking"]:
                for sec_obj in secondary_objects:
                    # Place or position secondary objects
                    sec_result = await self._position_secondary_object(
                        primary_object, sec_obj, robot_pose, operation_type
                    )
                    results[f"secondary_{sec_obj}"] = sec_result
        
        return {
            "result": "success",
            "message": "Coordinated manipulation completed",
            "results": results,
            "operation_type": operation_type,
            "timestamp": datetime.now()
        }
    
    async def _position_secondary_object(self, primary_object: str, secondary_object: str, 
                                         robot_pose: Pose, operation_type: str) -> Dict[str, Any]:
        """
        Position a secondary object relative to the primary object.
        
        :param primary_object: Primary object
        :param secondary_object: Secondary object to position
        :param robot_pose: Current robot pose
        :param operation_type: Type of operation to perform
        :return: Result of positioning operation
        """
        # In a real implementation, this would perform complex coordinated manipulation
        # For this simulation, we'll just do a regular grasp-and-place operation
        return await self.move_object(
            secondary_object, 
            # Calculate target pose based on primary object position and operation
            target_pose=Pose(
                x=robot_pose.x + 0.5,  # Place next to robot for now
                y=robot_pose.y + 0.5,
                z=robot_pose.z + 0.2,
                rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
            ),
            robot_pose=robot_pose
        )
    
    async def estimate_force_requirements(self, action: ActionStep, object_id: str) -> Dict[str, Any]:
        """
        Estimate the forces required for a manipulation action.
        
        :param action: The manipulation action to analyze
        :param object_id: ID of the object involved
        :return: Estimated force requirements
        """
        object_info = await self._locate_object(object_id)
        if not object_info:
            return {
                "object_id": object_id,
                "error": f"Object {object_id} not found",
                "timestamp": datetime.now()
            }
        
        obj_weight = object_info["properties"].get("weight", 1.0)  # Default 1kg
        gravity = 9.81  # m/s^2
        
        # Calculate force requirements based on action type
        if action.action_type == ActionType.MANIPULATION:
            action_param = action.parameters.get("action", "").lower()
            
            if "grasp" in action_param or "pick" in action_param:
                # For grasping, need to overcome weight plus safety factor
                required_force = obj_weight * gravity * 1.5  # Safety factor of 1.5
            elif "place" in action_param or "set" in action_param:
                # For placing, need to control descent gently
                required_force = obj_weight * gravity * 0.5  # Lower force for controlled placement
            elif "lift" in action_param or "raise" in action_param:
                required_force = obj_weight * gravity * 2.0  # Extra force for acceleration
            else:
                required_force = obj_weight * gravity * 1.0  # Default force
        
        return {
            "object_id": object_id,
            "estimated_weight": obj_weight,
            "gravity": gravity,
            "required_force_newtons": required_force,
            "force_limit_exceeded": required_force > self.grasp_force_limit,
            "safety_margin": self.grasp_force_limit / (required_force + 0.1),  # +0.1 to avoid division by zero
            "timestamp": datetime.now()
        }


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    async def example():
        # Create the manipulation service
        manipulator = ObjectManipulationService()
        
        # Create a robot pose
        robot_pose = Pose(
            x=0.0,
            y=0.0,
            z=0.0,
            rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
        )
        
        # Example: Try to grasp an object
        print("Attempting to grasp an object...")
        result = await manipulator.grasp_object("object_1", robot_pose)
        print(f"Grasp result: {result}")
        
        # Example: Try to place an object
        target_pose = Pose(
            x=1.0,
            y=0.5,
            z=0.2,
            rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
        )
        
        print("Attempting to place an object...")
        result = await manipulator.place_object("object_1", target_pose, robot_pose)
        print(f"Place result: {result}")
        
        # Example: Estimate manipulability
        print("Estimating manipulability...")
        assessment = await manipulator.estimate_manipulability("object_1", robot_pose)
        print(f"Manipulability assessment: {assessment}")
    
    # Run the example
    # asyncio.run(example())
    
    # Example with advanced service
    async def advanced_example():
        advanced_manipulator = AdvancedObjectManipulationService()
        
        # Example: Grasp multiple objects
        objects_to_grasp = [
            {"id": "object_1", "class": "cup"},
            {"id": "object_2", "class": "book"},
            {"id": "object_3", "class": "box"}
        ]
        
        robot_pose = Pose(
            x=0.0,
            y=0.0,
            z=0.0,
            rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
        )
        
        print("Attempting to grasp multiple objects...")
        multi_result = await advanced_manipulator.grasp_multiple_objects(objects_to_grasp, robot_pose)
        print(f"Multi-grasp result: {multi_result}")
        
        # Example: Coordinated manipulation
        print("Attempting coordinated manipulation...")
        coord_result = await advanced_manipulator.coordinated_manipulation(
            "object_1", ["object_2"], robot_pose, "stacking"
        )
        print(f"Coordinated manipulation result: {coord_result}")
    
    # Run the advanced example
    # asyncio.run(advanced_example())