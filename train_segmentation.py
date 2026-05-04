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

def train_unet():
    device = torch.device('cpu') # Forcing CPU for hackathon compatibility as requested
    model = UNet().to(device)
    
    dataset = SyntheticSurgicalDataset("output/images", "output/ground_truth")
    # If dataset is empty, skip gracefully
    if len(dataset) == 0:
        print("No training data found. Please run synthetic_generator.py first.")
        return
        
    loader = DataLoader(dataset, batch_size=4, shuffle=True)
    
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    epochs = 10
    print(f"Starting Training for {epochs} epochs on {device}...")
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        for images, masks in loader:
            images = images.to(device)
            masks = masks.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss/len(loader):.4f}")
        
    Path("models").mkdir(exist_ok=True)
    torch.save(model.state_dict(), "models/unet_surgeguard.pth")
    print("Model saved to models/unet_surgeguard.pth")

if __name__ == "__main__":
    train_unet()