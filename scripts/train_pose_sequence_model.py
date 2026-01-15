"""
Train a simple LSTM on pose keypoint sequences saved as .npy arrays.
Expect dataset layout:
datasets/pose_npy/train/{class}/*.npy  (each .npy is (T, N, 2) or flattened shape)
"""
import argparse
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class PoseNpyDataset(Dataset):
    def __init__(self, root, classes, seq_len=32):
        self.root = Path(root)
        self.samples = []
        self.seq_len = seq_len
        for idx, cls in enumerate(classes):
            p = self.root / cls
            if not p.exists():
                continue
            for f in p.glob("*.npy"):
                self.samples.append((str(f), idx))
    def __len__(self):
        return len(self.samples)
    def __getitem__(self, i):
        path, label = self.samples[i]
        arr = np.load(path)  # expected shape (T, N, 2) or (T, D)
        if arr.ndim == 3:
            T, N, C = arr.shape
            flat = arr.reshape(T, N*C)
        else:
            flat = arr
        # pad or sample to seq_len
        if flat.shape[0] >= self.seq_len:
            indices = np.linspace(0, flat.shape[0]-1, self.seq_len).astype(int)
            seq = flat[indices]
        else:
            pad = np.zeros((self.seq_len - flat.shape[0], flat.shape[1]), dtype=flat.dtype)
            seq = np.vstack([flat, pad])
        seq = torch.tensor(seq, dtype=torch.float32).transpose(0,1)  # (D, T)
        return seq, label

class PoseLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=128, num_layers=2, num_classes=3):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=False)
        self.fc = nn.Linear(hidden_size, num_classes)
    def forward(self, x):
        # x: (B, C, T) -> LSTM expects (T, B, C)
        x = x.permute(2,0,1)
        out, (h, c) = self.lstm(x)
        # take last timestep
        last = out[-1]
        return self.fc(last)

def train(args):
    train_root = Path(args.data_root) / "train"
    classes = [p.name for p in train_root.iterdir() if p.is_dir()]
    classes.sort()
    print("Classes:", classes)
    ds = PoseNpyDataset(train_root, classes, seq_len=args.seq_len)
    val_ds = PoseNpyDataset(Path(args.data_root) / "val", classes, seq_len=args.seq_len)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=True)
    vloader = DataLoader(val_ds, batch_size=args.batch_size)

    sample_input, _ = ds[0]
    input_size = sample_input.shape[0]
    model = PoseLSTM(input_size, hidden_size=args.hidden_size, num_layers=args.num_layers, num_classes=len(classes))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(args.epochs):
        model.train()
        total = 0
        acc = 0
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)
            opt.zero_grad()
            out = model(x)
            loss = loss_fn(out, y)
            loss.backward()
            opt.step()
            preds = out.argmax(dim=1)
            acc += (preds == y).sum().item()
            total += y.size(0)
        print(f"Epoch {epoch+1}/{args.epochs} train_acc={acc/total if total else 0:.3f}")
        # save checkpoint
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        torch.save({"model_state_dict": model.state_dict(), "classes": classes}, out_dir / f"pose_lstm_epoch{epoch+1}.pth")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seq-len", dest="seq_len", type=int, default=32)
    parser.add_argument("--hidden-size", dest="hidden_size", type=int, default=128)
    parser.add_argument("--num-layers", dest="num_layers", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--output-dir", default="models/pose_lstm")
    args = parser.parse_args()
    train(args)
