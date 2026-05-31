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
        self.d1 = DoubleConv(in_channels, 16)
        self.p1 = nn.MaxPool2d(2)
        self.d2 = DoubleConv(16, 32)
        self.p2 = nn.MaxPool2d(2)
        self.d3 = DoubleConv(32, 64)
        
        self.up1 = nn.ConvTranspose2d(64, 32, 2, stride=2)
        self.u1 = DoubleConv(64, 32)
        self.up2 = nn.ConvTranspose2d(32, 16, 2, stride=2)
        self.u2 = DoubleConv(32, 16)
        
        self.out = nn.Conv2d(16, out_channels, 1)

    def forward(self, x):
        c1 = self.d1(x)
        c2 = self.d2(self.p1(c1))
        c3 = self.d3(self.p2(c2))
        
        u1 = self.up1(c3)
        u1 = torch.cat([u1, c2], dim=1)
        u1 = self.u1(u1)
        
        u2 = self.up2(u1)
        u2 = torch.cat([u2, c1], dim=1)
        u2 = self.u2(u2)
        
        return self.out(u2)

# --- Dataset Loader ---
import torchvision.transforms.functional as TF
import random

class SyntheticSurgicalDataset(Dataset):
    def __init__(self, img_dir, mask_dir, augment=False):
        self.img_dir = Path(img_dir)
        self.mask_dir = Path(mask_dir)
        self.images = list(self.img_dir.glob("*.png"))
        self.augment = augment

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = str(self.images[idx])
        mask_path = str(self.mask_dir / self.images[idx].name)

        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (64, 64)) # Extremely fast training size
        
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, (64, 64))
        
        # Convert to PyTorch tensors
        image_t = torch.tensor(image.astype(np.float32) / 255.0).permute(2, 0, 1)
        mask_t = torch.tensor(mask.astype(np.float32) / 255.0).unsqueeze(0)
        
        if self.augment:
            # Spatial augmentations (applied to both)
            if random.random() > 0.5:
                image_t = TF.hflip(image_t)
                mask_t = TF.hflip(mask_t)
            if random.random() > 0.5:
                image_t = TF.vflip(image_t)
                mask_t = TF.vflip(mask_t)
                
            # Color augmentations (applied only to image)
            # Reduced hue jitter to preserve "red" blood characteristics
            hue_factor = random.uniform(-0.1, 0.1)
            image_t = TF.adjust_hue(image_t, hue_factor)
            sat_factor = random.uniform(0.8, 1.2)
            image_t = TF.adjust_saturation(image_t, sat_factor)
            bright_factor = random.uniform(0.8, 1.2)
            image_t = TF.adjust_brightness(image_t, bright_factor)

        return image_t, mask_t

from torch.utils.data import Subset

def train_unet():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = UNet().to(device)
    
    dataset_train = SyntheticSurgicalDataset("output/images", "output/ground_truth", augment=True)
    dataset_val = SyntheticSurgicalDataset("output/images", "output/ground_truth", augment=False)
    
    # If dataset is empty, skip gracefully
    if len(dataset_train) == 0:
        print("No training data found in output/images. Please generate data first.")
        return
    
    # Data Leakage Fix: Proper train/val/test split (80/10/10)
    total_size = len(dataset_train)
    train_size = int(0.8 * total_size)
    val_size = int(0.1 * total_size)
    test_size = total_size - train_size - val_size
    
    # Fixed random split for separate augment and no-augment datasets
    indices = torch.randperm(total_size).tolist()
    train_dataset = Subset(dataset_train, indices[:train_size])
    val_dataset = Subset(dataset_val, indices[train_size:train_size+val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)
    
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    import sys
    epochs = 10
    if "--epochs" in sys.argv:
        try:
            epochs = int(sys.argv[sys.argv.index("--epochs") + 1])
        except:
            pass
    print(f"Starting Training for {epochs} epochs on {device}...")
    
    from tqdm import tqdm
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
        for images, masks in pbar:
            images = images.to(device)
            masks = masks.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            pbar.set_postfix(loss=loss.item())
            
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
        
        print(f"Epoch {epoch+1}/{epochs} Summary - Train Loss: {epoch_loss/len(train_loader):.4f}, Val Loss: {val_loss/len(val_loader):.4f}", flush=True)
        
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