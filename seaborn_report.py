import cv2
import torch
import numpy as np
import os
import glob
import random
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from train_segmentation import UNet
from phase2_aiml import UNetGradCAM

def generate_seaborn_report(img_dir, num_samples=15, out_report="output/surgeguard_performance_report.png"):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = UNet().to(device)
    model_path = "models/unet_surgeguard.pth"
    
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        print("Model loaded.")
    
    grad_cam = UNetGradCAM(model, target_layer_name='u3')
    
    # Get random images
    all_paths = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        all_paths.extend(glob.glob(os.path.join(img_dir, ext)))
    
    samples = random.sample(all_paths, min(len(all_paths), num_samples))
    
    data = []
    results_vis = []
    
    print(f"Generating report for {len(samples)} samples...")
    for path in samples:
        img = cv2.imread(path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_input = cv2.resize(img_rgb, (128, 128))
        img_tensor = torch.tensor(img_input.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0).to(device)
        
        heatmap, pred_mask = grad_cam.generate_heatmap(img_tensor)
        red_area = np.sum(pred_mask > 0.5)
        
        data.append({
            "Filename": os.path.basename(path),
            "RedArea": red_area,
            "Status": "BLEED" if red_area > 500 else "NORMAL" # Simple threshold for report
        })
        results_vis.append((img_rgb, pred_mask, heatmap))

    df = pd.DataFrame(data)
    
    # Create the Visual Report
    sns.set_theme(style="darkgrid")
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 4)
    
    # Plot 1: Distribution of Red Areas
    ax1 = fig.add_subplot(gs[0, :2])
    sns.histplot(data=df, x="RedArea", hue="Status", kde=True, ax=ax1, palette="magma")
    ax1.set_title("Distribution of Detected Bleed Areas", fontsize=16)
    
    # Plot 2: Status Breakdown
    ax2 = fig.add_subplot(gs[0, 2:])
    df["Status"].value_counts().plot.pie(autopct='%1.1f%%', ax=ax2, colors=['#ff9999','#66b3ff'])
    ax2.set_title("Detection Breakdown", fontsize=16)
    
    # Plot 3-6: Sample Visuals
    for i in range(4):
        if i < len(results_vis):
            ax_img = fig.add_subplot(gs[1, i])
            ax_img.imshow(results_vis[i][0])
            ax_img.set_title(f"Sample {i+1}: Original", fontsize=10)
            ax_img.axis('off')
            
            ax_heat = fig.add_subplot(gs[2, i])
            # Blend heatmap for visual report
            h = cv2.resize(results_vis[i][2], (results_vis[i][0].shape[1], results_vis[i][0].shape[0]))
            ax_heat.imshow(results_vis[i][0])
            ax_heat.imshow(h, cmap='jet', alpha=0.5)
            ax_heat.set_title(f"Sample {i+1}: AI Heatmap", fontsize=10)
            ax_heat.axis('off')

    plt.tight_layout()
    plt.savefig(out_report)
    print(f"Report saved to {out_report}")

if __name__ == "__main__":
    real_data = r"D:\ANIL A\archive\miccai2022_sisvse_dataset\images\real"
    generate_seaborn_report(real_data)
