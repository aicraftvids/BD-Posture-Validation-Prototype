#!/usr/bin/env python3
"""
Model Downloader for Enhanced Features
Downloads pre-trained models for court detection and shuttlecock tracking
"""

import os
import sys
from pathlib import Path

def download_models():
    """
    Download required model files
    
    Models needed:
    1. court_kpRCNN.pth (~100MB) - Court detection
    2. tracknet_model.pth (~50MB) - Shuttlecock tracking
    
    Note: These models are from SoloShuttlePose project
    """
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Model Download Instructions")
    print("=" * 60)
    print()
    print("The enhanced features require pre-trained models from SoloShuttlePose.")
    print()
    print("To download models:")
    print()
    print("1. Clone SoloShuttlePose repository:")
    print("   git clone https://github.com/sunwuzhou03/SoloShuttlePose.git")
    print()
    print("2. Copy model files:")
    print("   cp SoloShuttlePose/src/models/weights/court_kpRCNN.pth models/")
    print("   cp SoloShuttlePose/src/models/weights/tracknet_model.pth models/")
    print()
    print("3. Or download directly from:")
    print("   https://github.com/sunwuzhou03/SoloShuttlePose/tree/main/src/models/weights")
    print()
    print("=" * 60)
    print()
    print("Note: The application will work without these models using fallback")
    print("detection methods, but accuracy will be reduced.")
    print()
    
    # Check if models exist
    court_model = models_dir / "court_kpRCNN.pth"
    track_model = models_dir / "tracknet_model.pth"
    
    print("Current model status:")
    print(f"  Court detection: {'✓ Found' if court_model.exists() else '✗ Missing'}")
    print(f"  Ball tracking:   {'✓ Found' if track_model.exists() else '✗ Missing'}")
    print()
    
    if court_model.exists() and track_model.exists():
        print("✓ All models are available!")
        return True
    else:
        print("⚠ Some models are missing. Enhanced features will use fallback methods.")
        return False

if __name__ == "__main__":
    download_models()
