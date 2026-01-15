import cv2
import mediapipe as mp
import numpy as np
from collections import defaultdict
from moviepy import ImageSequenceClip
from typing import Dict, Any, List, Optional
import math
import os
from datetime import datetime

# Import new features (v1.1 and v1.2)
try:
    from court_detector import CourtDetector
    from shuttlecock_tracker import ShuttlecockTracker
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False
    print("Enhanced features (v1.1) not available")

try:
    from perspective_transform import PerspectiveTransformer, extract_court_corners
    from professional_poses import ProfessionalPoseLibrary
    from advanced_analysis import AdvancedAnalyzer
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False
    print("Advanced features (v1.2) not available")

mp_pose = mp.solutions.pose

# geometry helpers
def angle_between_points(a, b, c):
    """
    Compute angle ABC (in degrees) where b is vertex.
    a, b, c are (x, y) tuples.
    Returns None if points invalid.
    """
    try:
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        ba = a - b
        bc = c - b
        if np.linalg.norm(ba) == 0 or np.linalg.norm(bc) == 0:
            return None
        cosang = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        cosang = float(max(min(cosang, 1.0), -1.0))
        ang = math.degrees(math.acos(cosang))
        return ang
    except Exception:
        return None

def normalize_landmarks(landmarks, w, h):
    pts = []
    for lm in landmarks:
        pts.append((lm.x * w, lm.y * h))
    return pts

def draw_landmarks_on_image(image, landmarks):
    annotated = image.copy()
    for (x, y) in landmarks:
        if x is None or y is None:
            continue
        cv2.circle(annotated, (int(x), int(y)), 3, (0, 255, 0), -1)
    connections = [
        (11, 13), (13, 15),  # left arm
        (12, 14), (14, 16),  # right arm
        (11, 12),            # shoulders
        (23, 25), (25, 27),  # left leg
        (24, 26), (26, 28),  # right leg
        (23, 24),            # hips
    ]
    for a, b in connections:
        if a < len(landmarks) and b < len(landmarks):
            xa, ya = landmarks[a]
            xb, yb = landmarks[b]
            if xa is None or ya is None or xb is None or yb is None:
                continue
            # Changed to green to match keypoints
            cv2.line(annotated, (int(xa), int(ya)), (int(xb), int(yb)), (0, 255, 0), 2)
    return annotated

# contact detection using wrist velocity
def detect_contact_frame_by_wrist(landmarks_seq: List[List[tuple]]):
    """
    Returns best_frame_index, avg_wrist_velocity, velocities_list
    Uses both wrists (if present) and returns the frame index with max combined instantaneous velocity.
    """
    velocities = []
    for i in range(1, len(landmarks_seq)):
        prev = landmarks_seq[i-1]
        cur = landmarks_seq[i]
        vel = 0.0
        for idx in (15, 16):  # left wrist, right wrist
            if idx < len(prev) and idx < len(cur):
                pv = prev[idx]
                cv = cur[idx]
                if pv[0] is not None and cv[0] is not None:
                    vel += math.hypot(cv[0]-pv[0], cv[1]-pv[1])
        velocities.append(vel)
    if not velocities:
        return 0, 0.0, velocities
    best_idx = int(np.argmax(velocities)) + 1  # +1 because velocities computed from frame diffs
    avg_v = float(np.mean(velocities))
    return best_idx, avg_v, velocities

def detect_shot_by_heuristic(keypoint_seq: List[List[tuple]]):
    """
    Fallback heuristic: uses wrist velocity around contact to guess shot type.
    """
    contact_idx, avg_v, velocities = detect_contact_frame_by_wrist(keypoint_seq)
    # thresholds tuned for prototype; adjust with real data
    if avg_v > 40:
        return "smash"
    elif avg_v > 18:
        return "drive/clear"
    elif avg_v > 6:
        return "drop"
    else:
        return "net/unknown"

# optional model inference (PyTorch) — kept modular and optional
def try_run_shot_model(video_path: str, model_path: Optional[str]):
    if not model_path:
        return None, "no_model"
    try:
        import torch
        from model_utils import load_model_for_inference, predict_video_shot
    except Exception as e:
        return None, f"torch_import_error: {e}"
    try:
        model = load_model_for_inference(model_path)
        pred = predict_video_shot(video_path, model)
        return pred, "model_ok"
    except Exception as e:
        return None, f"inference_error: {e}"

# posture evaluation focusing on contact frame (+/- neighborhood)
def evaluate_posture(landmarks_seq: List[List[tuple]], contact_idx: int, neighborhood: int = 3):
    """
    Evaluate posture by inspecting frames in [contact_idx - neighborhood, contact_idx + neighborhood].
    Returns structured report including measured angles and suggestions.
    """
    N = len(landmarks_seq)
    if N == 0:
        return {
            "frames_inspected": 0,
            "angle_stats": {},
            "suggestions": [],
            "raw_counts": {}
        }
    start = max(0, contact_idx - neighborhood)
    end = min(N - 1, contact_idx + neighborhood)
    angle_records = defaultdict(list)
    frames_checked = 0
    for i in range(start, end + 1):
        lm = landmarks_seq[i]
        frames_checked += 1
        try:
            left_hip = lm[23]
            right_hip = lm[24]
            left_knee = lm[25]
            right_knee = lm[26]
            left_ankle = lm[27]
            right_ankle = lm[28]
            left_shoulder = lm[11]
            right_shoulder = lm[12]
            left_elbow = lm[13]
            right_elbow = lm[14]
            left_wrist = lm[15]
            right_wrist = lm[16]
        except Exception:
            continue

        # knee angles
        lk_ang = angle_between_points(left_hip, left_knee, left_ankle)
        rk_ang = angle_between_points(right_hip, right_knee, right_ankle)

        # elbow angles
        le_ang = angle_between_points(left_shoulder, left_elbow, left_wrist)
        re_ang = angle_between_points(right_shoulder, right_elbow, right_wrist)

        # torso lean: angle between shoulder-mid to hip-mid vs vertical
        torso_angle = None
        try:
            shoulder_mid = ((left_shoulder[0]+right_shoulder[0])/2, (left_shoulder[1]+right_shoulder[1])/2)
            hip_mid = ((left_hip[0]+right_hip[0])/2, (left_hip[1]+right_hip[1])/2)
            dx = shoulder_mid[0] - hip_mid[0]
            dy = shoulder_mid[1] - hip_mid[1]
            if dx != 0 or dy != 0:
                torso_angle = abs(math.degrees(math.atan2(dx, dy)))  # 0=vertical
        except Exception:
            torso_angle = None

        # record
        if lk_ang is not None:
            angle_records['left_knee'].append(lk_ang)
        if rk_ang is not None:
            angle_records['right_knee'].append(rk_ang)
        if le_ang is not None:
            angle_records['left_elbow'].append(le_ang)
        if re_ang is not None:
            angle_records['right_elbow'].append(re_ang)
        if torso_angle is not None:
            angle_records['torso_angle'].append(torso_angle)

    # aggregate stats
    stats = {}
    for k, vals in angle_records.items():
        try:
            stats[k] = {
                "mean": float(np.mean(vals)),
                "median": float(np.median(vals)),
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
                "samples": int(len(vals))
            }
        except Exception:
            stats[k] = {"samples": int(len(vals))}

    # rules & suggestions (rule-based coaching heuristics)
    suggestions = []
    raw_counts = {}

    # knee flex guidance
    lk_mean = stats.get('left_knee', {}).get('mean', None)
    rk_mean = stats.get('right_knee', {}).get('mean', None)
    if lk_mean and rk_mean:
        if lk_mean > 155 and rk_mean > 155:
            suggestions.append("Both knees appear very straight near contact — increase knee flex (aim ~120-140°) to lower center of gravity.")
            raw_counts["knee_too_straight"] = 1
        elif lk_mean < 100 or rk_mean < 100:
            suggestions.append("One knee is very bent (angle < 100°). Ensure weight distribution and avoid over-bending to prevent strain.")
            raw_counts["knee_over_bent"] = 1

    # elbow extension
    re_mean = stats.get('right_elbow', {}).get('mean', None)
    le_mean = stats.get('left_elbow', {}).get('mean', None)
    if re_mean:
        if re_mean < 140:
            suggestions.append("Racket-arm (right) elbow is not extended at contact; work on full extension drills to add power.")
            raw_counts["elbow_not_extended"] = 1
    if le_mean:
        if le_mean < 140:
            suggestions.append("Racket-arm (left) elbow is not extended at contact; consider extension drills.")
            raw_counts["elbow_not_extended_left"] = 1

    # torso angle
    torso_mean = stats.get('torso_angle', {}).get('mean', None)
    if torso_mean:
        if torso_mean > 25:
            suggestions.append("Significant torso lateral lean detected; work on core and footwork to keep torso more vertical at contact.")
            raw_counts["torso_large_lean"] = 1

    summary = {
        "frames_inspected": frames_checked,
        "angle_stats": stats,
        "suggestions": suggestions,
        "raw_counts": raw_counts
    }
    return summary

def process_video(input_path: str, output_path: str, shot_model_path: Optional[str] = None,
                 enable_court_detection: bool = True,
                 enable_shuttle_tracking: bool = True,
                 enable_advanced_analysis: bool = True) -> Dict[str, Any]:
    """
    Enhanced Pipeline (v1.2):
    - Read frames
    - Run MediaPipe Pose
    - Detect court boundaries (v1.1) - optional
    - Track shuttlecock (v1.1) - optional
    - Collect keypoints
    - Detect contact frame (enhanced with ball tracking)
    - Apply perspective transform (v1.2) - optional
    - Run optional model-based shot classifier
    - Evaluate posture at contact
    - Compare to professional poses (v1.2) - optional
    - Calculate distance measurements (v1.2) - optional
    - Write annotated video and return enhanced report
    """
    # Initialize enhanced features based on flags
    court_detector = None
    shuttle_tracker = None
    advanced_analyzer = None
    
    if ENHANCED_FEATURES_AVAILABLE and (enable_court_detection or enable_shuttle_tracking):
        if enable_court_detection:
            court_detector = CourtDetector()
        if enable_shuttle_tracking:
            shuttle_tracker = ShuttlecockTracker()
        print(f"✓ Enhanced features (v1.1) initialized: court={enable_court_detection}, shuttle={enable_shuttle_tracking}")
    
    if ADVANCED_FEATURES_AVAILABLE and enable_advanced_analysis:
        advanced_analyzer = AdvancedAnalyzer()
        print("✓ Advanced features (v1.2) initialized")
    
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frames = []
    landmarks_seq = []
    shuttle_positions = []
    court_detected = False
    court_info = None

    with mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        frame_idx = 0
        success, frame = cap.read()
        while success:
            h, w = frame.shape[:2]
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)
            normalized = [(None, None)] * 33
            
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                pts = normalize_landmarks(lm, w, h)
                normalized = pts
                annotated = draw_landmarks_on_image(frame, pts)
            else:
                annotated = frame.copy()
            
            # v1.1: Detect court (only on first few frames for efficiency)
            if court_detector and not court_detected and frame_idx < 10:
                court_result = court_detector.detect_court(frame)
                if court_result and court_result.get('detected'):
                    court_info = court_result
                    court_detected = True
                    # Initialize perspective transform if advanced features available
                    if advanced_analyzer and court_result.get('keypoints') is not None:
                        advanced_analyzer.initialize_perspective(court_result['keypoints'])
                    print(f"✓ Court detected at frame {frame_idx}")
            
            # v1.1: Track shuttlecock
            shuttle_pos = None
            if shuttle_tracker:
                shuttle_pos = shuttle_tracker.detect_shuttlecock(frame)
                shuttle_positions.append(shuttle_pos)
                
                # Draw shuttlecock on annotated frame
                if shuttle_pos:
                    cv2.circle(annotated, shuttle_pos, 8, (0, 255, 255), -1)
                    cv2.circle(annotated, shuttle_pos, 12, (0, 255, 0), 2)
            
            # Draw court overlay if detected
            if court_detected and court_detector and court_info:
                annotated = court_detector.draw_court(annotated, court_info)
            
            frames.append(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
            landmarks_seq.append(normalized)
            frame_idx += 1
            success, frame = cap.read()

    cap.release()

    # Enhanced contact detection (v1.1): combine wrist velocity + ball tracking
    contact_idx, avg_wrist_v, wrist_vels = detect_contact_frame_by_wrist(landmarks_seq)
    
    # Refine contact detection with shuttlecock tracking
    if shuttle_tracker and any(shuttle_positions):
        # Extract wrist positions for comparison
        wrist_positions = []
        for lm in landmarks_seq:
            if len(lm) > 16 and lm[16][0] is not None:
                wrist_positions.append(lm[16])  # Right wrist
            else:
                wrist_positions.append(None)
        
        # Find contact using ball-wrist proximity
        ball_contact = shuttle_tracker.detect_contact_frame(shuttle_positions, wrist_positions)
        if ball_contact is not None:
            contact_idx = ball_contact
            print(f"✓ Contact refined using shuttlecock tracking: frame {contact_idx}")
    
    contact_time = contact_idx / (fps or 25)

    # run optional model
    model_shot_pred = None
    model_status = None
    if shot_model_path:
        model_shot_pred, model_status = try_run_shot_model(input_path, shot_model_path)
        if model_shot_pred is None:
            shot = detect_shot_by_heuristic(landmarks_seq)
        else:
            shot = model_shot_pred
    else:
        model_status = "no_model_provided"
        shot = detect_shot_by_heuristic(landmarks_seq)

    # posture evaluation at contact
    posture_report = evaluate_posture(landmarks_seq, contact_idx, neighborhood=3)
    
    # v1.2: Advanced analysis with perspective transform and professional comparison
    advanced_measurements = {}
    professional_comparison = {}
    
    if advanced_analyzer and court_detected:
        # Get measured angles from posture report
        measured_angles = {}
        if posture_report and 'angles' in posture_report:
            measured_angles = posture_report['angles']
        
        # Compare to professional poses
        if measured_angles:
            pro_comparison = advanced_analyzer.compare_to_professional(shot, measured_angles)
            if 'error' not in pro_comparison:
                professional_comparison = pro_comparison
                print(f"✓ Professional comparison: Score {pro_comparison.get('overall_score', 0):.1f}/100")
        
        # Calculate distance measurements with perspective transform
        if contact_idx < len(landmarks_seq):
            contact_landmarks = landmarks_seq[contact_idx]
            # Convert to dict format for advanced analyzer
            landmarks_dict = {}
            if len(contact_landmarks) > 27:
                landmarks_dict['left_ankle'] = contact_landmarks[27]
                landmarks_dict['right_ankle'] = contact_landmarks[28]
                landmarks_dict['hip_center'] = (
                    (contact_landmarks[23][0] + contact_landmarks[24][0]) / 2,
                    (contact_landmarks[23][1] + contact_landmarks[24][1]) / 2
                ) if contact_landmarks[23][0] and contact_landmarks[24][0] else None
            
            if landmarks_dict:
                adv_analysis = advanced_analyzer.analyze_with_perspective(
                    landmarks_dict, 
                    (frames[0].shape[0], frames[0].shape[1])
                )
                if adv_analysis.get('measurements'):
                    advanced_measurements = adv_analysis['measurements']
                    print(f"✓ Distance measurements calculated")

    # annotate contact frame visually on annotated frames
    annotated_frames = []
    for i, img in enumerate(frames):
        fimg = img.copy()
        if i == contact_idx:
            h, w = fimg.shape[:2]
            cv2.putText(fimg, f"CONTACT @ {contact_time:.2f}s", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            # Draw professional comparison score if available
            if professional_comparison and 'overall_score' in professional_comparison:
                score = professional_comparison['overall_score']
                cv2.putText(fimg, f"Form Score: {score:.1f}/100", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            # try to draw wrists if present
            if i < len(landmarks_seq):
                lm = landmarks_seq[i]
                for idx in (15, 16):
                    if idx < len(lm):
                        x, y = lm[idx]
                        if x is not None:
                            cv2.circle(fimg, (int(x), int(y)), 8, (0, 0, 255), -1)
        
        # Draw shuttlecock trajectory (only if enough valid detections)
        if shuttle_tracker and shuttle_positions:
            valid_count = sum(1 for pos in shuttle_positions[:i+1] if pos)
            # Only draw trajectory if we have at least 5 valid detections
            if valid_count >= 5:
                fimg = shuttle_tracker.draw_trajectory(fimg, shuttle_positions[:i+1], i)
        
        annotated_frames.append(fimg)

    # write annotated video
    clip = ImageSequenceClip(annotated_frames, fps=fps)
    tmp_out = output_path
    clip.write_videofile(tmp_out, codec="libx264", audio=False, logger=None)

    # Build enhanced report
    report = {
        "input_video": os.path.basename(input_path),
        "annotated_video": os.path.basename(output_path),
        "fps": fps,
        "frames": len(frames),
        "contact_frame_index": int(contact_idx),
        "contact_time_seconds": float(contact_time),
        "avg_wrist_velocity": float(avg_wrist_v),
        "wrist_velocity_series_length": len(wrist_vels),
        "detected_shot": shot,
        "model_status": model_status,
        "posture_report": posture_report,
        
        # v1.1 features
        "court_detected": court_detected,
        "shuttlecock_tracked": any(shuttle_positions),
        "trajectory_stats": shuttle_tracker.get_trajectory_stats() if shuttle_tracker else {},
        
        # v1.2 features
        "advanced_measurements": advanced_measurements,
        "professional_comparison": professional_comparison,
        "perspective_enabled": advanced_analyzer.perspective.is_initialized() if advanced_analyzer and advanced_analyzer.perspective else False,
        
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "version": "1.2"
    }
    
    return report
