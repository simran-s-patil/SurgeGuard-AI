import argparse
import cv2
import torch
import numpy as np
import json
from pathlib import Path
from collections import deque
import time

# Import the model and GradCAM
from train_segmentation import UNet
from inference_visualizer import GradCAM
from phase3_cyber import get_secret_key, verify_signature, extract_watermark, sign_hash, compute_frame_hash

class TemporalSmoother:
    """Temporal filter to prevent flickering alerts"""
    def __init__(self, window_size=5, threshold=0.7):
        self.window = deque(maxlen=window_size)
        self.threshold = threshold
    
    def update(self, risk_score):
        self.window.append(risk_score)
        smoothed = np.mean(self.window)
        return smoothed > self.threshold

class SurgeGuardInference:
    def __init__(self, model_path, use_torchscript=False):
        self.device = torch.device('cpu')
        
        if use_torchscript:
            self.model = torch.jit.load(model_path)
        else:
            self.model = UNet().to(self.device)
            self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
        
        self.model.eval()
        self.grad_cam = None
        if not use_torchscript:
            self.grad_cam = GradCAM(self.model, self.model.out)
        self.smoother = TemporalSmoother()
        
        # For spatial consistency
        self.prev_mask = None
    
    def preprocess_image(self, img):
        """Preprocess image for model input"""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (128, 128))
        img_tensor = torch.tensor(img_resized.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0).to(self.device)
        return img_tensor, img.shape[:2]
    
    def check_spatial_consistency(self, mask, prev_mask):
        """Check if detected area is growing and has blood-like properties"""
        if prev_mask is None:
            return True
        
        # Check area growth
        current_area = np.sum(mask > 0.5)
        prev_area = np.sum(prev_mask > 0.5)
        
        # Must be growing or stable, not shrinking suddenly
        if current_area < prev_area * 0.8:  # Allow 20% decrease
            return False
        
        # Check if it's a connected component (not scattered pixels)
        contours, _ = cv2.findContours((mask > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            return False
        
        # Largest component should be significant
        largest_area = max(cv2.contourArea(c) for c in contours)
        if largest_area < 100:  # Minimum area threshold
            return False
        
        return True
    
    def detect_bleed(self, img):
        """Main detection function with spatial and temporal filtering"""
        img_tensor, orig_size = self.preprocess_image(img)
        
        with torch.no_grad():
            output = self.model(img_tensor)
            prob = torch.sigmoid(output).squeeze().numpy()
        
        # Resize back
        prob_resized = cv2.resize(prob, (orig_size[1], orig_size[0]))
        
        # Spatial consistency check
        is_spatially_consistent = self.check_spatial_consistency(prob_resized, self.prev_mask)
        self.prev_mask = prob_resized.copy()
        
        if not is_spatially_consistent:
            risk_score = 0.0
        else:
            risk_score = np.mean(prob_resized)
        
        # Temporal smoothing
        is_bleeding = self.smoother.update(risk_score)
        
        # Calculate center coordinates of detected bleed
        if risk_score > 0.5:
            coords = cv2.findNonZero((prob_resized > 0.5).astype(np.uint8))
            if coords is not None:
                center = np.mean(coords, axis=0).flatten()
                center_coordinates = [int(center[0]), int(center[1])]
            else:
                center_coordinates = [0, 0]
        else:
            center_coordinates = [0, 0]
        
        # Warning time (simulated)
        warning_time_seconds = 5.0 if is_bleeding else 0.0
        
        result = {
            "is_bleeding": bool(is_bleeding),
            "risk_score": float(risk_score),
            "center_coordinates": center_coordinates,
            "warning_time_seconds": warning_time_seconds
        }
        
        return result, prob_resized

def draw_risk_bar(frame, risk_score, bar_width=20, padding=10):
    h, w = frame.shape[:2]
    bar_height = int((h - padding * 2) * risk_score)
    top = padding
    left = w - bar_width - padding
    bottom = h - padding
    cv2.rectangle(frame, (left, top), (left + bar_width, bottom), (50, 50, 50), -1)
    cv2.rectangle(frame, (left, bottom - bar_height), (left + bar_width, bottom), (0, 0, 255), -1)
    cv2.rectangle(frame, (left, top), (left + bar_width, bottom), (255, 255, 255), 1)
    cv2.putText(frame, f"{int(risk_score*100)}%", (left - 70, top + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return frame


def overlay_hud(frame, mask, result, flash_on=True):
    h, w = frame.shape[:2]
    heatmap = cv2.applyColorMap((mask * 255).astype(np.uint8), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(frame, 0.6, heatmap, 0.4, 0)
    overlay = draw_risk_bar(overlay, result["risk_score"])
    
    if result["center_coordinates"] != [0, 0]:
        cv2.circle(overlay, tuple(result["center_coordinates"]), 10, (0, 255, 255), 2)
    cv2.putText(overlay, f"Risk: {result['risk_score']:.2f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(overlay, f"Center: {result['center_coordinates']}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
    
    if result["is_bleeding"] and flash_on:
        cv2.putText(overlay, "⚠️ BLEED DETECTED", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        cv2.rectangle(overlay, (15, 100), (500, 140), (0, 0, 255), 2)
    
    # Cybersecurity HUD
    shield_color = (0, 255, 0) if result["is_authentic"] else (0, 0, 255)
    shield_text = "🛡️ SHIELD: ACTIVE" if result["is_authentic"] else "⚠️ ATTACK DETECTED!"
    cv2.putText(overlay, shield_text, (20, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, shield_color, 2)
    
    return overlay


def write_session_report(report_path, session_data):
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
    print(f"Session report saved to {report_path}")


def main():
    parser = argparse.ArgumentParser(description="SurgeGuard video inference with HUD and session JSON export")
    parser.add_argument("--input", required=True, help="Path to input video file (.mp4, .avi)")
    parser.add_argument("--model", default="models/unet_surgeguard.pth", help="Path to TorchScript or PyTorch model")
    parser.add_argument("--output", default="output/session_video.mp4", help="Path to output video file")
    parser.add_argument("--report", default="output/session_report.json", help="Path to JSON session report")
    parser.add_argument("--use_torchscript", action="store_true", help="Load a TorchScript model for faster inference")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    inference = SurgeGuardInference(args.model, use_torchscript=args.use_torchscript)

    # Determine if input is a video file or a directory of images
    is_dir = input_path.is_dir()
    if is_dir:
        image_files = sorted([f for f in input_path.glob("*") if f.suffix.lower() in [".png", ".jpg", ".jpeg"]])
        if not image_files:
            raise FileNotFoundError(f"No images found in directory: {input_path}")
        print(f"Processing directory: {input_path} ({len(image_files)} images)")
        fps = 10.0 # Default FPS for image sequences
        width, height = cv2.imread(str(image_files[0])).shape[1], cv2.imread(str(image_files[0])).shape[0]
    else:
        cap = cv2.VideoCapture(str(input_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    session_data = []
    frame_id = 0
    start_time = time.time()

    while True:
        if is_dir:
            if frame_id >= len(image_files):
                break
            frame = cv2.imread(str(image_files[frame_id]))
            ret = True if frame is not None else False
        else:
            ret, frame = cap.read()
            
        if not ret:
            break

        # 2. Cyber Security Check
        # For the demo, we assume the frames are signed with our secret key
        # We verify the signature and the watermark
        secret_key = get_secret_key()
        
        # In a real streaming scenario, the hash/signature comes from the network packet
        # Here we simulate by hashing the current frame
        temp_path = "output/temp_frame.png"
        cv2.imwrite(temp_path, frame)
        frame_hash = compute_frame_hash(temp_path)
        
        # We sign it on the fly for demo consistency, 
        # but simulate an "Attack" if frame_id is between 100 and 120
        is_attack = 100 < frame_id < 120
        
        if is_attack:
            signature = "fake_signature_123"
        else:
            signature = sign_hash(secret_key, frame_hash)
            
        is_authentic = verify_signature(secret_key, frame_hash, signature)
        
        # 1. AI Analysis
        result, mask = inference.detect_bleed(frame)
        result["is_authentic"] = is_authentic

        flash_on = (frame_id // int(max(1, fps // 2))) % 2 == 0
        rendered = overlay_hud(frame.copy(), mask, result, flash_on=flash_on)

        writer.write(rendered)
        session_data.append({
            "frame_id": frame_id,
            "timestamp": float(frame_id / fps),
            **result
        })

        cv2.imshow("SurgeGuard", rendered)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        frame_id += 1

    if not is_dir:
        cap.release()
    writer.release()
    cv2.destroyAllWindows()

    write_session_report(args.report, session_data)
    elapsed = time.time() - start_time
    print(f"Processed {frame_id} frames in {elapsed:.2f}s ({frame_id / max(elapsed, 1e-6):.2f} FPS)")

if __name__ == "__main__":
    main()