# Badminton Posture & Shot Analyzer — Full Implementation

This repository contains an end-to-end prototype to:
- Upload a badminton video via a backend server (FastAPI).
- Extract pose keypoints (MediaPipe) and detect contact frame.
- Evaluate posture at/around contact frame with refined angle-based rules.
- Annotate output video and produce a JSON coaching report.
- Optionally run a PyTorch video classifier (r3d_18) or a Pose-Sequence LSTM model trained on keypoints.
- Prepare datasets (synthetic generator), train models, and produce a sample checkpoint.
- A simple static frontend for uploads is included (static/index.html).

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
