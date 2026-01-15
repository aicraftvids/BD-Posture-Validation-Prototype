"""
Court Detection Module
Adapted from SoloShuttlePose by Wuzhou Sun et al.
https://github.com/sunwuzhou03/SoloShuttlePose
Licensed under MIT License

Simplified for integration with BD-Posture-Validation-Prototype
"""

import torch
import cv2
import numpy as np
from typing import Optional, Dict, Tuple
import os


class CourtDetector:
    """Detects badminton court boundaries and keypoints"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.court_keypoints = None
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def load_model(self, model_path: str):
        """Load pre-trained court detection model"""
        try:
            self.model = torch.load(model_path, map_location=self.device)
            self.model.eval()
            print(f"Court detection model loaded from {model_path}")
        except Exception as e:
            print(f"Warning: Could not load court model: {e}")
            self.model = None
    
    def detect_court(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Detect court in a single frame
        
        Returns:
            Dict with court keypoints and confidence, or None if no model
        """
        if self.model is None:
            return self._fallback_detection(frame)
        
        try:
            # Preprocess frame
            img_tensor = self._preprocess(frame)
            
            # Run detection
            with torch.no_grad():
                predictions = self.model([img_tensor.to(self.device)])
            
            if len(predictions) > 0 and len(predictions[0]['keypoints']) > 0:
                keypoints = predictions[0]['keypoints'][0].cpu().numpy()
                scores = predictions[0]['keypoints_scores'][0].cpu().numpy()
                
                return {
                    'keypoints': keypoints,
                    'scores': scores,
                    'detected': True
                }
        except Exception as e:
            print(f"Court detection error: {e}")
        
        return None
    
    def _preprocess(self, frame: np.ndarray) -> torch.Tensor:
        """Preprocess frame for model input"""
        # Convert BGR to RGB
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Normalize to [0, 1]
        img = img.astype(np.float32) / 255.0
        # Convert to tensor (C, H, W)
        img_tensor = torch.from_numpy(img).permute(2, 0, 1)
        return img_tensor
    
    def _fallback_detection(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Fallback court detection using traditional CV when model unavailable
        Uses line detection to find court boundaries
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, 
                                minLineLength=100, maxLineGap=10)
        
        if lines is not None and len(lines) > 4:
            # Simple heuristic: assume court is present
            return {
                'keypoints': None,
                'scores': None,
                'detected': True,
                'method': 'fallback'
            }
        
        return None
    
    def draw_court(self, frame: np.ndarray, court_info: Dict) -> np.ndarray:
        """Draw court overlay on frame"""
        annotated = frame.copy()
        
        if court_info is None or not court_info.get('detected'):
            return annotated
        
        keypoints = court_info.get('keypoints')
        if keypoints is not None:
            # Draw keypoints
            for i, (x, y, v) in enumerate(keypoints):
                if v > 0:  # Visible keypoint
                    cv2.circle(annotated, (int(x), int(y)), 5, (0, 255, 0), -1)
                    cv2.putText(annotated, str(i), (int(x)+10, int(y)), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Draw court lines (connect keypoints)
            self._draw_court_lines(annotated, keypoints)
        
        return annotated
    
    def _draw_court_lines(self, frame: np.ndarray, keypoints: np.ndarray):
        """Draw court boundary lines"""
        # Standard badminton court keypoint connections
        # Adjust based on your keypoint model structure
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Outer boundary
            (4, 5), (5, 6), (6, 7), (7, 4),  # Service lines
        ]
        
        for start_idx, end_idx in connections:
            if start_idx < len(keypoints) and end_idx < len(keypoints):
                start = keypoints[start_idx]
                end = keypoints[end_idx]
                if start[2] > 0 and end[2] > 0:  # Both visible
                    cv2.line(frame, 
                           (int(start[0]), int(start[1])),
                           (int(end[0]), int(end[1])),
                           (0, 255, 255), 2)
    
    def get_court_region(self, frame_shape: Tuple[int, int]) -> Optional[Tuple]:
        """
        Get court bounding region for cropping/normalization
        
        Returns:
            (x, y, w, h) tuple or None
        """
        if self.court_keypoints is None:
            return None
        
        keypoints = self.court_keypoints
        valid_points = keypoints[keypoints[:, 2] > 0]
        
        if len(valid_points) < 4:
            return None
        
        x_min = int(valid_points[:, 0].min())
        x_max = int(valid_points[:, 0].max())
        y_min = int(valid_points[:, 1].min())
        y_max = int(valid_points[:, 1].max())
        
        return (x_min, y_min, x_max - x_min, y_max - y_min)
