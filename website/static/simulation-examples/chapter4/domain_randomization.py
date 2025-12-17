#!/usr/bin/env python3

"""
Domain Randomization Example

This script demonstrates domain randomization techniques for sim-to-real transfer.
Domain randomization involves randomizing simulation parameters to make policies 
robust to variations in the real world.
"""

import random
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import torch
import torch.nn as nn


class DomainRandomizer:
    """
    A class to implement domain randomization techniques for sim-to-real transfer.
    """
    
    def __init__(self, env):
        self.env = env
        self.param_ranges = {
            'lighting': (0.1, 1.0),  # Intensity range
            'color': (0.0, 1.0),     # Color variation
            'friction': (0.1, 1.0),  # Friction range
            'mass': (0.5, 2.0),      # Mass multiplier
            'gravity': (8.8, 10.8),  # Gravity range
        }
    
    def randomize_environment(self):
        """Randomize environment parameters for domain randomization"""
        # Randomize lighting
        lighting_intensity = random.uniform(
            self.param_ranges['lighting'][0], 
            self.param_ranges['lighting'][1]
        )
        
        # Randomize object colors
        object_color = [random.uniform(0, 1) for _ in range(3)]
        
        # Randomize friction coefficients
        friction = random.uniform(
            self.param_ranges['friction'][0], 
            self.param_ranges['friction'][1]
        )
        
        # Randomize object masses
        mass_multiplier = random.uniform(
            self.param_ranges['mass'][0], 
            self.param_ranges['mass'][1]
        )
        
        # Randomize gravity
        gravity_val = random.uniform(
            self.param_ranges['gravity'][0], 
            self.param_ranges['gravity'][1]
        )
        
        # Apply randomizations to environment
        # (In a real implementation, these would set actual environment parameters)
        randomization_params = {
            'lighting': lighting_intensity,
            'color': object_color,
            'friction': friction,
            'mass': mass_multiplier,
            'gravity': gravity_val
        }
        
        return randomization_params


class SystemIdentifier:
    """
    A class to perform system identification to match simulation to reality.
    """
    
    def __init__(self, sim_env, real_robot):
        self.sim_env = sim_env
        self.real_robot = real_robot
        self.parameters = {
            'mass': 1.0,
            'friction': 0.1,
            'inertia': 0.1,
            'actuator_gain': 1.0
        }
    
    def collect_data(self):
        """Simulate collecting input-output data from real robot"""
        # In a real implementation, this would interface with the actual robot
        # For this example, we'll simulate data collection
        
        # Generate test inputs
        inputs = []
        outputs = []
        
        for _ in range(10):  # Collect 10 data points
            # Random input
            input_signal = np.random.uniform(-1, 1, size=5)
            
            # Simulate a real robot response with some noise
            # (In reality, this would come from the actual robot)
            real_output = input_signal * 0.8 + np.random.normal(0, 0.05, size=5)
            
            inputs.append(input_signal)
            outputs.append(real_output)
        
        return np.array(inputs), np.array(outputs)
    
    def simulate_with_params(self, params, inputs):
        """Simulate the system with given parameters"""
        # Update simulation parameters
        sim_outputs = []
        
        for input_signal in inputs:
            # Simulate a response using the parameters
            # This is a simplified example - real systems would have complex dynamics
            output = input_signal * params['actuator_gain'] * 0.9  # Simulate actuator gain
            output += np.random.normal(0, params['friction'] * 0.1, size=input_signal.shape)  # Add friction-like noise
            
            sim_outputs.append(output)
        
        return np.array(sim_outputs)
    
    def objective_function(self, param_vector):
        """Objective function to minimize - measures difference between sim and real"""
        # Convert parameter vector back to dictionary
        params = {
            'mass': param_vector[0],
            'friction': param_vector[1],
            'inertia': param_vector[2],
            'actuator_gain': param_vector[3]
        }
        
        # Collect data from real system
        inputs, real_outputs = self.collect_data()
        
        # Get simulation outputs with current parameters
        sim_outputs = self.simulate_with_params(params, inputs)
        
        # Calculate error between real and simulated outputs
        error = np.mean((real_outputs - sim_outputs)**2)
        
        print(f"Parameter vector: {param_vector}, Error: {error}")
        
        return error
    
    def identify_system(self):
        """Identify system parameters using optimization"""
        # Initial parameter guess
        initial_params = np.array([1.0, 0.1, 0.1, 1.0])
        
        # Optimize parameters
        result = minimize(
            self.objective_function,
            initial_params,
            method='BFGS',
            options={'disp': True, 'maxiter': 20}
        )
        
        # Update parameters with optimized values
        self.parameters = {
            'mass': result.x[0],
            'friction': result.x[1],
            'inertia': result.x[2],
            'actuator_gain': result.x[3]
        }
        
        print(f"Optimized parameters: {self.parameters}")
        return self.parameters


class SimToRealPipeline:
    """
    A complete pipeline to combine domain randomization and system identification.
    """
    
    def __init__(self):
        # For this example, we don't have actual environments
        # so we'll just create placeholders
        self.domain_randomizer = DomainRandomizer(None)
        self.system_identifier = SystemIdentifier(None, None)
    
    def train_with_domain_randomization(self, episodes=1000):
        """Train policy in randomized simulation environment"""
        print(f"Training with domain randomization for {episodes} episodes...")
        
        for episode in range(episodes):
            # Randomize environment for each episode
            rand_params = self.domain_randomizer.randomize_environment()
            
            # In a real implementation, we would train a policy here
            # For this example, we'll just print the randomization parameters
            if episode % 200 == 0:
                print(f"Episode {episode}: Randomization params = {rand_params}")
        
        print("Domain randomization training complete!")
    
    def execute_pipeline(self):
        """Execute the complete sim-to-real pipeline"""
        print("Starting Sim-to-Real Pipeline...")
        print("="*40)
        
        print("\n1. Training with domain randomization...")
        self.train_with_domain_randomization()
        
        print("\n2. Identifying system parameters...")
        identified_params = self.system_identifier.identify_system()
        
        print("\n3. Pipeline complete!")
        print(f"Final parameters: {identified_params}")


def plot_domain_randomization_example():
    """Plot an example showing domain randomization effect"""
    # Generate example data for visualization
    x = np.linspace(0, 10, 1000)
    original = np.sin(x)  # Original signal
    
    # Simulate domain randomization by adding various noise patterns
    randomized = []
    for i in range(5):  # 5 different randomized versions
        noise = np.random.uniform(-0.1, 0.1, size=x.shape) * (0.5 + i*0.1)  # Increasing noise
        randomized.append(original + noise)
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Plot original signal
    plt.subplot(2, 1, 1)
    plt.plot(x, original, label='Original Signal', linewidth=2, color='blue')
    plt.title('Domain Randomization: Original Signal')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot randomized signals
    plt.subplot(2, 1, 2)
    colors = ['red', 'green', 'orange', 'purple', 'brown']
    for i, rand_signal in enumerate(randomized):
        plt.plot(x, rand_signal, label=f'Randomized {i+1}', alpha=0.7, color=colors[i % len(colors)])
    
    plt.title('Domain Randomization: Multiple Randomized Versions')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def main():
    """Main function demonstrating sim-to-real transfer techniques."""
    print("Sim-to-Real Transfer Techniques Demo")
    print("="*50)
    
    # Example 1: Domain randomization
    print("\n1. Domain Randomization Example:")
    print("-" * 30)
    
    # Create a simple environment placeholder
    env = type('Environment', (), {})()
    domain_rand = DomainRandomizer(env)
    
    # Randomize environment multiple times to show variation
    for i in range(3):
        params = domain_rand.randomize_environment()
        print(f"Randomization {i+1}: {params}")
    
    print("\n2. System Identification Example:")
    print("-" * 30)
    
    # Create placeholders for simulation and real environments
    sim_env = type('SimEnv', (), {})()
    real_robot = type('RealRobot', (), {})()
    
    sys_id = SystemIdentifier(sim_env, real_robot)
    try:
        identified_params = sys_id.identify_system()
        print(f"Identified parameters: {identified_params}")
    except Exception as e:
        print(f"System identification failed: {e}")
        print("This is expected in this example since we don't have real environments")
    
    # Example 3: Complete pipeline
    print("\n3. Complete Sim-to-Real Pipeline:")
    print("-" * 30)
    
    pipeline = SimToRealPipeline()
    pipeline.execute_pipeline()
    
    print("\n4. Visualizing Domain Randomization:")
    print("-" * 30)
    print("Generating plot to visualize domain randomization effect...")
    print("(In a real environment, this would show before/after results)")
    
    # Uncomment the following line to plot the visualization
    # plot_domain_randomization_example()


if __name__ == '__main__':
    main()