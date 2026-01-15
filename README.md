# Badminton Posture & Shot Analyzer — Full Implementation

This repository contains an end-to-end prototype to:
- Upload a badminton video via a backend server (FastAPI).
- Extract pose keypoints (MediaPipe) and detect contact frame.
- **🆕 Detect court boundaries and shuttlecock trajectory** (v1.1)
- **🆕 Professional pose comparison and distance measurements** (v1.2)
- Evaluate posture at/around contact frame with refined angle-based rules.
- Annotate output video and produce a JSON coaching report.
- Optionally run a PyTorch video classifier (r3d_18) or a Pose-Sequence LSTM model trained on keypoints.
- Prepare datasets (synthetic generator), train models, and produce a sample checkpoint.
- A simple static frontend for uploads is included (static/index.html).

## What's New in v1.2 🚀

✨ **Advanced Analysis** (adapted from [badminton-pose-analysis](https://github.com/deepaktalwardt/badminton-pose-analysis)):
- 🎯 **Perspective Transform**: Normalizes camera angles for accurate measurements
- 🏆 **Professional Comparison**: Compare your form against Lee Chong Wei & Tai Tzu Ying
- 📏 **Distance Measurements**: Real-world measurements (stance width, lunge distance)
- 📊 **Consistency Tracking**: Monitor form consistency across multiple attempts
- 🗺️ **Bird's-Eye View**: Top-down court visualization

## What's New in v1.1

✨ **Enhanced Features** (adapted from [SoloShuttlePose](https://github.com/sunwuzhou03/SoloShuttlePose)):
- 🎾 **Court Detection**: Automatically identifies court boundaries
- 🏸 **Shuttlecock Tracking**: Tracks ball trajectory and position
- 🎯 **Improved Contact Detection**: Combines ball tracking with wrist velocity
- 📊 **Enhanced Visualizations**: Court overlays and trajectory paths

**Documentation:**
- [ENHANCED_FEATURES.md](ENHANCED_FEATURES.md) - v1.1 setup and usage
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - v1.2 professional analysis

Quickstart (local)
1. Create a virtualenv and install:
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Run server (CPU prototype):
   uvicorn main:app --reload --port 8000

3. Open http://localhost:8000 and use the upload form.

Optional: use a trained shot classification model
- If you have a PyTorch checkpoint, set:
  export SHOT_MODEL_PATH=/path/to/checkpoint.pth
- The server will attempt to load and use it; otherwise it uses the heuristic detector.

Training examples
- To train a video classifier (r3d_18 transfer learning) use:
  python scripts/train_shot_classifier.py --data-root datasets --epochs 8 --output-dir models/video_model

- To train a pose LSTM on keypoint .npy sequences:
  python scripts/train_pose_sequence_model.py --data-root datasets/pose_npy --output-dir models/pose_lstm --epochs 10

Generate a tiny sample checkpoint (quick-run)
1. bash scripts/generate_sample_checkpoint.sh

Notes / limitations
- This is a prototype. For production, collect real annotated video data, improve models, use GPU workers, and apply calibration for robust angles.
- MediaPipe 2D poses are affected by camera perspective. Consider multi-view or depth data for precise correction suggestions.
