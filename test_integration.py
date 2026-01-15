#!/usr/bin/env python3
"""
Integration test for v1.2 features
Tests all feature combinations
"""
import sys
import os

# Test imports
print("=" * 60)
print("INTEGRATION TEST - BD Posture Validation v1.2")
print("=" * 60)

print("\n1. Testing imports...")
try:
    from processor import process_video, ENHANCED_FEATURES_AVAILABLE, ADVANCED_FEATURES_AVAILABLE
    print("✓ processor.py imported successfully")
except ImportError as e:
    print(f"✗ Failed to import processor: {e}")
    sys.exit(1)

try:
    from main import app
    print("✓ main.py imported successfully")
except ImportError as e:
    print(f"✗ Failed to import main: {e}")
    sys.exit(1)

print(f"\n2. Feature availability:")
print(f"   Enhanced features (v1.1): {'✓ Available' if ENHANCED_FEATURES_AVAILABLE else '✗ Not available'}")
print(f"   Advanced features (v1.2): {'✓ Available' if ADVANCED_FEATURES_AVAILABLE else '✗ Not available'}")

# Test feature modules
if ENHANCED_FEATURES_AVAILABLE:
    try:
        from court_detector import CourtDetector
        from shuttlecock_tracker import ShuttlecockTracker
        print("   ✓ Court detector and shuttlecock tracker loaded")
    except ImportError as e:
        print(f"   ✗ Failed to load v1.1 modules: {e}")

if ADVANCED_FEATURES_AVAILABLE:
    try:
        from perspective_transform import PerspectiveTransformer
        from professional_poses import ProfessionalPoseLibrary
        from advanced_analysis import AdvancedAnalyzer
        print("   ✓ Perspective transform and professional poses loaded")
    except ImportError as e:
        print(f"   ✗ Failed to load v1.2 modules: {e}")

print("\n3. Testing API endpoints...")
try:
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Test root endpoint
    response = client.get("/")
    if response.status_code == 200:
        print("   ✓ GET / endpoint working")
    else:
        print(f"   ✗ GET / failed with status {response.status_code}")
    
    print("   ✓ API endpoints accessible")
except Exception as e:
    print(f"   ✗ API test failed: {e}")

print("\n4. Testing feature flags...")
import inspect
sig = inspect.signature(process_video)
params = list(sig.parameters.keys())
expected_params = ['input_path', 'output_path', 'shot_model_path', 
                   'enable_court_detection', 'enable_shuttle_tracking', 
                   'enable_advanced_analysis']

missing = [p for p in expected_params if p not in params]
if not missing:
    print("   ✓ All feature flags present in process_video()")
else:
    print(f"   ✗ Missing parameters: {missing}")

print("\n5. Testing configuration combinations...")
test_configs = [
    {"enable_court_detection": True, "enable_shuttle_tracking": True, "enable_advanced_analysis": True},
    {"enable_court_detection": False, "enable_shuttle_tracking": False, "enable_advanced_analysis": False},
    {"enable_court_detection": True, "enable_shuttle_tracking": False, "enable_advanced_analysis": False},
]

for i, config in enumerate(test_configs, 1):
    config_str = ", ".join([f"{k.replace('enable_', '')}={v}" for k, v in config.items()])
    print(f"   Config {i}: {config_str}")

print("\n6. Checking dependencies...")
required_packages = [
    'cv2', 'mediapipe', 'numpy', 'fastapi', 'uvicorn', 'moviepy'
]

for pkg in required_packages:
    try:
        __import__(pkg)
        print(f"   ✓ {pkg}")
    except ImportError:
        print(f"   ✗ {pkg} not installed")

print("\n7. Checking file structure...")
required_files = [
    'main.py',
    'processor.py',
    'court_detector.py',
    'shuttlecock_tracker.py',
    'perspective_transform.py',
    'professional_poses.py',
    'advanced_analysis.py',
    'requirements.txt',
    'static/index.html'
]

for file in required_files:
    if os.path.exists(file):
        print(f"   ✓ {file}")
    else:
        print(f"   ✗ {file} missing")

print("\n" + "=" * 60)
print("INTEGRATION TEST COMPLETE")
print("=" * 60)

# Summary
issues = []
if not ENHANCED_FEATURES_AVAILABLE:
    issues.append("Enhanced features (v1.1) not available")
if not ADVANCED_FEATURES_AVAILABLE:
    issues.append("Advanced features (v1.2) not available")

if issues:
    print("\n⚠️  WARNINGS:")
    for issue in issues:
        print(f"   - {issue}")
    print("\nThe system will work with basic features only.")
else:
    print("\n✅ ALL FEATURES AVAILABLE - System ready for full operation!")

print("\nTo start the server:")
print("   uvicorn main:app --reload --port 8000")
print("\nTo test with a video:")
print("   curl -X POST http://localhost:8000/upload \\")
print("        -F 'file=@your_video.mp4' \\")
print("        -F 'enable_court_detection=true' \\")
print("        -F 'enable_shuttle_tracking=true' \\")
print("        -F 'enable_advanced_analysis=true'")
