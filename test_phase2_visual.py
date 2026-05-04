import cv2
import torch
import numpy as np
import os
from pathlib import Path
import glob

from train_segmentation import UNet
from phase2_aiml import UNetGradCAM, overlay_gradcam

def test_on_real_data(img_dir="output/images", out_dir="output/phase2_results", num_images=5):
    device = torch.device('cpu')
    
    # Load Model
    model = UNet().to(device)
    model_path = "models/unet_surgeguard.pth"
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        print(f"Model loaded from {model_path}")
    else:
        print(f"Warning: Model weights not found at {model_path}. Using untrained model.")
        
    grad_cam = UNetGradCAM(model, target_layer_name='u3')
    
    # Ensure output directory exists
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    
    # Get image paths
    img_paths = sorted(glob.glob(f"{img_dir}/*.png"))[:num_images]
    
    if not img_paths:
        print(f"No images found in {img_dir}")
        return
        
    print(f"Testing on {len(img_paths)} images from {img_dir}...")
    
    for idx, path in enumerate(img_paths):
        # Load and preprocess image
        original_img = cv2.imread(path)
        if original_img is None:
            print(f"Failed to read {path}")
            continue
            
        img_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (128, 128))
        img_tensor = torch.tensor(img_resized.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0).to(device)
        
        # Run Grad-CAM
        heatmap, pred_mask = grad_cam.generate_heatmap(img_tensor)
        
        # Calculate red pixel area
        binary_mask = (pred_mask > 0.5).astype(np.float32)
        red_pixel_area = np.sum(binary_mask)
        
        # Overlay heatmap on original image
        overlay = overlay_gradcam(original_img, heatmap)
        
        # Resize pred_mask to match original image for visualization
        pred_mask_resized = cv2.resize(pred_mask, (original_img.shape[1], original_img.shape[0]))
        pred_mask_vis = (pred_mask_resized * 255).astype(np.uint8)
        pred_mask_colored = cv2.cvtColor(pred_mask_vis, cv2.COLOR_GRAY2BGR)
        
        # Combine Original | Prediction Mask | Grad-CAM Overlay
        combined = np.hstack((original_img, pred_mask_colored, overlay))
        
        # Save output
        filename = Path(path).name
        out_path = os.path.join(out_dir, f"gradcam_{filename}")
        cv2.imwrite(out_path, combined)
        
        print(f"Processed {filename} | Predicted Red Area (128x128 res): {red_pixel_area:.1f} | Saved: {out_path}")

if __name__ == "__main__":
    # Test on the first 10 synthetic twin images
    test_on_real_data(num_images=10)
