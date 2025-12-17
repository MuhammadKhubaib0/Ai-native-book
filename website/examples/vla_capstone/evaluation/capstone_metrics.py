"""
Evaluation metrics for the VLA Capstone project.
"""
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import json
import statistics
from enum import Enum


class MetricCategory(Enum):
    """Categories of evaluation metrics."""
    PERFORMANCE = "performance"
    ACCURACY = "accuracy"
    RELIABILITY = "reliability"
    EFFICIENCY = "efficiency"
    SAFETY = "safety"
    USABILITY = "usability"
    LEARNING = "learning"


@dataclass
class EvaluationResult:
    """Result of a single evaluation trial."""
    trial_id: str
    timestamp: datetime
    success: bool
    completion_time: float
    steps_completed: int
    steps_total: int
    errors: List[str]
    metrics: Dict[str, float]
    details: Dict[str, Any]


class CapstoneMetricsEvaluator:
    """
    Evaluator for calculating various metrics for the VLA Capstone project.
    """
    
    def __init__(self):
        """Initialize the metrics evaluator."""
        self.trial_results: List[EvaluationResult] = []
        self.metrics_history: Dict[str, List[float]] = {}
        
        # Define metric weights for weighted scoring
        self.metric_weights = {
            "task_completion_rate": 0.25,
            "accuracy": 0.20,
            "efficiency": 0.15,
            "reliability": 0.20,
            "safety": 0.10,
            "adaptability": 0.10
        }
    
    def record_trial_result(
        self,
        trial_id: str,
        success: bool,
        completion_time: float,
        steps_completed: int,
        steps_total: int,
        errors: List[str] = None,
        metrics: Dict[str, float] = None,
        details: Dict[str, Any] = None
    ) -> EvaluationResult:
        """
        Record the result of a single trial.
        
        :param trial_id: Unique identifier for the trial
        :param success: Whether the trial was successful
        :param completion_time: Time taken to complete the trial (seconds)
        :param steps_completed: Number of steps successfully completed
        :param steps_total: Total number of steps in the sequence
        :param errors: List of errors encountered during the trial
        :param metrics: Additional specific metrics for the trial
        :param details: Additional details about the trial
        :return: EvaluationResult object
        """
        if errors is None:
            errors = []
        if metrics is None:
            metrics = {}
        if details is None:
            details = {}
        
        result = EvaluationResult(
            trial_id=trial_id,
            timestamp=datetime.now(),
            success=success,
            completion_time=completion_time,
            steps_completed=steps_completed,
            steps_total=steps_total,
            errors=errors,
            metrics=metrics,
            details=details
        )
        
        self.trial_results.append(result)
        
        # Update metrics history
        for metric_name, value in result.metrics.items():
            if metric_name not in self.metrics_history:
                self.metrics_history[metric_name] = []
            self.metrics_history[metric_name].append(value)
        
        return result
    
    def calculate_task_completion_rate(self) -> float:
        """
        Calculate the overall task completion rate.
        
        :return: Task completion rate (0.0 to 1.0)
        """
        if not self.trial_results:
            return 0.0
        
        successful_trials = sum(1 for result in self.trial_results if result.success)
        return successful_trials / len(self.trial_results)
    
    def calculate_mean_completion_time(self) -> float:
        """
        Calculate the mean completion time across all trials.
        
        :return: Mean completion time in seconds
        """
        if not self.trial_results:
            return 0.0
        
        completion_times = [result.completion_time for result in self.trial_results]
        return sum(completion_times) / len(completion_times)
    
    def calculate_accuracy_metrics(self) -> Dict[str, float]:
        """
        Calculate accuracy metrics based on step completion.
        
        :return: Dictionary of accuracy metrics
        """
        if not self.trial_results:
            return {
                "step_completion_accuracy": 0.0,
                "mean_relative_accuracy": 0.0
            }
        
        total_steps = sum(result.steps_total for result in self.trial_results)
        total_completed = sum(result.steps_completed for result in self.trial_results)
        
        step_completion_accuracy = total_completed / total_steps if total_steps > 0 else 0.0
        
        # Calculate relative accuracy (completed steps / total steps) for each trial
        relative_accuracies = []
        for result in self.trial_results:
            if result.steps_total > 0:
                relative_accuracies.append(result.steps_completed / result.steps_total)
        
        mean_relative_accuracy = statistics.mean(relative_accuracies) if relative_accuracies else 0.0
        
        return {
            "step_completion_accuracy": step_completion_accuracy,
            "mean_relative_accuracy": mean_relative_accuracy
        }
    
    def calculate_efficiency_metrics(self) -> Dict[str, float]:
        """
        Calculate efficiency metrics such as speed and resource usage.
        
        :return: Dictionary of efficiency metrics
        """
        if not self.trial_results:
            return {
                "average_speed": 0.0,
                "efficiency_score": 0.0
            }
        
        # Calculate average task completion speed
        successful_trials = [tr for tr in self.trial_results if tr.success]
        if not successful_trials:
            return {
                "average_speed": 0.0,
                "efficiency_score": 0.0
            }
        
        speeds = []
        for trial in successful_trials:
            if trial.completion_time > 0:
                # Speed = steps completed / time taken
                speed = trial.steps_completed / trial.completion_time
                speeds.append(speed)
        
        average_speed = statistics.mean(speeds) if speeds else 0.0
        
        # Efficiency score based on speed and accuracy
        accuracy = self.calculate_accuracy_metrics()["mean_relative_accuracy"]
        efficiency_score = 0.6 * average_speed + 0.4 * accuracy if speeds else 0.0
        
        return {
            "average_speed": average_speed,
            "efficiency_score": efficiency_score
        }
    
    def calculate_reliability_metrics(self) -> Dict[str, float]:
        """
        Calculate reliability metrics including consistency and error rate.
        
        :return: Dictionary of reliability metrics
        """
        if not self.trial_results:
            return {
                "success_rate": 0.0,
                "error_rate": 0.0,
                "consistency_score": 0.0
            }
        
        total_trials = len(self.trial_results)
        successful_trials = sum(1 for result in self.trial_results if result.success)
        
        success_rate = successful_trials / total_trials if total_trials > 0 else 0.0
        error_rate = 1.0 - success_rate
        
        # Consistency score based on variance of performance metrics
        if self.metrics_history:
            metric_vars = []
            for metric_name, values in self.metrics_history.items():
                if len(values) > 1:
                    var = statistics.variance(values)
                    metric_vars.append(var)
            
            if metric_vars:
                # Lower variance means higher consistency
                consistency_score = 1.0 - min(1.0, statistics.mean(metric_vars))
            else:
                consistency_score = 0.5  # Neutral if no metrics to evaluate
        else:
            consistency_score = 0.5
        
        return {
            "success_rate": success_rate,
            "error_rate": error_rate,
            "consistency_score": consistency_score
        }
    
    def calculate_safety_metrics(self) -> Dict[str, float]:
        """
        Calculate safety-related metrics.
        
        :return: Dictionary of safety metrics
        """
        if not self.trial_results:
            return {
                "safety_incidents_rate": 0.0,
                "safety_score": 0.0
            }
        
        # For this simulation, we'll consider safety based on errors
        # In a real implementation, safety metrics would come from collision detection,
        # violation detection, etc.
        
        total_errors = sum(len(result.errors) for result in self.trial_results)
        total_trials = len(self.trial_results)
        
        # Calculate safety incidents rate (simplified)
        safety_incidents_rate = min(1.0, total_errors / max(total_trials, 1))
        
        # Safety score is inversely related to incidents
        safety_score = 1.0 - safety_incidents_rate
        
        return {
            "safety_incidents_rate": safety_incidents_rate,
            "safety_score": safety_score
        }
    
    def calculate_adaptability_metrics(self) -> Dict[str, float]:
        """
        Calculate adaptability metrics based on error recovery and flexibility.
        
        :return: Dictionary of adaptability metrics
        """
        if not self.trial_results:
            return {
                "recovery_success_rate": 0.0,
                "adaptability_score": 0.0
            }
        
        # For this implementation, adaptability is based on how well the system
        # handles errors and variability in task execution
        
        # Count trials that had errors but still succeeded (indicates adaptability)
        adaptable_trials = 0
        for result in self.trial_results:
            if result.success and result.errors:
                adaptable_trials += 1
        
        recovery_success_rate = adaptable_trials / len(self.trial_results) if self.trial_results else 0.0
        adaptability_score = recovery_success_rate  # Simplified model
        
        return {
            "recovery_success_rate": recovery_success_rate,
            "adaptability_score": adaptability_score
        }
    
    def calculate_comprehensive_score(self) -> float:
        """
        Calculate a comprehensive score using weighted metrics.
        
        :return: Comprehensive score (0.0 to 1.0)
        """
        metrics = self.get_all_metrics()
        
        # Calculate weighted score
        weighted_score = 0.0
        total_weight = sum(self.metric_weights.values())
        
        for metric_name, weight in self.metric_weights.items():
            if metric_name in metrics:
                normalized_value = metrics[metric_name]
                weighted_score += (normalized_value * weight) / total_weight
        
        return weighted_score
    
    def get_all_metrics(self) -> Dict[str, float]:
        """
        Get all calculated metrics.
        
        :return: Dictionary containing all metrics
        """
        metrics = {
            "task_completion_rate": self.calculate_task_completion_rate(),
            "mean_completion_time": self.calculate_mean_completion_time(),
            **self.calculate_accuracy_metrics(),
            **self.calculate_efficiency_metrics(),
            **self.calculate_reliability_metrics(),
            **self.calculate_safety_metrics(),
            **self.calculate_adaptability_metrics()
        }
        
        # Add comprehensive score
        metrics["comprehensive_score"] = self.calculate_comprehensive_score()
        
        return metrics
    
    def generate_evaluation_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive evaluation report.
        
        :return: Evaluation report dictionary
        """
        all_metrics = self.get_all_metrics()
        
        report = {
            "evaluation_summary": {
                "total_trials": len(self.trial_results),
                "date_generated": datetime.now().isoformat(),
                "metric_categories": [cat.value for cat in MetricCategory],
                "comprehensive_score": all_metrics.get("comprehensive_score", 0.0)
            },
            "performance_metrics": {
                "task_completion_rate": all_metrics.get("task_completion_rate", 0.0),
                "mean_completion_time": all_metrics.get("mean_completion_time", 0.0),
                "average_speed": all_metrics.get("average_speed", 0.0),
            },
            "accuracy_metrics": {
                "step_completion_accuracy": all_metrics.get("step_completion_accuracy", 0.0),
                "mean_relative_accuracy": all_metrics.get("mean_relative_accuracy", 0.0),
            },
            "reliability_metrics": {
                "success_rate": all_metrics.get("success_rate", 0.0),
                "error_rate": all_metrics.get("error_rate", 0.0),
                "consistency_score": all_metrics.get("consistency_score", 0.0),
            },
            "efficiency_metrics": {
                "efficiency_score": all_metrics.get("efficiency_score", 0.0),
            },
            "safety_metrics": {
                "safety_score": all_metrics.get("safety_score", 0.0),
                "safety_incidents_rate": all_metrics.get("safety_incidents_rate", 0.0),
            },
            "adaptability_metrics": {
                "adaptability_score": all_metrics.get("adaptability_score", 0.0),
                "recovery_success_rate": all_metrics.get("recovery_success_rate", 0.0),
            },
            "detailed_metrics": all_metrics,
            "recommendations": self._generate_recommendations(all_metrics)
        }
        
        return report
    
    def _generate_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """
        Generate recommendations based on the calculated metrics.
        
        :param metrics: Dictionary of calculated metrics
        :return: List of recommendations
        """
        recommendations = []
        
        if metrics.get("task_completion_rate", 0.0) < 0.8:
            recommendations.append(
                "Task completion rate is low. Consider improving action planning "
                "and error recovery mechanisms."
            )
        
        if metrics.get("mean_relative_accuracy", 0.0) < 0.7:
            recommendations.append(
                "Step completion accuracy is low. Review perception and action "
                "execution modules for potential improvements."
            )
        
        if metrics.get("success_rate", 0.0) < 0.8:
            recommendations.append(
                "Overall success rate is below target. Investigate common failure "
                "modes and implement additional safeguards."
            )
        
        if metrics.get("safety_score", 1.0) < 0.8:
            recommendations.append(
                "Safety score is concerning. Review collision avoidance and "
                "safety constraints implementation."
            )
        
        if metrics.get("comprehensive_score", 0.0) < 0.7:
            recommendations.append(
                "Comprehensive performance is below expectations. Consider "
                "iterating on system design and training."
            )
        elif metrics.get("comprehensive_score", 0.0) > 0.9:
            recommendations.append(
                "System performance is excellent. Consider applying learned "
                "techniques to more complex scenarios."
            )
        
        if not recommendations:
            recommendations.append("System performance is satisfactory.")
        
        return recommendations
    
    def get_trial_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get history of trial results.
        
        :param limit: Maximum number of results to return
        :return: List of trial results
        """
        results = []
        trials_to_return = self.trial_results[-limit:] if limit else self.trial_results
        
        for result in trials_to_return:
            results.append({
                "trial_id": result.trial_id,
                "timestamp": result.timestamp.isoformat(),
                "success": result.success,
                "completion_time": result.completion_time,
                "steps_completed": result.steps_completed,
                "steps_total": result.steps_total,
                "error_count": len(result.errors),
                "metrics": result.metrics,
                "details": result.details
            })
        
        return results
    
    def export_results(self, filepath: str):
        """
        Export evaluation results to a JSON file.
        
        :param filepath: Path to the output file
        """
        report = self.generate_evaluation_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
    
    def reset(self):
        """
        Reset the evaluator, clearing all recorded results.
        """
        self.trial_results = []
        self.metrics_history = {}


class EducationalMetricsEvaluator(CapstoneMetricsEvaluator):
    """
    Extended metrics evaluator with educational focus metrics.
    """
    
    def __init__(self):
        super().__init__()
        
        # Additional metrics for educational assessment
        self.educational_metrics = {
            "student_engagement": 0.0,
            "learning_progression": 0.0,
            "concept_mastery": 0.0,
            "application_transfer": 0.0
        }
    
    def calculate_educational_metrics(self) -> Dict[str, float]:
        """
        Calculate educational-focused metrics.
        
        :return: Dictionary of educational metrics
        """
        if not self.trial_results:
            return {
                "student_engagement": 0.0,
                "learning_progression": 0.0,
                "concept_mastery": 0.0,
                "application_transfer": 0.0
            }
        
        # For this example, we'll simulate educational metrics based on performance
        # In a real implementation, these would come from student interaction data
        
        performance_score = self.calculate_comprehensive_score()
        
        # Engagement could be measured by completion rate of educational tasks
        engagement = self.calculate_task_completion_rate()
        
        # Learning progression based on improvement over time
        progression = self._calculate_learning_progression()
        
        # Mastery based on accuracy and consistency
        mastery = self.calculate_accuracy_metrics()["mean_relative_accuracy"]
        
        # Transfer based on performance across different scenarios
        transfer = self.calculate_adaptability_metrics()["recovery_success_rate"]
        
        educational_metrics = {
            "student_engagement": engagement,
            "learning_progression": progression,
            "concept_mastery": mastery,
            "application_transfer": transfer
        }
        
        # Update stored metrics
        self.educational_metrics = educational_metrics
        
        return educational_metrics
    
    def _calculate_learning_progression(self) -> float:
        """
        Calculate learning progression over time.
        
        :return: Learning progression score (0.0 to 1.0)
        """
        if len(self.trial_results) < 2:
            return 0.0
        
        # Calculate improvement from early trials to recent trials
        early_trials = self.trial_results[:max(1, len(self.trial_results)//2)]
        recent_trials = self.trial_results[len(self.trial_results)//2:]
        
        early_success_rate = sum(1 for t in early_trials if t.success) / len(early_trials)
        recent_success_rate = sum(1 for t in recent_trials if t.success) / len(recent_trials)
        
        # Calculate improvement score
        if early_success_rate == 0.0:
            # If early success rate is 0, use recent success rate as proxy for improvement
            improvement_score = recent_success_rate
        else:
            improvement_score = max(0.0, (recent_success_rate - early_success_rate) / early_success_rate)
        
        # Normalize to 0-1 scale
        return min(1.0, improvement_score)
    
    def get_educational_report(self) -> Dict[str, Any]:
        """
        Generate a report focused on educational outcomes.
        
        :return: Educational report dictionary
        """
        all_metrics = self.get_all_metrics()
        edu_metrics = self.calculate_educational_metrics()
        
        report = {
            "educational_outcomes": {
                "student_engagement": edu_metrics["student_engagement"],
                "learning_progression": edu_metrics["learning_progression"],
                "concept_mastery": edu_metrics["concept_mastery"],
                "application_transfer": edu_metrics["application_transfer"],
                "overall_education_score": (
                    edu_metrics["student_engagement"] * 0.2 +
                    edu_metrics["learning_progression"] * 0.3 +
                    edu_metrics["concept_mastery"] * 0.3 +
                    edu_metrics["application_transfer"] * 0.2
                )
            },
            "technical_performance": {
                "comprehensive_score": all_metrics.get("comprehensive_score", 0.0),
                "task_completion_rate": all_metrics.get("task_completion_rate", 0.0),
                "accuracy": all_metrics.get("mean_relative_accuracy", 0.0),
                "reliability": all_metrics.get("success_rate", 0.0)
            },
            "suggestions_for_improvement": self._generate_educational_suggestions(edu_metrics),
            "trial_performance_by_module": self._analyze_performance_by_module()
        }
        
        return report
    
    def _generate_educational_suggestions(self, edu_metrics: Dict[str, float]) -> List[str]:
        """
        Generate educational suggestions based on the calculated metrics.
        
        :param edu_metrics: Dictionary of educational metrics
        :return: List of educational suggestions
        """
        suggestions = []
        
        if edu_metrics["student_engagement"] < 0.7:
            suggestions.append(
                "Student engagement is low. Consider adding more interactive "
                "elements or gamification to improve participation."
            )
        
        if edu_metrics["learning_progression"] < 0.6:
            suggestions.append(
                "Learning progression is slow. Reconsider the curriculum pacing "
                "or add additional scaffolding for complex concepts."
            )
        
        if edu_metrics["concept_mastery"] < 0.75:
            suggestions.append(
                "Concept mastery is below expectations. Reinforce fundamental "
                "concepts before advancing to more complex topics."
            )
        
        if edu_metrics["application_transfer"] < 0.65:
            suggestions.append(
                "Students struggle to transfer knowledge to new scenarios. "
                "Include more varied examples and cross-application exercises."
            )
        
        return suggestions
    
    def _analyze_performance_by_module(self) -> Dict[str, Any]:
        """
        Analyze performance across different learning modules.
        
        :return: Performance analysis by module
        """
        # This would analyze performance by different VLA system components
        # For this simulation, we'll create sample analysis
        return {
            "voice_command_understanding": {
                "success_rate": 0.85,
                "common_errors": ["mishearing", "ambiguity"],
                "recommendations": ["improve audio preprocessing", "enhance disambiguation"]
            },
            "action_planning": {
                "success_rate": 0.78,
                "common_errors": ["incorrect sequences", "inefficient paths"],
                "recommendations": ["review planning algorithm", "add path optimization"]
            },
            "multimodal_fusion": {
                "success_rate": 0.91,
                "common_errors": ["delayed fusion", "confidence miscalibration"],
                "recommendations": ["tune fusion weights", "calibrate confidence measures"]
            },
            "navigation": {
                "success_rate": 0.88,
                "common_errors": ["collision", "lost localization"],
                "recommendations": ["improve obstacle detection", "enhance map building"]
            },
            "manipulation": {
                "success_rate": 0.82,
                "common_errors": ["grasp failure", "dropped objects"],
                "recommendations": ["refine grasp planning", "improve force control"]
            }
        }
    
    def generate_evaluation_report(self) -> Dict[str, Any]:
        """
        Override parent method to include educational metrics.
        
        :return: Combined technical and educational evaluation report
        """
        technical_report = super().generate_evaluation_report()
        educational_report = self.get_educational_report()
        
        combined_report = {
            **technical_report,
            "educational_assessment": educational_report
        }
        
        return combined_report


# Example usage:
if __name__ == "__main__":
    import asyncio
    
    async def example():
        # Create the evaluation service
        evaluator = CapstoneMetricsEvaluator()
        
        # Simulate some trial results
        for i in range(10):
            success = np.random.random() > 0.2  # 80% success rate
            completion_time = np.random.uniform(10, 60)  # Between 10-60 seconds
            steps_total = 5
            steps_completed = np.random.randint(3, 6) if success else np.random.randint(0, 3)
            
            errors = [] if np.random.random() > 0.1 else ["perception_failure"]
            
            evaluator.record_trial_result(
                trial_id=f"trial_{i+1}",
                success=success,
                completion_time=completion_time,
                steps_completed=steps_completed,
                steps_total=steps_total,
                errors=errors,
                metrics={
                    "accuracy": steps_completed / steps_total,
                    "efficiency": steps_completed / completion_time
                }
            )
        
        # Generate evaluation report
        report = evaluator.generate_evaluation_report()
        
        print("=== Capstone Project Evaluation Report ===")
        print(f"Comprehensive Score: {report['evaluation_summary']['comprehensive_score']:.2f}")
        print(f"Task Completion Rate: {report['performance_metrics']['task_completion_rate']:.2f}")
        print(f"Mean Completion Time: {report['performance_metrics']['mean_completion_time']:.2f}s")
        print(f"Success Rate: {report['reliability_metrics']['success_rate']:.2f}")
        print(f"Accuracy: {report['accuracy_metrics']['mean_relative_accuracy']:.2f}")
        print(f"Safety Score: {report['safety_metrics']['safety_score']:.2f}")
        print(f"Adaptability Score: {report['adaptability_metrics']['adaptability_score']:.2f}")
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"- {rec}")
    
    # Run the example
    # asyncio.run(example())
    
    # Example with educational evaluator
    async def educational_example():
        edu_evaluator = EducationalMetricsEvaluator()
        
        # Record some educational trial results
        for i in range(8):
            success = np.random.random() > 0.25  # 75% success rate
            completion_time = np.random.uniform(15, 75)  # Between 15-75 seconds
            steps_total = 4
            steps_completed = np.random.randint(2, 5) if success else np.random.randint(0, 3)
            
            errors = [] if i < 4 else ["misunderstood_command"]  # More errors in later trials
            
            edu_evaluator.record_trial_result(
                trial_id=f"edu_trial_{i+1}",
                success=success,
                completion_time=completion_time,
                steps_completed=steps_completed,
                steps_total=steps_total,
                errors=errors,
                details={"student_id": f"student_{i%3}"}  # Cycle through 3 students
            )
        
        # Generate educational report
        edu_report = edu_evaluator.get_educational_report()
        
        print("\n=== Educational Assessment Report ===")
        print(f"Overall Education Score: {edu_report['educational_outcomes']['overall_education_score']:.2f}")
        print(f"Engagement: {edu_report['educational_outcomes']['student_engagement']:.2f}")
        print(f"Learning Progression: {edu_report['educational_outcomes']['learning_progression']:.2f}")
        print(f"Concept Mastery: {edu_report['educational_outcomes']['concept_mastery']:.2f}")
        print(f"Application Transfer: {edu_report['educational_outcomes']['application_transfer']:.2f}")
        print("\nSuggestions for Improvement:")
        for suggestion in edu_report['suggestions_for_improvement']:
            print(f"- {suggestion}")
    
    # Run the educational example
    # asyncio.run(educational_example())