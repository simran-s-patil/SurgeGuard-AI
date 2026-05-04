import os
import cv2
import albumentations as A
from pathlib import Path

def augment_data(dir_img, dir_mask, out_img, out_mask, num_variations=5):
    """
    Applies simultaneous augmentation to images and their masks.
    """
    path_img = Path(dir_img)
    path_mask = Path(dir_mask)
    path_out_img = Path(out_img)
    path_out_mask = Path(out_mask)
    
    path_out_img.mkdir(parents=True, exist_ok=True)
    path_out_mask.mkdir(parents=True, exist_ok=True)
    
    if not path_img.exists() or not path_mask.exists():
        print(f"Error: Directories not found. {path_img} or {path_mask}")
        return

    # Define the augmentation pipeline
    transform = A.Compose([
        A.Rotate(limit=30, p=0.7),
        A.HorizontalFlip(p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.8),
        A.GaussNoise(var_limit=(10.0, 50.0), p=0.5)
    ])
    
    files = [f.name for f in path_img.iterdir() if f.is_file()]
    print(f"Found {len(files)} images to augment.")
    
    for filename in files:
        img_path = str(path_img / filename)
        mask_path = str(path_mask / filename)
        
        if not Path(mask_path).exists():
            continue
            
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Albumentations expects RGB
        
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        
        if img is None or mask is None:
            continue
            
        # Save original as variation 0 (optional, but good for completeness)
        base_name = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        
        for i in range(num_variations):
            augmented = transform(image=img, mask=mask)
            aug_img = augmented['image']
            aug_mask = augmented['mask']
            
            aug_img_bgr = cv2.cvtColor(aug_img, cv2.COLOR_RGB2BGR)
            
            out_filename = f"{base_name}_aug_{i}{ext}"
            cv2.imwrite(str(path_out_img / out_filename), aug_img_bgr)
            cv2.imwrite(str(path_out_mask / out_filename), aug_mask)
            
    print(f"Augmentation complete. Saved {num_variations} variations per image to {out_img} and {out_mask}")

if __name__ == "__main__":
    img_dir = "SurgicalBlender/DeBlood_DeSmoke/data/trainB"
    mask_dir = "SurgicalBlender/DeBlood_DeSmoke/data/trainMask"
    out_img_dir = "SurgicalBlender/DeBlood_DeSmoke/data/augmented/trainB"
    out_mask_dir = "SurgicalBlender/DeBlood_DeSmoke/data/augmented/trainMask"
    
    augment_data(img_dir, mask_dir, out_img_dir, out_mask_dir)
