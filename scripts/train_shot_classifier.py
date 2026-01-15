"""
A simple transfer-learning script that fine-tunes a torchvision video model (r3d_18)
on a dataset organized as:
datasets/
  train/
    class1/
    class2/
  val/
    class1/
    class2/

This script is intentionally simple and meant as a starting point.
"""
import argparse
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
from torch.utils.data import DataLoader, Dataset
import numpy as np

class SimpleVideoDataset(Dataset):
    def __init__(self, root_dir, classes, num_frames=16):
        self.root_dir = Path(root_dir)
        self.samples = []
        self.num_frames = num_frames
        for idx, cls in enumerate(classes):
            p = self.root_dir / cls
            if not p.exists():
                continue
            for vid in p.glob("*.mp4"):
                self.samples.append((str(vid), idx))
    def __len__(self):
        return len(self.samples)
    def __getitem__(self, i):
        path, label = self.samples[i]
        from torchvision.io import read_video
        vr, _, _ = read_video(path, pts_unit='sec')
        total = vr.shape[0]
        if total == 0:
            # return zeros to avoid crashing; caller should handle
            import torch
            return torch.zeros((3, self.num_frames, 112, 112)), label
        indices = np.linspace(0, total-1, self.num_frames).astype(int)
        frames = vr[indices]  # (T, H, W, C)
        frames = frames.permute(3,0,1,2).float() / 255.0  # (C, T, H, W)
        return frames, label

def collate_fn(batch):
    xs = [b[0] for b in batch]
    ys = [b[1] for b in batch]
    import torch
    x = torch.stack(xs, dim=0)
    y = torch.tensor(ys, dtype=torch.long)
    return x, y

def train(args):
    train_root = Path(args.data_root) / "train"
    classes = [p.name for p in train_root.iterdir() if p.is_dir()]
    classes.sort()
    print("Classes:", classes)
    train_ds = SimpleVideoDataset(train_root, classes, num_frames=args.num_frames)
    val_ds = SimpleVideoDataset(Path(args.data_root) / "val", classes, num_frames=args.num_frames)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torchvision.models.video.r3d_18(pretrained=True)
    model.fc = nn.Linear(model.fc.in_features, len(classes))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    for epoch in range(args.epochs):
        model.train()
        total_loss = 0.0
        total = 0
        correct = 0
        for x, y in train_loader:
            x = x.to(device)
            y = y.to(device)
            optimizer.zero_grad()
            outputs = model(x)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * x.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += x.size(0)
        train_acc = correct / total if total else 0.0
        print(f"Epoch {epoch+1}/{args.epochs} train_loss={total_loss/total:.4f} train_acc={train_acc:.3f}")

        # validation
        model.eval()
        total = 0
        correct = 0
        with torch.no_grad():
            for x, y in val_loader:
                x = x.to(device)
                y = y.to(device)
                outputs = model(x)
                preds = outputs.argmax(dim=1)
                correct += (preds == y).sum().item()
                total += x.size(0)
        val_acc = correct / total if total else 0.0
        print(f"Validation acc: {val_acc:.3f}")

        # checkpoint
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ckpt_path = out_dir / f"shot_model_epoch{epoch+1}.pth"
        torch.save({"model_state_dict": model.state_dict(), "classes": classes}, ckpt_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, help="Root with train/val subfolders")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--num-frames", type=int, default=16)
    parser.add_argument("--output-dir", default="models")
    args = parser.parse_args()
    train(args)
