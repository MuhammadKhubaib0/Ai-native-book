#!/usr/bin/env python3

"""
System Identification Example

This script demonstrates system identification techniques for sim-to-real transfer.
System identification is the process of determining the actual parameters of a system 
from input-output data to better match the simulation model to reality.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy import signal
import random


class SystemIdentifier:
    """
    A class to perform system identification to match simulation to reality.
    """
    
    def __init__(self):
        self.target_params = {
            'mass': 1.2,      # True mass of the real system
            'friction': 0.15,  # True friction of the real system
            'inertia': 0.2,    # True inertia of the real system
            'actuator_gain': 0.95  # True actuator gain of the real system
        }
        
        # Initial guess for parameters
        self.current_params = {
            'mass': 1.0,
            'friction': 0.1,
            'inertia': 0.1,
            'actuator_gain': 1.0
        }
    
    def real_system_response(self, input_signal):
        """
        Simulate the response of a real system with unknown parameters.
        In a real implementation, this would interface with the actual physical system.
        """
        # Simulate a 2nd order system response: m*ẍ + b*ẋ + k*x = F
        # where m=mass, b=friction, k=stiffness (simplified)
        
        # For this example, create a simplified model
        time_steps = len(input_signal)
        dt = 0.01  # Time step
        
        # Initialize state variables
        position = np.zeros(time_steps)
        velocity = np.zeros(time_steps)
        
        # Use the target parameters to simulate the real system
        mass = self.target_params['mass']
        friction = self.target_params['friction']
        actuator_gain = self.target_params['actuator_gain']
        
        # Apply the system dynamics
        for i in range(1, time_steps):
            # Apply input force (scaled by actuator gain)
            force = input_signal[i] * actuator_gain
            
            # Calculate acceleration: a = (F - friction*v) / mass
            acceleration = (force - friction * velocity[i-1]) / mass
            
            # Update state
            velocity[i] = velocity[i-1] + acceleration * dt
            position[i] = position[i-1] + velocity[i] * dt
        
        # Add some measurement noise to simulate real sensors
        noise = np.random.normal(0, 0.01, size=position.shape)
        return position + noise
    
    def simulation_response(self, input_signal, params):
        """
        Simulate the response using current parameter estimates.
        """
        time_steps = len(input_signal)
        dt = 0.01  # Time step
        
        # Initialize state variables
        position = np.zeros(time_steps)
        velocity = np.zeros(time_steps)
        
        # Use the current parameter estimates
        mass = params['mass']
        friction = params['friction']
        actuator_gain = params['actuator_gain']
        
        # Apply the system dynamics
        for i in range(1, time_steps):
            # Apply input force (scaled by actuator gain)
            force = input_signal[i] * actuator_gain
            
            # Calculate acceleration: a = (F - friction*v) / mass
            acceleration = (force - friction * velocity[i-1]) / mass
            
            # Update state
            velocity[i] = velocity[i-1] + acceleration * dt
            position[i] = position[i-1] + velocity[i] * dt
        
        return position
    
    def generate_test_signal(self):
        """Generate a test signal for system identification."""
        # Generate a pseudorandom binary sequence (PRBS) or other informative signal
        t = np.linspace(0, 10, 1000)
        
        # Combine multiple signal types for system excitation
        step_signal = np.zeros_like(t)
        step_signal[100:200] = 1.0  # Step input
        step_signal[300:400] = -0.5  # Reverse step
        step_signal[500:600] = 0.7   # Another step
        
        # Add some sinusoidal components
        sin_signal = 0.5 * np.sin(2 * np.pi * 0.5 * t)  # 0.5Hz sinusoid
        sin_signal[700:900] += 0.3 * np.sin(2 * np.pi * 2.0 * t[700:900])  # Add 2Hz
        
        # Combine signals
        combined_signal = step_signal + 0.2 * sin_signal
        
        return combined_signal
    
    def objective_function(self, param_vector):
        """
        Objective function to minimize - measures difference between real and simulated responses.
        """
        # Convert parameter vector to dictionary
        params = {
            'mass': max(param_vector[0], 0.1),  # Ensure positive mass
            'friction': max(param_vector[1], 0.01),  # Ensure positive friction
            'inertia': max(param_vector[2], 0.01),  # Ensure positive inertia
            'actuator_gain': param_vector[3]
        }
        
        # Generate test signal
        test_signal = self.generate_test_signal()
        
        # Get response from real (simulated) system
        real_response = self.real_system_response(test_signal)
        
        # Get response from simulation with current parameters
        sim_response = self.simulation_response(test_signal, params)
        
        # Calculate error (mean squared error)
        error = np.mean((real_response - sim_response) ** 2)
        
        return error
    
    def identify_parameters(self):
        """Identify system parameters using optimization."""
        print("Starting system identification...")
        print(f"Target parameters: {self.target_params}")
        print(f"Initial guess: {self.current_params}")
        
        # Convert initial parameters to vector
        initial_params = np.array([
            self.current_params['mass'],
            self.current_params['friction'],
            self.current_params['inertia'],
            self.current_params['actuator_gain']
        ])
        
        # Optimize parameters
        result = minimize(
            self.objective_function,
            initial_params,
            method='BFGS',
            options={
                'disp': True,
                'maxiter': 100
            }
        )
        
        # Extract optimized parameters
        self.current_params = {
            'mass': max(result.x[0], 0.1),
            'friction': max(result.x[1], 0.01),
            'inertia': max(result.x[2], 0.01),
            'actuator_gain': result.x[3]
        }
        
        print(f"\nOptimized parameters: {self.current_params}")
        print(f"Target parameters: {self.target_params}")
        
        # Calculate parameter errors
        for param_name in self.target_params:
            error = abs(self.target_params[param_name] - self.current_params[param_name])
            error_pct = (error / self.target_params[param_name]) * 100
            print(f"  {param_name} error: {error:.4f} ({error_pct:.2f}%)")
        
        return self.current_params, result


def compare_system_responses(identifier, test_signal, title="System Response Comparison"):
    """Compare the responses of real and identified systems."""
    # Get responses
    real_response = identifier.real_system_response(test_signal)
    sim_response_initial = identifier.simulation_response(test_signal, identifier.current_params)
    
    # Temporarily update with identified parameters
    identified_params, _ = identifier.identify_parameters()
    sim_response_identified = identifier.simulation_response(test_signal, identified_params)
    
    # Create comparison plot
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(test_signal, label='Input Signal', alpha=0.7)
    plt.title('Input Signal')
    plt.xlabel('Time Step')
    plt.ylabel('Input')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 1, 2)
    plt.plot(real_response, label='Real System Response', linewidth=2)
    plt.plot(sim_response_initial, label='Simulation (Initial Params)', linestyle='--')
    plt.plot(sim_response_identified, label='Simulation (Identified Params)', linestyle='-.')
    plt.title(title)
    plt.xlabel('Time Step')
    plt.ylabel('Output')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def main():
    """Main function demonstrating system identification."""
    print("System Identification Demo")
    print("="*50)
    
    # Create system identifier
    identifier = SystemIdentifier()
    
    # Generate test signal
    print("\n1. Generating test signal for system identification...")
    test_signal = identifier.generate_test_signal()
    print(f"Test signal length: {len(test_signal)} samples")
    
    # Perform system identification
    print("\n2. Performing system identification...")
    identified_params, optimization_result = identifier.identify_parameters()
    
    # Evaluate the identification
    print(f"\n3. Optimization Result:")
    print(f"   Success: {optimization_result.success}")
    print(f"   Message: {optimization_result.message}")
    print(f"   Number of evaluations: {optimization_result.nfev}")
    print(f"   Final error: {optimization_result.fun:.6f}")
    
    # Compare responses
    print("\n4. Comparing system responses...")
    print("In a full implementation, we would visualize the comparison.")
    
    # Example: Generate a new signal to test the identified model
    new_signal = identifier.generate_test_signal()
    real_output = identifier.real_system_response(new_signal)
    identified_output = identifier.simulation_response(new_signal, identified_params)
    
    # Calculate similarity
    correlation = np.corrcoef(real_output, identified_output)[0, 1]
    mse = np.mean((real_output - identified_output) ** 2)
    
    print(f"\n5. Model Validation:")
    print(f"   Correlation between real and identified model: {correlation:.4f}")
    print(f"   Mean Squared Error: {mse:.6f}")
    
    # Suggest next steps
    print(f"\n6. Next Steps for Real Implementation:")
    print(f"   - Connect to actual hardware for data collection")
    print(f"   - Design more sophisticated test signals")
    print(f"   - Implement adaptive parameter updates")
    print(f"   - Validate across different operating conditions")
    print(f"   - Implement closed-loop validation tests")
    
    # Uncomment the following line to plot the comparison
    # compare_system_responses(identifier, test_signal)


if __name__ == '__main__':
    main()