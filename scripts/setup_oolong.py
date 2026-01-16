#!/usr/bin/env python3
"""Setup script for official OOLONG dataset."""

import os
import sys
import subprocess

def setup_official_oolong(data_dir: str = "data/oolong"):
    """Setup official OOLONG dataset.
    
    Args:
        data_dir: Directory to store the OOLONG dataset and repository
    """
    print("Setting up official OOLONG dataset...")
    
    # Create data directory
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Check if git is installed
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        
        # Clone OOLONG repository
        oolong_repo_dir = os.path.join(data_dir, "oolong")
        if not os.path.exists(oolong_repo_dir):
            print("Cloning OOLONG repository...")
            subprocess.run(
                ["git", "clone", "https://github.com/abertsch72/oolong.git", oolong_repo_dir],
                check=True,
                capture_output=True
            )
        else:
            print("OOLONG repository already cloned.")
        
        # Install dependencies
        requirements_file = os.path.join(oolong_repo_dir, "requirements.txt")
        if os.path.exists(requirements_file):
            print("Installing OOLONG dependencies...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                check=True,
                capture_output=True
            )
        else:
            print("No requirements.txt found. Skipping dependency installation.")
        
        print("✅ Official OOLONG dataset setup completed successfully!")
        print(f"OOLONG repository stored in: {os.path.abspath(oolong_repo_dir)}")
        print("\nTo use official OOLONG in your benchmark, set:")
        print('use_official_oolong: True in your configuration')
        print(f'oolong_data_dir: "{data_dir}"')
        print('oolong_dataset_split: "synth" or "real"')
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up OOLONG: {e}")
        print("Falling back to synthetic dataset generation...")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup official OOLONG dataset")
    parser.add_argument("--data-dir", type=str, default="data/oolong", help="Directory to store the OOLONG dataset")
    
    args = parser.parse_args()
    setup_official_oolong(args.data_dir)