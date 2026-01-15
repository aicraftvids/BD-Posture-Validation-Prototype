"""
Enhanced Processor with Court Detection and Shuttlecock Tracking
Integrates features from SoloShuttlePose
"""

import os
from pathlib import Path
from typing import Optional

# Import new modules
try:
    from court_detector import CourtDetector
    COURT_AVAILABLE = True
except ImportError:
    COURT_AVAILABLE = False
    print("Court detection not available")

try:
    from shuttlecock_tracker import ShuttlecockTracker
    SHUTTLE_AVAILABLE = True
except ImportError:
    SHUTTLE_AVAILABLE = False
    print("Shuttlecock tracking not available")


def get_enhanced_features(enable_court: bool = True, 
                          enable_shuttle: bool = True) -> dict:
    """
    Initialize enhanced features
    
    Args:
        enable_court: Enable court detection
        enable_shuttle: Enable shuttlecock tracking
        
    Returns:
        Dict with initialized detectors
    """
    features = {
        'court_detector': None,
        'shuttle_tracker': None,
        'court_enabled': False,
        'shuttle_enabled': False
    }
    
    models_dir = Path("models")
    
    # Initialize court detector
    if enable_court and COURT_AVAILABLE:
        court_model = models_dir / "court_kpRCNN.pth"
        if court_model.exists():
            features['court_detector'] = CourtDetector(str(court_model))
            features['court_enabled'] = True
            print("✓ Court detection enabled")
        else:
            features['court_detector'] = CourtDetector()  # Fallback mode
            features['court_enabled'] = True
            print("⚠ Court detection using fallback (no model)")
    
    # Initialize shuttlecock tracker
    if enable_shuttle and SHUTTLE_AVAILABLE:
        shuttle_model = models_dir / "tracknet_model.pth"
        if shuttle_model.exists():
            features['shuttle_tracker'] = ShuttlecockTracker(str(shuttle_model))
            features['shuttle_enabled'] = True
            print("✓ Shuttlecock tracking enabled")
        else:
            features['shuttle_tracker'] = ShuttlecockTracker()  # Fallback mode
            features['shuttle_enabled'] = True
            print("⚠ Shuttlecock tracking using fallback (no model)")
    
    return features


def enhance_frame_analysis(frame, landmarks, enhanced_features):
    """
    Add court and shuttlecock detection to frame analysis
    
    Args:
        frame: Video frame
        landmarks: MediaPipe pose landmarks
        enhanced_features: Dict from get_enhanced_features()
        
    Returns:
        Dict with enhanced analysis results
    """
    results = {
        'court_info': None,
        'shuttle_position': None
    }
    
    # Detect court
    if enhanced_features['court_enabled']:
        court_detector = enhanced_features['court_detector']
        results['court_info'] = court_detector.detect_court(frame)
    
    # Detect shuttlecock
    if enhanced_features['shuttle_enabled']:
        shuttle_tracker = enhanced_features['shuttle_tracker']
        results['shuttle_position'] = shuttle_tracker.detect_shuttlecock(frame)
    
    return results


def draw_enhanced_annotations(frame, enhanced_results):
    """
    Draw court and shuttlecock overlays
    
    Args:
        frame: Video frame
        enhanced_results: Results from enhance_frame_analysis()
        
    Returns:
        Annotated frame
    """
    annotated = frame.copy()
    
    # Draw court
    if enhanced_results.get('court_info'):
        # Simple court overlay (can be enhanced)
        cv2.putText(annotated, "Court Detected", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Draw shuttlecock
    shuttle_pos = enhanced_results.get('shuttle_position')
    if shuttle_pos:
        x, y = shuttle_pos
        cv2.circle(annotated, (x, y), 8, (0, 255, 255), -1)
        cv2.circle(annotated, (x, y), 12, (0, 255, 0), 2)
        cv2.putText(annotated, "Shuttle", (x + 15, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    
    return annotated
