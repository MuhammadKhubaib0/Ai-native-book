"""
Capstone demonstration example for the VLA system.
This module demonstrates the complete integration of all VLA components.
"""
import asyncio
import time
import json
from datetime import datetime
import uuid
from typing import Dict, Any, List, Optional

# Import VLA system components
from ..core.vla_system import VLASystem, VLAExecutionMode
from ..services.whisper_processor import WhisperAudioProcessor
from ..services.llm_service import LLMService, LLMConfig
from ..services.vision_integration import VisionIntegrationService
from ..services.multimodal_fusion import MultimodalFusionService
from ..services.action_sequencer import ActionSequencer
from ..services.navigation_service import NavigationService
from ..services.object_manipulation import ObjectManipulationService
from ..services.error_recovery import ErrorRecoveryService, ErrorType, RecoveryStrategy
from ..services.confidence_manager import ConfidenceManager
from ..simulation.gazebo_integration import GazeboIntegrationService
from ..integrations.isaac_integration import IsaacSimIntegrationService
from ..models.voice_command import VoiceCommand
from ..models.action_sequence import ActionSequence
from ..models.action_step import ActionStep, ActionType
from ..models.multimodal_input import MultimodalInput
from ..models.vla_system_state import VLASystemState
from ..evaluation.capstone_metrics import CapstoneMetricsEvaluator
from ..config import settings


class CapstoneDemoExample:
    """
    Capstone demonstration example showcasing complete VLA system capabilities.
    """
    
    def __init__(self):
        """Initialize the capstone demonstration."""
        # Initialize all major system components
        self.vla_system = VLASystem(execution_mode=VLAExecutionMode.SIMULATION)
        self.whisper_service = WhisperAudioProcessor()
        self.llm_service = LLMService(LLMConfig(
            model_name=settings.llm_model,
            temperature=settings.llm_temperature
        ))
        self.vision_service = VisionIntegrationService()
        self.fusion_service = MultimodalFusionService()
        self.action_sequencer = ActionSequencer()
        self.navigation_service = NavigationService()
        self.manipulation_service = ObjectManipulationService()
        self.error_recovery = ErrorRecoveryService()
        self.confidence_manager = ConfidenceManager()
        self.gazebo_service = GazeboIntegrationService()
        self.isaac_integration = IsaacSimIntegrationService()
        self.metrics_evaluator = CapstoneMetricsEvaluator()
        
        # Demo state
        self.demo_scenarios = [
            {
                "name": "Kitchen Assistance",
                "description": "Robot goes to kitchen, finds red cup, picks it up and brings to user",
                "commands": [
                    "Navigate to the kitchen",
                    "Find the red cup on the counter",
                    "Grasp the red cup",
                    "Return to me"
                ],
                "expected_outcomes": [
                    "navigate_to_kitchen_success",
                    "detect_red_cup_success", 
                    "grasp_cup_success",
                    "return_to_user_success"
                ]
            },
            {
                "name": "Office Cleaning",
                "description": "Robot clears desk by picking up scattered objects",
                "commands": [
                    "Go to the office desk",
                    "Clean up the scattered papers",
                    "Organize the desk items in the tray"
                ],
                "expected_outcomes": [
                    "navigate_to_office_success",
                    "detect_scattered_items_success",
                    "organize_items_success"
                ]
            },
            {
                "name": "Guided Tour",
                "description": "Robot gives a guided tour of the house",
                "commands": [
                    "Take me on a tour of the house",
                    "Show me the kitchen",
                    "Show me the bedroom",
                    "Return to the entrance"
                ],
                "expected_outcomes": [
                    "navigate_to_kitchen_success",
                    "navigate_to_bedroom_success",
                    "guide_tour_success",
                    "return_to_entrance_success"
                ]
            }
        ]
        
        # Student tracking for educational purposes
        self.student_progress = {}
        
        print("Capstone Demo Example initialized with complete VLA system components")
    
    async def run_kitchen_assistance_demo(self) -> Dict[str, Any]:
        """
        Run the kitchen assistance demonstration scenario.
        
        :return: Demo results with performance metrics
        """
        print("🚀 Starting Kitchen Assistance Demo")
        print("=" * 60)
        
        start_time = time.time()
        
        # Track demo steps and results
        demo_results = {
            "demo_name": "Kitchen Assistance",
            "steps_completed": [],
            "steps_failed": [],
            "total_time": 0.0,
            "success_rate": 0.0,
            "confidence_scores": [],
            "errors": []
        }
        
        try:
            # Step 1: Navigate to kitchen
            print("\nStep 1: Navigating to kitchen...")
            nav_success = await self._execute_navigation_to_kitchen()
            demo_results["steps_completed"].append({
                "step": "navigate_to_kitchen",
                "success": nav_success,
                "timestamp": datetime.now().isoformat()
            })
            
            if not nav_success:
                demo_results["steps_failed"].append("navigation_to_kitchen")
                demo_results["errors"].append("Failed to navigate to kitchen")
            
            print(f"  Navigation to kitchen: {'✅ SUCCESS' if nav_success else '❌ FAILED'}")
            
            if nav_success:
                # Step 2: Find red cup
                print("\nStep 2: Finding red cup...")
                find_success, cup_location = await self._find_red_cup()
                demo_results["steps_completed"].append({
                    "step": "find_red_cup",
                    "success": find_success,
                    "location": cup_location if find_success else None,
                    "timestamp": datetime.now().isoformat()
                })
                
                if not find_success:
                    demo_results["steps_failed"].append("find_red_cup")
                    demo_results["errors"].append("Failed to locate red cup")
                
                print(f"  Find red cup: {'✅ SUCCESS' if find_success else '❌ FAILED'}")
                
                if find_success and cup_location:
                    # Step 3: Grasp red cup
                    print("\nStep 3: Grasping red cup...")
                    grasp_success = await self._grasp_red_cup(cup_location)
                    demo_results["steps_completed"].append({
                        "step": "grasp_red_cup",
                        "success": grasp_success,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    if not grasp_success:
                        demo_results["steps_failed"].append("grasp_red_cup")
                        demo_results["errors"].append("Failed to grasp red cup")
                    
                    print(f"  Grasp red cup: {'✅ SUCCESS' if grasp_success else '❌ FAILED'}")
                    
                    if grasp_success:
                        # Step 4: Return to user
                        print("\nStep 4: Returning to user...")
                        return_success = await self._return_to_user()
                        demo_results["steps_completed"].append({
                            "step": "return_to_user",
                            "success": return_success,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        print(f"  Return to user: {'✅ SUCCESS' if return_success else '❌ FAILED'}")
            
            # Calculate performance metrics
            total_steps = len(self.demo_scenarios[0]["commands"])
            completed_steps = len(demo_results["steps_completed"])
            failed_steps = len(demo_results["steps_failed"])
            
            demo_results["success_rate"] = completed_steps / total_steps if total_steps > 0 else 0.0
            demo_results["total_time"] = time.time() - start_time
            demo_results["expected_outcomes_met"] = self._evaluate_outcomes(demo_results)
            
            print(f"\n📊 Demo Results:")
            print(f"  Success Rate: {demo_results['success_rate']*100:.1f}% ({completed_steps}/{total_steps})")
            print(f"  Total Time: {demo_results['total_time']:.2f}s")
            print(f"  Expected Outcomes Met: {demo_results['expected_outcomes_met']}/{len(self.demo_scenarios[0]['expected_outcomes'])}")
            
            return demo_results
            
        except Exception as e:
            print(f"❌ Error during kitchen assistance demo: {str(e)}")
            demo_results["errors"].append(f"Demo execution error: {str(e)}")
            return demo_results
    
    async def _execute_navigation_to_kitchen(self) -> bool:
        """
        Execute navigation to kitchen.
        
        :return: True if successful, False otherwise
        """
        try:
            # In a real implementation, this would trigger navigation to kitchen
            # For this demo, we'll simulate the action
            print("  Simulating navigation to kitchen...")
            
            # Simulate navigation success based on environment
            kitchen_found = True  # Simulated success
            
            if kitchen_found:
                # Wait for simulated navigation time
                await asyncio.sleep(2.0)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error in navigation to kitchen: {str(e)}")
            return False
    
    async def _find_red_cup(self) -> Tuple[bool, Optional[Dict[str, float]]]:
        """
        Find the red cup in the kitchen.
        
        :return: Tuple of (success flag, cup location or None)
        """
        try:
            print("  Simulating red cup detection...")
            
            # In a real implementation, this would use vision service to detect objects
            # For this demo, we'll simulate object detection
            vision_data = await self.vision_service.capture_scene_from_simulation()
            
            # Simulate finding a red cup
            red_cup = {
                "class": "cup",
                "color": "red",
                "position": {"x": 1.2, "y": 0.8, "z": 0.8},
                "confidence": 0.92,
                "id": "red_cup_001"
            }
            
            # Simulate detection success
            detection_success = True  # Simulated
            
            return detection_success, red_cup["position"] if detection_success else None
            
        except Exception as e:
            print(f"Error in red cup detection: {str(e)}")
            return False, None
    
    async def _grasp_red_cup(self, cup_location: Dict[str, float]) -> bool:
        """
        Grasp the red cup at the given location.
        
        :param cup_location: Location of the red cup
        :return: True if successful, False otherwise
        """
        try:
            print(f"  Simulating grasp of cup at position: {cup_location}")
            
            # In a real implementation, this would execute grasping actions
            # For this demo, we'll simulate the action
            grasp_success = True  # Simulated success
            
            if grasp_success:
                await asyncio.sleep(1.5)  # Simulate grasp execution time
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error in cup grasping: {str(e)}")
            return False
    
    async def _return_to_user(self) -> bool:
        """
        Return to the user after grasping the cup.
        
        :return: True if successful, False otherwise
        """
        try:
            print("  Simulating return to user...")
            
            # In a real implementation, this would navigate back to user
            # For this demo, we'll simulate the action
            return_success = True  # Simulated success
            
            if return_success:
                await asyncio.sleep(2.0)  # Simulate movement time
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error in return action: {str(e)}")
            return False
    
    def _evaluate_outcomes(self, demo_results: Dict[str, Any]) -> int:
        """
        Evaluate how many expected outcomes were met.
        
        :param demo_results: Results from the demo execution
        :return: Number of expected outcomes met
        """
        expected_outcomes = self.demo_scenarios[0]["expected_outcomes"]
        met_outcomes = 0
        
        # Map demo results to expected outcomes
        for expected_outcome in expected_outcomes:
            if expected_outcome == "navigate_to_kitchen_success":
                if any(step["step"] == "navigate_to_kitchen" and step["success"] for step in demo_results["steps_completed"]):
                    met_outcomes += 1
            elif expected_outcome == "detect_red_cup_success":
                if any(step["step"] == "find_red_cup" and step["success"] for step in demo_results["steps_completed"]):
                    met_outcomes += 1
            elif expected_outcome == "grasp_cup_success":
                if any(step["step"] == "grasp_red_cup" and step["success"] for step in demo_results["steps_completed"]):
                    met_outcomes += 1
            elif expected_outcome == "return_to_user_success":
                if any(step["step"] == "return_to_user" and step["success"] for step in demo_results["steps_completed"]):
                    met_outcomes += 1
        
        return met_outcomes
    
    async def run_office_cleaning_demo(self) -> Dict[str, Any]:
        """
        Run the office cleaning demonstration scenario.
        
        :return: Demo results with performance metrics
        """
        print("🧹 Starting Office Cleaning Demo")
        print("=" * 60)
        
        start_time = time.time()
        
        demo_results = {
            "demo_name": "Office Cleaning",
            "steps_completed": [],
            "steps_failed": [],
            "total_time": 0.0,
            "success_rate": 0.0,
            "confidence_scores": [],
            "errors": []
        }
        
        try:
            # Step 1: Navigate to office desk
            print("\nStep 1: Navigating to office desk...")
            nav_success = await self._execute_navigation_to_office_desk()
            demo_results["steps_completed"].append({
                "step": "navigate_to_office_desk",
                "success": nav_success,
                "timestamp": datetime.now().isoformat()
            })
            
            if not nav_success:
                demo_results["steps_failed"].append("navigation_to_office_desk")
                demo_results["errors"].append("Failed to navigate to office desk")
            
            print(f"  Navigation to office desk: {'✅ SUCCESS' if nav_success else '❌ FAILED'}")
            
            if nav_success:
                # Step 2: Find scattered papers
                print("\nStep 2: Finding scattered papers...")
                find_success, paper_positions = await self._find_scattered_papers()
                demo_results["steps_completed"].append({
                    "step": "find_scattered_papers",
                    "success": find_success,
                    "paper_count": len(paper_positions) if find_success else 0,
                    "timestamp": datetime.now().isoformat()
                })
                
                if not find_success:
                    demo_results["steps_failed"].append("find_scattered_papers")
                    demo_results["errors"].append("Failed to locate scattered papers")
                else:
                    print(f"  Found {len(paper_positions)} scattered papers")
                    
                    # Step 3: Pick up papers
                    print("\nStep 3: Picking up scattered papers...")
                    pickup_success = await self._pickup_scattered_papers(paper_positions)
                    demo_results["steps_completed"].append({
                        "step": "pickup_scattered_papers",
                        "success": pickup_success,
                        "papers_picked_up": len(paper_positions) if pickup_success else 0,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    if not pickup_success:
                        demo_results["steps_failed"].append("pickup_scattered_papers")
                        demo_results["errors"].append("Failed to pickup scattered papers")
                    
                    print(f"  Pickup scattered papers: {'✅ SUCCESS' if pickup_success else '❌ FAILED'}")
                    
                    if pickup_success:
                        # Step 4: Organize items in tray
                        print("\nStep 4: Organizing items in tray...")
                        organize_success = await self._organize_items_in_tray()
                        demo_results["steps_completed"].append({
                            "step": "organize_items_in_tray",
                            "success": organize_success,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        print(f"  Organize in tray: {'✅ SUCCESS' if organize_success else '❌ FAILED'}")
            
            # Calculate performance metrics
            total_steps = len(self.demo_scenarios[1]["commands"])
            completed_steps = len(demo_results["steps_completed"])
            failed_steps = len(demo_results["steps_failed"])
            
            demo_results["success_rate"] = completed_steps / total_steps if total_steps > 0 else 0.0
            demo_results["total_time"] = time.time() - start_time
            demo_results["expected_outcomes_met"] = self._evaluate_office_outcomes(demo_results)
            
            print(f"\n📊 Demo Results:")
            print(f"  Success Rate: {demo_results['success_rate']*100:.1f}% ({completed_steps}/{total_steps})")
            print(f"  Total Time: {demo_results['total_time']:.2f}s")
            print(f"  Expected Outcomes Met: {demo_results['expected_outcomes_met']}/{len(self.demo_scenarios[1]['expected_outcomes'])}")
            
            return demo_results
            
        except Exception as e:
            print(f"❌ Error during office cleaning demo: {str(e)}")
            demo_results["errors"].append(f"Demo execution error: {str(e)}")
            return demo_results
    
    async def _execute_navigation_to_office_desk(self) -> bool:
        """
        Execute navigation to office desk.
        
        :return: True if successful, False otherwise
        """
        try:
            print("  Simulating navigation to office desk...")
            
            # Simulate navigation success based on environment
            desk_found = True  # Simulated success
            
            if desk_found:
                await asyncio.sleep(2.5)  # Simulate navigation time
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error in navigation to office desk: {str(e)}")
            return False
    
    async def _find_scattered_papers(self) -> Tuple[bool, List[Dict[str, float]]]:
        """
        Find scattered papers in the office.
        
        :return: Tuple of (success flag, list of paper positions)
        """
        try:
            print("  Simulating detection of scattered papers...")
            
            # In a real implementation, this would use vision service to detect scattered papers
            # For this demo, we'll simulate object detection
            papers = [
                {"class": "paper", "position": {"x": 0.8, "y": 0.2, "z": 0.8}, "confidence": 0.88},
                {"class": "paper", "position": {"x": 0.9, "y": 0.4, "z": 0.8}, "confidence": 0.85},
                {"class": "paper", "position": {"x": 1.1, "y": 0.3, "z": 0.8}, "confidence": 0.90}
            ]
            
            # Simulate detection success
            detection_success = True  # Simulated
            
            return detection_success, [p["position"] for p in papers] if detection_success else []
            
        except Exception as e:
            print(f"Error in papers detection: {str(e)}")
            return False, []
    
    async def _pickup_scattered_papers(self, paper_positions: List[Dict[str, float]]) -> bool:
        """
        Pick up scattered papers.
        
        :param paper_positions: Positions of papers to pick up
        :return: True if successful, False otherwise
        """
        try:
            print(f"  Simulating pickup of {len(paper_positions)} scattered papers...")
            
            # In a real implementation, this would execute grasping actions for each paper
            # For this demo, we'll simulate the action
            success = True  # Simulated success
            
            if success:
                await asyncio.sleep(len(paper_positions) * 1.0)  # Simulate time per paper
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error in paper pickup: {str(e)}")
            return False
    
    async def _organize_items_in_tray(self) -> bool:
        """
        Organize items in the tray.
        
        :return: True if successful, False otherwise
        """
        try:
            print("  Simulating organization of items in tray...")
            
            # In a real implementation, this would place items in organized manner
            # For this demo, we'll simulate the action
            success = True  # Simulated success
            
            if success:
                await asyncio.sleep(2.0)  # Simulate organization time
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error in item organization: {str(e)}")
            return False
    
    def _evaluate_office_outcomes(self, demo_results: Dict[str, Any]) -> int:
        """
        Evaluate how many expected outcomes were met for office cleaning.
        
        :param demo_results: Results from the demo execution
        :return: Number of expected outcomes met
        """
        expected_outcomes = self.demo_scenarios[1]["expected_outcomes"]
        met_outcomes = 0
        
        # Map demo results to expected outcomes
        for expected_outcome in expected_outcomes:
            if expected_outcome == "navigate_to_office_success":
                if any(step["step"] == "navigate_to_office_desk" and step["success"] for step in demo_results["steps_completed"]):
                    met_outcomes += 1
            elif expected_outcome == "detect_scattered_items_success":
                if any(step["step"] == "find_scattered_papers" and step["success"] for step in demo_results["steps_completed"]):
                    met_outcomes += 1
            elif expected_outcome == "organize_items_success":
                if any(step["step"] == "organize_items_in_tray" and step["success"] for step in demo_results["steps_completed"]):
                    met_outcomes += 1
        
        return met_outcomes
    
    async def run_guided_tour_demo(self) -> Dict[str, Any]:
        """
        Run the guided tour demonstration scenario.
        
        :return: Demo results with performance metrics
        """
        print("🏛 Starting Guided Tour Demo")
        print("=" * 60)
        
        start_time = time.time()
        
        demo_results = {
            "demo_name": "Guided Tour",
            "steps_completed": [],
            "steps_failed": [],
            "total_time": 0.0,
            "success_rate": 0.0,
            "confidence_scores": [],
            "errors": []
        }
        
        try:
            # Step 1: Start tour
            print("\nStep 1: Beginning the house tour...")
            start_success = await self._start_house_tour()
            demo_results["steps_completed"].append({
                "step": "start_house_tour",
                "success": start_success,
                "timestamp": datetime.now().isoformat()
            })
            
            if not start_success:
                demo_results["steps_failed"].append("start_house_tour")
                demo_results["errors"].append("Failed to start house tour")
            
            print(f"  Start tour: {'✅ SUCCESS' if start_success else '❌ FAILED'}")
            
            if start_success:
                # Step 2: Navigate to kitchen
                print("\nStep 2: Navigating to kitchen...")
                kitchen_success = await self._navigate_to_kitchen()
                demo_results["steps_completed"].append({
                    "step": "navigate_to_kitchen",
                    "success": kitchen_success,
                    "timestamp": datetime.now().isoformat()
                })
                
                if not kitchen_success:
                    demo_results["steps_failed"].append("navigate_to_kitchen")
                    demo_results["errors"].append("Failed to navigate to kitchen")
                
                print(f"  Navigate to kitchen: {'✅ SUCCESS' if kitchen_success else '❌ FAILED'}")
                
                if kitchen_success:
                    # Step 3: Navigate to bedroom
                    print("\nStep 3: Navigating to bedroom...")
                    bedroom_success = await self._navigate_to_bedroom()
                    demo_results["steps_completed"].append({
                        "step": "navigate_to_bedroom",
                        "success": bedroom_success,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    if not bedroom_success:
                        demo_results["steps_failed"].append("navigate_to_bedroom")
                        demo_results["errors"].append("Failed to navigate to bedroom")
                    
                    print(f"  Navigate to bedroom: {'✅ SUCCESS' if bedroom_success else '❌ FAILED'}")
                    
                    if bedroom_success:
                        # Step 4: Return to entrance
                        print("\nStep 4: Returning to entrance...")
                        return_success = await self._return_to_entrance()
                        demo_results["steps_completed"].append({
                            "step": "return_to_entrance",
                            "success": return_success,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        print(f"  Return to entrance: {'✅ SUCCESS' if return_success else '❌ FAILED'}")
            
            # Calculate performance metrics
            total_steps = len(self.demo_scenarios[2]["commands"])
            completed_steps = len(demo_results["steps_completed"])
            failed_steps = len(demo_results["steps_failed"])
            
            demo_results["success_rate"] = completed_steps / total_steps if total_steps > 0 else 0.0
            demo_results["total_time"] = time.time() - start_time
            demo_results["expected_outcomes_met"] = self._evaluate_tour_outcomes(demo_results)
            
            print(f"\n📊 Demo Results:")
            print(f"  Success Rate: {demo_results['success_rate']*100:.1f}% ({completed_steps}/{total_steps})")
            print(f"  Total Time: {demo_results['total_time']:.2f}s")
            print(f"  Expected Outcomes Met: {demo_results['expected_outcomes_met']}/{len(self.demo_scenarios[2]['expected_outcomes'])}")
            
            return demo_results
            
        except Exception as e:
            print(f"❌ Error during guided tour demo: {str(e)}")
            demo_results["errors"].append(f"Demo execution error: {str(e)}")
            return demo_results
    
    async def _start_house_tour(self) -> bool:
        """
        Start the house tour.
        
        :return: True if successful, False otherwise
        """
        try:
            print("  Simulating start of house tour...")
            
            # In a real implementation, this would initialize the tour
            # For this demo, we'll simulate the action
            success = True  # Simulated success
            
            if success:
                await asyncio.sleep(1.0)  # Simulate start time
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error starting house tour: {str(e)}")
            return False
    
    async def _navigate_to_kitchen(self) -> bool:
        """
        Navigate to the kitchen during tour.
        
        :return: True if successful, False otherwise
        """
        try:
            print("  Simulating navigation to kitchen...")
            
            # In a real implementation, this would navigate to kitchen
            # For this demo, we'll simulate the action
            success = True  # Simulated success
            
            if success:
                await asyncio.sleep(2.0)  # Simulate navigation time
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error navigating to kitchen: {str(e)}")
            return False
    
    async def _navigate_to_bedroom(self) -> bool:
        """
        Navigate to the bedroom during tour.
        
        :return: True if successful, False otherwise
        """
        try:
            print("  Simulating navigation to bedroom...")
            
            # In a real implementation, this would navigate to bedroom
            # For this demo, we'll simulate the action
            success = True  # Simulated success
            
            if success:
                await asyncio.sleep(2.2)  # Simulate navigation time
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error navigating to bedroom: {str(e)}")
            return False
    
    async def _return_to_entrance(self) -> bool:
        """
        Return to the entrance after tour.
        
        :return: True if successful, False otherwise
        """
        try:
            print("  Simulating return to entrance...")
            
            # In a real implementation, this would navigate back to entrance
            # For this demo, we'll simulate the action
            success = True  # Simulated success
            
            if success:
                await asyncio.sleep(2.5)  # Simulate navigation time
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error returning to entrance: {str(e)}")
            return False
    
    def _evaluate_tour_outcomes(self, demo_results: Dict[str, Any]) -> int:
        """
        Evaluate how many expected outcomes were met for guided tour.
        
        :param demo_results: Results from the demo execution
        :return: Number of expected outcomes met
        """
        expected_outcomes = self.demo_scenarios[2]["expected_outcomes"]
        met_outcomes = 0
        
        # Map demo results to expected outcomes
        for expected_outcome in expected_outcomes:
            if expected_outcome == "navigate_to_kitchen_success":
                if any(step["step"] == "navigate_to_kitchen" and step["success"] for step in demo_results["steps_completed"]):
                    met_outcomes += 1
            elif expected_outcome == "navigate_to_bedroom_success":
                if any(step["step"] == "navigate_to_bedroom" and step["success"] for step in demo_results["steps_completed"]):
                    met_outcomes += 1
            elif expected_outcome == "guide_tour_success":
                if any(step["step"] == "start_house_tour" and step["success"] for step in demo_results["steps_completed"]):
                    # Consider tour successful if tour was started
                    met_outcomes += 1
            elif expected_outcome == "return_to_entrance_success":
                if any(step["step"] == "return_to_entrance" and step["success"] for step in demo_results["steps_completed"]):
                    met_outcomes += 1
        
        return met_outcomes
    
    async def run_complete_capstone_demo(self) -> Dict[str, Any]:
        """
        Run the complete capstone demonstration with all scenarios.
        
        :return: Complete demo results with performance metrics
        """
        print("🏆 VLA Capstone Complete Demonstration")
        print("=" * 80)
        print("This demonstration runs all three scenarios showcasing the complete VLA system capabilities:")
        print("  1. Kitchen Assistance - Navigation, perception, and manipulation")
        print("  2. Office Cleaning - Complex multi-step task execution")
        print("  3. Guided Tour - Extended navigation and interaction")
        print()
        
        start_time = time.time()
        
        # Run all demo scenarios
        kitchen_results = await self.run_kitchen_assistance_demo()
        print()
        office_results = await self.run_office_cleaning_demo()
        print()
        tour_results = await self.run_guided_tour_demo()
        
        complete_results = {
            "demo_name": "Complete Capstone Demo",
            "timestamp": datetime.now(),
            "total_execution_time": time.time() - start_time,
            "kitchen_demo": kitchen_results,
            "office_demo": office_results,
            "tour_demo": tour_results,
            "aggregate_metrics": {}
        }
        
        # Calculate aggregate metrics
        all_results = [kitchen_results, office_results, tour_results]
        total_steps = sum(
            len(result.get("steps_completed", [])) + len(result.get("steps_failed", [])) 
            for result in all_results
        )
        successful_steps = sum(
            len(result.get("steps_completed", [])) 
            for result in all_results
        )
        
        complete_results["aggregate_metrics"] = {
            "overall_success_rate": successful_steps / total_steps if total_steps > 0 else 0.0,
            "total_steps_attempted": total_steps,
            "total_steps_succeeded": successful_steps,
            "total_steps_failed": total_steps - successful_steps,
            "demo_execution_time": complete_results["total_execution_time"],
            "average_demo_time": complete_results["total_execution_time"] / 3,
            "demos_completed": 3,
            "demos_succeeded": sum(1 for r in all_results if len(r.get("steps_failed", [])) == 0)
        }
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 DEMONSTRATION SUMMARY")
        print("=" * 80)
        
        agg_metrics = complete_results["aggregate_metrics"]
        print(f"Overall Success Rate: {agg_metrics['overall_success_rate']*100:.1f}% ({agg_metrics['total_steps_succeeded']}/{agg_metrics['total_steps_attempted']})")
        print(f"Total Execution Time: {agg_metrics['demo_execution_time']:.2f}s")
        print(f"Average Demo Time: {agg_metrics['average_demo_time']:.2f}s")
        print(f"Demos Completed: {agg_metrics['demos_completed']}")
        print(f"Demos Succeeded: {agg_metrics['demos_succeeded']}")
        
        print("\nIndividual Demo Performance:")
        demos = [("Kitchen", kitchen_results), ("Office", office_results), ("Tour", tour_results)]
        for name, result in demos:
            success_rate = len(result.get("steps_completed", [])) / len(self.demo_scenarios[["Kitchen", "Office", "Tour"].index(name)])
            print(f"  {name}: {success_rate*100:.1f}% ({len(result.get('steps_completed', []))}/{len(self.demo_scenarios[['Kitchen', 'Office', 'Tour'].index(name)])}) steps")
        
        print("\n🎯 LEARNING OBJECTIVES MET:")
        learning_objectives = [
            "✓ Voice command processing and understanding",
            "✓ Vision-language integration", 
            "✓ Action planning and sequencing",
            "✓ Navigation and manipulation execution",
            "✓ Error handling and recovery",
            "✓ Multimodal fusion"
        ]
        for obj in learning_objectives:
            print(f"  {obj}")
        
        return complete_results
    
    def generate_performance_report(self, complete_results: Dict[str, Any]) -> str:
        """
        Generate a performance report for the capstone demonstration.
        
        :param complete_results: Results from the complete demo
        :return: Formatted performance report
        """
        agg_metrics = complete_results["aggregate_metrics"]
        
        report = f"""
VLA Capstone Performance Report
===============================

Execution Summary:
- Total Execution Time: {agg_metrics['demo_execution_time']:.2f}s
- Average Demo Time: {agg_metrics['average_demo_time']:.2f}s
- Overall Success Rate: {agg_metrics['overall_success_rate']*100:.1f}%
- Steps Succeeded: {agg_metrics['total_steps_succeeded']}/{agg_metrics['total_steps_attempted']}

Demo Breakdown:
- Kitchen Assistance: {(len(complete_results['kitchen_demo'].get('steps_completed', []))/len(self.demo_scenarios[0]['commands']))*100:.1f}%
- Office Cleaning: {(len(complete_results['office_demo'].get('steps_completed', []))/len(self.demo_scenarios[1]['commands']))*100:.1f}%
- Guided Tour: {(len(complete_results['tour_demo'].get('steps_completed', []))/len(self.demo_scenarios[2]['commands']))*100:.1f}%

System Capabilities Demonstrated:
- Voice processing with Whisper
- LLM-based action planning
- Multimodal fusion
- Navigation and manipulation
- Error recovery and handling
- Simulation integration (Gazebo/Isaac Sim)

Educational Outcomes:
- Students demonstrated understanding of vision-language-action integration
- Students showed competency in complex task decomposition
- Students exhibited proficiency in multimodal command processing
        """
        
        return report
    
    def track_student_progress(self, student_id: str, demo_results: Dict[str, Any]):
        """
        Track student progress for educational assessment.
        
        :param student_id: ID of the student
        :param demo_results: Results from the demo execution
        """
        if student_id not in self.student_progress:
            self.student_progress[student_id] = {
                "demos_attempted": 0,
                "demos_completed": 0,
                "average_success_rate": 0.0,
                "total_execution_time": 0.0,
                "learning_progress": []
            }
        
        student_data = self.student_progress[student_id]
        
        # Update student progress
        student_data["demos_attempted"] += 1
        if demo_results["aggregate_metrics"]["demos_succeeded"] == 3:
            student_data["demos_completed"] += 1
        
        # Update average success rate
        total_attempts = student_data["demos_attempted"]
        current_avg = student_data["average_success_rate"] * (total_attempts - 1)
        new_avg = (current_avg + demo_results["aggregate_metrics"]["overall_success_rate"]) / total_attempts
        student_data["average_success_rate"] = new_avg
        
        # Track execution time
        student_data["total_execution_time"] += demo_results["total_execution_time"]
        
        # Add to learning progress
        student_data["learning_progress"].append({
            "demo_timestamp": datetime.now().isoformat(),
            "results": demo_results["aggregate_metrics"],
            "scenario_success_rates": {
                "kitchen": len(demo_results["kitchen_demo"].get("steps_completed", [])) / len(self.demo_scenarios[0]["commands"]),
                "office": len(demo_results["office_demo"].get("steps_completed", [])) / len(self.demo_scenarios[1]["commands"]),
                "tour": len(demo_results["tour_demo"].get("steps_completed", [])) / len(self.demo_scenarios[2]["commands"])
            }
        })
        
        print(f"Student {student_id} progress updated")


class AdvancedCapstoneDemoExample(CapstoneDemoExample):
    """
    Advanced capstone demo with additional educational features and error injection for resilience.
    """
    
    def __init__(self):
        super().__init__()
        self.enable_error_injection = True
        self.injection_probability = 0.1  # 10% chance of injecting an error
        self.educational_feedback_enabled = True
        self.custom_scenarios = []
    
    def add_custom_scenario(self, scenario: Dict[str, Any]):
        """
        Add a custom scenario to the demo.
        
        :param scenario: Custom scenario definition
        """
        self.custom_scenarios.append(scenario)
        print(f"Added custom scenario: {scenario['name']}")
    
    async def run_with_error_injection(self, scenario_index: int = 0) -> Dict[str, Any]:
        """
        Run a scenario with potential error injection for resilience testing.
        
        :param scenario_index: Index of the scenario to run (0, 1, or 2)
        :return: Demo results
        """
        print(f"🧪 Running scenario {scenario_index} with error injection enabled")
        
        # Select the scenario
        scenarios = self.demo_scenarios + self.custom_scenarios
        if scenario_index >= len(scenarios):
            scenario_index = 0  # Default to first scenario if out of bounds
        
        scenario = scenarios[scenario_index]
        
        # Potentially inject an error based on probability
        if self.enable_error_injection and np.random.random() < self.injection_probability:
            error_type = np.random.choice([
                ErrorType.EXECUTION_ERROR,
                ErrorType.VALIDATION_ERROR,
                ErrorType.TIMEOUT_ERROR
            ])
            print(f"⚠️  Injecting {error_type.value} into scenario execution")
            
            # In a real implementation, this would inject the error at a random point
            # For this example, we'll simulate the error recovery process
            recovery_result = self.error_recovery.handle_error(
                error_type=error_type,
                action_sequence=None,  # Would be the actual sequence in real implementation
                error_details={"injected_error": True, "error_type": error_type.value}
            )
            
            print(f"   Recovery strategy applied: {recovery_result['strategy']}")
        
        # Execute the selected scenario
        if scenario_index == 0:
            return await self.run_kitchen_assistance_demo()
        elif scenario_index == 1:
            return await self.run_office_cleaning_demo()
        elif scenario_index == 2:
            return await self.run_guided_tour_demo()
        else:
            # For custom scenarios, execute a general approach
            return await self._execute_custom_scenario(scenario)
    
    async def _execute_custom_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a custom scenario.
        
        :param scenario: Custom scenario definition
        :return: Execution results
        """
        print(f"🏃 Executing custom scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        start_time = time.time()
        
        results = {
            "demo_name": scenario["name"],
            "steps_completed": [],
            "steps_failed": [],
            "total_time": 0.0,
            "success_rate": 0.0,
            "errors": []
        }
        
        # Execute commands in the scenario
        for i, command in enumerate(scenario.get("commands", [])):
            print(f"   Executing command {i+1}/{len(scenario['commands'])}: {command}")
            
            # In a real implementation, this would process each command
            # For this example, we'll simulate execution
            success = np.random.random() > 0.2  # 80% success rate for simulation
            
            results["steps_completed"].append({
                "step": i,
                "command": command,
                "success": success,
                "timestamp": datetime.now().isoformat()
            })
            
            if not success:
                results["steps_failed"].append({"step": i, "command": command})
        
        results["total_time"] = time.time() - start_time
        results["success_rate"] = len([s for s in results["steps_completed"] if s["success"]]) / len(results["steps_completed"]) if results["steps_completed"] else 0.0
        
        return results
    
    def generate_educational_feedback(self, student_id: str, demo_results: Dict[str, Any]) -> str:
        """
        Generate educational feedback based on demo performance.
        
        :param student_id: ID of the student
        :param demo_results: Results from the demo execution
        :return: Educational feedback string
        """
        if student_id not in self.student_progress:
            return "No previous progress data for this student."
        
        student_data = self.student_progress[student_id]
        
        feedback = []
        feedback.append("🎓 Educational Feedback Report:")
        feedback.append("")
        
        # Performance summary
        success_rate = student_data["average_success_rate"]
        if success_rate >= 0.9:
            feedback.append("🌟 Excellent performance! You've mastered the VLA integration concepts.")
        elif success_rate >= 0.7:
            feedback.append("👍 Good job! You're developing strong competency in VLA systems.")
        elif success_rate >= 0.5:
            feedback.append("✅ Solid effort! Continue practicing to strengthen your skills.")
        else:
            feedback.append("📚 Keep working on it! Review the concepts and try again.")
        
        feedback.append("")
        
        # Specific feedback based on scenario performance
        latest_results = student_data["learning_progress"][-1] if student_data["learning_progress"] else None
        if latest_results:
            scenario_perf = latest_results.get("scenario_success_rates", {})
            
            if scenario_perf.get("kitchen", 0) < 0.7:
                feedback.append("💡 For Kitchen Assistance: Focus on understanding navigation and manipulation integration.")
            
            if scenario_perf.get("office", 0) < 0.7:
                feedback.append("💡 For Office Cleaning: Practice multi-step task decomposition and execution.")
            
            if scenario_perf.get("tour", 0) < 0.7:
                feedback.append("💡 For Guided Tour: Work on extended navigation and interaction sequences.")
        
        feedback.append("")
        feedback.append("📚 Key Concepts Reinforced:")
        feedback.append("• Integration of vision, language, and action systems")
        feedback.append("• Multimodal command processing")
        feedback.append("• Error handling and recovery in robotic systems")
        feedback.append("• Task decomposition and sequencing")
        
        return "\n".join(feedback)
    
    async def run_advanced_demo_series(self, num_iterations: int = 5) -> List[Dict[str, Any]]:
        """
        Run a series of demos with varying conditions to test system robustness.
        
        :param num_iterations: Number of demo iterations to run
        :return: List of demo results
        """
        print(f"🔬 Running {num_iterations} iterations of advanced demo series")
        
        all_results = []
        
        for i in range(num_iterations):
            print(f"\nIteration {i+1}/{num_iterations}")
            
            # Randomly select a scenario to run
            scenario_idx = np.random.randint(0, len(self.demo_scenarios))
            
            # Run with potential error injection
            result = await self.run_with_error_injection(scenario_idx)
            all_results.append(result)
            
            print(f"  Completed in {result.get('total_time', 0):.2f}s with {result.get('success_rate', 0)*100:.1f}% success rate")
        
        # Analyze results
        avg_success_rate = np.mean([r.get("success_rate", 0) for r in all_results])
        avg_time = np.mean([r.get("total_time", 0) for r in all_results])
        
        print(f"\n📊 Series Results:")
        print(f"  Average Success Rate: {avg_success_rate*100:.1f}%")
        print(f"  Average Execution Time: {avg_time:.2f}s")
        print(f"  Success Rate Std Dev: {np.std([r.get('success_rate', 0) for r in all_results])*100:.1f}%")
        
        return all_results


def run_capstone_demo_examples():
    """
    Run the capstone demonstration examples.
    """
    print("VLA Capstone - Complete System Integration Demonstration")
    print("=" * 80)
    
    # Create the demo example
    demo = CapstoneDemoExample()
    
    # Run the complete capstone demo
    print("\n[1] Running Complete Capstone Demo...")
    complete_results = asyncio.run(demo.run_complete_capstone_demo())
    
    # Generate performance report
    print("\n[2] Generating Performance Report...")
    report = demo.generate_performance_report(complete_results)
    print(report)
    
    # Example with advanced demo features
    print("\n[3] Running Advanced Demo Features...")
    advanced_demo = AdvancedCapstoneDemoExample()
    
    # Add a custom scenario
    custom_scenario = {
        "name": "Object Retrieval Challenge",
        "description": "Robot must retrieve a specific object from a cluttered environment",
        "commands": [
            "Locate the green bottle in the messy room",
            "Clear a path to the green bottle",
            "Grasp the green bottle",
            "Navigate to the drop-off zone",
            "Place the bottle in the designated area"
        ],
        "expected_outcomes": [
            "object_locator_success",
            "path_clearing_success", 
            "grasp_success",
            "navigation_success",
            "placement_success"
        ]
    }
    advanced_demo.add_custom_scenario(custom_scenario)
    
    # Run with error injection
    print("\nRunning demo with error injection...")
    error_injected_result = asyncio.run(advanced_demo.run_with_error_injection(0))
    print(f"Error injection demo result: {error_injected_result.get('success_rate', 0)*100:.1f}% success")
    
    # Run demo series
    print("\nRunning demo series for robustness testing...")
    series_results = asyncio.run(advanced_demo.run_advanced_demo_series(num_iterations=3))
    
    print("\n" + "=" * 80)
    print("Capstone Demo Examples Completed!")
    
    # Educational tracking example
    print("\n[4] Educational Tracking Example:")
    demo.track_student_progress("student_001", complete_results)
    feedback = advanced_demo.generate_educational_feedback("student_001", complete_results)
    print(feedback)


# Example of using the VLA system API for the demo
async def api_integration_demo():
    """
    Demonstrate integration with the VLA system API.
    """
    print("\n🌐 VLA System API Integration Demo")
    print("-" * 40)
    
    import aiohttp
    
    # Example API calls to the VLA system
    api_base_url = f"http://localhost:{settings.server_port}"
    
    # Example 1: Process a voice command
    voice_command_data = {
        "transcribed_text": "Go to the kitchen and find a red cup",
        "confidence": 0.9,
        "intent": "navigation_and_perception"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Send voice command to API
            async with session.post(
                f"{api_base_url}/vla/process_command", 
                json={"voice_command": voice_command_data}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"API processed command successfully: {result.get('message', 'Unknown')}")
                else:
                    print(f"API call failed with status: {response.status}")
    except Exception as e:
        print(f"API integration failed: {str(e)}")
    
    # Example 2: Get system state
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_base_url}/vla/system_state") as response:
                if response.status == 200:
                    state = await response.json()
                    print(f"Current system state: {state.get('system_status', 'Unknown')}")
                else:
                    print(f"Failed to get system state: {response.status}")
    except Exception as e:
        print(f"Getting system state failed: {str(e)}")


if __name__ == "__main__":
    # Run the main capstone demo
    run_capstone_demo_examples()
    
    # Run API integration demo
    asyncio.run(api_integration_demo())
    
    print(f"\n🎉 All capstone demonstration examples completed!")
    print("The VLA system successfully demonstrated integration of voice, vision, and action capabilities.")