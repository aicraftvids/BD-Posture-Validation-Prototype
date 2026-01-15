"""
Shuttlecock Tracking Module
Adapted from SoloShuttlePose by Wuzhou Sun et al.
https://github.com/sunwuzhou03/SoloShuttlePose
Licensed under MIT License

Simplified for integration with BD-Posture-Validation-Prototype
"""

import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict
import torch


class ShuttlecockTracker:
    """Tracks shuttlecock position and trajectory"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.trajectory = []
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str):
        """Load TrackNet model for shuttlecock detection"""
        try:
            self.model = torch.load(model_path, map_location=self.device)
            self.model.eval()
            print(f"Shuttlecock tracking model loaded from {model_path}")
        except Exception as e:
            print(f"Warning: Could not load tracking model: {e}")
            self.model = None
    
    def track_sequence(self, frames: List[np.ndarray]) -> List[Optional[Tuple[int, int]]]:
        """
        Track shuttlecock across multiple frames
        
        Args:
            frames: List of video frames
            
        Returns:
            List of (x, y) positions or None for each frame
        """
        positions = []
        
        for i, frame in enumerate(frames):
            pos = self.detect_shuttlecock(frame)
            positions.append(pos)
            
            if pos:
                self.trajectory.append((i, pos[0], pos[1]))
        
        return positions
    
    def detect_shuttlecock(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Detect shuttlecock in a single frame
        
        Returns:
            (x, y) position or None if not detected
        """
        if self.model is None:
            return self._fallback_detection(frame)
        
        try:
            # Preprocess
            img_tensor = self._preprocess(frame)
            
            # Run detection
            with torch.no_grad():
                heatmap = self.model(img_tensor.unsqueeze(0).to(self.device))
            
            # Get position from heatmap
            heatmap = heatmap.squeeze().cpu().numpy()
            return self._heatmap_to_position(heatmap, frame.shape)
            
        except Exception as e:
            print(f"Shuttlecock detection error: {e}")
            return None
    
    def _preprocess(self, frame: np.ndarray) -> torch.Tensor:
        """Preprocess frame for model"""
        # Resize to model input size (typically 512x288 for TrackNet)
        img = cv2.resize(frame, (512, 288))
        img = img.astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img).permute(2, 0, 1)
        return img_tensor
    
    def _heatmap_to_position(self, heatmap: np.ndarray, 
                            original_shape: Tuple) -> Optional[Tuple[int, int]]:
        """Convert heatmap to (x, y) position"""
        # Find maximum in heatmap
        if heatmap.max() < 0.5:  # Confidence threshold
            return None
        
        y, x = np.unravel_index(heatmap.argmax(), heatmap.shape)
        
        # Scale back to original frame size
        h, w = original_shape[:2]
        x_scaled = int(x * w / heatmap.shape[1])
        y_scaled = int(y * h / heatmap.shape[0])
        
        return (x_scaled, y_scaled)
    
    def _fallback_detection(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Fallback detection using traditional CV
        Looks for small white/yellow circular objects (shuttlecock)
        """
        # Convert to grayscale for better detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Threshold for bright objects (shuttlecock is bright white)
        _, thresh = cv2.threshold(blurred, 240, 255, cv2.THRESH_BINARY)
        
        # Morphological operations to remove noise
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Filter for shuttlecock-sized objects (small, roughly circular)
        valid_contours = []
        for c in contours:
            area = cv2.contourArea(c)
            # Shuttlecock is typically 10-200 pixels in area
            if 10 < area < 200:
                # Check circularity
                perimeter = cv2.arcLength(c, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    # Shuttlecock should be roughly circular (circularity > 0.5)
                    if circularity > 0.5:
                        valid_contours.append(c)
        
        if not valid_contours:
            return None
        
        # Get centroid of the most circular small contour
        c = max(valid_contours, key=lambda x: 4 * np.pi * cv2.contourArea(x) / (cv2.arcLength(x, True) ** 2))
        M = cv2.moments(c)
        
        if M["m00"] == 0:
            return None
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        return (cx, cy)
    
    def detect_contact_frame(self, positions: List[Optional[Tuple]], 
                            wrist_positions: List[Tuple]) -> Optional[int]:
        """
        Detect contact frame by combining ball position and wrist proximity
        
        Args:
            positions: Shuttlecock positions per frame
            wrist_positions: Wrist positions per frame
            
        Returns:
            Frame index of contact or None
        """
        contact_candidates = []
        
        for i in range(len(positions)):
            if positions[i] is None:
                continue
            
            ball_x, ball_y = positions[i]
            
            # Check proximity to wrist
            if i < len(wrist_positions):
                wrist_x, wrist_y = wrist_positions[i]
                distance = np.sqrt((ball_x - wrist_x)**2 + (ball_y - wrist_y)**2)
                
                # If ball is close to wrist (within 50 pixels)
                if distance < 50:
                    contact_candidates.append((i, distance))
        
        if not contact_candidates:
            return None
        
        # Return frame with closest proximity
        return min(contact_candidates, key=lambda x: x[1])[0]
    
    def draw_trajectory(self, frame: np.ndarray, 
                       positions: List[Optional[Tuple]],
                       current_idx: int = -1) -> np.ndarray:
        """Draw shuttlecock trajectory on frame"""
        annotated = frame.copy()
        
        # Draw trajectory line
        valid_positions = [(i, pos) for i, pos in enumerate(positions) if pos]
        
        for i in range(len(valid_positions) - 1):
            idx1, pos1 = valid_positions[i]
            idx2, pos2 = valid_positions[i + 1]
            
            # Color gradient based on time (older = darker)
            alpha = 0.3 + 0.7 * (i / len(valid_positions))
            color = (0, int(255 * alpha), int(255 * alpha))
            
            cv2.line(annotated, pos1, pos2, color, 2)
        
        # Draw current position
        if current_idx >= 0 and current_idx < len(positions):
            pos = positions[current_idx]
            if pos:
                cv2.circle(annotated, pos, 8, (0, 255, 255), -1)
                cv2.circle(annotated, pos, 12, (0, 255, 0), 2)
        
        return annotated
    
    def get_trajectory_stats(self) -> Dict:
        """Get statistics about the trajectory"""
        if not self.trajectory:
            return {}
        
        positions = np.array([(x, y) for _, x, y in self.trajectory])
        
        return {
            'total_frames': len(self.trajectory),
            'avg_x': float(positions[:, 0].mean()),
            'avg_y': float(positions[:, 1].mean()),
            'max_height': float(positions[:, 1].min()),  # Y is inverted
            'trajectory_length': len(self.trajectory)
        }
    
    def clear_trajectory(self):
        """Clear stored trajectory"""
        self.trajectory = []
