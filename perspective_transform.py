"""
Perspective Transform Module
Adapted from deepaktalwardt/badminton-pose-analysis
Normalizes camera perspectives using court boundaries

Enables:
- Multi-angle video analysis
- Accurate distance measurements
- Pose comparison across different camera setups
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List


class PerspectiveTransformer:
    """Handles perspective transformation for court normalization"""
    
    def __init__(self):
        # Standard badminton singles court dimensions (meters)
        self.COURT_LENGTH = 13.4  # meters
        self.COURT_WIDTH = 6.1    # meters
        
        # Standard court keypoints (in meters from corner)
        self.standard_court_points = np.array([
            [0, 0],                          # Top-left
            [self.COURT_WIDTH, 0],           # Top-right
            [self.COURT_WIDTH, self.COURT_LENGTH],  # Bottom-right
            [0, self.COURT_LENGTH]           # Bottom-left
        ], dtype=np.float32)
        
        self.transform_matrix = None
        self.inverse_matrix = None
    
    def compute_homography(self, detected_court_points: np.ndarray) -> bool:
        """
        Compute homography matrix from detected court corners
        
        Args:
            detected_court_points: 4 corner points of detected court (x, y)
            
        Returns:
            True if successful, False otherwise
        """
        if detected_court_points is None or len(detected_court_points) != 4:
            return False
        
        try:
            # Compute homography matrix
            self.transform_matrix, _ = cv2.findHomography(
                detected_court_points,
                self.standard_court_points
            )
            
            # Compute inverse for reverse transformation
            self.inverse_matrix = np.linalg.inv(self.transform_matrix)
            
            return True
        except Exception as e:
            print(f"Homography computation failed: {e}")
            return False
    
    def transform_point(self, point: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Transform a point from image space to normalized court space
        
        Args:
            point: (x, y) in image coordinates
            
        Returns:
            (x, y) in normalized court coordinates (meters)
        """
        if self.transform_matrix is None:
            return None
        
        try:
            # Convert to homogeneous coordinates
            pt = np.array([[point[0], point[1]]], dtype=np.float32)
            pt = pt.reshape(-1, 1, 2)
            
            # Apply transformation
            transformed = cv2.perspectiveTransform(pt, self.transform_matrix)
            
            return (float(transformed[0][0][0]), float(transformed[0][0][1]))
        except Exception as e:
            print(f"Point transformation failed: {e}")
            return None
    
    def transform_points(self, points: List[Tuple[float, float]]) -> List[Optional[Tuple[float, float]]]:
        """Transform multiple points"""
        return [self.transform_point(pt) for pt in points]
    
    def inverse_transform_point(self, point: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """Transform from normalized court space back to image space"""
        if self.inverse_matrix is None:
            return None
        
        try:
            pt = np.array([[point[0], point[1]]], dtype=np.float32)
            pt = pt.reshape(-1, 1, 2)
            transformed = cv2.perspectiveTransform(pt, self.inverse_matrix)
            return (float(transformed[0][0][0]), float(transformed[0][0][1]))
        except Exception as e:
            print(f"Inverse transformation failed: {e}")
            return None
    
    def get_birds_eye_view(self, frame: np.ndarray, 
                           output_size: Tuple[int, int] = (610, 1340)) -> Optional[np.ndarray]:
        """
        Generate bird's-eye view of the court
        
        Args:
            frame: Input frame
            output_size: Size of output image (width, height) in pixels
                        Default: 610x1340 (1 pixel = 1cm)
            
        Returns:
            Transformed frame showing bird's-eye view
        """
        if self.transform_matrix is None:
            return None
        
        try:
            # Create destination points for bird's-eye view
            dst_points = np.array([
                [0, 0],
                [output_size[0], 0],
                [output_size[0], output_size[1]],
                [0, output_size[1]]
            ], dtype=np.float32)
            
            # Compute transformation for bird's-eye view
            M = cv2.getPerspectiveTransform(
                self.standard_court_points * 100,  # Convert to cm
                dst_points
            )
            
            # Apply transformation
            birds_eye = cv2.warpPerspective(frame, M, output_size)
            
            return birds_eye
        except Exception as e:
            print(f"Bird's-eye view generation failed: {e}")
            return None
    
    def calculate_distance(self, point1: Tuple[float, float], 
                          point2: Tuple[float, float]) -> Optional[float]:
        """
        Calculate euclidean distance between two points in meters
        
        Args:
            point1, point2: Points in image coordinates
            
        Returns:
            Distance in meters
        """
        # Transform both points to court space
        pt1_court = self.transform_point(point1)
        pt2_court = self.transform_point(point2)
        
        if pt1_court is None or pt2_court is None:
            return None
        
        # Calculate euclidean distance
        distance = np.sqrt(
            (pt1_court[0] - pt2_court[0])**2 + 
            (pt1_court[1] - pt2_court[1])**2
        )
        
        return float(distance)
    
    def calculate_lunge_distance(self, standing_pos: Tuple[float, float],
                                 lunge_pos: Tuple[float, float]) -> Optional[float]:
        """
        Calculate lunge distance (important for net shots)
        
        Args:
            standing_pos: Player's standing position (x, y)
            lunge_pos: Player's lunged position (x, y)
            
        Returns:
            Lunge distance in meters
        """
        return self.calculate_distance(standing_pos, lunge_pos)
    
    def calculate_reachability(self, center_pos: Tuple[float, float],
                              positions: List[Tuple[float, float]]) -> Optional[float]:
        """
        Calculate player's reachability radius
        
        Args:
            center_pos: Player's center position
            positions: List of positions player can reach
            
        Returns:
            Average reachability radius in meters
        """
        distances = []
        for pos in positions:
            dist = self.calculate_distance(center_pos, pos)
            if dist is not None:
                distances.append(dist)
        
        if not distances:
            return None
        
        return float(np.mean(distances))
    
    def is_initialized(self) -> bool:
        """Check if transformer is ready to use"""
        return self.transform_matrix is not None


def extract_court_corners(court_keypoints: np.ndarray) -> Optional[np.ndarray]:
    """
    Extract 4 corner points from court keypoints
    
    Args:
        court_keypoints: Array of court keypoints from detection
        
    Returns:
        4x2 array of corner points [top-left, top-right, bottom-right, bottom-left]
    """
    if court_keypoints is None or len(court_keypoints) < 4:
        return None
    
    # Assuming keypoints are ordered or we need to find corners
    # This is a simplified version - adjust based on your court detector output
    
    # Find extreme points
    points = court_keypoints[:, :2]  # x, y coordinates
    
    # Top-left: min x + y
    tl = points[np.argmin(points[:, 0] + points[:, 1])]
    
    # Top-right: max x, min y
    tr = points[np.argmax(points[:, 0] - points[:, 1])]
    
    # Bottom-right: max x + y
    br = points[np.argmax(points[:, 0] + points[:, 1])]
    
    # Bottom-left: min x, max y
    bl = points[np.argmin(points[:, 0] - points[:, 1])]
    
    corners = np.array([tl, tr, br, bl], dtype=np.float32)
    
    return corners
