#!/usr/bin/env python3

"""
Sensor Noise Modeling Example

This script demonstrates how to model sensor noise in simulation.
It shows how real sensors have various noise sources that can be 
simulated using different probability distributions.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


def model_lidar_noise(true_distances, std_dev=0.01):
    """
    Model LiDAR noise as Gaussian noise added to true distances.
    
    Args:
        true_distances: Array of true distance measurements
        std_dev: Standard deviation of the noise (meters)
    
    Returns:
        Array of noisy distance measurements
    """
    noise = np.random.normal(loc=0.0, scale=std_dev, size=true_distances.shape)
    return true_distances + noise


def model_depth_camera_noise(true_depths, baseline_noise=0.01, distance_factor=0.001):
    """
    Model depth camera noise with distance-dependent error.
    
    Args:
        true_depths: Array of true depth measurements
        baseline_noise: Baseline noise at 1m (meters)
        distance_factor: Factor for distance-dependent noise
    
    Returns:
        Array of noisy depth measurements
    """
    # Noise increases with depth
    depth_dependent_std = baseline_noise + (true_depths * distance_factor)
    noise = np.random.normal(loc=0.0, scale=depth_dependent_std)
    return true_depths + noise


def model_imu_noise(linear_acc_true, angular_vel_true):
    """
    Model IMU noise for linear acceleration and angular velocity.
    
    Args:
        linear_acc_true: Array of true linear acceleration values
        angular_vel_true: Array of true angular velocity values
    
    Returns:
        Tuple of (noisy_linear_acc, noisy_angular_vel)
    """
    # Linear acceleration noise (Gaussian with 1.7e-2 m/s^2 std)
    linear_acc_noise = np.random.normal(loc=0.0, scale=1.7e-2, size=linear_acc_true.shape)
    
    # Angular velocity noise (Gaussian with 1e-3 rad/s std)
    angular_vel_noise = np.random.normal(loc=0.0, scale=1e-3, size=angular_vel_true.shape)
    
    return linear_acc_true + linear_acc_noise, angular_vel_true + angular_vel_noise


def plot_sensor_noise():
    """Plot examples of different sensor noise models."""
    # Distance range for LiDAR
    distances = np.linspace(0.1, 30.0, 1000)
    
    # Generate noisy measurements
    lidar_noisy = model_lidar_noise(distances)
    
    # Depth camera noise (distance-dependent)
    depth_noisy = model_depth_camera_noise(distances)
    
    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: LiDAR noise
    axes[0, 0].scatter(distances, lidar_noisy - distances, alpha=0.6, s=1)
    axes[0, 0].set_xlabel('True Distance (m)')
    axes[0, 0].set_ylabel('Error (m)')
    axes[0, 0].set_title('LiDAR Measurement Error')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Depth camera noise
    axes[0, 1].scatter(distances, depth_noisy - distances, alpha=0.6, s=1)
    axes[0, 1].set_xlabel('True Distance (m)')
    axes[0, 1].set_ylabel('Error (m)')
    axes[0, 1].set_title('Depth Camera Measurement Error')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Histogram of LiDAR noise
    lidar_errors = lidar_noisy - distances
    axes[1, 0].hist(lidar_errors, bins=50, density=True, alpha=0.7)
    x_norm = np.linspace(lidar_errors.min(), lidar_errors.max(), 100)
    normal_fit = stats.norm.pdf(x_norm, loc=0, scale=0.01)
    axes[1, 0].plot(x_norm, normal_fit, 'r-', label='Fitted Normal Distribution')
    axes[1, 0].set_xlabel('LiDAR Error (m)')
    axes[1, 0].set_ylabel('Density')
    axes[1, 0].set_title('LiDAR Error Distribution')
    axes[1, 0].legend()
    
    # Plot 4: IMU noise characteristics
    t = np.linspace(0, 10, 1000)  # Time vector
    # Simulate some IMU values
    true_acc = np.sin(0.5*t)  # Example acceleration pattern
    true_vel = np.cos(0.3*t)  # Example angular velocity pattern
    
    noisy_acc, noisy_vel = model_imu_noise(true_acc, true_vel)
    
    axes[1, 1].plot(t, noisy_acc - true_acc, label='Linear Acc Error', alpha=0.7)
    axes[1, 1].plot(t, noisy_vel - true_vel, label='Angular Vel Error', alpha=0.7)
    axes[1, 1].set_xlabel('Time (s)')
    axes[1, 1].set_ylabel('Error')
    axes[1, 1].set_title('IMU Measurement Error Over Time')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def main():
    """Main function demonstrating sensor noise modeling."""
    print("Sensor Noise Modeling Example")
    print("="*40)
    
    # Example distances for LiDAR
    example_distances = np.array([1.0, 5.0, 10.0, 15.0, 20.0])
    noisy_distances = model_lidar_noise(example_distances)
    
    print("LiDAR Noise Example:")
    print("True distances:", example_distances)
    print("Noisy measurements:", noisy_distances)
    print("Errors:", noisy_distances - example_distances)
    print()
    
    # Example IMU values
    true_acc = np.array([0.0, 9.8, 0.0])  # Static with gravity
    true_vel = np.array([0.0, 0.0, 0.1])  # Slow rotation around z-axis
    
    noisy_acc, noisy_vel = model_imu_noise(true_acc, true_vel)
    
    print("IMU Noise Example:")
    print("True linear acceleration:", true_acc)
    print("Noisy measurement:", noisy_acc)
    print()
    print("True angular velocity:", true_vel)
    print("Noisy measurement:", noisy_vel)
    print()
    
    # Uncomment the following line to plot the noise characteristics
    # plot_sensor_noise()


if __name__ == '__main__':
    main()