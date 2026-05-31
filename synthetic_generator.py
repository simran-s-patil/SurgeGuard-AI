import os
import cv2
import random
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def process_mask_image(mask_img):
    """
    Converts a generated blood image (on black background) to a pure blood layer and an alpha mask.
    """
    gray = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)
    # The brighter the pixel, the more opaque it is. We can use gray as the alpha.
    alpha = np.clip(gray * 1.5, 0, 255).astype(np.uint8)
    return mask_img, alpha

def simple_augment_blood_mask(blood_rgb, blood_alpha):
    """
    Simple augmentation without albumentations
    """
    # Random rotation
    angle = random.uniform(-180, 180)
    rows, cols = blood_rgb.shape[:2]
    M = cv2.getRotationMatrix2D((cols/2, rows/2), angle, 1)
    blood_rgb = cv2.warpAffine(blood_rgb, M, (cols, rows), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    blood_alpha = cv2.warpAffine(blood_alpha, M, (cols, rows), borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    # Random flip
    if random.random() > 0.5:
        blood_rgb = cv2.flip(blood_rgb, 1)
        blood_alpha = cv2.flip(blood_alpha, 1)
    if random.random() > 0.5:
        blood_rgb = cv2.flip(blood_rgb, 0)
        blood_alpha = cv2.flip(blood_alpha, 0)

    # Random scale
    scale = random.uniform(0.5, 1.5)
    new_size = (int(cols * scale), int(rows * scale))
    blood_rgb = cv2.resize(blood_rgb, new_size, interpolation=cv2.INTER_LINEAR)
    blood_alpha = cv2.resize(blood_alpha, new_size, interpolation=cv2.INTER_LINEAR)

    # Pad back to original size
    if scale < 1.0:
        pad_x = (cols - new_size[0]) // 2
        pad_y = (rows - new_size[1]) // 2
        blood_rgb = cv2.copyMakeBorder(blood_rgb, pad_y, rows - new_size[1] - pad_y,
                                      pad_x, cols - new_size[0] - pad_x, cv2.BORDER_CONSTANT, value=0)
        blood_alpha = cv2.copyMakeBorder(blood_alpha, pad_y, rows - new_size[1] - pad_y,
                                        pad_x, cols - new_size[0] - pad_x, cv2.BORDER_CONSTANT, value=0)
    else:
        blood_rgb = cv2.resize(blood_rgb, (cols, rows), interpolation=cv2.INTER_LINEAR)
        blood_alpha = cv2.resize(blood_alpha, (cols, rows), interpolation=cv2.INTER_LINEAR)

    return blood_rgb, blood_alpha

def generate_vitals(twin_id, out_list, bleed_minute=3):
    """
    Generates 600 rows (10 mins) of vitals.
    Bleeding starts at `bleed_minute`.
    Base HR = ~70, Base BP = 120/80.
    40% HR increase = 98. 25% BP drop = 90/60.
    """
    base_hr = random.randint(65, 75)
    base_sys = random.randint(115, 125)
    base_dia = random.randint(75, 85)

    target_hr = base_hr * 1.40
    target_sys = base_sys * 0.75
    target_dia = base_dia * 0.75

    # Calculate per-second step once bleeding starts (remaining seconds)
    bleed_start_sec = bleed_minute * 60
    remaining_secs = 600 - bleed_start_sec

    hr_step = (target_hr - base_hr) / remaining_secs if remaining_secs > 0 else 0
    sys_step = (base_sys - target_sys) / remaining_secs if remaining_secs > 0 else 0
    dia_step = (base_dia - target_dia) / remaining_secs if remaining_secs > 0 else 0

    curr_hr = float(base_hr)
    curr_sys = float(base_sys)
    curr_dia = float(base_dia)

    for sec in range(600):
        is_bleeding = 1 if sec < 600 and sec >= bleed_start_sec else 0

        if is_bleeding:
            curr_hr += hr_step
            curr_sys -= sys_step
            curr_dia -= dia_step

        # Add slight natural noise
        noise_hr = random.uniform(-1, 1)
        noise_bp = random.uniform(-2, 2)

        out_list.append({
            "twin_id": twin_id,
            "second": sec,
            "heart_rate": round(curr_hr + noise_hr, 1),
            "systolic_bp": round(curr_sys + noise_bp, 1),
            "diastolic_bp": round(curr_dia + noise_bp, 1),
            "is_bleeding": is_bleeding
        })

def main(num_samples=1000):
    clean_dir = Path("seed_data/clean")
    mask_dir = Path("seed_data/masks")

    out_img_dir = Path("output/images")
    out_gt_dir = Path("output/ground_truth")

    out_img_dir.mkdir(parents=True, exist_ok=True)
    out_gt_dir.mkdir(parents=True, exist_ok=True)

    clean_files = list(clean_dir.glob("*.png"))
    mask_files = list(mask_dir.glob("*.png"))

    if not clean_files or not mask_files:
        print("Missing seed data in seed_data/clean or seed_data/masks.")
        return

    print(f"Loaded {len(clean_files)} clean bases and {len(mask_files)} mask bases.")

    vitals_data = []

    for i in tqdm(range(num_samples), desc="Generating Twins"):
        twin_id = f"twin_{i:04d}"
        is_negative = random.random() < 0.2 # 20% chance of negative sample (no blood)

        # 1. Random Selection
        clean_path = random.choice(clean_files)
        clean_img = cv2.imread(str(clean_path))
        clean_img = cv2.resize(clean_img, (512, 512))

        if is_negative:
            # Negative sample: just the clean image, black mask
            blended = clean_img
            gt_mask = np.zeros((512, 512), dtype=np.uint8)
        else:
            # Positive sample: blend with blood
            mask_path = random.choice(mask_files)
            raw_mask_img = cv2.imread(str(mask_path))
            raw_mask_img = cv2.resize(raw_mask_img, (512, 512))

            # Extract RGB blood and alpha from the black-background image
            blood_rgb, blood_alpha = process_mask_image(raw_mask_img)

            # Simple augmentation instead of albumentations
            aug_blood, aug_alpha = simple_augment_blood_mask(blood_rgb, blood_alpha)

            # Random Opacity scaling (0.4 to 0.8)
            opacity = random.uniform(0.4, 0.8)

            # Normalize alpha to 0-1 range and apply opacity factor
            alpha_norm = (aug_alpha.astype(float) / 255.0) * opacity
            alpha_norm = np.expand_dims(alpha_norm, axis=-1)

            # Blend
            blended = clean_img * (1 - alpha_norm) + aug_blood * alpha_norm
            blended = np.clip(blended, 0, 255).astype(np.uint8)

            # Ground Truth Mask (binary)
            _, gt_mask = cv2.threshold(aug_alpha, 30, 255, cv2.THRESH_BINARY)

        # Save Outputs
        cv2.imwrite(str(out_img_dir / f"{twin_id}.png"), blended)
        cv2.imwrite(str(out_gt_dir / f"{twin_id}.png"), gt_mask)

        # Generate Vitals (bleeding starts later for positives, stays base for negatives)
        generate_vitals(twin_id, vitals_data, bleed_minute=3 if not is_negative else 10)

    # Save Vitals
    df = pd.DataFrame(vitals_data)
    df.to_csv("output/vitals.csv", index=False)
    print(f"\nSuccessfully generated {num_samples} twins and saved vitals.csv to output/")

if __name__ == "__main__":
    import sys
    num = 100
    if len(sys.argv) > 1:
        num = int(sys.argv[1])
    main(num_samples=num)
