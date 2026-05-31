import torch
import cv2
import numpy as np
from pathlib import Path
from train_segmentation import UNet, SyntheticSurgicalDataset
from torch.utils.data import DataLoader

def calculate_metrics(pred, target):
    """Calculates Pixel Accuracy and Dice Coefficient."""
    pred = (pred > 0.5).float()
    
    # 1. Pixel Accuracy
    correct = (pred == target).float()
    pixel_acc = correct.sum() / correct.numel()
    
    # 2. Dice Coefficient
    intersection = (pred * target).sum()
    dice = (2. * intersection) / (pred.sum() + target.sum() + 1e-8)
    
    return pixel_acc.item(), dice.item()

def evaluate():
    print("--- SurgeGuard AI Model Evaluation ---")
    
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    MODEL_PATH = "models/unet_surgeguard.pth"
    
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model not found at {MODEL_PATH}")
        return

    # Load Model
    model = UNet().to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
    model.eval()
    
    # Load Dataset (Using the 'val' set if available, otherwise just some samples)
    dataset = SyntheticSurgicalDataset("output/images", "output/ground_truth", augment=False)
    if len(dataset) == 0:
        print("Error: No data found in output/images or output/ground_truth")
        return
        
    loader = DataLoader(dataset, batch_size=1, shuffle=False)
    
    total_acc = 0
    total_dice = 0
    count = 0
    
    print(f"Evaluating {len(dataset)} samples...")
    
    with torch.no_grad():
        for img, mask in loader:
            img, mask = img.to(DEVICE), mask.to(DEVICE)
            output = model(img)
            
            acc, dice = calculate_metrics(torch.sigmoid(output), mask)
            total_acc += acc
            total_dice += dice
            count += 1
            
    avg_acc = (total_acc / count) * 100
    avg_dice = (total_dice / count) * 100
    
    print("\n" + "="*40)
    print(f"FINAL ACCURACY REPORT")
    print("="*40)
    print(f"Average Pixel Accuracy:  {avg_acc:.2f}%")
    print(f"Average Dice Coefficient: {avg_dice:.2f}%")
    print("="*40)
    print("Interpretation:")
    print("- Accuracy > 90%: Excellent pixel classification.")
    print("- Dice > 80%: Strong overlap with real bleeding zones.")
    print("="*40)

if __name__ == "__main__":
    import os
    evaluate()
