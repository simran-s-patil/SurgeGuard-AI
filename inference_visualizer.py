import cv2
import torch
import numpy as np
from pathlib import Path
from train_segmentation import UNet

def overlay_heatmap(image, probability_mask, colormap=cv2.COLORMAP_JET):
    # Scale probabilities to 0-255
    heatmap = (probability_mask * 255).astype(np.uint8)
    heatmap = cv2.applyColorMap(heatmap, colormap)
    
    # Overlay using alpha blend
    overlay = cv2.addWeighted(image, 0.6, heatmap, 0.4, 0)
    return overlay

def generate_comparison(original_path, hacked_path, model_path, out_path):
    device = torch.device('cpu')
    model = UNet().to(device)
    
    if not Path(model_path).exists():
        print(f"Error: Model {model_path} not found.")
        return
        
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()

    orig_img = cv2.imread(original_path)
    hacked_img = cv2.imread(hacked_path)

    if orig_img is None or hacked_img is None:
        print("Images not found!")
        return

    # Resize for inference
    def run_inference(img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (128, 128))
        img_tensor = torch.tensor(img_resized.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0).to(device)
        
        with torch.no_grad():
            output = model(img_tensor)
            prob = torch.sigmoid(output).squeeze().numpy()
            
        prob_resized = cv2.resize(prob, (img.shape[1], img.shape[0]))
        return prob_resized

    prob_orig = run_inference(orig_img)
    prob_hacked = run_inference(hacked_img)

    heatmap_orig = overlay_heatmap(orig_img, prob_orig)
    heatmap_hacked = overlay_heatmap(hacked_img, prob_hacked)

    # Combine into 1x3 grid: Original, Orig Heatmap, Hacked Image
    combined = np.hstack((orig_img, heatmap_orig, hacked_img))
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(out_path, combined)
    print(f"Comparison image saved to {out_path}")

if __name__ == "__main__":
    orig_path = "output/images/twin_0000.png"
    hacked_path = "output/adversarial/hacked_twin_0000.png"
    model_path = "models/unet_surgeguard.pth"
    out_path = "output/adversarial/comparison.png"
    
    generate_comparison(orig_path, hacked_path, model_path, out_path)