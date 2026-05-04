import torch
import torch.nn as nn
import cv2
import numpy as np
from pathlib import Path
from train_segmentation import UNet

def fgsm_attack(image, epsilon, data_grad):
    # Collect the element-wise sign of the data gradient
    sign_data_grad = data_grad.sign()
    # Create the perturbed image by adjusting each pixel of the input image
    perturbed_image = image + epsilon * sign_data_grad
    # Adding clipping to maintain [0,1] range
    perturbed_image = torch.clamp(perturbed_image, 0, 1)
    return perturbed_image

def generate_adversarial_twin(img_path, model_path, out_path, epsilon=0.05):
    device = torch.device('cpu')
    model = UNet().to(device)
    
    if not Path(model_path).exists():
        print(f"Error: Model {model_path} not found.")
        return
        
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()

    # Load image
    original_img = cv2.imread(img_path)
    if original_img is None:
        print(f"Error: Image {img_path} not found.")
        return
        
    img_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (128, 128))
    img_tensor = torch.tensor(img_resized.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0).to(device)
    
    # We want to fool the model into thinking there is NO blood (target = zeros)
    target_mask = torch.zeros((1, 1, 128, 128), dtype=torch.float32).to(device)
    
    img_tensor.requires_grad = True
    
    output = model(img_tensor)
    criterion = nn.BCEWithLogitsLoss()
    
    # Calculate loss: we want to MINIMIZE the loss w.r.t the empty mask 
    # (so it predicts no blood). Thus we take a gradient step towards the target.
    loss = criterion(output, target_mask)
    model.zero_grad()
    loss.backward()
    
    data_grad = img_tensor.grad.data
    
    # To minimize loss, we subtract the gradient sign (gradient descent on input)
    perturbed_tensor = fgsm_attack(img_tensor, -epsilon, data_grad)
    
    # Convert back to image
    perturbed_np = perturbed_tensor.squeeze().detach().permute(1, 2, 0).numpy()
    perturbed_np = (perturbed_np * 255).astype(np.uint8)
    perturbed_bgr = cv2.cvtColor(perturbed_np, cv2.COLOR_RGB2BGR)
    
    # Resize back to original size (512x512)
    perturbed_bgr = cv2.resize(perturbed_bgr, (original_img.shape[1], original_img.shape[0]))
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(out_path, perturbed_bgr)
    print(f"Adversarial Hacked Image saved to {out_path}")

if __name__ == "__main__":
    img_path = "output/images/twin_0000.png"
    model_path = "models/unet_surgeguard.pth"
    out_path = "output/adversarial/hacked_twin_0000.png"
    generate_adversarial_twin(img_path, model_path, out_path, epsilon=0.1)