# Integration Plan: SoloShuttlePose → BD-Posture-Validation-Prototype

## Phase 1: Analysis Complete ✅

### SoloShuttlePose Key Components Identified:

1. **Court Detection** (`src/models/CourtDetect.py`)
   - Uses Keypoint R-CNN
   - Detects court boundaries and lines
   - Model: `court_kpRCNN.pth`

2. **Shuttlecock Tracking** (`src/tools/BallDetect.py`)
   - Uses TrackNet model
   - Tracks ball trajectory
   - Event detection for hits

3. **Net Detection** (`src/models/NetDetect.py`)
   - Identifies net position
   - Uses keypoint detection

4. **Rally Extraction** (`src/tools/VideoClip.py`)
   - Auto-clips rally segments
   - Based on ball detection

---

## Phase 2: Integration Strategy

### What We'll Add to Your Project:

#### Feature 1: Court Detection (Priority: HIGH)
**Benefits:**
- Normalizes player position analysis
- Provides spatial context for posture
- Helps identify shot types by court position

**Implementation:**
- Extract court detection module
- Simplify to work without full pipeline
- Add court overlay to output video

#### Feature 2: Shuttlecock Tracking (Priority: HIGH)
**Benefits:**
- More accurate contact frame detection
- Validates wrist velocity method
- Shows ball trajectory in output

**Implementation:**
- Integrate TrackNet model
- Combine with existing contact detection
- Add trajectory visualization

#### Feature 3: Rally Extraction (Priority: MEDIUM)
**Benefits:**
- Auto-clips relevant segments
- Reduces processing time
- Focuses analysis on actual play

**Implementation:**
- Add pre-processing step
- Extract rally segments before pose analysis
- Optional feature (can be disabled)

---

## Phase 3: Technical Requirements

### New Dependencies:
```txt
# Add to requirements.txt
torchvision>=0.15.0  # Already have ✅
opencv-python>=4.8.0  # Already have ✅
pillow>=9.0.0  # Need to add
scikit-learn>=1.0.0  # For court detection
```

### Model Files Needed:
1. `court_kpRCNN.pth` (~100MB) - Court detection
2. `tracknet_model.pth` (~50MB) - Ball tracking
3. `net_kpRCNN.pth` (~80MB) - Net detection

**Total:** ~230MB of model files

---

## Phase 4: Architecture Changes

### Current Structure:
```
BD-Posture-Validation-Prototype/
├── main.py (FastAPI)
├── processor.py (Pose + Posture)
└── model_utils.py (Shot classifier)
```

### Enhanced Structure:
```
BD-Posture-Validation-Prototype/
├── main.py (FastAPI)
├── processor.py (Pose + Posture)
├── model_utils.py (Shot classifier)
├── court_detector.py (NEW - Court detection)
├── ball_tracker.py (NEW - Shuttlecock tracking)
├── rally_extractor.py (NEW - Rally clipping)
└── models/
    ├── court_kpRCNN.pth
    ├── tracknet_model.pth
    └── net_kpRCNN.pth
```

---

## Phase 5: Implementation Steps

### Step 1: Setup (15 min)
- [ ] Create new modules
- [ ] Update requirements.txt
- [ ] Add model download script

### Step 2: Court Detection (45 min)
- [ ] Extract CourtDetect class
- [ ] Simplify for standalone use
- [ ] Add to processor pipeline
- [ ] Test with sample video

### Step 3: Ball Tracking (60 min)
- [ ] Extract TrackNet integration
- [ ] Combine with contact detection
- [ ] Add trajectory visualization
- [ ] Test accuracy vs wrist velocity

### Step 4: Rally Extraction (30 min)
- [ ] Extract VideoClip logic
- [ ] Add as optional pre-processing
- [ ] Update API endpoint
- [ ] Test with full match video

### Step 5: Integration Testing (30 min)
- [ ] Test full pipeline
- [ ] Compare before/after results
- [ ] Performance benchmarking
- [ ] Update documentation

**Total Estimated Time: 3 hours**

---

## Phase 6: Expected Improvements

### Before Integration:
- ✅ Pose estimation
- ✅ Posture analysis
- ✅ Contact detection (wrist velocity)
- ❌ No court context
- ❌ No ball tracking
- ❌ Manual video trimming

### After Integration:
- ✅ Pose estimation
- ✅ Posture analysis
- ✅ Contact detection (wrist + ball)
- ✅ Court-aware analysis
- ✅ Ball trajectory visualization
- ✅ Auto rally extraction

---

## Phase 7: Licensing & Attribution

### Required Attribution:
```python
# Add to README.md and source files:
"""
Court detection, shuttlecock tracking, and rally extraction features
adapted from SoloShuttlePose by Wuzhou Sun et al.
https://github.com/sunwuzhou03/SoloShuttlePose
Licensed under MIT License
"""
```

---

## Phase 8: Rollout Plan

### Version 1.1 (Minimal Integration)
- Court detection only
- Basic ball tracking
- Keep existing features

### Version 1.2 (Full Integration)
- Rally extraction
- Enhanced visualizations
- Performance optimizations

### Version 2.0 (Future)
- Multi-player support
- Advanced tactics analysis
- Real-time processing

---

## Next Steps

1. **Confirm approach** - Proceed with integration?
2. **Download models** - Get required model files
3. **Start implementation** - Begin with court detection
4. **Iterative testing** - Test each feature independently

**Ready to proceed?**
