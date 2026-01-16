#!/usr/bin/env python3
"""Setup script for BrowseComp-Plus dataset."""

import os
import sys
import subprocess
from datasets import load_dataset

def setup_browsecomp_plus(data_dir: str = "data", hf_token: str = None):
    """Setup BrowseComp-Plus dataset.
    
    Args:
        data_dir: Directory to store the dataset
        hf_token: Hugging Face token for accessing the dataset (optional)
    """
    print("Setting up BrowseComp-Plus dataset...")
    
    # Create data directory
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Install required packages
        print("Installing required packages...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "datasets"],
            check=True,
            capture_output=True
        )
        
        # Download queries
        print("Downloading queries...")
        queries = load_dataset("Tevatron/browsecomp-plus", split="queries", token=hf_token)
        queries.to_json(os.path.join(data_dir, "queries.jsonl"), lines=True)
        
        # Download corpus (not obfuscated)
        print("Downloading corpus...")
        corpus = load_dataset("Tevatron/browsecomp-plus-corpus", split="train", token=hf_token)
        corpus.to_json(os.path.join(data_dir, "corpus.jsonl"), lines=True)
        
        print("✅ BrowseComp-Plus dataset setup completed successfully!")
        print(f"Dataset stored in: {os.path.abspath(data_dir)}")
        print("\nTo use BrowseComp-Plus in your benchmark, set:")
        print('use_browsecomp_plus: True in your configuration')
        print(f'browsecomp_plus_data_dir: "{data_dir}"')
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up BrowseComp-Plus: {e}")
        print("Falling back to synthetic dataset generation...")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup BrowseComp-Plus dataset")
    parser.add_argument("--data-dir", type=str, default="data", help="Directory to store the dataset")
    parser.add_argument("--hf-token", type=str, default=None, help="Hugging Face token for accessing the dataset")
    
    args = parser.parse_args()
    setup_browsecomp_plus(args.data_dir, args.hf_token)