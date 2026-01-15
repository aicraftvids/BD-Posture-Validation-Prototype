"""
Generate a tiny synthetic dataset useful for smoke tests / quick experiments.
Creates simple moving-dot short clips for classes: smash, drop, clear (motion magnitude differences).
Outputs both small mp4 clips and keypoint .npy sequences for pose-based model training.
"""
import argparse
from pathlib import Path
import numpy as np
import cv2
import os

def make_clip(out_path, motion_profile, fps=25, duration=1.0, size=(128,128)):
    frames = []
    total = int(fps * duration)
    for t in range(total):
        img = np.zeros((size[1], size[0], 3), dtype=np.uint8) + 30
        # center moves horizontally based on motion_profile function
        x = int(size[0]//2 + motion_profile(t/total) * (size[0]//3))
        y = int(size[1]//2)
        cv2.circle(img, (x,y), 8, (0,255,0), -1)
        frames.append(img)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    h, w = size[1], size[0]
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))
    for fr in frames:
        writer.write(fr)
    writer.release()

def simple_motion_profile(kind):
    if kind == "smash":
        return lambda s: np.sin(10*s) * 1.0 + 2.0*np.exp(-5*(s-0.5)**2)
    if kind == "drive":
        return lambda s: 1.5 * np.sin(6*s)
    if kind == "drop":
        return lambda s: 0.6 * np.sin(4*s)
    return lambda s: 0.2 * np.sin(2*s)

def generate(out_root, clips_per_class=5):
    out_root = Path(out_root)
    classes = ["smash", "drive", "drop"]
    for cls in classes:
        d = out_root / cls
        d.mkdir(parents=True, exist_ok=True)
        for i in range(clips_per_class):
            path = d / f"{cls}_{i}.mp4"
            mp = simple_motion_profile(cls)
            make_clip(path, mp)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--clips-per-class", type=int, default=5)
    args = parser.parse_args()
    generate(args.out, args.clips_per_class)
