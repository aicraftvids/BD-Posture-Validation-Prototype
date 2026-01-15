"""
Model utilities for optional shot classifier inference and training helpers.

- load_model_for_inference(model_path)
- predict_video_shot(video_path, model)

This module uses torchvision video models as a convenient transfer-learning base.
Inference code assumes the model expects a tensor of shape (B, C, T, H, W) normalized per ImageNet stats.
"""
from typing import Any
import torch
import torchvision
import torchvision.transforms as T
import torchvision.io as io
import numpy as np

def load_model_for_inference(model_path: str):
    """
    Load a saved checkpoint. The checkpoint is expected to contain a state dict or full model.
    """
    device = torch.device("cpu")
    model = torchvision.models.video.r3d_18(pretrained=True)
    ckpt = torch.load(model_path, map_location=device)
    if isinstance(ckpt, dict) and 'model_state_dict' in ckpt:
        model.load_state_dict(ckpt['model_state_dict'], strict=False)
    elif isinstance(ckpt, dict) and any(k.startswith('layer') or k.startswith('fc') for k in ckpt.keys()):
        model.load_state_dict(ckpt, strict=False)
    else:
        try:
            model = ckpt
        except Exception:
            pass
    model.eval()
    return model

def read_video_clip(video_path: str, num_frames: int = 16, resize=(112, 112)):
    """
    Read a video, sample num_frames evenly, return tensor (C, T, H, W)
    """
    vr, _, _ = io.read_video(video_path, pts_unit='sec')
    total = vr.shape[0]
    if total == 0:
        raise RuntimeError("No frames in video")
    indices = np.linspace(0, total - 1, num_frames).astype(int)
    frames = vr[indices]  # (T, H, W, C)
    frames = frames.permute(0, 3, 1, 2) / 255.0  # (T, C, H, W)
    import torch
    transform = T.Compose([
        T.ConvertImageDtype(torch.float32),
        T.Resize(resize),
        T.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])
    out_frames = []
    for f in frames:
        out_frames.append(transform(f))
    out = torch.stack(out_frames, dim=1)  # (C, T, H, W)
    return out

def predict_video_shot(video_path: str, model: Any, device: str = "cpu", num_frames: int = 16):
    import torch
    inp = read_video_clip(video_path, num_frames=num_frames)
    inp = inp.unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(inp)
        if isinstance(out, tuple) or isinstance(out, list):
            out = out[0]
        probs = torch.nn.functional.softmax(out, dim=1)
        top1 = torch.argmax(probs, dim=1).item()
    return {"pred_index": int(top1), "top_confidence": float(probs[0, top1])}
