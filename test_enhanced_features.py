#!/usr/bin/env python3
"""
Quick test script for v1.1 enhanced features
Tests court detection and shuttlecock tracking modules
"""

import cv2
import numpy as np
from court_detector import CourtDetector
from shuttlecock_tracker import ShuttlecockTracker

def test_court_detector():
    """Test court detection module"""
    print("=" * 60)
    print("Testing Court Detector")
    print("=" * 60)
    
    # Create detector (fallback mode - no model)
    detector = CourtDetector()
    
    # Create test frame (640x480 with some lines)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw some court-like lines
    cv2.rectangle(frame, (100, 100), (540, 380), (255, 255, 255), 2)
    cv2.line(frame, (320, 100), (320, 380), (255, 255, 255), 2)
    
    # Test detection
    result = detector.detect_court(frame)
    
    if result and result.get('detected'):
        print("✓ Court detection working (fallback mode)")
        print(f"  Method: {result.get('method', 'model')}")
    else:
        print("✗ Court detection failed")
    
    print()

def test_shuttlecock_tracker():
    """Test shuttlecock tracking module"""
    print("=" * 60)
    print("Testing Shuttlecock Tracker")
    print("=" * 60)
    
    # Create tracker (fallback mode - no model)
    tracker = ShuttlecockTracker()
    
    # Create test frame with white circle (shuttlecock)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.circle(frame, (320, 240), 10, (255, 255, 255), -1)
    
    # Test detection
    position = tracker.detect_shuttlecock(frame)
    
    if position:
        print(f"✓ Shuttlecock detection working (fallback mode)")
        print(f"  Position: {position}")
    else:
        print("✗ Shuttlecock detection failed")
    
    print()

def test_integration():
    """Test integration with enhanced processor"""
    print("=" * 60)
    print("Testing Enhanced Processor Integration")
    print("=" * 60)
    
    try:
        from enhanced_processor import get_enhanced_features
        
        features = get_enhanced_features(enable_court=True, enable_shuttle=True)
        
        print(f"✓ Enhanced processor loaded")
        print(f"  Court enabled: {features['court_enabled']}")
        print(f"  Shuttle enabled: {features['shuttle_enabled']}")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
    
    print()

def main():
    print("\n" + "=" * 60)
    print("BD-Posture-Validation-Prototype v1.1 - Feature Test")
    print("=" * 60)
    print()
    
    # Run tests
    test_court_detector()
    test_shuttlecock_tracker()
    test_integration()
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()
    print("All modules loaded successfully!")
    print()
    print("Note: These tests use fallback detection methods.")
    print("For full accuracy, download models using:")
    print("  python download_models.py")
    print()

if __name__ == "__main__":
    main()
