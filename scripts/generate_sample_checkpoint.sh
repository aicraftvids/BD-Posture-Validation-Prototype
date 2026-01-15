#!/usr/bin/env bash
set -e
echo "Generating tiny synthetic dataset..."
python scripts/generate_synthetic_dataset.py --out datasets/synthetic --clips-per-class 6

echo "Splitting into train/val for quick demo..."
mkdir -p datasets/demo/train datasets/demo/val
for cls in smash drive drop; do
  mkdir -p datasets/demo/train/$cls datasets/demo/val/$cls
  i=0
  for f in datasets/synthetic/$cls/*.mp4; do
    if [ $((i % 5)) -eq 0 ]; then
      cp "$f" datasets/demo/val/$cls/
    else
      cp "$f" datasets/demo/train/$cls/
    fi
    i=$((i+1))
  done
done

echo "Running 1 epoch training of video model (quick demo)..."
python scripts/train_shot_classifier.py --data-root datasets/demo --epochs 1 --batch-size 2 --output-dir models/sample_video_model

echo "Done. Check models/sample_video_model for checkpoint."
