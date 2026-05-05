import argparse
import threading
import queue
import cv2
import torch
import numpy as np
import json
import traceback
from pathlib import Path
from collections import deque
import time

from train_segmentation import UNet
from inference_visualizer import GradCAM
from security.input_validator import (
    spatial_frequency_denoise,
    FrameIntegrityMonitor,
)
from security.privacy_shield import PrivacyWrapper
from security.output_protector import (
    sign_payload,
    encrypt_packet,
    authorize_role,
    DEFAULT_PRIVATE_SECRET,
)

class TemporalSmoother:
    """Temporal filter to prevent flickering alerts."""
    def __init__(self, window_size=5, threshold=0.7):
        self.window = deque(maxlen=window_size)
        self.threshold = threshold

    def update(self, risk_score):
        self.window.append(risk_score)
        smoothed = np.mean(self.window)
        return smoothed > self.threshold


class ConfirmationBuffer:
    """Confirm persistent bleed across consecutive frames."""
    def __init__(self, required_frames=3, growth_threshold=0.05):
        self.required_frames = required_frames
        self.growth_threshold = growth_threshold
        self.history = deque(maxlen=required_frames)

    def update(self, risk_score, area):
        self.history.append((risk_score, area))
        if len(self.history) < self.required_frames:
            return False

        growing = True
        prev_area = self.history[0][1]
        for _, current_area in list(self.history)[1:]:
            if current_area < prev_area * (1 - self.growth_threshold):
                growing = False
                break
            prev_area = current_area

        return growing and all(r > 0.5 for r, _ in self.history)


class SurgeGuardInference:
    def __init__(self, model_path, use_torchscript=False):
        self.device = torch.device('cpu')
        self.use_torchscript = use_torchscript

        if use_torchscript:
            self.model = torch.jit.load(model_path)
        else:
            self.model = UNet().to(self.device)
            self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
            self.grad_cam = GradCAM(self.model, self.model.out)

        self.model.eval()
        self.smoother = TemporalSmoother()
        self.confirmation_buffer = ConfirmationBuffer(required_frames=4, growth_threshold=0.1)
        self.prev_mask = None
    
    def preprocess_image(self, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (128, 128))
        img_tensor = torch.tensor(img_resized.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0).to(self.device)
        return img_tensor, img.shape[:2]

    def check_spatial_consistency(self, mask, prev_mask):
        if prev_mask is None:
            return True

        current_area = np.sum(mask > 0.5)
        prev_area = np.sum(prev_mask > 0.5)
        if prev_area == 0:
            return current_area > 0

        if current_area < prev_area * 0.8:
            return False

        contours, _ = cv2.findContours((mask > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            return False
        largest_area = max(cv2.contourArea(c) for c in contours)
        return largest_area >= 100

    def detect_bleed(self, img):
        img_tensor, orig_size = self.preprocess_image(img)
        with torch.no_grad():
            output = self.model(img_tensor)
            prob = torch.sigmoid(output).squeeze().cpu().numpy()

        prob_resized = cv2.resize(prob, (orig_size[1], orig_size[0]))
        is_spatially_consistent = self.check_spatial_consistency(prob_resized, self.prev_mask)
        self.prev_mask = prob_resized.copy()

        risk_score = 0.0 if not is_spatially_consistent else float(np.mean(prob_resized))
        is_bleeding = self.smoother.update(risk_score)
        bleed_area = int(np.count_nonzero(prob_resized > 0.5))
        critical_confirmed = self.confirmation_buffer.update(risk_score, bleed_area)

        if critical_confirmed:
            alert_level = 'CRITICAL'
        elif is_bleeding:
            alert_level = 'WARNING'
        else:
            alert_level = 'NORMAL'

        if risk_score > 0.5:
            coords = cv2.findNonZero((prob_resized > 0.5).astype(np.uint8))
            if coords is not None:
                center = np.mean(coords, axis=0).flatten()
                center_coordinates = [int(center[0]), int(center[1])]
            else:
                center_coordinates = [0, 0]
        else:
            center_coordinates = [0, 0]

        warning_time_seconds = 5.0 if alert_level == 'CRITICAL' else 0.0
        result = {
            'is_bleeding': bool(is_bleeding),
            'risk_score': risk_score,
            'center_coordinates': center_coordinates,
            'warning_time_seconds': warning_time_seconds,
            'alert_level': alert_level,
            'bleed_area': bleed_area,
        }
        return result, prob_resized

def draw_risk_bar(frame, risk_score, bar_width=24, padding=12):
    h, w = frame.shape[:2]
    bar_height = int((h - padding * 2) * min(max(risk_score, 0.0), 1.0))
    top = padding
    left = w - bar_width - padding
    bottom = h - padding
    cv2.rectangle(frame, (left, top), (left + bar_width, bottom), (50, 50, 50), -1)
    cv2.rectangle(frame, (left, bottom - bar_height), (left + bar_width, bottom), (0, 0, 255), -1)
    cv2.rectangle(frame, (left, top), (left + bar_width, bottom), (255, 255, 255), 1)
    cv2.putText(frame, f"{int(risk_score * 100):02d}%", (left - 68, top + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    return frame


<<<<<<< HEAD
def render_fail_safe(frame):
    cv2.putText(frame, "SECURITY BREACH: MANUAL VIEW", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    cv2.putText(frame, "AI OVERLAYS DISABLED", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    cv2.rectangle(frame, (10, 10), (frame.shape[1] - 10, frame.shape[0] - 10), (0, 0, 255), 4)
    return frame


def overlay_hud(frame, mask, result, flash_on=True, security_status=True):
    if not security_status:
        return render_fail_safe(frame)

=======
def overlay_hud(frame, mask, result, flash_on=True):
    h, w = frame.shape[:2]
>>>>>>> d767a1e02a85062eaa52e7730160e7e379879d50
    heatmap = cv2.applyColorMap((mask * 255).astype(np.uint8), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(frame, 0.6, heatmap, 0.4, 0)
    overlay = draw_risk_bar(overlay, result['risk_score'])

    if result['center_coordinates'] != [0, 0]:
        cv2.circle(overlay, tuple(result['center_coordinates']), 10, (0, 255, 255), 2)
    cv2.putText(overlay, f"Risk: {result['risk_score']:.2f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(overlay, f"Level: {result['alert_level']}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

    if result['alert_level'] == 'CRITICAL' and flash_on:
        cv2.putText(overlay, "⚠️ BLEED DETECTED", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        cv2.rectangle(overlay, (15, 100), (500, 140), (0, 0, 255), 2)
<<<<<<< HEAD
=======
    
    # Cybersecurity HUD
    shield_color = (0, 255, 0) if result["is_authentic"] else (0, 0, 255)
    shield_text = "🛡️ SHIELD: ACTIVE" if result["is_authentic"] else "⚠️ ATTACK DETECTED!"
    cv2.putText(overlay, shield_text, (20, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, shield_color, 2)
    
>>>>>>> d767a1e02a85062eaa52e7730160e7e379879d50
    return overlay


def write_session_report(report_path, session_data):
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
    print(f"Session report saved to {report_path}")


class VideoPipeline:
    def __init__(self, input_path, output_path, report_path, model_path, use_torchscript=False, secret_key=DEFAULT_PRIVATE_SECRET):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.report_path = Path(report_path)
        self.secret_key = secret_key
        self.use_torchscript = use_torchscript
        self.inference = SurgeGuardInference(model_path, use_torchscript=use_torchscript)
        self.privacy_wrapper = PrivacyWrapper(epsilon=1.0, sensitivity=1.0)
        self.integrity_monitor = FrameIntegrityMonitor()

        self.raw_queue = queue.Queue(maxsize=8)
        self.validated_queue = queue.Queue(maxsize=8)
        self.result_queue = queue.Queue(maxsize=16)
        self.stop_event = threading.Event()

    def capture_loop(self):
        cap = cv2.VideoCapture(str(self.input_path))
        if not cap.isOpened():
            raise RuntimeError(f"Unable to open video: {self.input_path}")

        frame_id = 0
        try:
            while not self.stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    break
                self.raw_queue.put((frame_id, frame), timeout=1)
                frame_id += 1
        except Exception:
            traceback.print_exc()
        finally:
            self.raw_queue.put(None)
            cap.release()

    def validation_loop(self):
        try:
            while not self.stop_event.is_set():
                item = self.raw_queue.get(timeout=1)
                if item is None:
                    self.validated_queue.put(None)
                    break

                frame_id, frame = item
                try:
                    clean_frame = spatial_frequency_denoise(frame)
                    integrity = self.integrity_monitor.update(clean_frame)
                    tampered = integrity['tampered']
                except Exception:
                    integrity = {'frame_hash': None, 'chain_hash': None, 'tampered': True}
                    tampered = True
                    traceback.print_exc()

                self.validated_queue.put({
                    'frame_id': frame_id,
                    'raw_frame': frame,
                    'clean_frame': clean_frame if not tampered else frame,
                    'integrity': integrity,
                    'tampered': tampered,
                }, timeout=1)
        except Exception:
            traceback.print_exc()
            self.validated_queue.put(None)

    def inference_loop(self):
        try:
            while not self.stop_event.is_set():
                item = self.validated_queue.get(timeout=1)
                if item is None:
                    self.result_queue.put(None)
                    break

                frame_id = item['frame_id']
                raw_frame = item['raw_frame']
                integrity = item['integrity']
                tampered = item['tampered']
                security_status = not tampered

                if tampered:
                    decision_packet = {
                        'frame_id': frame_id,
                        'timestamp': float(frame_id),
                        'integrity_status': 'BREACH',
                        'privacy_epsilon': self.privacy_wrapper.epsilon,
                    }
                    encrypted = encrypt_packet(decision_packet, secret_key=self.secret_key)
                    self.result_queue.put({
                        'frame_id': frame_id,
                        'raw_frame': raw_frame,
                        'security_status': False,
                        'encrypted_packet': encrypted,
                        'signature': sign_payload(decision_packet, private_secret=self.secret_key),
                    }, timeout=1)
                    continue

                try:
                    result, mask = self.inference.detect_bleed(item['clean_frame'])
                    decision_packet = {
                        'frame_id': frame_id,
                        'timestamp': float(frame_id),
                        'is_bleeding': result['is_bleeding'],
                        'risk_score': result['risk_score'],
                        'center_coordinates': result['center_coordinates'],
                        'warning_time_seconds': result['warning_time_seconds'],
                        'alert_level': result['alert_level'],
                        'integrity_status': 'OK',
                        'privacy_epsilon': self.privacy_wrapper.epsilon,
                        'frame_hash': integrity['frame_hash'],
                        'chain_hash': integrity['chain_hash'],
                    }
                    encrypted_packet = encrypt_packet(decision_packet, secret_key=self.secret_key)
                    packet_signature = sign_payload(decision_packet, private_secret=self.secret_key)
                except Exception:
                    traceback.print_exc()
                    decision_packet = {
                        'frame_id': frame_id,
                        'timestamp': float(frame_id),
                        'is_bleeding': False,
                        'risk_score': 0.0,
                        'center_coordinates': [0, 0],
                        'warning_time_seconds': 0.0,
                        'alert_level': 'FAIL_SAFE',
                        'integrity_status': 'ERROR',
                        'privacy_epsilon': self.privacy_wrapper.epsilon,
                        'frame_hash': integrity.get('frame_hash'),
                        'chain_hash': integrity.get('chain_hash'),
                    }
                    encrypted_packet = encrypt_packet(decision_packet, secret_key=self.secret_key)
                    packet_signature = sign_payload(decision_packet, private_secret=self.secret_key)

                self.result_queue.put({
                    'frame_id': frame_id,
                    'raw_frame': raw_frame,
                    'security_status': security_status,
                    'result': result,
                    'mask': mask,
                    'encrypted_packet': encrypted_packet,
                    'signature': packet_signature,
                }, timeout=1)
        except Exception:
            traceback.print_exc()
            self.result_queue.put(None)

    def run(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(self.input_path))
        if not cap.isOpened():
            raise RuntimeError(f"Unable to open video: {self.input_path}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        writer = cv2.VideoWriter(str(self.output_path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

        capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        validation_thread = threading.Thread(target=self.validation_loop, daemon=True)
        inference_thread = threading.Thread(target=self.inference_loop, daemon=True)

        capture_thread.start()
        validation_thread.start()
        inference_thread.start()

        session_data = []
        frame_count = 0
        start_time = time.time()

        try:
            while True:
                item = self.result_queue.get(timeout=2)
                if item is None:
                    break

                frame_id = item['frame_id']
                raw_frame = item['raw_frame']
                security_status = item.get('security_status', True)

                if not security_status:
                    rendered = render_fail_safe(raw_frame.copy())
                else:
                    rendered = overlay_hud(
                        raw_frame.copy(),
                        item['mask'],
                        item['result'],
                        flash_on=(frame_id % 20) < 10,
                        security_status=True,
                    )

                writer.write(rendered)
                session_data.append({
                    'frame_id': frame_id,
                    'encrypted_decision_packet': item['encrypted_packet'],
                    'signature': item['signature'],
                })

                cv2.imshow('SurgeGuard', rendered)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                frame_count += 1
        except queue.Empty:
            print('Result queue timed out; terminating.')
        except Exception:
            traceback.print_exc()
        finally:
            self.stop_event.set()
            writer.release()
            cv2.destroyAllWindows()
            write_session_report(self.report_path, session_data)
            elapsed = time.time() - start_time
            print(f"Processed {frame_count} frames in {elapsed:.2f}s ({frame_count / max(elapsed, 1e-6):.2f} FPS)")
            print(f"SURGEON RBAC ack allowed: {authorize_role('SURGEON', 'ACK_BLEED_ALERT')}")


def main():
<<<<<<< HEAD
    parser = argparse.ArgumentParser(description='SurgeGuard threaded video inference with decision packet encryption')
    parser.add_argument('--input', required=True, help='Path to input video file (.mp4, .avi)')
    parser.add_argument('--model', default='models/unet_surgeguard.pt', help='Path to TorchScript or PyTorch model')
    parser.add_argument('--output', default='output/session_video.mp4', help='Path to output video file')
    parser.add_argument('--report', default='output/session_report.json', help='Path to JSON session report')
    parser.add_argument('--use_torchscript', action='store_true', help='Load a TorchScript model for faster inference')
    parser.add_argument('--secret-key', default=DEFAULT_PRIVATE_SECRET, help='Secret key for packet encryption and signing')
    args = parser.parse_args()

    pipeline = VideoPipeline(
        input_path=args.input,
        output_path=args.output,
        report_path=args.report,
        model_path=args.model,
        use_torchscript=args.use_torchscript,
        secret_key=args.secret_key,
    )
    pipeline.run()
=======
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
>>>>>>> d767a1e02a85062eaa52e7730160e7e379879d50


<<<<<<< HEAD
if __name__ == '__main__':
=======
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
>>>>>>> d767a1e02a85062eaa52e7730160e7e379879d50
    main()