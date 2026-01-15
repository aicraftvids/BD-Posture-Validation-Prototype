# API Quick Reference - v1.2

## Endpoint

```
POST http://localhost:8000/upload
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | File | Required | Video file to process |
| `enable_court_detection` | Boolean | `true` | Enable court boundary detection (v1.1) |
| `enable_shuttle_tracking` | Boolean | `true` | Enable shuttlecock tracking (v1.1) |
| `enable_advanced_analysis` | Boolean | `true` | Enable perspective transform and professional comparison (v1.2) |

## Usage Examples

### 1. Full Analysis (All Features)
```bash
curl -X POST http://localhost:8000/upload \
  -F 'file=@video.mp4' \
  -F 'enable_court_detection=true' \
  -F 'enable_shuttle_tracking=true' \
  -F 'enable_advanced_analysis=true'
```

**Use when:** You want comprehensive analysis with all features

**Output includes:**
- Pose detection and posture analysis
- Court boundary overlay
- Shuttlecock trajectory
- Enhanced contact detection
- Professional pose comparison
- Distance measurements

### 2. Basic Analysis (Pose Only)
```bash
curl -X POST http://localhost:8000/upload \
  -F 'file=@video.mp4' \
  -F 'enable_court_detection=false' \
  -F 'enable_shuttle_tracking=false' \
  -F 'enable_advanced_analysis=false'
```

**Use when:** You only need pose and posture analysis

**Output includes:**
- Pose detection
- Posture analysis
- Basic contact detection
- Shot classification

### 3. Court + Pose (No Shuttle)
```bash
curl -X POST http://localhost:8000/upload \
  -F 'file=@video.mp4' \
  -F 'enable_court_detection=true' \
  -F 'enable_shuttle_tracking=false' \
  -F 'enable_advanced_analysis=false'
```

**Use when:** You want court overlay but not shuttle tracking

**Output includes:**
- Pose detection
- Court boundary overlay
- Posture analysis
- Basic contact detection

### 4. Shuttle Tracking Only (No Court)
```bash
curl -X POST http://localhost:8000/upload \
  -F 'file=@video.mp4' \
  -F 'enable_court_detection=false' \
  -F 'enable_shuttle_tracking=true' \
  -F 'enable_advanced_analysis=false'
```

**Use when:** You want shuttle trajectory without court detection

**Output includes:**
- Pose detection
- Shuttlecock trajectory
- Enhanced contact detection
- Posture analysis

### 5. Advanced Analysis Only
```bash
curl -X POST http://localhost:8000/upload \
  -F 'file=@video.mp4' \
  -F 'enable_court_detection=false' \
  -F 'enable_shuttle_tracking=false' \
  -F 'enable_advanced_analysis=true'
```

**Use when:** You want professional comparison without tracking

**Output includes:**
- Pose detection
- Posture analysis
- Professional pose comparison
- Distance measurements (if perspective available)

## Response Format

```json
{
  "status": "done",
  "annotated_video": "outputs/xxx_annotated.mp4",
  "report": {
    "version": "1.2",
    "input_video": "xxx_video.mp4",
    "fps": 30.0,
    "frames": 848,
    "contact_frame_index": 750,
    "contact_time_seconds": 25.0,
    "detected_shot": "smash",
    
    "posture_report": {
      "angle_stats": {...},
      "suggestions": [...]
    },
    
    "court_detected": true,
    "shuttlecock_tracked": true,
    "trajectory_stats": {...},
    
    "advanced_measurements": {...},
    "professional_comparison": {...},
    "perspective_enabled": false,
    
    "generated_at": "2026-01-15T14:49:53.676884Z"
  }
}
```

## Feature Matrix

| Feature | Basic | +Court | +Shuttle | +Advanced | Full |
|---------|-------|--------|----------|-----------|------|
| Pose Detection | ✅ | ✅ | ✅ | ✅ | ✅ |
| Posture Analysis | ✅ | ✅ | ✅ | ✅ | ✅ |
| Contact Detection | Basic | Basic | Enhanced | Basic | Enhanced |
| Court Overlay | ❌ | ✅ | ❌ | ❌ | ✅ |
| Shuttle Trajectory | ❌ | ❌ | ✅ | ❌ | ✅ |
| Professional Comparison | ❌ | ❌ | ❌ | ✅ | ✅ |
| Distance Measurements | ❌ | ❌ | ❌ | ✅ | ✅ |
| Output Size | Smallest | Medium | Medium | Medium | Largest |
| Processing Speed | Fastest | Fast | Fast | Fast | Slower |

## Python API

```python
from processor import process_video

# Full analysis
report = process_video(
    "input.mp4",
    "output.mp4",
    enable_court_detection=True,
    enable_shuttle_tracking=True,
    enable_advanced_analysis=True
)

# Basic analysis
report = process_video(
    "input.mp4",
    "output.mp4",
    enable_court_detection=False,
    enable_shuttle_tracking=False,
    enable_advanced_analysis=False
)

# Custom combination
report = process_video(
    "input.mp4",
    "output.mp4",
    enable_court_detection=True,
    enable_shuttle_tracking=False,
    enable_advanced_analysis=True
)
```

## Performance Guidelines

### When to Enable Features

**Court Detection:**
- ✅ Enable: Fixed camera, full court visible
- ❌ Disable: Moving camera, partial court view

**Shuttle Tracking:**
- ✅ Enable: Clear shuttlecock visibility, good lighting
- ❌ Disable: Poor lighting, fast rallies, occlusion

**Advanced Analysis:**
- ✅ Enable: Need professional comparison, distance measurements
- ❌ Disable: Quick analysis, basic feedback only

### Processing Time Estimates

| Video Length | Basic | Full Features |
|--------------|-------|---------------|
| 10 seconds | ~5s | ~6s |
| 30 seconds | ~14s | ~16s |
| 1 minute | ~28s | ~32s |
| 5 minutes | ~2m20s | ~2m40s |

*Times based on 30fps video, CPU processing*

## Error Handling

### Feature Not Available
If a feature module is missing, the system will:
1. Log a warning
2. Continue with available features
3. Set feature flag to `false` in report

Example:
```json
{
  "court_detected": false,
  "shuttlecock_tracked": false,
  "advanced_measurements": {},
  "professional_comparison": {}
}
```

### Invalid Parameters
Invalid boolean values default to `true`:
```bash
# These all enable the feature
-F 'enable_court_detection=true'
-F 'enable_court_detection=1'
-F 'enable_court_detection=yes'
```

## Tips

1. **Start with full features** to see what's available
2. **Disable features** if processing is too slow
3. **Enable court detection** for better spatial analysis
4. **Enable shuttle tracking** for accurate contact detection
5. **Enable advanced analysis** for coaching feedback

## Support

For issues or questions:
- Check `server.log` for feature initialization messages
- Run `python test_integration.py` to verify setup
- See `INTEGRATION_TEST_RESULTS.md` for detailed test results
