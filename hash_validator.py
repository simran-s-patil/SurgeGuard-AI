import hashlib
import cv2
import pandas as pd
from pathlib import Path
import json
import numpy as np

def compute_frame_hash(image_path):
    """
    Compute SHA-256 hash of an image frame
    """
    image = cv2.imread(str(image_path))
    if image is None:
        return None

    # Convert to bytes
    image_bytes = image.tobytes()

    # Compute hash
    hash_obj = hashlib.sha256(image_bytes)
    return hash_obj.hexdigest()

def validate_video_stream(image_dir, expected_hashes=None):
    """
    Validate a stream of images against expected hashes
    """
    image_dir = Path(image_dir)
    if not image_dir.exists():
        print(f"Image directory {image_dir} not found.")
        return False

    image_files = sorted(list(image_dir.glob("*.png")))
    current_hashes = {}

    tampered_frames = []

    for img_path in image_files:
        hash_val = compute_frame_hash(img_path)
        if hash_val:
            current_hashes[img_path.name] = hash_val

            if expected_hashes and img_path.name in expected_hashes:
                if hash_val != expected_hashes[img_path.name]:
                    tampered_frames.append(img_path.name)

    # Save current hashes
    with open('frame_hashes.json', 'w') as f:
        json.dump(current_hashes, f, indent=2)

    if expected_hashes:
        integrity_score = 1.0 - (len(tampered_frames) / len(image_files))
        print(f"Integrity Score: {integrity_score:.4f}")
        print(f"Tampered frames: {tampered_frames}")

        return len(tampered_frames) == 0
    else:
        print("Hash validation baseline created. Run again with expected_hashes to validate.")
        return True

def detect_anomalies(image_dir, baseline_stats=None):
    """
    Detect anomalies in frame statistics (simple tampering detection)
    """
    image_dir = Path(image_dir)
    image_files = sorted(list(image_dir.glob("*.png")))

    anomalies = []

    for img_path in image_files:
        image = cv2.imread(str(img_path))
        if image is None:
            continue

        # Compute simple statistics
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_val = np.mean(gray)
        std_val = np.std(gray)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()

        stats = {
            'mean': mean_val,
            'std': std_val,
            'hist_entropy': -np.sum(hist * np.log2(hist + 1e-10))
        }

        if baseline_stats:
            # Check for anomalies (simple threshold-based)
            if abs(stats['mean'] - baseline_stats['mean']) > 10 or \
               abs(stats['std'] - baseline_stats['std']) > 5:
                anomalies.append(img_path.name)

    if baseline_stats:
        print(f"Anomalous frames detected: {anomalies}")
    else:
        # Compute baseline
        all_stats = []
        for img_path in image_files[:100]:  # Use first 100 for baseline
            image = cv2.imread(str(img_path))
            if image is None:
                continue
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            all_stats.append({
                'mean': np.mean(gray),
                'std': np.std(gray)
            })

        baseline_stats = {
            'mean': np.mean([s['mean'] for s in all_stats]),
            'std': np.mean([s['std'] for s in all_stats])
        }

        with open('baseline_stats.json', 'w') as f:
            json.dump(baseline_stats, f, indent=2)

        print("Baseline statistics saved.")

    return anomalies

if __name__ == "__main__":
    image_dir = "output/images"

    # First run: create baseline
    print("Creating hash baseline...")
    validate_video_stream(image_dir)

    print("Creating statistical baseline...")
    detect_anomalies(image_dir)

    # To validate against baseline, load and pass expected_hashes
    # Example:
    # with open('frame_hashes.json', 'r') as f:
    #     expected_hashes = json.load(f)
    # is_valid = validate_video_stream(image_dir, expected_hashes)</content>
<parameter name="filePath">e:\BTech CS with AI\OvernightHackathonDhi\hash_validator.py