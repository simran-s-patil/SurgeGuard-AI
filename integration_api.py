import json
from defense_shield import compute_frame_hash
import torch
import cv2
import numpy as np
from train_segmentation import UNet

def generate_payload(frame_path, expected_hash, model_path):
    # 1. Check Integrity
    current_hash = compute_frame_hash(frame_path)
    integrity_score = 100 if current_hash == expected_hash else 0
    
    # 2. Check Risk (U-Net)
    device = torch.device('cpu')
    model = UNet().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()
    
    img = cv2.imread(frame_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_tensor = torch.tensor(cv2.resize(img_rgb, (128, 128)).astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0)
    
    with torch.no_grad():
        output = model(img_tensor)
        prob = torch.sigmoid(output).squeeze().numpy()
    
    # Calculate bleeding risk score as the max probability in the frame
    risk_score = round(float(np.max(prob)) * 100, 2)
    
    payload = {
        "device_id": "laparoscope_01",
        "frame_hash": current_hash,
        "integrity_score": integrity_score,
        "risk_score": risk_score,
        "privacy_status": True,
        "alert": risk_score > 50.0
    }
    
    print(json.dumps(payload, indent=4))
    return payload

if __name__ == "__main__":
    expected = compute_frame_hash("output/images/twin_0000.png")
    print("Testing Integration Payload for original twin:")
    generate_payload("output/images/twin_0000.png", expected, "models/unet_surgeguard.pth")
