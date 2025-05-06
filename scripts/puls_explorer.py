#!/usr/bin/env python
"""
Script to explore the Pulse Engine installation and find usable state files.
"""

import os
import sys
import importlib.util
import glob

# Add the Pulse Engine path to the Python path
pulse_path = "/Users/volker/Work/Puls/builds/install/python"
if pulse_path not in sys.path:
    sys.path.insert(0, pulse_path)

def find_module_location(module_name):
    """Find the location of an installed module"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return None
        
        # Get the module location
        if spec.origin:
            return os.path.dirname(os.path.abspath(spec.origin))
        return None
    except ImportError:
        return None

def find_files_recursively(start_dir, pattern):
    """Find all files matching a pattern recursively"""
    matches = []
    for root, dirnames, filenames in os.walk(start_dir):
        for filename in glob.fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    return matches

def main():
    """Explore the Pulse Engine installation"""
    print("Exploring Pulse Engine installation...\n")
    
    # Try to import pulse and find its location
    try:
        pulse_module_loc = find_module_location("pulse")
        print(f"Pulse module location: {pulse_module_loc}")
        
        # Find the installation root (likely one or two directories up)
        install_dir = os.path.dirname(pulse_module_loc)
        parent_dir = os.path.dirname(install_dir)
        
        # Check if we can find the engine module and its version
        try:
            from pulse.engine.PulseEngine import version, hash
            print(f"Pulse Engine version: {version()}-{hash()}")
        except (ImportError, AttributeError):
            print("Could not determine Pulse Engine version")
        
        # Potential locations for data files
        data_dirs = [
            os.path.join(install_dir, "data"),
            os.path.join(parent_dir, "data"),
            os.path.join(parent_dir, "share", "pulse"),
            os.path.join(parent_dir, "share", "data"),
            os.path.join(install_dir, "share", "pulse"),
            os.path.join(parent_dir, "bin"),
            os.path.join(parent_dir, "share")
        ]
        
        # Look for state files in those directories
        print("\nSearching for state files...")
        found_state_files = []
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                print(f"\nExploring directory: {data_dir}")
                state_files = find_files_recursively(data_dir, "*.json")
                
                # Filter for likely state files
                for file_path in state_files:
                    if "state" in file_path.lower() or "@0s" in file_path:
                        found_state_files.append(file_path)
                        print(f"  Found potential state file: {file_path}")
        
        if not found_state_files:
            print("No state files found in the expected locations.")
            
        # Also look for substance files and other configurations
        print("\nSearching for substance files...")
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                substance_files = find_files_recursively(data_dir, "*.json")
                for file_path in substance_files:
                    if "substance" in file_path.lower():
                        print(f"  Found substance file: {file_path}")
        
        # Look for Python examples
        print("\nSearching for example files...")
        example_files = []
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                examples = find_files_recursively(data_dir, "*.py")
                for file_path in examples:
                    if "example" in file_path.lower() or "howto" in file_path.lower():
                        example_files.append(file_path)
                        print(f"  Found example file: {file_path}")
        
        # If no examples found in data dirs, look in other commonly used directories
        if not example_files:
            example_dirs = [
                os.path.join(parent_dir, "examples"),
                os.path.join(parent_dir, "sdk"),
                os.path.join(install_dir, "examples"),
                os.path.join(parent_dir, "doc", "examples")
            ]
            
            for example_dir in example_dirs:
                if os.path.exists(example_dir):
                    examples = find_files_recursively(example_dir, "*.py")
                    for file_path in examples:
                        if "example" in file_path.lower() or "howto" in file_path.lower():
                            example_files.append(file_path)
                            print(f"  Found example file: {file_path}")
                            
    except ImportError:
        print("Failed to import pulse module. Make sure the path is correct.")
        sys.exit(1)
        
    print("\nExploration complete.")

if __name__ == "__main__":
    main()