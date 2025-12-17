"""
Service for handling navigation in the VLA system for humanoid robots.
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import asyncio
from datetime import datetime
import math
from dataclasses import dataclass

from ..models.vla_system_state import Pose
from ..simulation.gazebo_integration import GazeboIntegrationService
from ..services.vision_integration import VisionIntegrationService
from ..config import settings


@dataclass
class Waypoint:
    """Represents a navigation waypoint."""
    x: float
    y: float
    z: float = 0.0
    theta: float = 0.0  # Orientation in radians
    tolerance: float = 0.1  # How close to get to the waypoint (meters)
    action: Optional[str] = None  # Optional action at this waypoint


@dataclass
class Path:
    """Represents a navigation path."""
    waypoints: List[Waypoint]
    total_distance: float = 0.0
    estimated_time: float = 0.0


class NavigationService:
    """
    Service for handling navigation tasks in the VLA system for humanoid robots.
    """
    
    def __init__(self):
        """Initialize the navigation service."""
        self.gazebo_service = GazeboIntegrationService()
        self.vision_service = VisionIntegrationService()
        
        # Navigation configuration
        self.max_linear_velocity = 0.5  # m/s
        self.max_angular_velocity = 1.0  # rad/s
        self.linear_tolerance = 0.1     # meters
        self.angular_tolerance = 0.1    # radians
        self.obstacle_buffer = 0.3      # buffer distance around obstacles
        self.planning_resolution = 0.05  # grid resolution for path planning
        self.local_map_size = 10.0      # size of local map for planning (meters)
        
        # Robot-specific parameters
        self.robot_radius = 0.3  # radius of robot footprint for planning
        self.robot_height = 1.2  # height of robot for 3D considerations
        
        # Navigation state
        self.current_path: Optional[Path] = None
        self.current_waypoint_index = 0
        self.is_navigating = False
        self.current_goal: Optional[Waypoint] = None
        
        # Cost map parameters
        self.collision_cost = 100.0
        self.traversable_cost = 1.0
        self.unknown_cost = 50.0
    
    async def plan_path(self, start_pose: Pose, target_pose: Pose) -> Optional[Path]:
        """
        Plan a path from the start pose to the target pose.
        
        :param start_pose: Starting pose of the robot
        :param target_pose: Target pose to navigate to
        :return: Planned path or None if no path is possible
        """
        try:
            # In a real implementation, this would use a path planning algorithm like A*, RRT, or Dijkstra
            # For this simulation, we'll use a simplified approach
            
            # Check if start and target are in valid positions
            if not await self._is_traversable(start_pose.x, start_pose.y) or \
               not await self._is_traversable(target_pose.x, target_pose.y):
                print("Start or target position is not traversable")
                return None
            
            # Create waypoints for the path
            # For this simple implementation, we'll create a straight-line path
            # with intermediate waypoints for humanoid walking
            waypoints = await self._create_straight_line_path(start_pose, target_pose)
            
            # Calculate path metrics
            total_distance = self._calculate_path_distance(waypoints)
            estimated_time = total_distance / self.max_linear_velocity
            
            path = Path(
                waypoints=waypoints,
                total_distance=total_distance,
                estimated_time=estimated_time
            )
            
            return path
            
        except Exception as e:
            print(f"Error planning path: {str(e)}")
            return None
    
    async def _create_straight_line_path(self, start_pose: Pose, target_pose: Pose) -> List[Waypoint]:
        """
        Create a straight-line path between two poses.
        
        :param start_pose: Starting pose
        :param target_pose: Target pose
        :return: List of waypoints forming the path
        """
        # Calculate the direct distance and heading
        dx = target_pose.x - start_pose.x
        dy = target_pose.y - start_pose.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # For humanoid navigation, we don't want to take large steps
        # So we'll break the path into smaller segments
        step_size = 0.3  # Max step size for humanoid
        num_steps = max(1, int(distance / step_size))
        
        waypoints = []
        
        for i in range(num_steps + 1):
            fraction = i / num_steps if num_steps > 0 else 0
            x = start_pose.x + dx * fraction
            y = start_pose.y + dy * fraction
            z = start_pose.z  # Keep constant height for now
            
            # Calculate orientation towards target
            if i < num_steps:  # Not the final waypoint
                next_dx = target_pose.x - x
                next_dy = target_pose.y - y
                theta = math.atan2(next_dy, next_dx)
            else:
                # Use target orientation for final waypoint
                # Extract theta from target pose's orientation quaternion
                qw = target_pose.rotation.get('qw', 1.0)
                qz = target_pose.rotation.get('qz', 0.0)
                theta = 2 * math.atan2(qz, qw)  # Convert quat to yaw angle
            
            waypoint = Waypoint(
                x=x,
                y=y,
                z=z,
                theta=theta,
                tolerance=self.linear_tolerance
            )
            
            # Add the waypoint if it's traversable
            if await self._is_traversable(x, y):
                waypoints.append(waypoint)
            else:
                # If the waypoint isn't traversable, try to find an alternative
                print(f"Waypoint {i} at ({x:.2f}, {y:.2f}) is not traversable")
                # In a real implementation, this would implement a more sophisticated avoidance
                # For now, we'll skip this problematic waypoint
        
        return waypoints
    
    def _calculate_path_distance(self, waypoints: List[Waypoint]) -> float:
        """
        Calculate the total distance of a path.
        
        :param waypoints: List of waypoints forming the path
        :return: Total distance in meters
        """
        if len(waypoints) <= 1:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(waypoints)):
            dx = waypoints[i].x - waypoints[i-1].x
            dy = waypoints[i].y - waypoints[i-1].y
            dz = waypoints[i].z - waypoints[i-1].z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            total_distance += dist
        
        return total_distance
    
    async def _is_traversable(self, x: float, y: float) -> bool:
        """
        Check if a position is traversable.
        
        :param x: X-coordinate
        :param y: Y-coordinate
        :return: True if traversable, False otherwise
        """
        # In a real implementation, this would check against a map of obstacles
        # For this simulation, we'll assume the space is mostly traversable
        # but with some randomly placed obstacles
        
        # Simulate some static obstacles
        obstacles = [
            (3.0, 1.0, 0.5),  # x, y, radius
            (-1.0, -1.5, 0.7),
            (2.0, -0.5, 0.4)
        ]
        
        for obs_x, obs_y, obs_radius in obstacles:
            distance = math.sqrt((x - obs_x)**2 + (y - obs_y)**2)
            if distance <= (obs_radius + self.robot_radius):
                return False  # Position is too close to an obstacle
        
        # Check boundaries (assuming a 10m x 10m area)
        boundary_margin = 0.5
        if x < -5.0 + boundary_margin or x > 5.0 - boundary_margin:
            return False
        if y < -5.0 + boundary_margin or y > 5.0 - boundary_margin:
            return False
        
        return True  # Position is traversable
    
    async def navigate_to_waypoint(self, waypoint: Waypoint) -> bool:
        """
        Navigate the robot to a specific waypoint.
        
        :param waypoint: Target waypoint to navigate to
        :return: True if successful, False otherwise
        """
        try:
            # Get current robot pose
            current_robot_state = await self.gazebo_service.get_robot_state()
            current_pose = current_robot_state.get("pose", {"x": 0.0, "y": 0.0, "z": 0.0, "rotation": {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}})
            
            current_x = current_pose["x"]
            current_y = current_pose["y"]
            
            # Calculate distance to waypoint
            dx = waypoint.x - current_x
            dy = waypoint.y - current_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Check if already close enough
            if distance <= waypoint.tolerance:
                print(f"Already at waypoint ({waypoint.x:.2f}, {waypoint.y:.2f}), within tolerance ({waypoint.tolerance:.2f})")
                return True
            
            # Move toward the waypoint
            success = await self._move_toward_waypoint(waypoint)
            
            if success:
                print(f"Successfully reached waypoint ({waypoint.x:.2f}, {waypoint.y:.2f})")
                
                # If there's an action associated with this waypoint, execute it
                if waypoint.action:
                    action_success = await self._execute_waypoint_action(waypoint.action)
                    if not action_success:
                        print(f"Waypoint action '{waypoint.action}' failed")
                        return False
                
                return True
            else:
                print(f"Failed to reach waypoint ({waypoint.x:.2f}, {waypoint.y:.2f})")
                return False
                
        except Exception as e:
            print(f"Error navigating to waypoint: {str(e)}")
            return False
    
    async def _move_toward_waypoint(self, waypoint: Waypoint) -> bool:
        """
        Move the robot toward a specific waypoint.
        
        :param waypoint: Target waypoint to move toward
        :return: True if successful, False otherwise
        """
        try:
            # Get current robot pose
            current_robot_state = await self.gazebo_service.get_robot_state()
            current_pose = current_robot_state.get("pose", {"x": 0.0, "y": 0.0, "z": 0.0})
            
            current_x = current_pose["x"]
            current_y = current_pose["y"]
            
            # Calculate required movement
            dx = waypoint.x - current_x
            dy = waypoint.y - current_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Calculate required rotation to face the waypoint
            current_yaw = self._extract_yaw_from_pose(current_pose)
            target_yaw = math.atan2(dy, dx)
            
            # Calculate rotation needed
            rotation_needed = target_yaw - current_yaw
            # Normalize to [-π, π]
            while rotation_needed > math.pi:
                rotation_needed -= 2 * math.pi
            while rotation_needed < -math.pi:
                rotation_needed += 2 * math.pi
            
            # Rotate to face the target
            rotation_success = await self._rotate_robot(rotation_needed)
            if not rotation_success:
                return False
            
            # Move forward to reach the target
            movement_success = await self._move_forward(distance)
            if not movement_success:
                return False
            
            # Optionally rotate to final orientation
            if abs(waypoint.theta - target_yaw) > self.angular_tolerance:
                final_rotation = waypoint.theta - target_yaw
                await self._rotate_robot(final_rotation)
            
            return True
            
        except Exception as e:
            print(f"Error moving toward waypoint: {str(e)}")
            return False
    
    def _extract_yaw_from_pose(self, pose: Dict[str, Any]) -> float:
        """
        Extract yaw angle from robot pose (represented as quaternion).
        
        :param pose: Robot pose with quaternion orientation
        :return: Yaw angle in radians
        """
        rotation = pose.get("rotation", {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0})
        qx, qy, qz, qw = rotation["qx"], rotation["qy"], rotation["qz"], rotation["qw"]
        
        # Convert quaternion to euler angles (yaw around z-axis)
        siny_cosp = 2 * (qw * qz + qx * qy)
        cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        return yaw
    
    async def _rotate_robot(self, angle_radians: float) -> bool:
        """
        Rotate the robot by the specified angle.
        
        :param angle_radians: Angle to rotate in radians
        :return: True if successful, False otherwise
        """
        try:
            # In a real implementation, this would send rotation commands to the robot
            # For this simulation, we'll just simulate the rotation
            
            # Calculate time needed for rotation at max angular velocity
            rotation_time = abs(angle_radians) / self.max_angular_velocity
            
            # Simulate the rotation
            print(f"Rotating by {math.degrees(angle_radians):.2f} degrees...")
            await asyncio.sleep(min(rotation_time, 2.0))  # Limit to 2 seconds
            
            return True
            
        except Exception as e:
            print(f"Error rotating robot: {str(e)}")
            return False
    
    async def _move_forward(self, distance_meters: float) -> bool:
        """
        Move the robot forward by the specified distance.
        
        :param distance_meters: Distance to move forward in meters
        :return: True if successful, False otherwise
        """
        try:
            # In a real implementation, this would move the robot's legs to achieve forward motion
            # For this simulation, we'll just simulate the movement
            
            # Calculate time needed for movement at max linear velocity
            movement_time = distance_meters / self.max_linear_velocity
            
            # Simulate the movement
            print(f"Moving forward {distance_meters:.2f} meters...")
            await asyncio.sleep(min(movement_time, 5.0))  # Limit to 5 seconds
            
            return True
            
        except Exception as e:
            print(f"Error moving robot forward: {str(e)}")
            return False
    
    async def _execute_waypoint_action(self, action: str) -> bool:
        """
        Execute an action associated with a waypoint.
        
        :param action: Action to execute
        :return: True if successful, False otherwise
        """
        # In a real implementation, this could involve perception, manipulation, etc.
        # For this simulation, we'll just log the action
        print(f"Executing waypoint action: {action}")
        await asyncio.sleep(0.5)  # Simulate action execution time
        return True
    
    async def navigate_to_pose(self, target_pose: Pose) -> bool:
        """
        Navigate the robot to a specific pose.
        
        :param target_pose: Target pose to navigate to
        :return: True if successful, False otherwise
        """
        try:
            # Plan the path
            current_robot_state = await self.gazebo_service.get_robot_state()
            current_pose = current_robot_state.get("pose", {"x": 0.0, "y": 0.0, "z": 0.0})
            
            start_pose = Pose(
                x=current_pose["x"],
                y=current_pose["y"],
                z=current_pose["z"],
                rotation=current_pose.get("rotation", {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0})
            )
            
            path = await self.plan_path(start_pose, target_pose)
            if not path:
                print("Failed to plan path to target pose")
                return False
            
            # Follow the path
            for waypoint in path.waypoints:
                success = await self.navigate_to_waypoint(waypoint)
                if not success:
                    print(f"Failed to navigate to waypoint ({waypoint.x:.2f}, {waypoint.y:.2f})")
                    return False
            
            print(f"Successfully navigated to target pose ({target_pose.x:.2f}, {target_pose.y:.2f})")
            return True
            
        except Exception as e:
            print(f"Error navigating to pose: {str(e)}")
            return False
    
    async def navigate_to_location(self, x: float, y: float, z: float = 0.0) -> bool:
        """
        Navigate the robot to a specific location (x, y, z).
        
        :param x: Target X coordinate
        :param y: Target Y coordinate
        :param z: Target Z coordinate (default 0.0)
        :return: True if successful, False otherwise
        """
        target_pose = Pose(
            x=x,
            y=y,
            z=z,
            rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
        )
        
        return await self.navigate_to_pose(target_pose)
    
    async def follow_path(self, path: Path) -> bool:
        """
        Follow a pre-planned path.
        
        :param path: Path to follow
        :return: True if successful, False otherwise
        """
        try:
            self.current_path = path
            self.current_waypoint_index = 0
            self.is_navigating = True
            
            for i, waypoint in enumerate(path.waypoints):
                self.current_waypoint_index = i
                
                print(f"Navigating to waypoint {i+1}/{len(path.waypoints)}: ({waypoint.x:.2f}, {waypoint.y:.2f})")
                
                success = await self.navigate_to_waypoint(waypoint)
                if not success:
                    print(f"Failed to follow path at waypoint {i+1}")
                    return False
            
            self.is_navigating = False
            print("Successfully followed path")
            return True
            
        except Exception as e:
            print(f"Error following path: {str(e)}")
            self.is_navigating = False
            return False
    
    async def stop_navigation(self):
        """
        Stop the current navigation.
        """
        self.is_navigating = False
        self.current_path = None
        print("Navigation stopped")
    
    async def get_current_position(self) -> Optional[Pose]:
        """
        Get the current position of the robot.
        
        :return: Current robot pose or None if unavailable
        """
        try:
            robot_state = await self.gazebo_service.get_robot_state()
            pose_data = robot_state.get("pose", {})
            
            if pose_data:
                return Pose(
                    x=pose_data.get("x", 0.0),
                    y=pose_data.get("y", 0.0),
                    z=pose_data.get("z", 0.0),
                    rotation=pose_data.get("rotation", {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0})
                )
            else:
                return None
        except Exception as e:
            print(f"Error getting current position: {str(e)}")
            return None
    
    async def get_navigation_status(self) -> Dict[str, Any]:
        """
        Get the current status of navigation.
        
        :return: Navigation status information
        """
        current_pos = await self.get_current_position()
        
        status = {
            "is_navigating": self.is_navigating,
            "current_path_exists": self.current_path is not None,
            "current_waypoint_index": self.current_waypoint_index,
            "total_waypoints": len(self.current_path.waypoints) if self.current_path else 0,
            "current_position": {
                "x": current_pos.x if current_pos else None,
                "y": current_pos.y if current_pos else None,
                "z": current_pos.z if current_pos else None
            } if current_pos else None,
            "current_goal": {
                "x": self.current_goal.x if self.current_goal else None,
                "y": self.current_goal.y if self.current_goal else None,
                "z": self.current_goal.z if self.current_goal else None
            } if self.current_goal else None,
            "timestamp": datetime.now()
        }
        
        return status
    
    async def navigate_with_obstacle_avoidance(self, target_pose: Pose) -> bool:
        """
        Navigate to a target pose with dynamic obstacle avoidance.
        
        :param target_pose: Target pose to navigate to
        :return: True if successful, False otherwise
        """
        try:
            # Get current robot position
            current_pos = await self.get_current_position()
            if not current_pos:
                print("Could not get current robot position")
                return False
            
            start_pose = Pose(
                x=current_pos.x,
                y=current_pos.y,
                z=current_pos.z,
                rotation=current_pos.rotation
            )
            
            # Plan initial path
            path = await self.plan_path(start_pose, target_pose)
            if not path:
                print("Could not plan initial path")
                return False
            
            # Navigate the path with obstacle checking
            return await self._navigate_with_obstacle_avoidance(path, target_pose)
            
        except Exception as e:
            print(f"Error in navigation with obstacle avoidance: {str(e)}")
            return False
    
    async def _navigate_with_obstacle_avoidance(self, initial_path: Path, target_pose: Pose) -> bool:
        """
        Navigate a path with active obstacle avoidance.
        
        :param initial_path: Initial planned path
        :param target_pose: Final target pose
        :return: True if successful, False otherwise
        """
        # For this simplified implementation, we'll follow the path
        # and replan if we encounter unexpected obstacles
        
        for i, waypoint in enumerate(initial_path.waypoints):
            # Check for obstacles before moving to the waypoint
            if not await self._check_path_clear_to_waypoint(waypoint):
                print(f"Obstacle detected on path to waypoint {i+1}, replanning...")
                
                # Get current position
                current_pos = await self.get_current_position()
                if not current_pos:
                    return False
                
                # Replan from current position to final target
                updated_path = await self.plan_path(current_pos, target_pose)
                if not updated_path:
                    print("Could not replan path after obstacle detection")
                    return False
                
                # Follow the updated path from this point
                success = await self.follow_path(updated_path)
                return success
            
            # Navigate to the waypoint
            success = await self.navigate_to_waypoint(waypoint)
            if not success:
                print(f"Failed to navigate to waypoint {i+1}")
                
                # Try to replan from current position to final target
                current_pos = await self.get_current_position()
                if current_pos:
                    updated_path = await self.plan_path(current_pos, target_pose)
                    if updated_path:
                        return await self.follow_path(updated_path)
                
                return False
        
        return True
    
    async def _check_path_clear_to_waypoint(self, waypoint: Waypoint) -> bool:
        """
        Check if the path to a waypoint is clear of obstacles.
        
        :param waypoint: Waypoint to check
        :return: True if clear, False if obstructed
        """
        # In a real implementation, this would use sensor data to check the path
        # For this simulation, we'll assume the path is clear unless specifically known to have obstacles
        return await self._is_traversable(waypoint.x, waypoint.y)


class AdvancedNavigationService(NavigationService):
    """
    Advanced navigation service with additional capabilities.
    """
    
    def __init__(self):
        super().__init__()
        
        # Advanced navigation features
        self.use_local_map = True
        self.enable_dynamic_replanning = True
        self.enable_multi_goal_navigation = True
        self.enable_social_navigation = False  # For human-aware navigation
        
        # Humanoid-specific navigation parameters
        self.step_height = 0.1  # Height to lift foot during walking (meters)
        self.swing_period = 0.5  # Time for one step (seconds)
        self.zmp_margin = 0.05   # Zero moment point safety margin (meters)
        
        # Trajectory planning for humanoid walking
        self.walk_trajectory_generator = None
        self.balance_controller = None
    
    async def plan_humanoid_trajectory(self, start_pose: Pose, target_pose: Pose) -> Optional[Path]:
        """
        Plan a trajectory specifically for humanoid walking.
        
        :param start_pose: Starting pose of the humanoid
        :param target_pose: Target pose to navigate to
        :return: Planned humanoid trajectory or None if not possible
        """
        try:
            # Use standard path planning for the high-level path
            standard_path = await self.plan_path(start_pose, target_pose)
            if not standard_path:
                return None
            
            # For humanoid navigation, convert the path to a sequence of footsteps
            # This is a simplified approach - real humanoid navigation is much more complex
            footsteps = await self._generate_footsteps_from_path(standard_path)
            
            # Create a humanoid-appropriate path
            waypoints = []
            for i, (left_pos, right_pos) in enumerate(footsteps):
                # For each step, create a waypoint where the body should be
                # positioned between the feet
                body_x = (left_pos[0] + right_pos[0]) / 2
                body_y = (left_pos[1] + right_pos[1]) / 2
                
                theta = math.atan2(right_pos[1] - left_pos[1], right_pos[0] - left_pos[0])
                
                waypoint = Waypoint(
                    x=body_x,
                    y=body_y,
                    z=start_pose.z,  # Keep consistent height
                    theta=theta,
                    tolerance=self.linear_tolerance,
                    action="adjust_balance"
                )
                waypoints.append(waypoint)
            
            # Calculate metrics
            total_distance = self._calculate_path_distance(waypoints)
            estimated_time = len(footsteps) * self.swing_period  # Approximate time
            
            humanoid_path = Path(
                waypoints=waypoints,
                total_distance=total_distance,
                estimated_time=estimated_time
            )
            
            return humanoid_path
            
        except Exception as e:
            print(f"Error planning humanoid trajectory: {str(e)}")
            return None
    
    async def _generate_footsteps_from_path(self, path: Path) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Generate a sequence of footsteps for humanoid navigation based on a path.
        
        :param path: Path to generate footsteps for
        :return: List of tuples containing (left_foot_position, right_foot_position)
        """
        footsteps = []
        
        # For this simplified implementation, we'll alternate footsteps
        # along the path, keeping them shoulder-width apart
        shoulder_width = 0.3  # meters
        
        for i, waypoint in enumerate(path.waypoints):
            if i % 2 == 0:  # Even indices: left foot forward
                left_foot = (waypoint.x, waypoint.y)
                right_foot = (waypoint.x - shoulder_width/2, waypoint.y)
            else:  # Odd indices: right foot forward
                right_foot = (waypoint.x, waypoint.y)
                left_foot = (waypoint.x - shoulder_width/2, waypoint.y)
            
            footsteps.append((left_foot, right_foot))
        
        return footsteps
    
    async def navigate_with_balance_control(self, target_pose: Pose) -> bool:
        """
        Navigate to a target pose with active balance control.
        
        :param target_pose: Target pose to navigate to
        :return: True if successful, False otherwise
        """
        try:
            # Plan a humanoid-appropriate trajectory
            current_pos = await self.get_current_position()
            if not current_pos:
                return False
            
            start_pose = Pose(
                x=current_pos.x,
                y=current_pos.y,
                z=current_pos.z,
                rotation=current_pos.rotation
            )
            
            path = await self.plan_humanoid_trajectory(start_pose, target_pose)
            if not path:
                print("Could not plan humanoid-appropriate trajectory")
                return False
            
            # Follow the path with balance control
            return await self._follow_path_with_balance_control(path)
            
        except Exception as e:
            print(f"Error in navigation with balance control: {str(e)}")
            return False
    
    async def _follow_path_with_balance_control(self, path: Path) -> bool:
        """
        Follow a path with active balance control for humanoid stability.
        
        :param path: Path to follow with balance control
        :return: True if successful, False otherwise
        """
        try:
            for i, waypoint in enumerate(path.waypoints):
                print(f"Following path with balance control - Waypoint {i+1}/{len(path.waypoints)}")
                
                # Check balance before taking step
                if not await self._is_balance_stable():
                    print("Robot is not balanced, attempting recovery...")
                    recovery_success = await self._attempt_balance_recovery()
                    if not recovery_success:
                        print("Could not recover balance, stopping navigation")
                        return False
                
                # Proceed with navigation step
                success = await self.navigate_to_waypoint(waypoint)
                if not success:
                    print(f"Failed to navigate to waypoint {i+1} with balance control")
                    
                    # Try balance recovery before giving up
                    await self._attempt_balance_recovery()
                    return False
                
                # After each step, verify balance
                await asyncio.sleep(0.1)  # Brief pause to settle
                if not await self._is_balance_stable():
                    print("Balance compromised after step, attempting recovery...")
                    recovery_success = await self._attempt_balance_recovery()
                    if not recovery_success:
                        print("Could not recover balance, stopping navigation")
                        return False
            
            print("Successfully completed path with balance control")
            return True
            
        except Exception as e:
            print(f"Error following path with balance control: {str(e)}")
            return False
    
    async def _is_balance_stable(self) -> bool:
        """
        Check if the humanoid robot is currently stable.
        
        :return: True if stable, False otherwise
        """
        # In a real implementation, this would check sensor data
        # such as IMU readings, foot pressure sensors, or visual estimates
        # For this simulation, we'll return True (assume stable)
        return True
    
    async def _attempt_balance_recovery(self) -> bool:
        """
        Attempt to recover balance if the robot is unstable.
        
        :return: True if recovery was successful, False otherwise
        """
        print("Attempting balance recovery...")
        
        # In a real implementation, this would execute balancing motions
        # such as shifting weight, moving arms, or adjusting stance
        # For this simulation, we'll just pause and return True
        
        await asyncio.sleep(0.5)
        print("Balance recovery attempt completed")
        return True
    
    async def navigate_to_multiple_goals(self, goals: List[Pose]) -> Dict[str, Any]:
        """
        Navigate to multiple goals in sequence.
        
        :param goals: List of goal poses to visit
        :return: Detailed results of multi-goal navigation
        """
        if not self.enable_multi_goal_navigation:
            return {
                "success": False,
                "message": "Multi-goal navigation not enabled",
                "completed_goals": [],
                "failed_goals": goals,
                "timestamp": datetime.now()
            }
        
        completed_goals = []
        failed_goals = []
        
        for i, goal in enumerate(goals):
            print(f"Moving to goal {i+1}/{len(goals)}: ({goal.x:.2f}, {goal.y:.2f})")
            
            success = await self.navigate_to_pose(goal)
            
            if success:
                completed_goals.append(goal)
                print(f"Successfully reached goal {i+1}")
            else:
                failed_goals.append(goal)
                print(f"Failed to reach goal {i+1}, continuing to next goal")
        
        results = {
            "success": len(failed_goals) == 0,
            "message": f"Completed {len(completed_goals)} of {len(goals)} goals",
            "completed_goals": completed_goals,
            "failed_goals": failed_goals,
            "total_goals": len(goals),
            "completion_rate": len(completed_goals) / len(goals) if goals else 0,
            "timestamp": datetime.now()
        }
        
        return results


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    async def example():
        # Create the navigation service
        navigator = NavigationService()
        
        # Example: Navigate to a specific pose
        target_pose = Pose(
            x=2.0,
            y=1.5,
            z=0.0,
            rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
        )
        
        print("Starting navigation to target...")
        success = await navigator.navigate_to_pose(target_pose)
        print(f"Navigation success: {success}")
        
        # Example: Plan a path
        start_pose = Pose(
            x=0.0,
            y=0.0,
            z=0.0,
            rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
        )
        
        print("Planning path from start to target...")
        path = await navigator.plan_path(start_pose, target_pose)
        if path:
            print(f"Path planned with {len(path.waypoints)} waypoints, distance: {path.total_distance:.2f}m")
        
        # Get navigation status
        status = await navigator.get_navigation_status()
        print(f"Navigation status: {status}")
    
    # Run the example
    # asyncio.run(example())
    
    # Example with advanced service
    async def advanced_example():
        advanced_navigator = AdvancedNavigationService()
        
        # Example: Navigate with balance control
        target_pose = Pose(
            x=1.5,
            y=0.5,
            z=0.0,
            rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}
        )
        
        print("Starting navigation with balance control...")
        success = await advanced_navigator.navigate_with_balance_control(target_pose)
        print(f"Navigation with balance control success: {success}")
        
        # Example: Navigate to multiple goals
        goals = [
            Pose(x=1.0, y=0.0, z=0.0, rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}),
            Pose(x=1.0, y=1.0, z=0.0, rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}),
            Pose(x=0.0, y=1.0, z=0.0, rotation={"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0})
        ]
        
        print("Navigating to multiple goals...")
        multi_results = await advanced_navigator.navigate_to_multiple_goals(goals)
        print(f"Multi-goal navigation results: {multi_results}")
    
    # Run the advanced example
    # asyncio.run(advanced_example())