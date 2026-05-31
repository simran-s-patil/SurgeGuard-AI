import os
import cv2
import json
import time
import base64
import asyncio
import torch
import numpy as np
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Import local modules
from train_segmentation import UNet
from phase3_cyber import sign_hash, generate_secret_key, compute_frame_hash, embed_watermark
from surgeguard_inference import overlay_hud
from phase2_aiml import UNetGradCAM, overlay_gradcam

app = FastAPI()

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Load AI Model
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "models/unet_surgeguard.pth"
model = UNet().to(DEVICE)
if os.path.exists(MODEL_PATH):
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
model.eval()

# Initialize Grad-CAM
grad_cam = UNetGradCAM(model, target_layer_name='u2')

SECRET_KEY = generate_secret_key()

@app.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "filename": file.filename,
        "video_path": str(file_path)
    }

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Initial config from client
        data = await websocket.receive_text()
        config = json.loads(data)
        video_path = config.get("video_path")
        attack_mode = config.get("attack_mode", False)
        epsilon = config.get("epsilon", 1.0)

        if not video_path or not os.path.exists(video_path):
            await websocket.send_json({"error": "Video file not found"})
            await websocket.close()
            return

        cap = cv2.VideoCapture(video_path)
        frame_id = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            start_time = time.time()
            
            # AI Inference
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_input = cv2.resize(img_rgb, (128, 128)).astype(np.float32) / 255.0
            img_tensor = torch.tensor(img_input).permute(2, 0, 1).unsqueeze(0).to(DEVICE)
            
            # Generate Heatmap and Prediction
            heatmap, prob = grad_cam.generate_heatmap(img_tensor)
            
            mask = (prob > 0.5).astype(np.uint8)
            risk_score = float(np.max(prob))
            
            # Centroid of the bleed area
            coords = np.column_stack(np.where(mask > 0))
            centroid = [float(np.mean(coords[:, 1])), float(np.mean(coords[:, 0]))] if len(coords) > 0 else [0.0, 0.0]

            # Security Check (Simulation for Demo)
            temp_frame_path = f"temp_frame_{frame_id}.png"
            cv2.imwrite(temp_frame_path, frame)
            f_hash = compute_frame_hash(temp_frame_path)
            signature = sign_hash(SECRET_KEY, f_hash)
            os.remove(temp_frame_path)

            # Adversarial Attack Simulation
            is_attack = False
            if attack_mode:
                is_attack = True if epsilon > 0.5 else False

            # HUD Overlay
            hud_result = {
                'risk_score': risk_score,
                'center_coordinates': [int(centroid[0]), int(centroid[1])],
                'alert_level': 'CRITICAL' if risk_score > 0.5 else 'NORMAL',
                'is_authentic': not is_attack
            }

            rendered = overlay_hud(
                frame.copy(),
                cv2.resize(mask, (frame.shape[1], frame.shape[0])),
                hud_result,
                flash_on=(frame_id % 20) < 10,
                security_status=not is_attack
            )

            # Encode main frame
            _, buffer = cv2.imencode('.jpg', rendered)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            # Encode standalone heatmap
            heatmap_img = overlay_gradcam(frame.copy(), heatmap)
            _, h_buffer = cv2.imencode('.jpg', heatmap_img)
            heatmap_base64 = base64.b64encode(h_buffer).decode('utf-8')

            # Vitals Simulation
            vitals = {
                "heart_rate": 70 + int(risk_score * 40) + np.random.randint(-2, 2),
                "systolic_bp": 110 + int(risk_score * 30) + np.random.randint(-3, 3),
                "respiratory_rate": 14 + int(risk_score * 10) + np.random.randint(-1, 1)
            }

            payload = {
                "frame_base64": frame_base64,
                "heatmap_base64": heatmap_base64,
                "risk_score": risk_score,
                "is_bleeding": risk_score > 0.5,
                "centroid": centroid,
                "security_status": {
                    "adversarial_attack": is_attack,
                    "integrity_score": 0 if is_attack else 100,
                    "signature": signature
                },
                "anonymized_vitals": vitals,
                "processing_latency_ms": int((time.time() - start_time) * 1000)
            }

            await websocket.send_json(payload)
            frame_id += 1
            
            # Control frame rate
            await asyncio.sleep(0.03) 

        cap.release()
        await websocket.close()

    except Exception as e:
        print(f"WebSocket Error: {e}")
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
