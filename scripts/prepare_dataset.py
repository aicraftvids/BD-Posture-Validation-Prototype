"""
Helpers to prepare a dataset of short labeled clips from longer videos.

Example usage:
python scripts/prepare_dataset.py --source-dir raw_videos --out datasets --clip-duration 1.5 --stride 1.0 --label smash
"""
import argparse
import os
from pathlib import Path
import cv2

def extract_clips_for_label(source_dir, out_dir, label, clip_duration=1.0, stride=1.0):
    source_dir = Path(source_dir)
    out_dir = Path(out_dir) / label
    out_dir.mkdir(parents=True, exist_ok=True)
    for video_file in source_dir.glob("*.mp4"):
        cap = cv2.VideoCapture(str(video_file))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total / fps
        start = 0.0
        idx = 0
        while start + clip_duration <= duration:
            cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
            frames = []
            read_frames = int(clip_duration * fps)
            for _ in range(read_frames):
                ok, frame = cap.read()
                if not ok:
                    break
                frames.append(frame)
            if frames:
                out_path = out_dir / f"{video_file.stem}_{idx}.mp4"
                h, w = frames[0].shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))
                for fr in frames:
                    writer.write(fr)
                writer.release()
            idx += 1
            start += stride
        cap.release()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--clip-duration", type=float, default=1.0)
    parser.add_argument("--stride", type=float, default=0.5)
    args = parser.parse_args()
    extract_clips_for_label(args.source_dir, args.out, args.label, args.clip_duration, args.stride)

if __name__ == "__main__":
    main()
