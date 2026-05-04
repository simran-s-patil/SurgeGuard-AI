import cv2
import numpy as np
from pathlib import Path

def create_surgical_twin(bg_path, mask_path, out_path, blood_color=(0, 0, 139), alpha=0.6):
    """
    Overlays a blood mask onto a healthy background image.
    blood_color is BGR, default is Dark Red (0, 0, 139).
    """
    if not Path(bg_path).exists() or not Path(mask_path).exists():
        print("Error: Background or Mask image not found.")
        return

    bg_img = cv2.imread(bg_path)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

    if bg_img is None or mask is None:
        print("Error: Could not read images.")
        return

    # Resize mask to match background if necessary
    if bg_img.shape[:2] != mask.shape[:2]:
        print("Resizing mask to match background dimensions.")
        mask = cv2.resize(mask, (bg_img.shape[1], bg_img.shape[0]), interpolation=cv2.INTER_NEAREST)

    # Create a colored overlay for the blood
    blood_overlay = np.zeros_like(bg_img)
    blood_overlay[:] = blood_color

    # Normalize mask to 0-1 for blending
    mask_normalized = mask.astype(float) / 255.0
    
    # Expand dims so we can broadcast the multiplication over the 3 color channels
    mask_normalized = np.expand_dims(mask_normalized, axis=-1)

    # Blend: (1 - alpha * mask) * bg + (alpha * mask) * blood_color
    blended = bg_img * (1 - alpha * mask_normalized) + blood_overlay * (alpha * mask_normalized)
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(out_path, blended)
    print(f"Surgical Twin image saved to {out_path}")

if __name__ == "__main__":
    # Example usage
    bg_path = "healthy_bg.png"
    mask_path = "SurgicalBlender/DeBlood_DeSmoke/data/trainMask/img_001.png"
    out_path = "SurgicalBlender/DeBlood_DeSmoke/data/semi_synthetic/twin_001.png"
    create_surgical_twin(bg_path, mask_path, out_path)
    print("Surgical Twin script ready. Call create_surgical_twin() with appropriate paths.")
