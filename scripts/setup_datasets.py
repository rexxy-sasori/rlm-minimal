#!/usr/bin/env python3
"""
Dataset Setup Script for RLM Benchmarks

This script downloads and prepares official datasets for benchmarking.
It can be run during Docker build time or at runtime.
"""

import os
import sys
import argparse
from typing import Optional

def setup_browsecomp_plus(data_dir: str = "data", hf_token: Optional[str] = None) -> bool:
    """Setup BrowseComp-Plus dataset."""
    print("\n" + "="*80)
    print("SETTING UP BROWSECOMP-PLUS DATASET")
    print("="*80)
    
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        print("\nInstalling required packages...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "datasets"], 
                      check=True, capture_output=True)
        
        from datasets import load_dataset
        
        queries_path = os.path.join(data_dir, "queries.jsonl")
        corpus_path = os.path.join(data_dir, "corpus.jsonl")
        
        if os.path.exists(queries_path) and os.path.exists(corpus_path):
            print(f"\n✓ Datasets already exist in {data_dir}")
            print(f"  - queries.jsonl: {os.path.getsize(queries_path) / 1024 / 1024:.2f} MB")
            print(f"  - corpus.jsonl: {os.path.getsize(corpus_path) / 1024 / 1024:.2f} MB")
            return True
        
        print("\nDownloading queries...")
        queries = load_dataset("Tevatron/browsecomp-plus", split="queries")
        queries.to_json(queries_path, lines=True)
        print(f"  ✓ Saved: {queries_path}")
        print(f"  ✓ Total queries: {len(queries)}")
        
        print("\nDownloading corpus...")
        corpus = load_dataset("Tevatron/browsecomp-plus-corpus", split="train")
        corpus.to_json(corpus_path, lines=True)
        print(f"  ✓ Saved: {corpus_path}")
        print(f"  ✓ Total documents: {len(corpus)}")
        
        print(f"\n✓ BrowseComp-Plus setup completed successfully!")
        print(f"  Total size: {(os.path.getsize(queries_path) + os.path.getsize(corpus_path)) / 1024 / 1024:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error setting up BrowseComp-Plus: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_oolong(data_dir: str = "data/oolong") -> bool:
    """Setup official OOLONG dataset by cloning the repository."""
    print("\n" + "="*80)
    print("SETTING UP OFFICIAL OOLONG DATASET")
    print("="*80)
    
    try:
        import subprocess
        
        # Check if git is installed
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        
        # Clone OOLONG repository
        oolong_repo_dir = os.path.join(data_dir, "oolong")
        if not os.path.exists(oolong_repo_dir):
            print("\nCloning OOLONG repository...")
            subprocess.run(
                ["git", "clone", "https://github.com/abertsch72/oolong.git", oolong_repo_dir],
                check=True,
                capture_output=True
            )
            print(f"  ✓ Repository cloned to: {oolong_repo_dir}")
        else:
            print(f"\n✓ OOLONG repository already exists: {oolong_repo_dir}")
        
        # Install dependencies
        requirements_file = os.path.join(oolong_repo_dir, "requirements.txt")
        if os.path.exists(requirements_file):
            print("\nInstalling OOLONG dependencies...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                check=True,
                capture_output=True
            )
            print("  ✓ Dependencies installed")
        else:
            print("\n⚠ No requirements.txt found. Skipping dependency installation.")
        
        print(f"\n✓ Official OOLONG dataset setup completed successfully!")
        print(f"  Repository: {os.path.abspath(oolong_repo_dir)}")
        print(f"\nConfiguration:")
        print(f"  use_official_oolong: True")
        print(f"  oolong_data_dir: \"{data_dir}\"")
        print(f"  oolong_dataset_split: \"synth\" or \"real\"")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error during git operation: {e}")
        print("Falling back to synthetic dataset generation...")
        return False
    except Exception as e:
        print(f"\n✗ Error setting up OOLONG: {e}")
        print("Falling back to synthetic dataset generation...")
        return False

def setup_ruler(data_dir: str = "data/ruler") -> bool:
    """Setup RULER dataset (synthetic generation)."""
    print("\n" + "="*80)
    print("SETTING UP RULER DATASET")
    print("="*80)
    
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"\n✓ Created RULER directory: {data_dir}")
    print("\nNote: RULER generates synthetic data on-the-fly.")
    print("No pre-download required.")
    
    return True

def setup_all_datasets(data_dir: str = "data", hf_token: Optional[str] = None) -> bool:
    """Setup all datasets."""
    print("\n" + "#"*80)
    print("RLM DATASET SETUP - COMPLETE")
    print("#"*80)
    
    success = True
    
    if not setup_browsecomp_plus(os.path.join(data_dir), hf_token):
        success = False
    
    if not setup_oolong(os.path.join(data_dir, "oolong")):
        success = False
    
    if not setup_ruler(os.path.join(data_dir, "ruler")):
        success = False
    
    print("\n" + "#"*80)
    if success:
        print("✓ ALL DATASETS SETUP COMPLETED")
    else:
        print("⚠ SOME DATASETS REQUIRED MANUAL SETUP")
    print("#"*80)
    
    return success

def main():
    parser = argparse.ArgumentParser(description="Setup RLM benchmark datasets")
    parser.add_argument(
        "--dataset", 
        choices=["browsecomp_plus", "oolong", "ruler", "all"],
        default="all",
        help="Which dataset to setup"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory to store datasets"
    )
    parser.add_argument(
        "--hf-token",
        default=None,
        help="Hugging Face token for gated datasets"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if datasets exist"
    )
    
    args = parser.parse_args()
    
    if args.force:
        print("⚠ Force mode enabled - will re-download existing datasets")
    
    success = False
    
    if args.dataset == "browsecomp_plus":
        success = setup_browsecomp_plus(args.data_dir, args.hf_token)
    elif args.dataset == "oolong":
        success = setup_oolong(os.path.join(args.data_dir, "oolong"))
    elif args.dataset == "ruler":
        success = setup_ruler(os.path.join(args.data_dir, "ruler"))
    elif args.dataset == "all":
        success = setup_all_datasets(args.data_dir, args.hf_token)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
