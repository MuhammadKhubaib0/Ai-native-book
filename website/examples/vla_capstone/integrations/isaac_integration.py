"""
Integration service for connecting with Isaac Sim for perception capabilities.
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
import cv2
from PIL import Image
import json
import requests

from ..models.vla_system_state import VLASystemState, Pose
from ..models.multimodal_input import MultimodalInput
from ..models.action_step import ActionStep
from ..services.vision_integration import VisionIntegrationService
from ..simulation.gazebo_integration import GazeboIntegrationService
from ..config import settings


class IsaacSimIntegrationService:
    """
    Service for integrating with Isaac Sim for perception capabilities in the VLA system.
    """
    
    def __init__(self, isaac_sim_url: str = "http://localhost:8211"):
        """
        Initialize the Isaac Sim integration service.
        
        :param isaac_sim_url: URL for Isaac Sim REST API
        """
        self.isaac_sim_url = isaac_sim_url
        self.session = None
        self.connected = False
        self.scene_loaded = False
        
        # Initialize vision service for processing Isaac Sim data
        self.vision_service = VisionIntegrationService()
        
        # Isaac Sim specific parameters
        self.camera_names = ["ego_camera", "front_camera", "realsense_camera"]
        self.sensor_config = {
            "enabled": True,
            "resolution": [640, 480],
            "frequency": 30
        }
    
    async def connect_to_isaac(self) -> bool:
        """
        Connect to Isaac Sim.
        
        :return: True if connection successful, False otherwise
        """
        try:
            # Create session
            self.session = requests.Session()
            
            # Test connection by getting Isaac Sim status
            response = self.session.get(f"{self.isaac_sim_url}/status", timeout=5)
            
            if response.status_code == 200:
                self.connected = True
                print("Successfully connected to Isaac Sim")
                
                # Set up the perception sensors
                await self.setup_perception_sensors()
                
                return True
            else:
                print(f"Failed to connect to Isaac Sim, status code: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("Failed to connect to Isaac Sim - connection refused")
            return False
        except Exception as e:
            print(f"Error connecting to Isaac Sim: {str(e)}")
            return False
    
    async def disconnect_from_isaac(self):
        """
        Disconnect from Isaac Sim.
        """
        if self.session:
            self.session.close()
        self.connected = False
        self.scene_loaded = False
        print("Disconnected from Isaac Sim")
    
    async def setup_perception_sensors(self):
        """
        Set up perception sensors in Isaac Sim.
        """
        if not self.connected:
            print("Not connected to Isaac Sim")
            return
        
        try:
            for cam_name in self.camera_names:
                # Configure camera sensor
                config = {
                    "name": cam_name,
                    "resolution": self.sensor_config["resolution"],
                    "enabled": self.sensor_config["enabled"]
                }
                
                response = self.session.post(
                    f"{self.isaac_sim_url}/sensors/camera/configure",
                    json=config,
                    timeout=5
                )
                
                if response.status_code != 200:
                    print(f"Failed to configure camera {cam_name}")
                else:
                    print(f"Successfully configured camera {cam_name}")
            
            print("Perception sensors configured")
            
        except Exception as e:
            print(f"Error setting up perception sensors: {str(e)}")
    
    async def load_scene(self, scene_path: str) -> bool:
        """
        Load a scene in Isaac Sim.
        
        :param scene_path: Path to the scene file
        :return: True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected to Isaac Sim")
            return False
        
        try:
            payload = {
                "scene_path": scene_path,
                "settings": {
                    "physics": True,
                    "rendering": True,
                    "sensors": True
                }
            }
            
            response = self.session.post(
                f"{self.isaac_sim_url}/scene/load",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.scene_loaded = True
                print(f"Scene loaded successfully: {scene_path}")
                return True
            else:
                print(f"Failed to load scene, status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error loading scene: {str(e)}")
            return False
    
    async def get_isaac_sim_data(self) -> Optional[Dict[str, Any]]:
        """
        Get perception data from Isaac Sim.
        
        :return: Perception data dictionary or None if failed
        """
        if not self.connected or not self.scene_loaded:
            print("Not connected or scene not loaded")
            return None
        
        try:
            # Get data from all cameras
            sim_data = {
                "timestamp": datetime.now().isoformat(),
                "cameras": {},
                "objects": {},
                "robot_state": {}
            }
            
            for cam_name in self.camera_names:
                # Get camera data
                response = self.session.get(
                    f"{self.isaac_sim_url}/sensors/camera/{cam_name}/data",
                    timeout=5
                )
                
                if response.status_code == 200:
                    img_data = response.json()
                    sim_data["cameras"][cam_name] = img_data
                else:
                    print(f"Failed to get data from camera {cam_name}")
            
            # Get object information
            objects_response = self.session.get(
                f"{self.isaac_sim_url}/scene/objects",
                timeout=5
            )
            
            if objects_response.status_code == 200:
                sim_data["objects"] = objects_response.json()
            
            # Get robot state
            robot_state_response = self.session.get(
                f"{self.isaac_sim_url}/robots/current_state",
                timeout=5
            )
            
            if robot_state_response.status_code == 200:
                sim_data["robot_state"] = robot_state_response.json()
            
            return sim_data
            
        except Exception as e:
            print(f"Error getting Isaac Sim data: {str(e)}")
            return None
    
    async def process_isaac_sim_perception(self, sim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process perception data from Isaac Sim.
        
        :param sim_data: Raw data from Isaac Sim
        :return: Processed perception results
        """
        # Use the vision service to process Isaac Sim data
        processed_data = {
            "processed_frames": [],
            "object_detections": [],
            "depth_maps": [],
            "segmentation_masks": [],
            "pose_estimates": []
        }
        
        # Process data from each camera
        for cam_name, camera_data in sim_data.get("cameras", {}).items():
            frame_result = await self.vision_service._process_single_frame(
                {
                    "image": camera_data.get("image_data", ""),
                    "width": camera_data.get("width", 640),
                    "height": camera_data.get("height", 480),
                    "format": camera_data.get("format", "rgb8"),
                    "pose_info": camera_data.get("pose_info", {})
                }
            )
            
            processed_data["processed_frames"].append(frame_result)
        
        # Extract object detections from sim data
        for obj_name, obj_data in sim_data.get("objects", {}).items():
            processed_obj = {
                "name": obj_name,
                "class": obj_data.get("class", "unknown"),
                "position": obj_data.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}),
                "rotation": obj_data.get("rotation", {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}),
                "bbox": obj_data.get("bbox", [0.0, 0.0, 1.0, 1.0]),  # [x, y, width, height]
                "visible": obj_data.get("visible", True),
                "confidence": 1.0  # Isaac Sim provides ground truth
            }
            processed_data["object_detections"].append(processed_obj)
        
        return processed_data
    
    async def integrate_with_vla_system(self, vla_system_state: VLASystemState) -> MultimodalInput:
        """
        Integrate Isaac Sim perception data with the VLA system.
        
        :param vla_system_state: Current state of the VLA system
        :return: Multimodal input with Isaac Sim data
        """
        # Get perception data from Isaac Sim
        sim_data = await self.get_isaac_sim_data()
        if not sim_data:
            print("Could not get Isaac Sim data for integration")
            return None
        
        # Process the perception data
        processed_data = await self.process_isaac_sim_perception(sim_data)
        
        # Create multimodal input combining Isaac Sim data with VLA state
        multimodal_input = MultimodalInput(
            id=f"isaac_sim_input_{int(datetime.now().timestamp())}",
            visual_data={
                "objects": processed_data["object_detections"],
                "processed_frames": processed_data["processed_frames"],
                "scene_description": "Generated from Isaac Sim environment"
            },
            sensor_data={
                "robot_state": sim_data.get("robot_state", {}),
                "cameras": sim_data.get("cameras", {}),
                "timestamp": datetime.now()
            },
            confidence=0.95,  # Isaac Sim provides ground truth, high confidence
            timestamp=datetime.now()
        )
        
        return multimodal_input
    
    async def set_robot_position(self, position: Dict[str, float], orientation: Dict[str, float]) -> bool:
        """
        Set the robot's position and orientation in Isaac Sim.
        
        :param position: Position vector {x, y, z}
        :param orientation: Orientation as quaternion {qx, qy, qz, qw}
        :return: True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected to Isaac Sim")
            return False
        
        try:
            payload = {
                "position": position,
                "orientation": orientation
            }
            
            response = self.session.post(
                f"{self.isaac_sim_url}/robots/set_position",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"Set robot position to ({position['x']}, {position['y']}, {position['z']})")
                return True
            else:
                print(f"Failed to set robot position, status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error setting robot position: {str(e)}")
            return False
    
    async def execute_action_in_isaac(self, action_step: ActionStep) -> bool:
        """
        Execute an action in Isaac Sim.
        
        :param action_step: Action to execute
        :return: True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected to Isaac Sim")
            return False
        
        try:
            # Convert action to Isaac Sim command
            if action_step.action_type == "navigation":
                # Execute navigation action
                target_pos = action_step.parameters
                position = {
                    "x": target_pos.get("x", 0.0),
                    "y": target_pos.get("y", 0.0),
                    "z": target_pos.get("z", 0.0)
                }
                orientation = {
                    "qx": target_pos.get("qx", 0.0),
                    "qy": target_pos.get("qy", 0.0),
                    "qz": target_pos.get("qz", 0.0),
                    "qw": target_pos.get("qw", 1.0)
                }
                
                success = await self.set_robot_position(position, orientation)
                return success
            
            elif action_step.action_type == "manipulation":
                # Execute manipulation action
                manipulation_payload = {
                    "action": action_step.parameters.get("action", "grasp"),
                    "object_id": action_step.parameters.get("object_id", ""),
                    "target_position": action_step.parameters.get("position", {})
                }
                
                response = self.session.post(
                    f"{self.isaac_sim_url}/manipulation/execute",
                    json=manipulation_payload,
                    timeout=action_step.timeout
                )
                
                return response.status_code == 200
            
            else:
                # For other action types, send as generic command
                action_payload = {
                    "action_type": str(action_step.action_type),
                    "parameters": action_step.parameters
                }
                
                response = self.session.post(
                    f"{self.isaac_sim_url}/actions/execute",
                    json=action_payload,
                    timeout=action_step.timeout
                )
                
                return response.status_code == 200
                
        except Exception as e:
            print(f"Error executing action in Isaac Sim: {str(e)}")
            return False
    
    async def get_tracked_objects(self) -> List[Dict[str, Any]]:
        """
        Get currently tracked objects from Isaac Sim.
        
        :return: List of tracked objects
        """
        if not self.connected:
            print("Not connected to Isaac Sim")
            return []
        
        try:
            response = self.session.get(f"{self.isaac_sim_url}/scene/objects", timeout=5)
            
            if response.status_code == 200:
                objects_data = response.json()
                
                # Format objects for VLA system
                formatted_objects = []
                for obj_id, obj_data in objects_data.items():
                    formatted_obj = {
                        "id": obj_id,
                        "class": obj_data.get("class", "unknown"),
                        "position": obj_data.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}),
                        "orientation": obj_data.get("orientation", {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}),
                        "bbox": obj_data.get("bbox", [0.0, 0.0, 1.0, 1.0]),
                        "visibility": obj_data.get("visibility", 1.0),
                        "is_dynamic": obj_data.get("is_dynamic", False)
                    }
                    formatted_objects.append(formatted_obj)
                
                return formatted_objects
            else:
                print(f"Failed to get tracked objects, status: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting tracked objects: {str(e)}")
            return []
    
    async def reset_isaac_environment(self) -> bool:
        """
        Reset the Isaac Sim environment to initial state.
        
        :return: True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected to Isaac Sim")
            return False
        
        try:
            response = self.session.post(f"{self.isaac_sim_url}/scene/reset", timeout=5)
            
            if response.status_code == 200:
                print("Isaac Sim environment reset")
                return True
            else:
                print(f"Failed to reset Isaac Sim environment, status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error resetting Isaac Sim environment: {str(e)}")
            return False
    
    async def run_isaac_episode(
        self,
        scene_path: str,
        action_sequence: List[ActionStep]
    ) -> Dict[str, Any]:
        """
        Run a complete episode in Isaac Sim with the provided action sequence.
        
        :param scene_path: Path to the scene to load
        :param action_sequence: Sequence of actions to execute
        :return: Episode results
        """
        episode_data = {
            "scene_path": scene_path,
            "actions_executed": [],
            "observations": [],
            "rewards": [],
            "success": False,
            "steps_taken": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Load the scene
        if not await self.load_scene(scene_path):
            episode_data["error"] = "Failed to load scene"
            return episode_data
        
        try:
            for i, action in enumerate(action_sequence):
                # Execute the action in Isaac Sim
                success = await self.execute_action_in_isaac(action)
                episode_data["actions_executed"].append({
                    "action": action.dict(),
                    "success": success
                })
                
                if not success:
                    episode_data["error"] = f"Action {i} failed"
                    break
                
                # Get observation after action
                sim_data = await self.get_isaac_sim_data()
                if sim_data:
                    processed_obs = await self.process_isaac_sim_perception(sim_data)
                    episode_data["observations"].append(processed_obs)
                
                # Calculate reward (in a real implementation, this would be more complex)
                reward = 1.0 if success else -1.0
                episode_data["rewards"].append(reward)
                episode_data["steps_taken"] += 1
            
            # Determine if the episode was successful
            # In a real implementation, this would check if goals were achieved
            episode_data["success"] = all(
                action["success"] for action in episode_data["actions_executed"]
            )
            
            print(f"Episode completed with {episode_data['steps_taken']} steps, success: {episode_data['success']}")
            return episode_data
            
        except Exception as e:
            episode_data["error"] = str(e)
            print(f"Error running Isaac Sim episode: {str(e)}")
            return episode_data


class AdvancedIsaacIntegrationService(IsaacSimIntegrationService):
    """
    Advanced Isaac Sim integration service with additional capabilities.
    """
    
    def __init__(self, isaac_sim_url: str = "http://localhost:8211"):
        super().__init__(isaac_sim_url)
        
        # Additional capabilities
        self.domain_randomization_enabled = True
        self.synthetic_data_generation_enabled = True
        self.annotation_generation_enabled = True
        self.experience_replay_enabled = True
        
        # Domain randomization parameters
        self.lighting_conditions = ["bright", "dim", "overcast", "backlit"]
        self.materials = ["wood", "metal", "plastic", "fabric"]
        self.backgrounds = ["office", "home", "industrial", "outdoor"]
    
    async def enable_domain_randomization(self, config: Dict[str, Any] = None):
        """
        Enable domain randomization in Isaac Sim for synthetic data generation.
        
        :param config: Configuration for domain randomization
        """
        if not self.connected:
            print("Not connected to Isaac Sim")
            return
        
        # Default configuration
        if config is None:
            config = {
                "lighting_randomization": True,
                "texture_randomization": True,
                "background_randomization": True,
                "material_randomization": True,
                "perturbation_magnitude": 0.5
            }
        
        try:
            response = self.session.post(
                f"{self.isaac_sim_url}/domain_randomization/enable",
                json=config,
                timeout=5
            )
            
            if response.status_code == 200:
                print("Domain randomization enabled")
            else:
                print(f"Failed to enable domain randomization, status: {response.status_code}")
                
        except Exception as e:
            print(f"Error enabling domain randomization: {str(e)}")
    
    async def generate_synthetic_perception_data(
        self,
        num_samples: int = 100,
        object_classes: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic perception data using Isaac Sim with domain randomization.
        
        :param num_samples: Number of synthetic samples to generate
        :param object_classes: Specific object classes to include
        :return: List of synthetic perception data samples
        """
        if not self.connected:
            print("Not connected to Isaac Sim")
            return []
        
        if object_classes is None:
            object_classes = ["cup", "box", "sphere", "capsule", "cylinder"]
        
        synthetic_data = []
        
        for i in range(num_samples):
            # Randomize environment if enabled
            if self.domain_randomization_enabled:
                await self.randomize_environment()
            
            # Place random objects in the scene
            await self.place_random_objects(object_classes)
            
            # Get perception data
            sim_data = await self.get_isaac_sim_data()
            if sim_data:
                processed_data = await self.process_isaac_sim_perception(sim_data)
                
                sample = {
                    "id": f"synthetic_sample_{i}",
                    "perception_data": processed_data,
                    "environment_config": sim_data.get("environment", {}),
                    "object_placement": sim_data.get("objects", {}),
                    "metadata": {
                        "lighting_condition": np.random.choice(self.lighting_conditions),
                        "materials": np.random.choice(self.materials),
                        "background": np.random.choice(self.backgrounds),
                        "timestamp": datetime.now().isoformat()
                    }
                }
                synthetic_data.append(sample)
        
        print(f"Generated {len(synthetic_data)} synthetic perception samples")
        return synthetic_data
    
    async def randomize_environment(self):
        """
        Randomize environment parameters in Isaac Sim.
        """
        if not self.connected:
            return
        
        try:
            random_config = {
                "lighting": np.random.choice(self.lighting_conditions),
                "materials": [np.random.choice(self.materials)],
                "background": np.random.choice(self.backgrounds),
                "clutter_level": np.random.uniform(0.1, 0.9),
                "camera_params": {
                    "position_variance": np.random.uniform(0.1, 0.5),
                    "orientation_variance": np.random.uniform(0.1, 0.3)
                }
            }
            
            response = self.session.post(
                f"{self.isaac_sim_url}/environment/randomize",
                json=random_config,
                timeout=5
            )
            
            if response.status_code == 200:
                print("Environment randomized")
            else:
                print(f"Failed to randomize environment, status: {response.status_code}")
                
        except Exception as e:
            print(f"Error randomizing environment: {str(e)}")
    
    async def place_random_objects(self, object_classes: List[str]):
        """
        Place random objects in the Isaac Sim scene.
        
        :param object_classes: Classes of objects to place
        """
        if not self.connected:
            return
        
        try:
            # Generate random object placements
            num_objects = np.random.randint(1, 5)  # Place 1-4 objects
            placements = []
            
            for _ in range(num_objects):
                obj_class = np.random.choice(object_classes)
                placement = {
                    "class": obj_class,
                    "position": {
                        "x": np.random.uniform(-2.0, 2.0),
                        "y": np.random.uniform(-2.0, 2.0),
                        "z": 0.0  # Start on ground
                    },
                    "rotation": {
                        "qx": np.random.uniform(-0.1, 0.1),
                        "qy": np.random.uniform(-0.1, 0.1),
                        "qz": np.random.uniform(-0.5, 0.5),
                        "qw": np.random.uniform(0.8, 1.0)
                    },
                    "scale": np.random.uniform(0.5, 1.5)
                }
                placements.append(placement)
            
            payload = {
                "placements": placements
            }
            
            response = self.session.post(
                f"{self.isaac_sim_url}/objects/place_random",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"Placed {num_objects} random objects")
            else:
                print(f"Failed to place random objects, status: {response.status_code}")
                
        except Exception as e:
            print(f"Error placing random objects: {str(e)}")
    
    async def generate_annotations(
        self,
        synthetic_samples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate annotations for synthetic perception data.
        
        :param synthetic_samples: List of synthetic perception samples
        :return: List of annotated samples
        """
        annotated_samples = []
        
        for sample in synthetic_samples:
            # Isaac Sim provides ground truth annotations
            annotations = {
                "objects": [],
                "keypoints": [],
                "segmentation": None,  # Would be generated if segmentation enabled
                "depth": sample["perception_data"].get("depth_maps", [])
            }
            
            # Extract object annotations
            for obj in sample["object_placement"].values():
                obj_annotation = {
                    "class": obj.get("class", "unknown"),
                    "position": obj.get("position", {"x": 0, "y": 0, "z": 0}),
                    "bbox": obj.get("bbox", [0, 0, 1, 1]),  # [x, y, width, height]
                    "pose": obj.get("rotation", {"qx": 0, "qy": 0, "qz": 0, "qw": 1}),
                    "visibility": 1.0,  # Ground truth visibility
                    "occlusion": 0.0    # No occlusion in simulation
                }
                annotations["objects"].append(obj_annotation)
            
            annotated_sample = {**sample, "annotations": annotations}
            annotated_samples.append(annotated_sample)
        
        print(f"Generated annotations for {len(annotated_samples)} samples")
        return annotated_samples


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    async def example():
        # Create the Isaac integration service
        isaac_integration = IsaacSimIntegrationService()
        
        # Connect to Isaac Sim
        connected = await isaac_integration.connect_to_isaac()
        print(f"Connected to Isaac Sim: {connected}")
        
        if connected:
            # Load a scene
            scene_loaded = await isaac_integration.load_scene("/scenes/simple_room.usd")
            print(f"Scene loaded: {scene_loaded}")
            
            if scene_loaded:
                # Get Isaac Sim data
                sim_data = await isaac_integration.get_isaac_sim_data()
                if sim_data:
                    print(f"Got Isaac Sim data with {len(sim_data.get('cameras', {}))} cameras")
                    
                    # Process perception data
                    processed_data = await isaac_integration.process_isaac_sim_perception(sim_data)
                    print(f"Processed {len(processed_data['object_detections'])} objects")
                
                # Get tracked objects
                tracked_objects = await isaac_integration.get_tracked_objects()
                print(f"Tracked {len(tracked_objects)} objects in Isaac Sim")
            
            # Disconnect from Isaac Sim
            await isaac_integration.disconnect_from_isaac()
    
    # Run the example
    # asyncio.run(example())
    
    # Example with advanced service
    async def advanced_example():
        advanced_integration = AdvancedIsaacIntegrationService()
        
        # Connect to Isaac Sim
        connected = await advanced_integration.connect_to_isaac()
        print(f"Connected to Isaac Sim: {connected}")
        
        if connected:
            # Enable domain randomization
            await advanced_integration.enable_domain_randomization()
            
            # Generate synthetic data
            synthetic_data = await advanced_integration.generate_synthetic_perception_data(
                num_samples=10,
                object_classes=["cube", "sphere", "cylinder"]
            )
            print(f"Generated {len(synthetic_data)} synthetic samples")
            
            # Generate annotations
            annotated_data = await advanced_integration.generate_annotations(synthetic_data)
            print(f"Generated annotations for {len(annotated_data)} samples")
            
            # Disconnect
            await advanced_integration.disconnect_from_isaac()
    
    # Run the advanced example
    # asyncio.run(advanced_example())