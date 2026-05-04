import cv2
import hashlib
from pathlib import Path
import json

def compute_frame_hash(img_path):
    """
    Computes a SHA-256 hash for the given image file.
    Ensures video stream integrity.
    """
    if not Path(img_path).exists():
        return None
        
    sha256 = hashlib.sha256()
    with open(img_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def sanitize_input(img_path, out_path):
    """
    Applies median blur to neutralize high-frequency noise from FGSM adversarial attacks.
    """
    img = cv2.imread(img_path)
    if img is None:
        print("Image not found.")
        return False
        
    # Median blur is highly effective against salt-and-pepper / sign-gradient noise
    sanitized = cv2.medianBlur(img, 3)
    cv2.imwrite(out_path, sanitized)
    return True

if __name__ == "__main__":
    test_img = "output/adversarial/hacked_twin_0000.png"
    out_sanitized = "output/adversarial/sanitized_twin_0000.png"
    
    # 1. Hashing
    original_hash = compute_frame_hash("output/images/twin_0000.png")
    hacked_hash = compute_frame_hash(test_img)
    print(f"Original Hash: {original_hash}")
    print(f"Hacked Hash:   {hacked_hash}")
    print(f"Integrity Valid: {original_hash == hacked_hash}")
    
    # 2. Sanitization
    success = sanitize_input(test_img, out_sanitized)
    if success:
        print(f"Sanitized frame saved to {out_sanitized}")
