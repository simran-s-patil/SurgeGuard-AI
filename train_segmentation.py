import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import cv2
import numpy as np
from pathlib import Path

# --- U-Net Architecture ---
class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.conv(x)

class UNet(nn.Module):
    def __init__(self, in_channels=3, out_channels=1):
        super().__init__()
        self.d1 = DoubleConv(in_channels, 64)
        self.p1 = nn.MaxPool2d(2)
        self.d2 = DoubleConv(64, 128)
        self.p2 = nn.MaxPool2d(2)
        self.d3 = DoubleConv(128, 256)
        self.p3 = nn.MaxPool2d(2)
        self.d4 = DoubleConv(256, 512)
        
        self.up1 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.u1 = DoubleConv(512, 256)
        self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.u2 = DoubleConv(256, 128)
        self.up3 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.u3 = DoubleConv(128, 64)
        
        self.out = nn.Conv2d(64, out_channels, 1)

    def forward(self, x):
        c1 = self.d1(x)
        c2 = self.d2(self.p1(c1))
        c3 = self.d3(self.p2(c2))
        c4 = self.d4(self.p3(c3))
        
        u1 = self.up1(c4)
        u1 = torch.cat([u1, c3], dim=1)
        u1 = self.u1(u1)
        
        u2 = self.up2(u1)
        u2 = torch.cat([u2, c2], dim=1)
        u2 = self.u2(u2)
        
        u3 = self.up3(u2)
        u3 = torch.cat([u3, c1], dim=1)
        u3 = self.u3(u3)
        
        return self.out(u3)

# --- Dataset Loader ---
class SyntheticSurgicalDataset(Dataset):
    def __init__(self, img_dir, mask_dir):
        self.img_dir = Path(img_dir)
        self.mask_dir = Path(mask_dir)
        self.images = list(self.img_dir.glob("*.png"))

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = str(self.images[idx])
        mask_path = str(self.mask_dir / self.images[idx].name)

        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (128, 128)) # Smaller for fast hackathon training
        image = image.astype(np.float32) / 255.0
        image = np.transpose(image, (2, 0, 1))

        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, (128, 128))
        mask = mask.astype(np.float32) / 255.0
        mask = np.expand_dims(mask, axis=0)

        return torch.tensor(image), torch.tensor(mask)

from torch.utils.data import random_split

def train_unet():
    device = torch.device('cpu') # Forcing CPU for hackathon compatibility as requested
    model = UNet().to(device)
    
    dataset = SyntheticSurgicalDataset("output/synthetic_twins", "output/ground_truth")
    # If dataset is empty, skip gracefully
    if len(dataset) == 0:
        print("No training data found. Please run synthetic_generator.py first.")
        return
    
    # Data Leakage Fix: Proper train/val/test split (80/10/10)
    total_size = len(dataset)
    train_size = int(0.8 * total_size)
    val_size = int(0.1 * total_size)
    test_size = total_size - train_size - val_size
    
    train_dataset, val_dataset, test_dataset = random_split(dataset, [train_size, val_size, test_size])
    
    train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False)
    
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    epochs = 10
    print(f"Starting Training for {epochs} epochs on {device}...")
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        for images, masks in train_loader:
            images = images.to(device)
            masks = masks.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for images, masks in val_loader:
                images = images.to(device)
                masks = masks.to(device)
                outputs = model(images)
                loss = criterion(outputs, masks)
                val_loss += loss.item()
        
        print(f"Epoch {epoch+1}/{epochs}, Train Loss: {epoch_loss/len(train_loader):.4f}, Val Loss: {val_loss/len(val_loader):.4f}")
        
    Path("models").mkdir(exist_ok=True)
    torch.save(model.state_dict(), "models/unet_surgeguard.pth")
    print("Model saved to models/unet_surgeguard.pth")

def analyze_temporal_sequence(masks):
    """
    Analyze a sequence of 30 masks for occult bleed detection.
    If the cumulative red pixel area increases by >15% from first to last frame, trigger alert.
    """
    if len(masks) != 30:
        raise ValueError("Sequence must contain exactly 30 masks")
    
    # Compute area for first and last frame
    area_first = np.sum(masks[0])
    area_last = np.sum(masks[-1])
    
    # Check if increase >15%
    if area_last > area_first * 1.15:
        return "Occult_Bleed_Alert: Cumulative red pixel area increased by >15%"
    else:
        return "No alert"

if __name__ == "__main__":
    train_unet()