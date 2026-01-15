"""
Advanced Analysis Module
Integrates perspective transform and professional pose comparison

New capabilities:
- Normalized pose analysis across camera angles
- Distance measurements (lunge, reachability)
- Professional pose comparison
- Consistency tracking
"""

from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    from perspective_transform import PerspectiveTransformer, extract_court_corners
    PERSPECTIVE_AVAILABLE = True
except ImportError:
    PERSPECTIVE_AVAILABLE = False

try:
    from professional_poses import ProfessionalPoseLibrary, calculate_consistency_score
    POSES_AVAILABLE = True
except ImportError:
    POSES_AVAILABLE = False


class AdvancedAnalyzer:
    """Advanced analysis with perspective transform and pro comparison"""
    
    def __init__(self):
        self.perspective = PerspectiveTransformer() if PERSPECTIVE_AVAILABLE else None
        self.pose_library = ProfessionalPoseLibrary() if POSES_AVAILABLE else None
        self.pose_history = []  # For consistency tracking
    
    def initialize_perspective(self, court_keypoints: np.ndarray) -> bool:
        """
        Initialize perspective transformer with detected court
        
        Args:
            court_keypoints: Detected court keypoints
            
        Returns:
            True if successful
        """
        if not PERSPECTIVE_AVAILABLE or self.perspective is None:
            return False
        
        corners = extract_court_corners(court_keypoints)
        if corners is None:
            return False
        
        return self.perspective.compute_homography(corners)
    
    def analyze_with_perspective(self, landmarks: Dict, 
                                 frame_shape: Tuple[int, int]) -> Dict:
        """
        Analyze pose with perspective correction
        
        Args:
            landmarks: Pose landmarks
            frame_shape: (height, width) of frame
            
        Returns:
            Analysis with distance measurements
        """
        results = {
            'perspective_enabled': False,
            'measurements': {}
        }
        
        if not self.perspective or not self.perspective.is_initialized():
            return results
        
        results['perspective_enabled'] = True
        
        # Extract key positions
        if 'left_ankle' in landmarks and 'right_ankle' in landmarks:
            left_ankle = landmarks['left_ankle']
            right_ankle = landmarks['right_ankle']
            
            # Calculate stance width in meters
            stance_width = self.perspective.calculate_distance(
                left_ankle, right_ankle
            )
            if stance_width:
                results['measurements']['stance_width'] = {
                    'value': stance_width,
                    'unit': 'meters',
                    'assessment': self._assess_stance_width(stance_width)
                }
        
        # Calculate lunge distance if applicable
        if 'hip_center' in landmarks and 'right_ankle' in landmarks:
            hip = landmarks['hip_center']
            ankle = landmarks['right_ankle']
            
            lunge_dist = self.perspective.calculate_distance(hip, ankle)
            if lunge_dist:
                results['measurements']['lunge_distance'] = {
                    'value': lunge_dist,
                    'unit': 'meters',
                    'assessment': self._assess_lunge_distance(lunge_dist)
                }
        
        return results
    
    def compare_to_professional(self, shot_type: str, 
                               measured_angles: Dict[str, float]) -> Dict:
        """
        Compare pose to professional template
        
        Args:
            shot_type: Type of shot (smash, net_drop, defense, backhand)
            measured_angles: Measured joint angles
            
        Returns:
            Comparison results with recommendations
        """
        if not POSES_AVAILABLE or self.pose_library is None:
            return {'error': 'Professional pose library not available'}
        
        return self.pose_library.compare_pose(shot_type, measured_angles)
    
    def track_consistency(self, shot_type: str, 
                         measured_angles: Dict[str, float]) -> Dict:
        """
        Track pose consistency over multiple attempts
        
        Args:
            shot_type: Type of shot
            measured_angles: Current measured angles
            
        Returns:
            Consistency analysis
        """
        # Add to history
        self.pose_history.append({
            'shot_type': shot_type,
            'angles': measured_angles
        })
        
        # Filter history for this shot type
        shot_history = [
            h['angles'] for h in self.pose_history 
            if h['shot_type'] == shot_type
        ]
        
        if len(shot_history) < 2:
            return {
                'message': 'Need at least 2 attempts for consistency analysis',
                'attempts': len(shot_history)
            }
        
        if not POSES_AVAILABLE:
            return {'error': 'Consistency tracking not available'}
        
        return calculate_consistency_score(shot_history, shot_type)
    
    def get_birds_eye_view(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Generate bird's-eye view of court"""
        if not self.perspective or not self.perspective.is_initialized():
            return None
        
        return self.perspective.get_birds_eye_view(frame)
    
    def _assess_stance_width(self, width: float) -> str:
        """Assess if stance width is appropriate"""
        if width < 0.4:
            return "Too narrow - widen stance for better balance"
        elif width > 0.8:
            return "Too wide - narrow stance for better mobility"
        else:
            return "Good stance width"
    
    def _assess_lunge_distance(self, distance: float) -> str:
        """Assess lunge distance"""
        if distance < 0.8:
            return "Short lunge - extend further for better reach"
        elif distance > 1.5:
            return "Very deep lunge - good reach but watch balance"
        else:
            return "Good lunge distance"
    
    def clear_history(self):
        """Clear pose history"""
        self.pose_history = []
    
    def get_available_features(self) -> Dict[str, bool]:
        """Check which advanced features are available"""
        return {
            'perspective_transform': PERSPECTIVE_AVAILABLE,
            'professional_comparison': POSES_AVAILABLE,
            'distance_measurements': PERSPECTIVE_AVAILABLE,
            'consistency_tracking': POSES_AVAILABLE,
            'birds_eye_view': PERSPECTIVE_AVAILABLE
        }


def create_advanced_report(basic_report: Dict, 
                          advanced_analysis: Dict,
                          pro_comparison: Optional[Dict] = None) -> Dict:
    """
    Combine basic and advanced analysis into comprehensive report
    
    Args:
        basic_report: Original posture analysis report
        advanced_analysis: Results from AdvancedAnalyzer
        pro_comparison: Optional professional comparison
        
    Returns:
        Enhanced report
    """
    enhanced = basic_report.copy()
    
    # Add advanced measurements
    if 'measurements' in advanced_analysis:
        enhanced['advanced_measurements'] = advanced_analysis['measurements']
    
    # Add professional comparison
    if pro_comparison and 'overall_score' in pro_comparison:
        enhanced['professional_comparison'] = {
            'score': pro_comparison['overall_score'],
            'assessment': pro_comparison.get('assessment', ''),
            'recommendations': pro_comparison.get('recommendations', []),
            'deviations': pro_comparison.get('deviations', {})
        }
    
    # Add perspective status
    enhanced['perspective_enabled'] = advanced_analysis.get('perspective_enabled', False)
    
    return enhanced
