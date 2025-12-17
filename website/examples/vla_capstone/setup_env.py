#!/usr/bin/env python3
"""
Script to set up the virtual environment for the VLA Capstone project.
This script is for documentation purposes to illustrate the setup process.
"""

import os
import sys
import subprocess
import venv


def create_virtual_environment():
    """
    Creates a virtual environment for the VLA project.
    """
    env_dir = os.path.join(os.path.dirname(__file__), "vla-env")
    
    print(f"Creating virtual environment at: {env_dir}")
    
    # Create the virtual environment
    venv.create(env_dir, with_pip=True)
    
    print(f"Virtual environment created successfully at: {env_dir}")
    
    # Install dependencies
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_file):
        pip_path = os.path.join(env_dir, "Scripts", "pip.exe") if os.name == "nt" else os.path.join(env_dir, "bin", "pip")
        
        print(f"Installing dependencies from: {requirements_file}")
        subprocess.check_call([pip_path, "install", "-r", requirements_file])
        
        print("Dependencies installed successfully")
    else:
        print(f"Requirements file not found: {requirements_file}")


if __name__ == "__main__":
    create_virtual_environment()