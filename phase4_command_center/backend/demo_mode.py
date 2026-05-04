import numpy as np
import cv2


def inject_fgsm_noise(frame, epsilon=0.03):
    """Simulate a fast gradient sign adversarial perturbation on a surgical frame."""
    image = frame.astype(np.float32) / 255.0
    gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    gradient_sign = np.sign(gx + gy)[:, :, None]
    perturbed = image + epsilon * gradient_sign
    perturbed = np.clip(perturbed, 0.0, 1.0)
    return (perturbed * 255.0).astype(np.uint8)


def create_attack_video(input_path, output_path, frames_to_attack=100):
    cap = cv2.VideoCapture(str(input_path))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    frame_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id < frames_to_attack:
            frame = inject_fgsm_noise(frame, epsilon=0.04)
        writer.write(frame)
        frame_id += 1

    cap.release()
    writer.release()
    return output_path
