import cv2
import torch
import numpy as np
from pathlib import Path
from train_segmentation import UNet
import torch.nn.functional as F

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        target_layer.register_forward_hook(self.save_activation)
        target_layer.register_backward_hook(self.save_gradient)
    
    def save_activation(self, module, input, output):
        self.activations = output
    
    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]
    
    def __call__(self, input_tensor, class_idx=None):
        self.model.eval()
        output = self.model(input_tensor)
        
        if class_idx is None:
            class_idx = 1  # Assume bleed class is 1
        
        # For segmentation, we need to backward on the output
        # Since output is (B,1,H,W), we can sum over spatial dims for each pixel or global
        # For simplicity, backward on the mean of the output (for bleed areas)
        output[:, class_idx, :, :].mean().backward()
        
        gradients = self.gradients
        activations = self.activations
        
        # Global average pooling on gradients
        weights = torch.mean(gradients, dim=[2, 3], keepdim=True)
        
        # Weighted combination of activations
        cam = torch.sum(weights * activations, dim=1, keepdim=True)
        cam = F.relu(cam)
        
        # Normalize
        cam = cam - cam.min()
        cam = cam / cam.max()
        
        return cam.squeeze().detach().numpy()

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

    # For Grad-CAM, target the last conv layer before output
    target_layer = model.out  # The last conv layer
    grad_cam = GradCAM(model, target_layer)

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
            
        # Grad-CAM
        cam = grad_cam(img_tensor)
        cam_resized = cv2.resize(cam, (img.shape[1], img.shape[0]))
        
        prob_resized = cv2.resize(prob, (img.shape[1], img.shape[0]))
        return prob_resized, cam_resized

    prob_orig, cam_orig = run_inference(orig_img)
    prob_hacked, cam_hacked = run_inference(hacked_img)

    heatmap_orig = overlay_heatmap(orig_img, cam_orig)  # Use Grad-CAM for heatmap
    heatmap_hacked = overlay_heatmap(hacked_img, cam_hacked)

    # Combine into 1x3 grid: Original, Grad-CAM Heatmap, Hacked Image
    combined = np.hstack((orig_img, heatmap_orig, hacked_img))
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(out_path, combined)
    print(f"Comparison image with Grad-CAM saved to {out_path}")

if __name__ == "__main__":
    orig_path = "output/images/twin_0000.png"
    hacked_path = "output/adversarial/hacked_twin_0000.png"
    model_path = "models/unet_surgeguard.pth"
    out_path = "output/adversarial/comparison.png"
    
    generate_comparison(orig_path, hacked_path, model_path, out_path)