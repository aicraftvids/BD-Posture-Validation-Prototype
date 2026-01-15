"""
Professional Pose Templates
Stores ideal poses for different shot types based on professional players

Enables comparison of amateur poses against professional standards
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PoseTemplate:
    """Template for a professional pose"""
    shot_type: str
    joint_angles: Dict[str, Tuple[float, float]]  # joint_name: (ideal_angle, tolerance)
    key_points: Dict[str, Tuple[float, float]]    # relative positions
    description: str


class ProfessionalPoseLibrary:
    """Library of professional badminton poses"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, PoseTemplate]:
        """Initialize pose templates based on professional players"""
        
        templates = {}
        
        # SMASH - Based on Lee Chong Wei's technique
        templates['smash'] = PoseTemplate(
            shot_type='smash',
            joint_angles={
                'right_elbow': (140.0, 15.0),      # Ideal: 140°, tolerance: ±15°
                'right_shoulder': (160.0, 20.0),    # Shoulder elevation
                'right_knee': (150.0, 20.0),        # Knee bend for power
                'left_knee': (160.0, 15.0),         # Support leg
                'torso_rotation': (45.0, 15.0),     # Body rotation
            },
            key_points={
                'racket_height': (0.9, 0.1),        # Relative to body height
                'weight_distribution': (0.6, 0.1),   # 60% on front foot
            },
            description="Professional smash technique with full arm extension and body rotation"
        )
        
        # NET DROP - Based on Tai Tzu Ying's finesse
        templates['net_drop'] = PoseTemplate(
            shot_type='net_drop',
            joint_angles={
                'right_elbow': (120.0, 20.0),       # More bent for control
                'right_knee': (90.0, 15.0),         # Deep lunge
                'left_knee': (170.0, 10.0),         # Extended back leg
                'right_ankle': (85.0, 10.0),        # Ankle flexion
            },
            key_points={
                'lunge_distance': (1.2, 0.3),       # meters from standing
                'racket_angle': (30.0, 15.0),       # degrees from horizontal
            },
            description="Net drop with deep lunge and controlled racket angle"
        )
        
        # DEFENSE - Defensive stance
        templates['defense'] = PoseTemplate(
            shot_type='defense',
            joint_angles={
                'right_elbow': (110.0, 20.0),       # Ready position
                'left_elbow': (110.0, 20.0),
                'right_knee': (130.0, 15.0),        # Bent knees for mobility
                'left_knee': (130.0, 15.0),
                'hip_angle': (100.0, 20.0),         # Low center of gravity
            },
            key_points={
                'stance_width': (0.6, 0.1),         # meters
                'center_of_gravity': (0.4, 0.1),    # relative height
            },
            description="Defensive stance with low center of gravity and quick reaction readiness"
        )
        
        # BACKHAND CLEAR
        templates['backhand'] = PoseTemplate(
            shot_type='backhand',
            joint_angles={
                'right_elbow': (150.0, 20.0),       # Extended for power
                'right_shoulder': (170.0, 15.0),    # Full extension
                'right_wrist': (160.0, 20.0),       # Wrist snap
                'torso_rotation': (-30.0, 15.0),    # Opposite rotation
            },
            key_points={
                'racket_path': (180.0, 30.0),       # Swing arc
                'follow_through': (0.8, 0.2),       # Completion percentage
            },
            description="Backhand clear with full arm extension and wrist snap"
        )
        
        return templates
    
    def get_template(self, shot_type: str) -> Optional[PoseTemplate]:
        """Get pose template for a shot type"""
        return self.templates.get(shot_type.lower())
    
    def compare_pose(self, shot_type: str, measured_angles: Dict[str, float]) -> Dict:
        """
        Compare measured angles against professional template
        
        Args:
            shot_type: Type of shot being analyzed
            measured_angles: Dict of measured joint angles
            
        Returns:
            Comparison results with deviations and recommendations
        """
        template = self.get_template(shot_type)
        
        if template is None:
            return {'error': f'No template found for {shot_type}'}
        
        results = {
            'shot_type': shot_type,
            'overall_score': 0.0,
            'deviations': {},
            'recommendations': []
        }
        
        total_score = 0
        count = 0
        
        for joint, (ideal, tolerance) in template.joint_angles.items():
            if joint in measured_angles:
                measured = measured_angles[joint]
                deviation = abs(measured - ideal)
                
                # Calculate score (0-100)
                if deviation <= tolerance:
                    score = 100 - (deviation / tolerance) * 30  # 70-100 range
                else:
                    score = max(0, 70 - (deviation - tolerance) * 2)  # Below 70
                
                total_score += score
                count += 1
                
                results['deviations'][joint] = {
                    'measured': measured,
                    'ideal': ideal,
                    'deviation': deviation,
                    'tolerance': tolerance,
                    'score': score,
                    'status': 'good' if deviation <= tolerance else 'needs_improvement'
                }
                
                # Generate recommendations
                if deviation > tolerance:
                    if measured < ideal:
                        direction = 'increase'
                        diff = ideal - measured
                    else:
                        direction = 'decrease'
                        diff = measured - ideal
                    
                    results['recommendations'].append({
                        'joint': joint,
                        'action': f'{direction.capitalize()} {joint} angle by {diff:.1f}°',
                        'current': measured,
                        'target': ideal,
                        'priority': 'high' if deviation > tolerance * 1.5 else 'medium'
                    })
        
        # Calculate overall score
        if count > 0:
            results['overall_score'] = total_score / count
        
        # Add general assessment
        if results['overall_score'] >= 85:
            results['assessment'] = 'Excellent - Very close to professional form'
        elif results['overall_score'] >= 70:
            results['assessment'] = 'Good - Minor adjustments needed'
        elif results['overall_score'] >= 50:
            results['assessment'] = 'Fair - Several areas need improvement'
        else:
            results['assessment'] = 'Needs Work - Significant form corrections required'
        
        return results
    
    def get_all_shot_types(self) -> List[str]:
        """Get list of available shot types"""
        return list(self.templates.keys())
    
    def get_ideal_angles(self, shot_type: str) -> Optional[Dict[str, float]]:
        """Get ideal angles for a shot type"""
        template = self.get_template(shot_type)
        if template:
            return {joint: ideal for joint, (ideal, _) in template.joint_angles.items()}
        return None


def calculate_consistency_score(pose_history: List[Dict[str, float]], 
                                shot_type: str) -> Dict:
    """
    Calculate consistency score across multiple attempts
    
    Args:
        pose_history: List of measured angles from multiple attempts
        shot_type: Type of shot
        
    Returns:
        Consistency analysis
    """
    if not pose_history:
        return {'error': 'No pose history provided'}
    
    # Calculate variance for each joint
    joint_variances = {}
    joint_means = {}
    
    # Get all joints that appear in history
    all_joints = set()
    for pose in pose_history:
        all_joints.update(pose.keys())
    
    for joint in all_joints:
        values = [pose.get(joint) for pose in pose_history if joint in pose]
        if values:
            joint_means[joint] = np.mean(values)
            joint_variances[joint] = np.std(values)
    
    # Calculate overall consistency score
    # Lower variance = higher consistency
    consistency_scores = {}
    for joint, variance in joint_variances.items():
        # Score: 100 for variance < 5°, decreasing for higher variance
        score = max(0, 100 - variance * 4)
        consistency_scores[joint] = {
            'mean_angle': joint_means[joint],
            'std_dev': variance,
            'consistency_score': score,
            'status': 'consistent' if variance < 10 else 'inconsistent'
        }
    
    overall_consistency = np.mean([s['consistency_score'] for s in consistency_scores.values()])
    
    return {
        'shot_type': shot_type,
        'attempts': len(pose_history),
        'overall_consistency': overall_consistency,
        'joint_consistency': consistency_scores,
        'assessment': (
            'Highly consistent' if overall_consistency >= 80 else
            'Moderately consistent' if overall_consistency >= 60 else
            'Inconsistent - needs practice'
        )
    }
