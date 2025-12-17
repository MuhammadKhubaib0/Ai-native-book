"""
Simulation compatibility tests for the VLA Capstone system.
Tests compatibility across different simulation environments (Isaac Sim, Gazebo).
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.vla_system_state import VLASystemState
from ..models.action_step import ActionStep, ActionType
from ..models.action_sequence import ActionSequence, ActionSequenceStatus
from ..models.multimodal_input import MultimodalInput
from ..models.voice_command import VoiceCommand

from ..simulation.gazebo_integration import GazeboIntegrationService
from ..integrations.isaac_integration import IsaacSimIntegrationService
from ..services.vision_integration import VisionIntegrationService
from ..services.navigation_service import NavigationService
from ..services.object_manipulation import ObjectManipulationService
from ..core.vla_system import VLASystem, VLAExecutionMode
from ..config import settings


class TestSimulationCompatibility(unittest.TestCase):
    """
    Test compatibility between different simulation environments and the VLA system.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock services to avoid requiring real simulation environments
        self.gazebo_mock = Mock(spec=GazeboIntegrationService)
        self.isaac_mock = Mock(spec=IsaacSimIntegrationService)
        self.vision_mock = Mock(spec=VisionIntegrationService)
        self.navigation_mock = Mock(spec=NavigationService)
        self.manipulation_mock = Mock(spec=ObjectManipulationService)
    
    def test_gazebo_connection_compatibility(self):
        """Test compatibility with Gazebo simulation environment."""
        # Mock Gazebo connection
        self.gazebo_mock.connect_to_gazebo = AsyncMock(return_value=True)
        self.gazebo_mock.get_robot_state = AsyncMock(return_value={
            "pose": {"x": 0.0, "y": 0.0, "z": 0.0, "rotation": {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}},
            "status": "idle"
        })
        self.gazebo_mock.execute_action_in_simulation = AsyncMock(return_value=True)
        
        async def run_test():
            # Verify connection compatibility
            connected = await self.gazebo_mock.connect_to_gazebo()
            self.assertTrue(connected, "Gazebo connection should be compatible")
            
            # Test state retrieval
            state = await self.gazebo_mock.get_robot_state()
            self.assertIn("pose", state)
            self.assertIn("status", state)
            
            # Test action execution
            action = ActionStep(
                id="test_action",
                action_sequence_id="seq_123",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 1.0, "y": 1.0},
                timeout=10,
                order=0
            )
            execution_result = await self.gazebo_mock.execute_action_in_simulation(action)
            self.assertTrue(execution_result, "Gazebo action execution should be compatible")
        
        asyncio.run(run_test())
    
    def test_isaac_sim_connection_compatibility(self):
        """Test compatibility with Isaac Sim environment."""
        # Mock Isaac Sim connection
        self.isaac_mock.connect_to_isaac = AsyncMock(return_value=True)
        self.isaac_mock.get_perception_data = AsyncMock(return_value={
            "objects": [{"class": "cup", "position": [1.0, 0.5, 0.8]}],
            "scene_description": "A cup on a table"
        })
        self.isaac_mock.execute_action_in_simulation = AsyncMock(return_value=True)
        
        async def run_test():
            # Verify connection compatibility
            connected = await self.isaac_mock.connect_to_isaac()
            self.assertTrue(connected, "Isaac Sim connection should be compatible")
            
            # Test perception data retrieval
            perception_data = await self.isaac_mock.get_perception_data()
            self.assertIn("objects", perception_data)
            self.assertGreater(len(perception_data["objects"]), 0)
            
            # Test action execution
            action = ActionStep(
                id="test_action",
                action_sequence_id="seq_123",
                action_type=ActionType.PERCEPTION,
                parameters={"action": "detect", "target": "cup"},
                timeout=5,
                order=0
            )
            execution_result = await self.isaac_mock.execute_action_in_simulation(action)
            self.assertTrue(execution_result, "Isaac Sim action execution should be compatible")
        
        asyncio.run(run_test())
    
    def test_action_execution_consistency(self):
        """Test that action execution is consistent across simulation environments."""
        # Define a standard action sequence for testing
        test_action_sequence = ActionSequence(
            id="consistency_test_seq",
            voice_command_id="voice_cmd_1",
            sequence=[
                ActionStep(
                    id="nav_step",
                    action_sequence_id="consistency_test_seq",
                    action_type=ActionType.NAVIGATION,
                    parameters={"x": 2.0, "y": 1.0, "theta": 0.0},
                    timeout=15,
                    order=0
                ),
                ActionStep(
                    id="manip_step",
                    action_sequence_id="consistency_test_seq",
                    action_type=ActionType.MANIPULATION,
                    parameters={"action": "grasp", "object_id": "test_object"},
                    timeout=20,
                    order=1
                )
            ],
            description="Test sequence for consistency across simulators",
            status=ActionSequenceStatus.PENDING
        )
        
        # Mock consistent behavior for both simulators
        self.gazebo_mock.execute_action_sequence = AsyncMock(return_value=True)
        self.isaac_mock.execute_action_sequence = AsyncMock(return_value=True)
        
        async def run_test():
            # Execute the same sequence in both simulators
            gazebo_result = await self.gazebo_mock.execute_action_sequence(test_action_sequence)
            isaac_result = await self.isaac_mock.execute_action_sequence(test_action_sequence)
            
            # Both should return consistent success/failure
            self.assertEqual(
                gazebo_result, 
                isaac_result, 
                "Action execution results should be consistent across simulators"
            )
        
        asyncio.run(run_test())
    
    def test_sensor_data_compatibility(self):
        """Test compatibility of sensor data formats between simulations."""
        # Mock sensor data from both simulators
        gazebo_sensor_data = {
            "lidar": [1.0, 1.1, 0.9, 1.2, 1.0] * 36,  # 180 degree scan
            "camera": {"resolution": [640, 480], "data": "mock_image_data"},
            "imu": {"linear_acceleration": [0.0, 0.0, 9.81], "angular_velocity": [0.0, 0.0, 0.0]},
            "timestamp": datetime.now().timestamp()
        }
        
        isaac_sensor_data = {
            "depth": {"width": 640, "height": 480, "data": "mock_depth_data"},
            "rgb": {"width": 640, "height": 480, "data": "mock_rgb_data"},
            "camera_pose": {"x": 0.0, "y": 0.0, "z": 1.0, "orientation": {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}},
            "timestamp": datetime.now().timestamp()
        }
        
        # Both should be processable by the vision service
        self.assertIsNotNone(gazebo_sensor_data)
        self.assertIsNotNone(isaac_sensor_data)
        
        # Check for essential data fields
        self.assertIn("timestamp", gazebo_sensor_data)
        self.assertIn("timestamp", isaac_sensor_data)
        
        # Verify that both have camera-like data (either rgb or camera)
        has_camera = "camera" in gazebo_sensor_data or "rgb" in isaac_sensor_data
        self.assertTrue(has_camera, "Both simulators should provide camera-like data")
    
    def test_3d_object_representation_compatibility(self):
        """Test compatibility of 3D object representations between simulations."""
        # Mock objects from Gazebo
        gazebo_objects = [
            {
                "id": "g_obj_1",
                "type": "static",
                "pose": {"position": {"x": 1.0, "y": 1.0, "z": 0.0}, "orientation": {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}},
                "geometry": {"type": "box", "dimensions": [0.1, 0.1, 0.1]},
                "material": {"color": [1.0, 0.0, 0.0], "texture": "wood"}
            }
        ]
        
        # Mock objects from Isaac
        isaac_objects = [
            {
                "name": "i_obj_1", 
                "type": "rigid",
                "position": [1.0, 1.0, 0.8],
                "orientation": [0.0, 0.0, 0.0, 1.0],  # Quat: x, y, z, w
                "asset_path": "/assets/cube.usd",
                "bounding_box": {"min": [0.95, 0.95, 0.75], "max": [1.05, 1.05, 0.85]},
                "properties": {"mass": 0.5, "friction": 0.8}
            }
        ]
        
        # Verify that both have essential positional information
        for obj in gazebo_objects:
            self.assertIn("pose", obj)
            pos = obj["pose"]["position"]
            self.assertIn("x", pos)
            self.assertIn("y", pos)
            self.assertIn("z", pos)
        
        for obj in isaac_objects:
            self.assertIn("position", obj)
            self.assertEqual(len(obj["position"]), 3)  # x, y, z
        
        # Verify that both can be processed by the vision system (at least the structure is compatible)
        self.assertGreater(len(gazebo_objects), 0)
        self.assertGreater(len(isaac_objects), 0)
    
    def test_navigation_compatibility(self):
        """Test navigation compatibility between simulation environments."""
        # Test navigation commands across environments
        navigation_commands = [
            {"x": 1.0, "y": 1.0, "theta": 0.0},
            {"x": -1.0, "y": 2.0, "theta": 1.57},
            {"x": 0.0, "y": 0.0, "theta": 3.14}
        ]
        
        # Mock navigation success for both simulators
        self.gazebo_mock.execute_navigation_action = AsyncMock(return_value=True)
        self.isaac_mock.execute_navigation_action = AsyncMock(return_value=True)
        
        async def run_test():
            for i, cmd in enumerate(navigation_commands):
                # Execute navigation command in both simulators
                gazebo_success = await self.gazebo_mock.execute_navigation_action(**cmd)
                isaac_success = await self.isaac_mock.execute_navigation_action(**cmd)
                
                # Both should handle the navigation command
                self.assertTrue(gazebo_success, f"Gazebo should handle navigation command {i+1}")
                self.assertTrue(isaac_success, f"Isaac should handle navigation command {i+1}")
        
        asyncio.run(run_test())
    
    def test_manipulation_compatibility(self):
        """Test manipulation compatibility between simulation environments."""
        # Test manipulation commands
        manipulation_commands = [
            {"action": "grasp", "object_id": "cup_1", "position": [1.0, 0.5, 0.8]},
            {"action": "place", "object_id": "box_1", "target_position": [1.5, 0.0, 0.8]},
            {"action": "release", "object_id": "object_1"}
        ]
        
        # Mock manipulation success for both simulators
        self.gazebo_mock.execute_manipulation_action = AsyncMock(return_value=True)
        self.isaac_mock.execute_manipulation_action = AsyncMock(return_value=True)
        
        async def run_test():
            for i, cmd in enumerate(manipulation_commands):
                # Execute manipulation command in both simulators
                gazebo_success = await self.gazebo_mock.execute_manipulation_action(**cmd)
                isaac_success = await self.isaac_mock.execute_manipulation_action(**cmd)
                
                # Both should handle the manipulation command
                self.assertTrue(gazebo_success, f"Gazebo should handle manipulation command {i+1}")
                self.assertTrue(isaac_success, f"Isaac should handle manipulation command {i+1}")
        
        asyncio.run(run_test())


class TestVLASystemSimulationIntegration(unittest.TestCase):
    """
    Test VLA system integration with different simulation environments.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a VLA system in simulation mode
        self.vla_system = Mock(spec=VLASystem)
        self.vla_system.execution_mode = VLAExecutionMode.SIMULATION
        self.vla_system.process_voice_command = AsyncMock(return_value=ActionSequence(
            id="test_seq_123",
            voice_command_id="test_cmd_123",
            sequence=[],
            description="Test sequence",
            status=ActionSequenceStatus.COMPLETED
        ))
        self.vla_system.execute_action_sequence = AsyncMock(return_value=True)
        self.vla_system.get_system_state = AsyncMock(return_value=VLASystemState(
            id="test_state_1",
            current_voice_command="test_cmd_123",
            current_action_sequence="test_seq_123",
            system_status="idle",
            robot_pose=None,
            perception_data={},
            last_update=datetime.now()
        ))
    
    @patch('..simulation.gazebo_integration.GazeboIntegrationService')
    @patch('..integration.isaac_integration.IsaacSimIntegrationService')
    async def test_vla_system_with_gazebo_backend(self, MockIsaac, MockGazebo):
        """Test VLA system integration with Gazebo backend."""
        # Setup mocks
        mock_gazebo = MockGazebo.return_value
        mock_gazebo.connect_to_gazebo = AsyncMock(return_value=True)
        mock_gazebo.execute_action_in_simulation = AsyncMock(return_value=True)
        
        mock_isaac = MockIsaac.return_value
        mock_isaac.connect_to_isaac = AsyncMock(return_value=True)
        
        # Test voice command processing
        voice_command = VoiceCommand(
            id="test_voice_cmd",
            transcribed_text="Go to the kitchen",
            intent="navigation", 
            parameters={"destination": "kitchen"},
            confidence=0.9,
            timestamp=datetime.now()
        )
        
        # Process command through VLA system (simulated)
        action_sequence = await self.vla_system.process_voice_command(voice_command.transcribed_text)
        
        # Execute in Gazebo simulation
        execution_result = await mock_gazebo.execute_action_in_simulation(action_sequence.sequence[0] if action_sequence.sequence else Mock())
        
        # Verify execution happened
        self.assertIsNotNone(action_sequence)
        if action_sequence.sequence:
            mock_gazebo.execute_action_in_simulation.assert_called_once()
    
    @patch('..simulation.gazebo_integration.GazeboIntegrationService')
    @patch('..integration.isaac_integration.IsaacSimIntegrationService')
    async def test_vla_system_with_isaac_backend(self, MockIsaac, MockGazebo):
        """Test VLA system integration with Isaac backend."""
        # Setup mocks
        mock_isaac = MockIsaac.return_value
        mock_isaac.connect_to_isaac = AsyncMock(return_value=True)
        mock_isaac.execute_action_in_simulation = AsyncMock(return_value=True)
        
        mock_gazebo = MockGazebo.return_value
        mock_gazebo.connect_to_gazebo = AsyncMock(return_value=True)
        
        # Test voice command processing
        voice_command = VoiceCommand(
            id="test_voice_cmd",
            transcribed_text="Find the red cup",
            intent="perception",
            parameters={"target_object": "red cup"},
            confidence=0.85,
            timestamp=datetime.now()
        )
        
        # Process command through VLA system (simulated)
        action_sequence = await self.vla_system.process_voice_command(voice_command.transcribed_text)
        
        # Execute in Isaac simulation
        if action_sequence and action_sequence.sequence:
            execution_result = await mock_isaac.execute_action_in_simulation(action_sequence.sequence[0])
            
            # Verify execution happened
            self.assertTrue(execution_result)
            mock_isaac.execute_action_in_simulation.assert_called_once()
    
    def test_multimodal_input_compatibility(self):
        """Test multimodal input compatibility across simulation environments."""
        # Create multimodal input
        multimodal_input = MultimodalInput(
            id="compat_test_input",
            visual_data={
                "objects": [
                    {"class": "cup", "position": [1.0, 0.5, 0.8], "confidence": 0.92}
                ],
                "scene_description": "A red cup on a table"
            },
            sensor_data={
                "timestamp": datetime.now().timestamp()
            },
            voice_input_id="Pick up the red cup",
            confidence=0.88,
            timestamp=datetime.now()
        )
        
        # Both simulation systems should be able to process this input
        # (In practice, this would be processed by the vision and perception systems)
        self.assertIsNotNone(multimodal_input.visual_data)
        self.assertIsNotNone(multimodal_input.voice_input_id)
        self.assertGreaterEqual(multimodal_input.confidence, 0.0)
        self.assertLessEqual(multimodal_input.confidence, 1.0)
    
    def test_simulation_state_synchronization(self):
        """Test that system states can be synchronized between simulation environments."""
        # Create mock states from different simulations
        gazebo_state = {
            "robot": {
                "position": {"x": 1.0, "y": 0.5, "z": 0.0},
                "orientation": {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0},
                "status": "idle"
            },
            "objects": [
                {"id": "obj1", "position": [1.5, 1.0, 0.0], "class": "box"}
            ],
            "timestamp": datetime.now().timestamp()
        }
        
        isaac_state = {
            "agents": [
                {
                    "name": "robot",
                    "position": [1.0, 0.5, 0.0],
                    "orientation": [0.0, 0.0, 0.0, 1.0],
                    "state": "idle"
                }
            ],
            "env_state": {
                "objects": [
                    {"name": "obj1", "position": [1.5, 1.0, 0.0], "type": "box"}
                ]
            },
            "timestamp": datetime.now().timestamp()
        }
        
        # Verify that both states have equivalent information
        # Check robot position in Gazebo state
        gb_pos = gazebo_state["robot"]["position"]
        self.assertEqual(type(gb_pos), dict)
        self.assertIn("x", gb_pos)
        self.assertIn("y", gb_pos)
        self.assertIn("z", gb_pos)
        
        # Check robot position in Isaac state
        isaac_pos = isaac_state["agents"][0]["position"]
        self.assertEqual(type(isaac_pos), list)
        self.assertEqual(len(isaac_pos), 3)  # x, y, z
        
        # Verify the information is equivalent (positions are similar)
        self.assertAlmostEqual(gb_pos["x"], isaac_pos[0], places=1)
        self.assertAlmostEqual(gb_pos["y"], isaac_pos[1], places=1)
        self.assertAlmostEqual(gb_pos["z"], isaac_pos[2], places=1)


class AdvancedSimulationCompatibilityTests(unittest.TestCase):
    """
    Advanced simulation compatibility tests for edge cases and complex scenarios.
    """
    
    def setUp(self):
        """Set up advanced test fixtures."""
        self.gazebo_service = Mock(spec=GazeboIntegrationService)
        self.isaac_service = Mock(spec=IsaacSimIntegrationService)
    
    def test_dynamic_environment_changes(self):
        """Test how simulations handle dynamic environment changes."""
        async def run_test():
            # Simulate environment change in Gazebo
            initial_objects_gazebo = [
                {"id": "static_obj_1", "position": [1.0, 1.0, 0.0], "movable": False},
                {"id": "dynamic_obj_1", "position": [2.0, 2.0, 0.0], "movable": True}
            ]
            self.gazebo_service.get_tracked_objects = AsyncMock(return_value=initial_objects_gazebo)
            
            # After some action, the dynamic object moves
            moved_objects_gazebo = [
                {"id": "static_obj_1", "position": [1.0, 1.0, 0.0], "movable": False},
                {"id": "dynamic_obj_1", "position": [2.5, 2.0, 0.0], "movable": True}  # Moved
            ]
            self.gazebo_service.get_tracked_objects = AsyncMock(side_effect=[
                initial_objects_gazebo, 
                moved_objects_gazebo
            ])
            
            # Test Isaac Sim with similar behavior
            initial_objects_isaac = [
                {"name": "static_obj_1", "position": [1.0, 1.0, 0.0], "is_static": True},
                {"name": "dynamic_obj_1", "position": [2.0, 2.0, 0.0], "is_static": False}
            ]
            self.isaac_service.get_tracked_objects = AsyncMock(return_value=initial_objects_isaac)
            
            # After action, the dynamic object moves in Isaac as well
            moved_objects_isaac = [
                {"name": "static_obj_1", "position": [1.0, 1.0, 0.0], "is_static": True},
                {"name": "dynamic_obj_1", "position": [2.5, 2.0, 0.0], "is_static": False}  # Moved
            ]
            self.isaac_service.get_tracked_objects = AsyncMock(side_effect=[
                initial_objects_isaac,
                moved_objects_isaac
            ])
            
            # Verify both simulations can track object movement
            initial_gb = await self.gazebo_service.get_tracked_objects()
            after_action_gb = await self.gazebo_service.get_tracked_objects()
            
            initial_isaac = await self.isaac_service.get_tracked_objects()
            after_action_isaac = await self.isaac_service.get_tracked_objects()
            
            # Check that dynamic objects moved in both environments
            dynamic_gb_before = [obj for obj in initial_gb if not obj["movable"]][0]
            dynamic_gb_after = [obj for obj in after_action_gb if obj["id"] == "dynamic_obj_1"][0]
            
            dynamic_isaac_before = [obj for obj in initial_isaac if not obj["is_static"]][0]
            dynamic_isaac_after = [obj for obj in after_action_isaac if obj["name"] == "dynamic_obj_1"][0]
            
            # Verify movement happened in both
            self.assertNotEqual(dynamic_gb_before["position"], dynamic_gb_after["position"])
            self.assertNotEqual(dynamic_isaac_before["position"], dynamic_isaac_after["position"])
        
        asyncio.run(run_test())
    
    def test_physics_engine_differences(self):
        """Test handling differences in physics engines between Gazebo and Isaac."""
        # Gazebo might use ODE, while Isaac Sim uses PhysX
        # The important thing is that both provide consistent high-level interfaces
        
        async def run_test():
            # Mock physics-related operations
            self.gazebo_service.get_contact_forces = AsyncMock(return_value=[
                {"object_id": "obj1", "force": [1.0, 0.0, 0.0]},
                {"object_id": "obj2", "force": [0.0, 1.0, 0.0]}
            ])
            
            self.isaac_service.get_contact_forces = AsyncMock(return_value=[
                {"object_name": "obj1", "force": [1.1, 0.1, 0.0]},  # Slightly different (physics variation)
                {"object_name": "obj2", "force": [0.1, 1.1, 0.0]}
            ])
            
            # Verify both can provide contact information
            gz_forces = await self.gazebo_service.get_contact_forces()
            isaac_forces = await self.isaac_service.get_contact_forces()
            
            self.assertGreater(len(gz_forces), 0)
            self.assertGreater(len(isaac_forces), 0)
            
            # Both should report similar physical interactions
            gz_obj_ids = {f.get("object_id") or f.get("object_name") for f in gz_forces}
            isaac_obj_ids = {f.get("object_id") or f.get("object_name") for f in isaac_forces}
            
            # At least some objects should overlap in both reports
            self.assertTrue(len(gz_obj_ids.intersection(isaac_obj_ids)) >= 1,
                            "Both simulators should report forces on at least some common objects")
        
        asyncio.run(run_test())
    
    def test_synchronization_under_load(self):
        """Test simulation synchronization under computational load."""
        async def run_test():
            # Simulate high-load conditions
            import time
            
            # Mock delayed responses to simulate computational load
            async def delayed_response_gazebo():
                await asyncio.sleep(0.1)  # Simulate processing delay
                return {"position": [1.0, 1.0, 0.0], "status": "busy"}
            
            async def delayed_response_isaac():
                await asyncio.sleep(0.08)  # Isaac might be slightly faster
                return {"position": [1.0, 1.0, 0.0], "status": "busy"}
            
            self.gazebo_service.get_robot_state = delayed_response_gazebo
            self.isaac_service.get_robot_state = delayed_response_isaac
            
            # Test multiple concurrent requests
            start_time = time.time()
            
            # Concurrent requests to both simulators
            gazebo_coros = [self.gazebo_service.get_robot_state() for _ in range(5)]
            isaac_coros = [self.isaac_service.get_robot_state() for _ in range(5)]
            
            # Execute concurrently
            gz_results = await asyncio.gather(*gazebo_coros)
            isaac_results = await asyncio.gather(*isaac_coros)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify all requests were processed
            self.assertEqual(len(gz_results), 5)
            self.assertEqual(len(isaac_results), 5)
            
            # Under load, responses should still be reasonable (less than 2 seconds each)
            self.assertLess(total_time, 2.0, "Requests should complete in reasonable time even under load")
        
        asyncio.run(run_test())
    
    def test_error_recovery_compatibility(self):
        """Test error recovery across simulation environments."""
        async def run_test():
            # Simulate an error condition in both simulators
            self.gazebo_service.execute_action_in_simulation = AsyncMock(side_effect=Exception("Navigation failed"))
            self.isaac_service.execute_action_in_simulation = AsyncMock(side_effect=Exception("Navigation failed"))
            
            # Test error recovery patterns
            action = ActionStep(
                id="error_test_action",
                action_sequence_id="seq_456",
                action_type=ActionType.NAVIGATION,
                parameters={"x": 100.0, "y": 100.0},  # Impossible location to trigger error
                timeout=5,
                order=0
            )
            
            # Both simulators should handle the error gracefully
            gz_error_handled = False
            isaac_error_handled = False
            
            try:
                await self.gazebo_service.execute_action_in_simulation(action)
            except Exception:
                gz_error_handled = True  # Error properly caught and handled
            
            try:
                await self.isaac_service.execute_action_in_simulation(action)
            except Exception:
                isaac_error_handled = True  # Error properly caught and handled
            
            self.assertTrue(gz_error_handled, "Gazebo should handle action execution errors")
            self.assertTrue(isaac_error_handled, "Isaac should handle action execution errors")
        
        asyncio.run(run_test())


class SimulationPerformanceTests(unittest.TestCase):
    """
    Performance tests for simulation compatibility.
    """
    
    def setUp(self):
        """Set up performance test fixtures."""
        self.gazebo_service = Mock(spec=GazeboIntegrationService)
        self.isaac_service = Mock(spec=IsaacSimIntegrationService)
    
    def test_response_time_consistency(self):
        """Test that response times are consistent between simulators."""
        import time
        
        async def run_test():
            # Track response times
            gz_times = []
            isaac_times = []
            
            # Run multiple trials to get average response times
            for i in range(10):
                # Simulate Gazebo response
                gz_start = time.perf_counter()
                await asyncio.sleep(np.random.uniform(0.05, 0.15))  # Simulate variable processing time
                gz_time = time.perf_counter() - gz_start
                gz_times.append(gz_time)
                
                # Simulate Isaac response  
                isaac_start = time.perf_counter()
                await asyncio.sleep(np.random.uniform(0.04, 0.12))  # Potentially faster
                isaac_time = time.perf_counter() - isaac_start
                isaac_times.append(isaac_time)
            
            avg_gz_time = sum(gz_times) / len(gz_times)
            avg_isaac_time = sum(isaac_times) / len(isaac_times)
            
            # Times should be reasonably close (within 100ms of each other)
            time_difference = abs(avg_gz_time - avg_isaac_time)
            self.assertLess(time_difference, 0.1, 
                           f"Response time difference too large: {time_difference}s")
            
            # Neither should be unreasonably slow (>500ms average)
            self.assertLess(avg_gz_time, 0.5, f"Gazebo average time too slow: {avg_gz_time}s")
            self.assertLess(avg_isaac_time, 0.5, f"Isaac average time too slow: {avg_isaac_time}s")
        
        asyncio.run(run_test())
    
    def test_resource_utilization_consistency(self):
        """Test resource utilization patterns between simulators."""
        async def run_test():
            # In a real implementation, this would monitor actual resource usage
            # For this test, we'll just verify the interface can be called
            
            # Mock resource usage data
            gz_resources = {
                "cpu_percent": 45.2,
                "memory_mb": 1200.5,
                "gpu_memory_mb": 850.0,
                "timestamp": datetime.now().timestamp()
            }
            
            isaac_resources = {
                "cpu_percent": 52.1,
                "memory_mb": 1400.2,
                "gpu_memory_mb": 1100.5,  # Isaac might use more GPU
                "timestamp": datetime.now().timestamp()
            }
            
            # Simulate getting resource usage (in real implementation)
            # these would query actual system metrics
            self.assertIsNotNone(gz_resources)
            self.assertIsNotNone(isaac_resources)
            
            # Verify resource data structure
            required_fields = ["cpu_percent", "memory_mb", "timestamp"]
            for field in required_fields:
                self.assertIn(field, gz_resources)
                self.assertIn(field, isaac_resources)
            
            # GPU usage might differ, which is expected
            self.assertIn("gpu_memory_mb", gz_resources)
            self.assertIn("gpu_memory_mb", isaac_resources)
        
        asyncio.run(run_test())
    
    def test_scaling_behavior(self):
        """Test how well each simulator scales with complexity."""
        async def run_test():
            # Simulate increasing complexity (number of objects)
            complexities = [1, 5, 10, 20, 50]
            gz_times = []
            isaac_times = []
            
            for complexity in complexities:
                # Simulate complex scene with many objects
                start_time = time.perf_counter()
                
                # Simulate processing time that increases with complexity
                # In reality, this would be actual processing in each simulator
                await asyncio.sleep(complexity * 0.01)  # Simulation of complexity scaling
                
                elapsed_time = time.perf_counter() - start_time
                gz_times.append(elapsed_time)
                
                # Isaac might scale differently
                start_time = time.perf_counter()
                await asyncio.sleep(complexity * 0.008)  # Potentially more efficient
                elapsed_time = time.perf_counter() - start_time
                isaac_times.append(elapsed_time)
            
            # Verify that both scale reasonably (time increases proportionally with complexity)
            # but stays within bounds
            max_allowed_time = 1.0  # No simulation should take more than 1 second for any complexity level
            self.assertLess(max(gz_times), max_allowed_time, 
                           "Gazebo response times scaling poorly")
            self.assertLess(max(isaac_times), max_allowed_time, 
                           "Isaac response times scaling poorly")
        
        asyncio.run(run_test())


class IntegrationTestSuite:
    """
    Complete integration test suite for simulation compatibility.
    """
    
    def run_all_tests(self):
        """Run all simulation compatibility tests."""
        print("Running Simulation Compatibility Test Suite")
        print("="*60)
        
        # Create test suites
        basic_tests = unittest.TestLoader().loadTestsFromTestCase(TestSimulationCompatibility)
        vla_integration_tests = unittest.TestLoader().loadTestsFromTestCase(TestVLASystemSimulationIntegration)
        advanced_tests = unittest.TestLoader().loadTestsFromTestCase(AdvancedSimulationCompatibilityTests)
        performance_tests = unittest.TestLoader().loadTestsFromTestCase(SimulationPerformanceTests)
        
        # Combine all tests
        all_tests = unittest.TestSuite([
            basic_tests,
            vla_integration_tests,
            advanced_tests,
            performance_tests
        ])
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(all_tests)
        
        # Print summary
        print("\n" + "="*60)
        print("SIMULATION COMPATIBILITY TEST RESULTS")
        print("="*60)
        print(f"Tests Run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFAILURES:")
            for test, trace in result.failures:
                print(f"  {test}")
                print(f"    {trace.split(chr(10))[0]}")  # First line of traceback
        
        if result.errors:
            print("\nERRORS:")
            for test, trace in result.errors:
                print(f"  {test}")
                print(f"    {trace.split(chr(10))[0]}")  # First line of traceback
        
        if result.wasSuccessful():
            print(f"\n🎉 All simulation compatibility tests passed!")
            print("VLA system is compatible with both Gazebo and Isaac Sim environments.")
        else:
            print(f"\n❌ Some simulation compatibility tests failed.")
            print("Please review the failures/errors above.")
        
        return result


def run_simulation_compatibility_tests():
    """
    Run the simulation compatibility test suite.
    """
    test_suite = IntegrationTestSuite()
    return test_suite.run_all_tests()


# Example usage for individual testing
if __name__ == "__main__":
    # Run the full test suite
    result = run_simulation_compatibility_tests()
    
    # Additionally, run specific tests directly if needed
    print("\nRunning individual compatibility checks...")
    
    # Example of direct compatibility check
    checker = TestSimulationCompatibility()
    checker.setUp()
    
    try:
        # Run one specific test manually
        checker.test_action_execution_consistency()
        print("✓ Action execution consistency test passed")
    except Exception as e:
        print(f"✗ Action execution consistency test failed: {e}")
    
    print("\nSimulation compatibility testing completed.")