import os
import cv2
import numpy as np
from pathlib import Path

def generate_masks(dir_clear, dir_bloody, dir_mask, threshold=30):
    """
    Generates binary blood masks by taking the difference between bloody and clear images.
    """
    path_a = Path(dir_clear)
    path_b = Path(dir_bloody)
    path_mask = Path(dir_mask)
    
    path_mask.mkdir(parents=True, exist_ok=True)
    
    if not path_a.exists() or not path_b.exists():
        print(f"Error: Directories not found. {path_a} or {path_b}")
        return

    common_files = set([f.name for f in path_a.iterdir() if f.is_file()]).intersection(
                   set([f.name for f in path_b.iterdir() if f.is_file()]))
                   
    print(f"Found {len(common_files)} pairs for mask generation.")
    
    for filename in common_files:
        img_a = cv2.imread(str(path_a / filename)) # Clear
        img_b = cv2.imread(str(path_b / filename)) # Bloody
        
        if img_a is None or img_b is None:
            continue
            
        # Absolute difference
        diff = cv2.absdiff(img_b, img_a)
        
        # Convert difference to grayscale
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Threshold to create binary mask
        _, mask = cv2.threshold(gray_diff, threshold, 255, cv2.THRESH_BINARY)
        
        # Optional: Morphological operations to clean up noise
        kernel = np.ones((3,3), np.uint8)
        mask_cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask_cleaned = cv2.morphologyEx(mask_cleaned, cv2.MORPH_CLOSE, kernel)
        
        cv2.imwrite(str(path_mask / filename), mask_cleaned)
        
    print(f"Mask generation complete. Saved to {dir_mask}")

if __name__ == "__main__":
    clear_dir = "SurgicalBlender/DeBlood_DeSmoke/data/trainA"
    bloody_dir = "SurgicalBlender/DeBlood_DeSmoke/data/trainB"
    mask_dir = "SurgicalBlender/DeBlood_DeSmoke/data/trainMask"
    generate_masks(clear_dir, bloody_dir, mask_dir)
